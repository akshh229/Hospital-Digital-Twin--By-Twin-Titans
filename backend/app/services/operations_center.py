"""Hospital digital twin operations services."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.alerts import PatientAlert
from app.services.alert_engine import process_vitals_for_alerts
from app.services.ops_store import (
    append_simulation_event,
    get_simulation_events,
    get_simulation_state,
    reset_simulation_state,
    update_simulation_state,
)
from app.services.recovery_projection import RECOVERY_CTES, hydrate_name_fields
from app.services.telemetry_writer import insert_clean_sample


PATIENT_OPERATIONS_QUERY = text(
    RECOVERY_CTES
    + """
    SELECT
        pa.patient_id,
        pa.patient_raw_id,
        pa.parity_flag,
        rd.name_cipher,
        rd.age,
        rd.ward,
        latest_vitals.bpm AS last_bpm,
        latest_vitals.oxygen AS last_oxygen,
        latest_vitals.timestamp AS last_vitals_timestamp,
        latest_vitals.quality_flag,
        COALESCE(presc_count.cnt, 0) AS prescription_count,
        EXISTS(
            SELECT 1 FROM patient_alerts
            WHERE patient_alerts.patient_id = pa.patient_id
              AND status = 'open'
        ) AS has_active_alert
    FROM patient_alias pa
    LEFT JOIN recovered_demographics rd
      ON rd.patient_raw_id = pa.patient_raw_id
     AND rd.parity_flag = pa.parity_flag
    LEFT JOIN LATERAL (
        SELECT bpm, oxygen, timestamp, quality_flag
        FROM resolved_telemetry rt
        WHERE rt.patient_raw_id = pa.patient_raw_id
          AND rt.resolved_parity = pa.parity_flag
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
    ) latest_vitals ON true
    LEFT JOIN (
        SELECT cp.patient_raw_id, rd_inner.parity_flag, COUNT(*) AS cnt
        FROM clean_prescriptions cp
        JOIN recovered_demographics rd_inner
          ON rd_inner.patient_raw_id = cp.patient_raw_id
         AND rd_inner.age = cp.age
        GROUP BY cp.patient_raw_id, rd_inner.parity_flag
    ) presc_count
      ON presc_count.patient_raw_id = pa.patient_raw_id
     AND presc_count.parity_flag = pa.parity_flag
    ORDER BY pa.patient_raw_id ASC, pa.parity_flag ASC
"""
)


ALERT_TIMELINE_QUERY = text(
    RECOVERY_CTES
    + """
    SELECT
        pa.id,
        pa.patient_id,
        pa.opened_at,
        pa.last_bpm,
        pa.last_oxygen,
        rd.name_cipher AS patient_name_cipher
    FROM patient_alerts pa
    LEFT JOIN patient_alias paa ON pa.patient_id = paa.patient_id
    LEFT JOIN recovered_demographics rd
      ON rd.patient_raw_id = paa.patient_raw_id
     AND rd.parity_flag = paa.parity_flag
    WHERE pa.status = 'open'
    ORDER BY pa.opened_at DESC
    LIMIT 6
"""
)


def _clamp(value: float, minimum: int, maximum: int) -> int:
    return int(max(minimum, min(maximum, round(value))))


def _response_id(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return _utcnow()
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return _utcnow()


def _load_patients(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(PATIENT_OPERATIONS_QUERY).mappings().all()
    hydrated = hydrate_name_fields(
        [dict(row) for row in rows],
        cipher_key="name_cipher",
        output_key="name",
    )

    patients: list[dict[str, Any]] = []
    for patient in hydrated:
        timestamp = patient.get("last_vitals_timestamp")
        if timestamp is not None and not isinstance(timestamp, str):
            patient["last_vitals_timestamp"] = timestamp.isoformat()
        patient["has_active_alert"] = bool(patient.get("has_active_alert"))
        patients.append(patient)
    return patients


def calculate_risk_score(patient: dict[str, Any], crisis_level: int = 0) -> int:
    """Generate an operational risk score from live vitals and alert state."""

    bpm = patient.get("last_bpm")
    oxygen = patient.get("last_oxygen")
    score = 12

    if bpm is None:
        score += 8
    elif bpm < 50:
        score += 34
    elif bpm < settings.ALERT_BPM_LOW:
        score += 22
    elif bpm > 135:
        score += 34
    elif bpm > 110:
        score += 24
    elif bpm > settings.ALERT_BPM_HIGH:
        score += 12

    if oxygen is None:
        score += 8
    elif oxygen < 85:
        score += 34
    elif oxygen < 90:
        score += 24
    elif oxygen < 94:
        score += 12

    if patient.get("has_active_alert"):
        score += 22

    score += min(patient.get("prescription_count", 0), 5) * 2
    score += crisis_level * 6

    return _clamp(score, 5, 100)


def classify_risk(score: int) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Guarded"
    return "Stable"


def recommend_unit(score: int) -> str:
    if score >= 75:
        return "ICU"
    if score >= 45:
        return "Step-down"
    return "Observation"


def _build_risk_reasons(patient: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    bpm = patient.get("last_bpm")
    oxygen = patient.get("last_oxygen")
    prescription_count = int(patient.get("prescription_count", 0) or 0)

    if patient.get("has_active_alert"):
        reasons.append("Open telemetry alert requires immediate review.")

    if oxygen is None:
        reasons.append("No recent oxygen sample is available.")
    elif oxygen < 85:
        reasons.append(f"Severe oxygen drop with SpO2 at {oxygen}%.")
    elif oxygen < 90:
        reasons.append(f"Low oxygen reserve with SpO2 at {oxygen}%.")
    elif oxygen < 94:
        reasons.append(f"Borderline oxygen reserve with SpO2 at {oxygen}%.")

    if bpm is None:
        reasons.append("No recent heart-rate sample is available.")
    elif bpm < 50:
        reasons.append(f"Bradycardic trend at {bpm} BPM.")
    elif bpm < settings.ALERT_BPM_LOW:
        reasons.append(f"Low heart rate at {bpm} BPM.")
    elif bpm > 135:
        reasons.append(f"Severe tachycardia at {bpm} BPM.")
    elif bpm > 110:
        reasons.append(f"Elevated heart rate at {bpm} BPM.")
    elif bpm > settings.ALERT_BPM_HIGH:
        reasons.append(f"Borderline tachycardia at {bpm} BPM.")

    if prescription_count >= 4:
        reasons.append("High medication coordination load increases bedside complexity.")
    elif prescription_count >= 2 and patient.get("has_active_alert"):
        reasons.append("Active medications add coordination pressure during escalation.")

    if not reasons:
        reasons.append("Stable vitals with no open telemetry breach.")

    return reasons[:3]


def _build_active_interventions(state: dict[str, Any]) -> list[dict[str, Any]]:
    interventions: list[dict[str, Any]] = []

    surge_bed_bonus = int(state.get("surge_bed_bonus", 0) or 0)
    oxygen_reserve_bonus = int(state.get("oxygen_reserve_bonus", 0) or 0)
    staffing_support_bonus = int(state.get("staffing_support_bonus", 0) or 0)

    if surge_bed_bonus > 0:
        interventions.append(
            {
                "id": "open-surge-beds",
                "label": "Surge beds active",
                "value": f"+{surge_bed_bonus} beds",
                "effect": "Expanded live ICU capacity to absorb overflow demand.",
            }
        )

    if oxygen_reserve_bonus > 0:
        interventions.append(
            {
                "id": "protect-oxygen-reserve",
                "label": "Oxygen reserve buffer",
                "value": f"+{oxygen_reserve_bonus}%",
                "effect": "Respiratory reserve support is currently lifting the oxygen network model.",
            }
        )

    if staffing_support_bonus > 0:
        interventions.append(
            {
                "id": "rebalance-nurse-coverage",
                "label": "Staff reinforcement",
                "value": f"+{staffing_support_bonus} staff",
                "effect": "Additional critical care coverage is widening staffing headroom.",
            }
        )

    return interventions


def _decorate_patients(
    patients: list[dict[str, Any]],
    *,
    crisis_level: int,
) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for patient in patients:
        risk_score = calculate_risk_score(patient, crisis_level)
        decorated.append(
            {
                **patient,
                "risk_score": risk_score,
                "risk_label": classify_risk(risk_score),
                "recommended_unit": recommend_unit(risk_score),
                "risk_reasons": _build_risk_reasons(patient),
            }
        )

    decorated.sort(
        key=lambda patient: (
            -patient["risk_score"],
            not patient["has_active_alert"],
            patient.get("last_oxygen") if patient.get("last_oxygen") is not None else 101,
            -(patient.get("last_bpm") or 0),
        )
    )
    return decorated


def _build_bed_heatmap(
    patients: list[dict[str, Any]],
    *,
    virtual_admissions: int,
    surge_bed_bonus: int = 0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    icu_capacity = settings.ICU_BED_CAPACITY + max(surge_bed_bonus, 0)
    occupied = patients[:icu_capacity]
    queue = patients[icu_capacity : icu_capacity + 6]
    total_demand = len(patients) + virtual_admissions
    overflow = max(total_demand - icu_capacity, 0)

    bed_tiles: list[dict[str, Any]] = []
    for index in range(icu_capacity):
        bed_id = f"ICU-{index + 1:02d}"
        zone = "North Pod" if index < icu_capacity / 2 else "South Pod"

        if index < len(occupied):
            patient = occupied[index]
            reason = (
                "Alert escalation routing"
                if patient["has_active_alert"]
                else f"{patient['risk_label']} acuity routing"
            )
            bed_tiles.append(
                {
                    "bed_id": bed_id,
                    "zone": zone,
                    "status": "occupied",
                    "assignment_reason": reason,
                    "patient": {
                        "patient_id": _response_id(patient["patient_id"]),
                        "patient_raw_id": patient["patient_raw_id"],
                        "patient_name": patient.get("name"),
                        "age": patient.get("age"),
                        "ward": patient.get("ward"),
                        "parity_flag": patient["parity_flag"],
                        "last_bpm": patient.get("last_bpm"),
                        "last_oxygen": patient.get("last_oxygen"),
                        "has_active_alert": patient["has_active_alert"],
                        "risk_score": patient["risk_score"],
                        "risk_label": patient["risk_label"],
                        "recommended_unit": patient["recommended_unit"],
                        "risk_reasons": patient["risk_reasons"],
                    },
                }
            )
        else:
            bed_tiles.append(
                {
                    "bed_id": bed_id,
                    "zone": zone,
                    "status": "available",
                    "assignment_reason": "Ready for incoming critical admissions",
                    "patient": None,
                }
            )

    queue_entries = [
        {
            "patient_id": _response_id(patient["patient_id"]),
            "patient_name": patient.get("name"),
            "patient_raw_id": patient["patient_raw_id"],
            "risk_score": patient["risk_score"],
            "risk_label": patient["risk_label"],
            "queue_reason": f"{patient['recommended_unit']} demand exceeds live ICU capacity",
            "recommended_unit": patient["recommended_unit"],
            "risk_reasons": patient["risk_reasons"],
        }
        for patient in queue
    ]
    return bed_tiles, queue_entries, overflow


def _resource_card(
    *,
    resource_key: str,
    label: str,
    subtitle: str,
    available: int,
    capacity: int,
    unit: str,
    status_thresholds: tuple[int, int],
    trend: str,
) -> dict[str, Any]:
    utilization = _clamp((available / capacity) * 100 if capacity else 0, 0, 100)
    warning_at, critical_at = status_thresholds
    status = "normal"
    if utilization <= critical_at:
        status = "critical"
    elif utilization <= warning_at:
        status = "warning"

    return {
        "resource_key": resource_key,
        "label": label,
        "subtitle": subtitle,
        "available": available,
        "capacity": capacity,
        "unit": unit,
        "utilization_percent": utilization,
        "status": status,
        "trend": trend,
    }


def _build_resource_panels(
    patients: list[dict[str, Any]],
    *,
    crisis_level: int,
    speed: float,
    virtual_admissions: int,
    oxygen_reserve_bonus: int = 0,
    staffing_support_bonus: int = 0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    critical = sum(1 for patient in patients if patient["risk_score"] >= 80)
    high = sum(1 for patient in patients if 60 <= patient["risk_score"] < 80)
    guarded = sum(1 for patient in patients if 40 <= patient["risk_score"] < 60)
    occupied = min(len(patients), settings.ICU_BED_CAPACITY)

    oxygen_percent = _clamp(
        100
        - (critical * 8 + high * 4 + guarded * 2 + crisis_level * 7 + virtual_admissions * 3)
        + oxygen_reserve_bonus,
        10,
        100,
    )
    ventilators_available = max(0, 12 - critical - math.ceil(high / 2) - crisis_level)
    nurses_available = max(
        0,
        18 - occupied - critical - math.ceil(guarded / 2) - crisis_level + staffing_support_bonus,
    )
    vasopressor_percent = _clamp(
        100 - (critical * 9 + high * 3 + crisis_level * 8),
        8,
        100,
    )

    cards = [
        _resource_card(
            resource_key="oxygen_network",
            label="Oxygen network",
            subtitle="Central line reserve",
            available=oxygen_percent,
            capacity=100,
            unit="%",
            status_thresholds=(45, 25),
            trend="falling" if crisis_level else "stable",
        ),
        _resource_card(
            resource_key="ventilators",
            label="Ventilator bank",
            subtitle="Available mechanical support units",
            available=ventilators_available,
            capacity=12,
            unit="units",
            status_thresholds=(4, 2),
            trend="falling" if critical else "stable",
        ),
        _resource_card(
            resource_key="critical_care_nurses",
            label="Critical care nurses",
            subtitle="Staffing headroom on shift",
            available=nurses_available,
            capacity=18,
            unit="staff",
            status_thresholds=(6, 3),
            trend="falling" if occupied > 8 else "stable",
        ),
        _resource_card(
            resource_key="vasopressor_stock",
            label="Vasopressor stock",
            subtitle="Estimated medication reserve",
            available=vasopressor_percent,
            capacity=100,
            unit="%",
            status_thresholds=(50, 30),
            trend="falling" if crisis_level else "stable",
        ),
    ]

    forecast: list[dict[str, Any]] = []
    forecast_speed = max(speed, 0.5)
    now = _utcnow()
    for step in range(6):
        degrade = step * forecast_speed
        forecast.append(
            {
                "time_label": (now + timedelta(hours=step * 2)).strftime("%H:%M"),
                "oxygen_network_percent": _clamp(
                    oxygen_percent - degrade * (3 + crisis_level),
                    8,
                    100,
                ),
                "staff_load_percent": _clamp(
                    100 - nurses_available * 4 + degrade * (4 + crisis_level),
                    20,
                    100,
                ),
                "ventilator_usage_percent": _clamp(
                    100 - (ventilators_available / 12) * 100 + degrade * (3 + crisis_level),
                    10,
                    100,
                ),
                "vasopressor_stock_percent": _clamp(
                    vasopressor_percent - degrade * (4 + crisis_level),
                    6,
                    100,
                ),
            }
        )

    return cards, forecast


def _build_operations_trust(
    patients: list[dict[str, Any]],
    *,
    state: dict[str, Any],
) -> dict[str, Any]:
    complete_samples = sum(
        1
        for patient in patients
        if patient.get("last_bpm") is not None and patient.get("last_oxygen") is not None
    )
    timestamps = [
        _parse_timestamp(patient["last_vitals_timestamp"])
        for patient in patients
        if patient.get("last_vitals_timestamp")
    ]

    last_telemetry_at = max(timestamps) if timestamps else None
    telemetry_age_seconds = (
        max(int((_utcnow() - last_telemetry_at).total_seconds()), 0)
        if last_telemetry_at is not None
        else None
    )
    coverage_percent = _clamp(
        (complete_samples / max(len(patients), 1)) * 100,
        0,
        100,
    )

    if state.get("is_paused"):
        telemetry_state = "paused"
    elif telemetry_age_seconds is None or telemetry_age_seconds > int(
        settings.SIMULATOR_INTERVAL_SECONDS * 5
    ):
        telemetry_state = "watch"
    else:
        telemetry_state = "live"

    if telemetry_age_seconds is None:
        confidence_label = "low"
        confidence_reason = "No recent patient telemetry samples are flowing into the command center."
    elif telemetry_age_seconds > int(settings.SIMULATOR_INTERVAL_SECONDS * 8) or coverage_percent < 40:
        confidence_label = "low"
        confidence_reason = (
            f"Telemetry is stale or incomplete; only {coverage_percent}% of patients have a full vitals pair."
        )
    elif telemetry_age_seconds > int(settings.SIMULATOR_INTERVAL_SECONDS * 4) or coverage_percent < 70:
        confidence_label = "medium"
        confidence_reason = (
            f"Telemetry is usable but outside the ideal freshness window with {coverage_percent}% complete coverage."
        )
    else:
        confidence_label = "high"
        confidence_reason = (
            f"Telemetry is current with {coverage_percent}% of patients carrying a fresh vitals pair."
        )

    if state.get("is_paused") and confidence_label == "high":
        confidence_label = "medium"
        confidence_reason = "Simulation is paused, so the command room is reviewing the last committed snapshot."

    overlay_active = (
        state.get("active_scenario") != "baseline"
        or int(state.get("crisis_level", 0)) > 0
        or int(state.get("virtual_admissions", 0)) > 0
    )

    return {
        "telemetry_state": telemetry_state,
        "simulator_status": "paused" if state.get("is_paused") else "running",
        "data_source": (
            "Live telemetry with simulated crisis overlay"
            if overlay_active
            else "Live telemetry stream"
        ),
        "confidence_label": confidence_label,
        "confidence_reason": confidence_reason,
        "last_telemetry_at": last_telemetry_at,
        "telemetry_age_seconds": telemetry_age_seconds,
    }


def _build_briefing(
    *,
    summary: dict[str, Any],
    resource_cards: list[dict[str, Any]],
    trust: dict[str, Any],
    patients: list[dict[str, Any]],
) -> dict[str, Any]:
    critical_resources = [card for card in resource_cards if card["status"] == "critical"]
    warning_resources = [card for card in resource_cards if card["status"] == "warning"]
    top_patients = [patient for patient in patients if patient["risk_score"] >= 80][:2]

    if summary["overflow_patients"] > 1 or critical_resources:
        headline = "Capacity strain requires intervention"
        summary_text = (
            "The next 15 minutes should focus on queue relief, protecting reserves, "
            "and reviewing the sickest patients first."
        )
    elif summary["active_alerts"] > 0 or summary["attention_patients"] > 0 or warning_resources:
        headline = "Clinical pressure is rising but manageable"
        summary_text = (
            "Routing, bedside review, and staffing need close coordination to keep "
            "the ICU ahead of incoming demand."
        )
    else:
        headline = "ICU operations remain within a stable margin"
        summary_text = (
            "Bed flow, alerts, and core resource reserves are inside the normal "
            "operating envelope right now."
        )

    changes: list[str] = []
    if summary["overflow_patients"] > 0:
        changes.append(
            f"{summary['overflow_patients']} patients are waiting beyond the {summary['icu_capacity']}-bed ICU map."
        )
    else:
        changes.append("No patients are waiting outside the live ICU bed map.")

    if top_patients:
        patient_names = ", ".join(
            patient.get("name") or patient["patient_raw_id"] for patient in top_patients
        )
        changes.append(f"Highest-acuity pressure is centered on {patient_names}.")
    elif summary["active_alerts"] > 0:
        changes.append(
            f"{summary['active_alerts']} telemetry alerts are active and still driving bedside review."
        )
    else:
        changes.append("No open telemetry breaches are currently driving escalations.")

    constrained_resource = critical_resources[:1] or warning_resources[:1]
    if constrained_resource:
        resource = constrained_resource[0]
        changes.append(
            f"{resource['label']} is down to {resource['available']}{resource['unit']} remaining and trending {resource['trend']}."
        )
    elif trust["telemetry_state"] == "live" and trust.get("telemetry_age_seconds") is not None:
        changes.append(
            f"Telemetry confidence is {trust['confidence_label']} with the latest samples {trust['telemetry_age_seconds']}s old."
        )
    else:
        changes.append(trust["confidence_reason"])

    return {
        "headline": headline,
        "summary": summary_text,
        "changes": changes[:3],
    }


def _projection_metric(
    *,
    key: str,
    label: str,
    current_value: int,
    projected_value: int,
    unit: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "current_value": current_value,
        "projected_value": projected_value,
        "delta": projected_value - current_value,
        "unit": unit,
    }


def _observed_metric(
    *,
    key: str,
    label: str,
    baseline_value: int,
    current_value: int,
    unit: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "baseline_value": baseline_value,
        "current_value": current_value,
        "delta": current_value - baseline_value,
        "unit": unit,
    }


def _capture_intervention_baseline(
    *,
    summary: dict[str, Any],
    resource_cards: list[dict[str, Any]],
) -> dict[str, int]:
    resource_by_key = {card["resource_key"]: card for card in resource_cards}
    return {
        "icu_capacity": int(summary.get("icu_capacity", 0) or 0),
        "overflow_patients": int(summary.get("overflow_patients", 0) or 0),
        "attention_patients": int(summary.get("attention_patients", 0) or 0),
        "active_alerts": int(summary.get("active_alerts", 0) or 0),
        "oxygen_network": int(resource_by_key.get("oxygen_network", {}).get("available", 0) or 0),
        "critical_care_nurses": int(
            resource_by_key.get("critical_care_nurses", {}).get("available", 0) or 0
        ),
    }


def _recommendation_state(
    *,
    action: dict[str, Any],
    summary: dict[str, Any],
    state: dict[str, Any],
) -> tuple[str, str, str, bool, str | None]:
    action_id = action["id"]
    action_type = action["action_type"]

    if action_type == "advisory":
        return (
            "recommended",
            "Advisory guidance",
            "This recommendation informs the operator but does not trigger a simulator-side action.",
            False,
            None,
        )

    if action_type == "control":
        control_action = action.get("control_action")
        if control_action == "resume":
            return (
                "recommended",
                "Control action",
                "The simulator is paused and can be resumed directly from this recommendation.",
                bool(state.get("is_paused")),
                "Resume twin",
            )
        return (
            "recommended",
            "Control action",
            "This recommendation maps to a simulator control rather than a clinical intervention.",
            True,
            "Run control",
        )

    if action_id == "open-surge-beds":
        surge_bed_bonus = int(state.get("surge_bed_bonus", 0) or 0)
        if surge_bed_bonus >= 4:
            return (
                "saturated",
                "Maximum surge active",
                "All configured surge-bed increments are already active in the live ICU map.",
                False,
                None,
            )
        if surge_bed_bonus > 0:
            return (
                "active",
                f"{surge_bed_bonus} surge beds active",
                "Surge capacity is already engaged and can still be expanded by one additional step.",
                True,
                "Add 2 more surge beds",
            )
        return (
            "recommended",
            "Ready to apply",
            "No surge-bed capacity is currently active in the routing model.",
            True,
            "Open surge beds",
        )

    if action_id == "protect-oxygen-reserve":
        oxygen_reserve_bonus = int(state.get("oxygen_reserve_bonus", 0) or 0)
        if oxygen_reserve_bonus >= 24:
            return (
                "saturated",
                "Reserve fully buffered",
                "The oxygen reserve model is already running at its configured reinforcement limit.",
                False,
                None,
            )
        if oxygen_reserve_bonus > 0:
            return (
                "active",
                f"+{oxygen_reserve_bonus}% reserve active",
                "Respiratory reserve protection is already engaged and can still be reinforced once more.",
                True,
                "Add reserve buffer",
            )
        return (
            "recommended",
            "Ready to apply",
            "No oxygen reserve reinforcement is currently active.",
            True,
            "Protect oxygen reserve",
        )

    if action_id == "rebalance-nurse-coverage":
        staffing_support_bonus = int(state.get("staffing_support_bonus", 0) or 0)
        if staffing_support_bonus >= 6:
            return (
                "saturated",
                "Staff support maxed",
                "All configured critical-care reinforcement steps are already active.",
                False,
                None,
            )
        if staffing_support_bonus > 0:
            return (
                "active",
                f"+{staffing_support_bonus} staff active",
                "Additional staffing support is already live and can still be widened by one more step.",
                True,
                "Add staffing support",
            )
        return (
            "recommended",
            "Ready to apply",
            "No staffing reinforcement is currently active in the live model.",
            True,
            "Rebalance coverage",
        )

    if action_id == "review-alerting-patients":
        active_alerts = int(summary.get("active_alerts", 0) or 0)
        if state.get("last_intervention_id") == action_id:
            return (
                "recently_applied",
                "Recently applied",
                "Alert review was the most recent operator action and its impact is shown below.",
                active_alerts > 0,
                "Review next alert" if active_alerts > 0 else None,
            )
        return (
            "recommended",
            "Ready to apply",
            "No alert-review intervention has been recorded as the latest operator action.",
            active_alerts > 0,
            "Run alert review" if active_alerts > 0 else None,
        )

    return (
        "recommended",
        "Ready to apply",
        "This intervention is available to the operator.",
        True,
        "Apply now",
    )


def _build_action_observation(
    *,
    action_id: str,
    summary: dict[str, Any],
    resource_cards: list[dict[str, Any]],
    state: dict[str, Any],
) -> tuple[str | None, list[dict[str, Any]]]:
    baseline = state.get("last_intervention_baseline") or {}
    if state.get("last_intervention_id") != action_id or not baseline:
        return None, []

    resource_by_key = {card["resource_key"]: card for card in resource_cards}
    current_overflow = int(summary.get("overflow_patients", 0) or 0)
    current_attention = int(summary.get("attention_patients", 0) or 0)
    current_alerts = int(summary.get("active_alerts", 0) or 0)
    current_capacity = int(summary.get("icu_capacity", 0) or 0)
    current_oxygen = int(resource_by_key.get("oxygen_network", {}).get("available", 0) or 0)
    current_nurses = int(
        resource_by_key.get("critical_care_nurses", {}).get("available", 0) or 0
    )

    if action_id == "open-surge-beds":
        baseline_capacity = int(baseline.get("icu_capacity", current_capacity) or 0)
        baseline_overflow = int(baseline.get("overflow_patients", current_overflow) or 0)
        return (
            f"Observed ICU capacity move from {baseline_capacity} to {current_capacity} beds while overflow shifted from {baseline_overflow} to {current_overflow}.",
            [
                _observed_metric(
                    key="icu_capacity",
                    label="ICU capacity",
                    baseline_value=baseline_capacity,
                    current_value=current_capacity,
                    unit="beds",
                ),
                _observed_metric(
                    key="overflow_patients",
                    label="Overflow queue",
                    baseline_value=baseline_overflow,
                    current_value=current_overflow,
                    unit="patients",
                ),
            ],
        )

    if action_id == "protect-oxygen-reserve":
        baseline_oxygen = int(baseline.get("oxygen_network", current_oxygen) or 0)
        baseline_alerts = int(baseline.get("active_alerts", current_alerts) or 0)
        return (
            f"Observed oxygen reserve moved from {baseline_oxygen}% to {current_oxygen}% while alert pressure shifted from {baseline_alerts} to {current_alerts}.",
            [
                _observed_metric(
                    key="oxygen_network",
                    label="Oxygen network",
                    baseline_value=baseline_oxygen,
                    current_value=current_oxygen,
                    unit="%",
                ),
                _observed_metric(
                    key="active_alerts",
                    label="Open alerts",
                    baseline_value=baseline_alerts,
                    current_value=current_alerts,
                    unit="alerts",
                ),
            ],
        )

    if action_id == "rebalance-nurse-coverage":
        baseline_nurses = int(baseline.get("critical_care_nurses", current_nurses) or 0)
        baseline_attention = int(baseline.get("attention_patients", current_attention) or 0)
        return (
            f"Observed staffing headroom move from {baseline_nurses} to {current_nurses} while the attention set shifted from {baseline_attention} to {current_attention}.",
            [
                _observed_metric(
                    key="critical_care_nurses",
                    label="Critical care nurses",
                    baseline_value=baseline_nurses,
                    current_value=current_nurses,
                    unit="staff",
                ),
                _observed_metric(
                    key="attention_patients",
                    label="Attention set",
                    baseline_value=baseline_attention,
                    current_value=current_attention,
                    unit="patients",
                ),
            ],
        )

    if action_id == "review-alerting-patients":
        baseline_alerts = int(baseline.get("active_alerts", current_alerts) or 0)
        baseline_attention = int(baseline.get("attention_patients", current_attention) or 0)
        return (
            f"Observed alert volume move from {baseline_alerts} to {current_alerts} while the bedside attention set shifted from {baseline_attention} to {current_attention}.",
            [
                _observed_metric(
                    key="active_alerts",
                    label="Open alerts",
                    baseline_value=baseline_alerts,
                    current_value=current_alerts,
                    unit="alerts",
                ),
                _observed_metric(
                    key="attention_patients",
                    label="Attention set",
                    baseline_value=baseline_attention,
                    current_value=current_attention,
                    unit="patients",
                ),
            ],
        )

    return None, []


def _project_action_outcome(
    *,
    action_id: str,
    summary: dict[str, Any],
    resource_cards: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    overflow = int(summary.get("overflow_patients", 0) or 0)
    active_alerts = int(summary.get("active_alerts", 0) or 0)
    attention_patients = int(summary.get("attention_patients", active_alerts + overflow) or 0)

    resource_by_key = {card["resource_key"]: card for card in resource_cards}
    oxygen_available = int(resource_by_key.get("oxygen_network", {}).get("available", 0) or 0)
    oxygen_unit = resource_by_key.get("oxygen_network", {}).get("unit", "%")
    nurses_available = int(
        resource_by_key.get("critical_care_nurses", {}).get("available", 0) or 0
    )
    nurse_unit = resource_by_key.get("critical_care_nurses", {}).get("unit", "staff")

    if action_id == "open-surge-beds":
        projected_overflow = max(overflow - 2, 0)
        projected_attention = max(attention_patients - 1, 0)
        return (
            "Projected to release queue pressure within the next 30 minutes by creating routing headroom.",
            [
                _projection_metric(
                    key="overflow_patients",
                    label="Overflow queue",
                    current_value=overflow,
                    projected_value=projected_overflow,
                    unit="patients",
                ),
                _projection_metric(
                    key="attention_patients",
                    label="Attention set",
                    current_value=attention_patients,
                    projected_value=projected_attention,
                    unit="patients",
                ),
            ],
        )

    if action_id == "protect-oxygen-reserve":
        projected_oxygen = min(oxygen_available + 12, 100)
        projected_alerts = max(active_alerts - 1, 0)
        return (
            "Projected to stabilize respiratory reserve and reduce escalation pressure from oxygen-related deterioration.",
            [
                _projection_metric(
                    key="oxygen_network",
                    label="Oxygen network",
                    current_value=oxygen_available,
                    projected_value=projected_oxygen,
                    unit=oxygen_unit,
                ),
                _projection_metric(
                    key="active_alerts",
                    label="Open alerts",
                    current_value=active_alerts,
                    projected_value=projected_alerts,
                    unit="alerts",
                ),
            ],
        )

    if action_id == "rebalance-nurse-coverage":
        projected_nurses = nurses_available + 3
        projected_attention = max(attention_patients - 1, 0)
        return (
            "Projected to widen staffing margin and shorten bedside response time for the current acuity set.",
            [
                _projection_metric(
                    key="critical_care_nurses",
                    label="Critical care nurses",
                    current_value=nurses_available,
                    projected_value=projected_nurses,
                    unit=nurse_unit,
                ),
                _projection_metric(
                    key="attention_patients",
                    label="Attention set",
                    current_value=attention_patients,
                    projected_value=projected_attention,
                    unit="patients",
                ),
            ],
        )

    if action_id == "review-alerting-patients":
        projected_alerts = max(active_alerts - 1, 0)
        projected_attention = max(attention_patients - 1, 0)
        return (
            "Projected to convert one active escalation into a monitored case if bedside intervention happens immediately.",
            [
                _projection_metric(
                    key="active_alerts",
                    label="Open alerts",
                    current_value=active_alerts,
                    projected_value=projected_alerts,
                    unit="alerts",
                ),
                _projection_metric(
                    key="attention_patients",
                    label="Attention set",
                    current_value=attention_patients,
                    projected_value=projected_attention,
                    unit="patients",
                ),
            ],
        )

    if action_id == "validate-telemetry-freshness":
        return (
            "Projected to improve confidence in the next routing decision rather than directly changing clinical load.",
            [],
        )

    if action_id == "resume-simulator-when-ready":
        return (
            "Projected to restore forecasting visibility for the next intervention cycle.",
            [],
        )

    return (
        "Projected to maintain the current operating posture over the next 30 minutes.",
        [],
    )


def _build_recommended_actions(
    *,
    summary: dict[str, Any],
    resource_cards: list[dict[str, Any]],
    trust: dict[str, Any],
    state: dict[str, Any],
    patients: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    overflow_count = int(summary.get("overflow_patients", 0))
    if overflow_count > 0:
        actions.append(
            {
                "id": "open-surge-beds",
                "action_type": "intervention",
                "control_action": None,
                "priority": "critical" if overflow_count > 2 else "warning",
                "title": "Open surge beds or accelerate step-down transfers",
                "rationale": f"{overflow_count} patients are waiting beyond live ICU capacity and need a routing release valve.",
                "owner": "Hospital ops lead",
            }
        )

    oxygen_card = next(
        (card for card in resource_cards if card["resource_key"] == "oxygen_network"),
        None,
    )
    if oxygen_card and oxygen_card["status"] != "normal":
        actions.append(
            {
                "id": "protect-oxygen-reserve",
                "action_type": "intervention",
                "control_action": None,
                "priority": "critical" if oxygen_card["status"] == "critical" else "warning",
                "title": "Protect oxygen reserve and verify manifold pressure",
                "rationale": (
                    f"Oxygen network reserve is at {oxygen_card['available']}{oxygen_card['unit']} "
                    f"and trending {oxygen_card['trend']}."
                ),
                "owner": "Respiratory lead",
            }
        )

    nurse_card = next(
        (card for card in resource_cards if card["resource_key"] == "critical_care_nurses"),
        None,
    )
    if nurse_card and nurse_card["status"] != "normal":
        actions.append(
            {
                "id": "rebalance-nurse-coverage",
                "action_type": "intervention",
                "control_action": None,
                "priority": "warning",
                "title": "Rebalance critical care nurse coverage",
                "rationale": (
                    f"Only {nurse_card['available']} staff remain inside the current headroom model."
                ),
                "owner": "Charge nurse",
            }
        )

    active_alerts = int(summary.get("active_alerts", 0))
    if active_alerts > 0:
        top_alert_patient = next(
            (patient for patient in patients if patient.get("has_active_alert")),
            None,
        )
        patient_name = (
            top_alert_patient.get("name") or top_alert_patient["patient_raw_id"]
            if top_alert_patient
            else "the alerting cohort"
        )
        actions.append(
            {
                "id": "review-alerting-patients",
                "action_type": "intervention",
                "control_action": None,
                "priority": "critical" if active_alerts > 2 else "warning",
                "title": "Review alerting patients for immediate escalation",
                "rationale": f"{active_alerts} telemetry alerts are active, led by {patient_name}.",
                "owner": "ICU attending",
            }
        )

    if trust.get("telemetry_state") == "watch":
        actions.append(
            {
                "id": "validate-telemetry-freshness",
                "action_type": "advisory",
                "control_action": None,
                "priority": "warning",
                "title": "Validate telemetry freshness before major routing changes",
                "rationale": trust["confidence_reason"],
                "owner": "Technical operator",
            }
        )

    if state.get("is_paused"):
        actions.append(
            {
                "id": "resume-simulator-when-ready",
                "action_type": "control",
                "control_action": "resume",
                "priority": "normal",
                "title": "Resume the simulator after command review",
                "rationale": "The command room is paused on the last snapshot and will need playback resumed for continued forecasting.",
                "owner": "Simulation operator",
            }
        )

    if not actions:
        actions.append(
            {
                "id": "maintain-current-posture",
                "action_type": "advisory",
                "control_action": None,
                "priority": "normal",
                "title": "Maintain monitored routing posture",
                "rationale": "Current demand, alerts, and reserves do not require an immediate intervention.",
                "owner": "Command desk",
            }
        )

    for action in actions:
        projected_summary, projected_metrics = _project_action_outcome(
            action_id=action["id"],
            summary=summary,
            resource_cards=resource_cards,
        )
        action["projected_summary"] = projected_summary
        action["projected_window_minutes"] = 30
        action["projected_metrics"] = projected_metrics
        (
            action["state"],
            action["state_label"],
            action["state_reason"],
            action["can_apply"],
            action["apply_label"],
        ) = _recommendation_state(
            action=action,
            summary=summary,
            state=state,
        )
        observed_summary, observed_metrics = _build_action_observation(
            action_id=action["id"],
            summary=summary,
            resource_cards=resource_cards,
            state=state,
        )
        action["observed_summary"] = observed_summary
        action["observed_metrics"] = observed_metrics

    priority_order = {"critical": 3, "warning": 2, "normal": 1}
    actions.sort(key=lambda action: priority_order[action["priority"]], reverse=True)
    return actions[:3]


def _build_summary(
    patients: list[dict[str, Any]],
    *,
    bed_tiles: list[dict[str, Any]],
    overflow_count: int,
) -> dict[str, Any]:
    attention_patients = sum(1 for patient in patients if patient["risk_score"] >= 60)
    average_risk = _clamp(
        sum(patient["risk_score"] for patient in patients) / max(len(patients), 1),
        0,
        100,
    )
    return {
        "total_patients": len(patients),
        "icu_capacity": len(bed_tiles),
        "icu_occupied": sum(1 for bed in bed_tiles if bed["status"] == "occupied"),
        "overflow_patients": overflow_count,
        "active_alerts": sum(1 for patient in patients if patient["has_active_alert"]),
        "average_risk_score": average_risk,
        "attention_patients": attention_patients,
        "updated_at": _utcnow(),
    }


def _delta_metric(
    *,
    key: str,
    label: str,
    baseline_value: int,
    current_value: int,
    higher_is_better: bool,
) -> dict[str, Any]:
    delta = current_value - baseline_value
    if delta == 0:
        direction = "flat"
        status = "unchanged"
    else:
        direction = "up" if delta > 0 else "down"
        improved = current_value > baseline_value if higher_is_better else current_value < baseline_value
        status = "improved" if improved else "degraded"

    return {
        "key": key,
        "label": label,
        "baseline_value": baseline_value,
        "current_value": current_value,
        "delta": delta,
        "direction": direction,
        "status": status,
    }


def _build_scenario_comparison(
    *,
    baseline_summary: dict[str, Any],
    current_summary: dict[str, Any],
    baseline_resources: list[dict[str, Any]],
    current_resources: list[dict[str, Any]],
    state: dict[str, Any],
) -> dict[str, Any]:
    summary_metrics = [
        _delta_metric(
            key="icu_occupied",
            label="Beds occupied",
            baseline_value=int(baseline_summary["icu_occupied"]),
            current_value=int(current_summary["icu_occupied"]),
            higher_is_better=False,
        ),
        _delta_metric(
            key="overflow_patients",
            label="Overflow queue",
            baseline_value=int(baseline_summary["overflow_patients"]),
            current_value=int(current_summary["overflow_patients"]),
            higher_is_better=False,
        ),
        _delta_metric(
            key="active_alerts",
            label="Open alerts",
            baseline_value=int(baseline_summary["active_alerts"]),
            current_value=int(current_summary["active_alerts"]),
            higher_is_better=False,
        ),
        _delta_metric(
            key="average_risk_score",
            label="Average risk",
            baseline_value=int(baseline_summary["average_risk_score"]),
            current_value=int(current_summary["average_risk_score"]),
            higher_is_better=False,
        ),
    ]

    baseline_by_key = {resource["resource_key"]: resource for resource in baseline_resources}
    current_by_key = {resource["resource_key"]: resource for resource in current_resources}
    resource_metrics: list[dict[str, Any]] = []
    for key in [
        "oxygen_network",
        "ventilators",
        "critical_care_nurses",
        "vasopressor_stock",
    ]:
        baseline_resource = baseline_by_key.get(key)
        current_resource = current_by_key.get(key)
        if not baseline_resource or not current_resource:
            continue
        resource_metrics.append(
            _delta_metric(
                key=key,
                label=current_resource["label"],
                baseline_value=int(baseline_resource["available"]),
                current_value=int(current_resource["available"]),
                higher_is_better=True,
            )
        )

    return {
        "baseline_label": "Baseline operations",
        "current_label": state.get("crisis_label") or "Current scenario",
        "summary_metrics": summary_metrics,
        "resource_metrics": resource_metrics,
    }


def _severity_from_summary(summary: dict[str, Any]) -> str:
    if int(summary.get("overflow_patients", 0)) >= 3 or int(summary.get("active_alerts", 0)) >= 2:
        return "critical"
    if int(summary.get("overflow_patients", 0)) > 0 or int(summary.get("active_alerts", 0)) > 0:
        return "warning"
    return "normal"


def _current_focus_note(summary: dict[str, Any]) -> str:
    if int(summary.get("overflow_patients", 0)) > 0:
        return "Overflow pressure is the leading issue in the current command-room view."
    if int(summary.get("active_alerts", 0)) > 0:
        return "Active telemetry alerts are the leading issue in the current command-room view."
    return "No single incident dominates the current operating picture."


def _rewind_checkpoint(
    *,
    event: dict[str, Any],
    icu_occupied: int,
    overflow_patients: int,
    active_alerts: int,
    attention_patients: int,
) -> tuple[int, int, int, int, str]:
    focus_note = "This checkpoint rewinds one command-room event."
    next_icu = icu_occupied
    next_overflow = overflow_patients
    next_alerts = active_alerts
    next_attention = attention_patients

    if event["event_type"] == "capacity":
        next_overflow = max(overflow_patients - 1, 0)
        next_attention = max(attention_patients - 1, 0)
        focus_note = "Overflow pressure is reduced by one reconstructed checkpoint before the latest queue spike."
    elif event["event_type"] == "alert":
        next_alerts = max(active_alerts - 1, 0)
        next_attention = max(attention_patients - 1, 0)
        focus_note = "One telemetry breach is rewound to show the command picture before the latest alert."
    elif event["event_type"] == "routing":
        next_icu = max(icu_occupied - 1, 0)
        next_attention = max(attention_patients - 1, 0)
        focus_note = "One routing allocation is rewound to show the bed map before the latest reassignment."
    elif event["event_type"] == "simulation":
        focus_note = "This checkpoint marks a simulator state transition without changing patient demand directly."

    return next_icu, next_overflow, next_alerts, next_attention, focus_note


def _build_incident_replay_frames(
    *,
    timeline: list[dict[str, Any]],
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = [
        {
            "id": "current-state",
            "timestamp": _parse_timestamp(summary.get("updated_at")),
            "title": "Current command state",
            "severity": _severity_from_summary(summary),
            "phase_label": "Current state",
            "summary": "Latest reconstructed checkpoint from the live command stream.",
            "icu_occupied": int(summary.get("icu_occupied", 0)),
            "overflow_patients": int(summary.get("overflow_patients", 0)),
            "active_alerts": int(summary.get("active_alerts", 0)),
            "attention_patients": int(summary.get("attention_patients", 0)),
            "focus_note": _current_focus_note(summary),
        }
    ]

    rewind_icu = int(summary.get("icu_occupied", 0))
    rewind_overflow = int(summary.get("overflow_patients", 0))
    rewind_alerts = int(summary.get("active_alerts", 0))
    rewind_attention = int(summary.get("attention_patients", 0))

    for index, event in enumerate(timeline[:4], start=1):
        (
            rewind_icu,
            rewind_overflow,
            rewind_alerts,
            rewind_attention,
            focus_note,
        ) = _rewind_checkpoint(
            event=event,
            icu_occupied=rewind_icu,
            overflow_patients=rewind_overflow,
            active_alerts=rewind_alerts,
            attention_patients=rewind_attention,
        )
        frames.append(
            {
                "id": f"replay-{event['id']}",
                "timestamp": _parse_timestamp(event["timestamp"]),
                "title": event["title"],
                "severity": event["severity"],
                "phase_label": f"Checkpoint {index}",
                "summary": event["description"],
                "icu_occupied": rewind_icu,
                "overflow_patients": rewind_overflow,
                "active_alerts": rewind_alerts,
                "attention_patients": rewind_attention,
                "focus_note": focus_note,
            }
        )

    return frames


def _build_timeline(
    db: Session,
    *,
    bed_tiles: list[dict[str, Any]],
    overflow_count: int,
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for event in get_simulation_events(limit=settings.OPS_TIMELINE_LIMIT):
        events.append({**event, "timestamp": _parse_timestamp(event.get("timestamp"))})

    alert_rows = db.execute(ALERT_TIMELINE_QUERY).mappings().all()
    alert_events = hydrate_name_fields(
        [dict(row) for row in alert_rows],
        cipher_key="patient_name_cipher",
        output_key="patient_name",
    )
    for alert in alert_events:
        events.append(
            {
                "id": f"alert-{alert['id']}",
                "timestamp": alert["opened_at"],
                "event_type": "alert",
                "severity": "critical",
                "title": f"Telemetry breach for {alert.get('patient_name') or alert['patient_id']}",
                "description": f"BPM {alert.get('last_bpm') or '--'} and SpO2 {alert.get('last_oxygen') or '--'} require critical care attention.",
                "patient_id": str(alert["patient_id"]),
                "bed_id": None,
            }
        )

    for bed_tile in bed_tiles[:4]:
        patient = bed_tile.get("patient")
        if patient is None:
            continue

        events.append(
            {
                "id": f"routing-{bed_tile['bed_id']}-{patient['patient_id']}",
                "timestamp": _utcnow(),
                "event_type": "routing",
                "severity": "critical" if patient["risk_score"] >= 80 else "warning",
                "title": f"{bed_tile['bed_id']} assigned to {patient.get('patient_name') or patient['patient_raw_id']}",
                "description": f"Risk {patient['risk_score']}/100 routed through {patient['recommended_unit']} allocation logic.",
                "patient_id": _response_id(patient["patient_id"]),
                "bed_id": bed_tile["bed_id"],
            }
        )

    if overflow_count > 0:
        events.append(
            {
                "id": f"overflow-{overflow_count}",
                "timestamp": _utcnow(),
                "event_type": "capacity",
                "severity": "warning" if overflow_count < 4 else "critical",
                "title": f"{overflow_count} patients waiting for ICU routing",
                "description": "Overflow demand exceeds live bed capacity and requires intervention or surge beds.",
                "patient_id": None,
                "bed_id": None,
            }
        )

    if state.get("is_paused"):
        events.append(
            {
                "id": "paused-state",
                "timestamp": _parse_timestamp(state.get("updated_at")),
                "event_type": "simulation",
                "severity": "warning",
                "title": "Simulation paused",
                "description": "Scenario engine is paused while the command team reviews current capacity.",
                "patient_id": None,
                "bed_id": None,
            }
        )

    events.sort(key=lambda event: _parse_timestamp(event["timestamp"]), reverse=True)
    return events[: settings.OPS_TIMELINE_LIMIT]


def get_operations_overview(db: Session) -> dict[str, Any]:
    state = get_simulation_state()
    raw_patients = _load_patients(db)
    decorated_patients = _decorate_patients(
        raw_patients,
        crisis_level=int(state.get("crisis_level", 0)),
    )
    baseline_patients = _decorate_patients(
        raw_patients,
        crisis_level=0,
    )

    bed_tiles, queue_entries, overflow_count = _build_bed_heatmap(
        decorated_patients,
        virtual_admissions=int(state.get("virtual_admissions", 0)),
        surge_bed_bonus=int(state.get("surge_bed_bonus", 0)),
    )
    baseline_bed_tiles, _, baseline_overflow_count = _build_bed_heatmap(
        baseline_patients,
        virtual_admissions=0,
        surge_bed_bonus=0,
    )
    resource_cards, resource_forecast = _build_resource_panels(
        decorated_patients,
        crisis_level=int(state.get("crisis_level", 0)),
        speed=float(state.get("speed", 1.0)),
        virtual_admissions=int(state.get("virtual_admissions", 0)),
        oxygen_reserve_bonus=int(state.get("oxygen_reserve_bonus", 0)),
        staffing_support_bonus=int(state.get("staffing_support_bonus", 0)),
    )
    baseline_resource_cards, _ = _build_resource_panels(
        baseline_patients,
        crisis_level=0,
        speed=1.0,
        virtual_admissions=0,
        oxygen_reserve_bonus=0,
        staffing_support_bonus=0,
    )
    timeline = _build_timeline(
        db,
        bed_tiles=bed_tiles,
        overflow_count=overflow_count,
        state=state,
    )
    summary = _build_summary(
        decorated_patients,
        bed_tiles=bed_tiles,
        overflow_count=overflow_count,
    )
    baseline_summary = _build_summary(
        baseline_patients,
        bed_tiles=baseline_bed_tiles,
        overflow_count=baseline_overflow_count,
    )
    trust = _build_operations_trust(
        decorated_patients,
        state=state,
    )
    briefing = _build_briefing(
        summary=summary,
        resource_cards=resource_cards,
        trust=trust,
        patients=decorated_patients,
    )
    recommended_actions = _build_recommended_actions(
        summary=summary,
        resource_cards=resource_cards,
        trust=trust,
        state=state,
        patients=decorated_patients,
    )
    scenario_comparison = _build_scenario_comparison(
        baseline_summary=baseline_summary,
        current_summary=summary,
        baseline_resources=baseline_resource_cards,
        current_resources=resource_cards,
        state=state,
    )
    replay_frames = _build_incident_replay_frames(
        timeline=timeline,
        summary=summary,
    )

    return {
        "summary": summary,
        "simulation": {
            **state,
            "active_interventions": _build_active_interventions(state),
            "updated_at": _parse_timestamp(state.get("updated_at")),
        },
        "briefing": briefing,
        "trust": trust,
        "recommended_actions": recommended_actions,
        "scenario_comparison": scenario_comparison,
        "replay_frames": replay_frames,
        "bed_heatmap": bed_tiles,
        "triage_queue": queue_entries,
        "resource_cards": resource_cards,
        "resource_forecast": resource_forecast,
        "timeline": timeline,
    }


def _scenario_defaults(scenario: str, severity: str) -> tuple[int, int, str]:
    severity_level = {"minor": 1, "major": 2, "extreme": 3}.get(severity, 2)
    labels = {
        "surge_admissions": "Mass admission surge",
        "oxygen_shortage": "Oxygen network degradation",
        "acuity_cluster": "High-acuity cluster",
    }
    virtual_admissions = 0
    if scenario == "surge_admissions":
        virtual_admissions = 2 + severity_level
    return severity_level, virtual_admissions, labels.get(scenario, "Escalation event")


def _close_open_alerts(db: Session, limit: int = 1) -> int:
    alerts = (
        db.query(PatientAlert)
        .filter(PatientAlert.status == "open")
        .order_by(PatientAlert.opened_at.asc())
        .limit(limit)
        .all()
    )

    for alert in alerts:
        alert.status = "closed"
        alert.closed_at = _utcnow()
        alert.consecutive_normal_count = settings.ALERT_DEBOUNCE_COUNT

    if alerts:
        db.commit()

    return len(alerts)


def _apply_intervention(
    db: Session,
    *,
    current_state: dict[str, Any],
    intervention_id: str,
    baseline: dict[str, int],
) -> None:
    base_updates: dict[str, Any] = {
        "last_action": "apply_intervention",
        "last_intervention_id": intervention_id,
        "last_intervention_at": _utcnow().isoformat(),
        "last_intervention_baseline": baseline,
    }
    title = "Intervention applied"
    description = "Command center intervention updated the ICU twin."
    severity = "normal"

    if intervention_id == "open-surge-beds":
        next_surge_bonus = min(int(current_state.get("surge_bed_bonus", 0)) + 2, 4)
        next_virtual_admissions = max(int(current_state.get("virtual_admissions", 0)) - 2, 0)
        update_simulation_state(
            **base_updates,
            surge_bed_bonus=next_surge_bonus,
            virtual_admissions=next_virtual_admissions,
        )
        title = "Surge beds opened"
        description = "Two surge-capacity beds were activated and queue pressure was reduced."
        severity = "warning"
    elif intervention_id == "protect-oxygen-reserve":
        next_oxygen_bonus = min(int(current_state.get("oxygen_reserve_bonus", 0)) + 12, 24)
        update_simulation_state(
            **base_updates,
            oxygen_reserve_bonus=next_oxygen_bonus,
        )
        title = "Oxygen reserve protected"
        description = "Respiratory reserve buffers were applied to stabilize the oxygen network."
        severity = "warning"
    elif intervention_id == "rebalance-nurse-coverage":
        next_staffing_bonus = min(int(current_state.get("staffing_support_bonus", 0)) + 3, 6)
        update_simulation_state(
            **base_updates,
            staffing_support_bonus=next_staffing_bonus,
        )
        title = "Critical care coverage rebalanced"
        description = "Charge coverage was reinforced to widen bedside staffing headroom."
        severity = "warning"
    elif intervention_id == "review-alerting-patients":
        closed_count = _close_open_alerts(db, limit=1)
        update_simulation_state(**base_updates)
        title = "Alert review executed"
        if closed_count > 0:
            description = "One open telemetry alert was resolved after immediate bedside review."
            severity = "normal"
        else:
            description = "No open telemetry alerts were available to resolve at this checkpoint."
            severity = "warning"
    else:
        update_simulation_state(**base_updates)
        title = "Unknown intervention"
        description = f"Intervention '{intervention_id}' is not recognized by the simulation control layer."
        severity = "warning"

    append_simulation_event(
        {
            "event_type": "intervention",
            "severity": severity,
            "title": title,
            "description": description,
            "intervention_id": intervention_id,
        }
    )


def _inject_crisis_samples(
    db: Session,
    patients: list[dict[str, Any]],
    *,
    scenario: str,
    crisis_level: int,
    patient_count: int,
) -> None:
    if not patients:
        return

    now = _utcnow()
    targets = patients[:patient_count]
    for offset, patient in enumerate(targets):
        for burst in range(settings.ALERT_DEBOUNCE_COUNT):
            bpm = 118 + crisis_level * 6 + offset * 2
            oxygen = 94

            if scenario == "oxygen_shortage":
                bpm = 108 + crisis_level * 4 + offset
                oxygen = max(78, 89 - crisis_level * 3 - offset)
            elif scenario == "acuity_cluster":
                bpm = 126 + crisis_level * 5 + offset * 3
                oxygen = max(82, 92 - crisis_level * 2 - offset)

            timestamp = now + timedelta(seconds=offset * 4 + burst)
            clean = insert_clean_sample(
                db,
                patient_raw_id=patient["patient_raw_id"],
                parity_flag=patient["parity_flag"],
                bpm=bpm,
                oxygen=oxygen,
                source_device=f"OPS-{scenario.upper()}",
                timestamp=timestamp,
            )
            process_vitals_for_alerts(
                patient["patient_id"],
                clean.bpm,
                clean.oxygen,
                db,
            )

    db.commit()


def apply_simulation_action(
    db: Session,
    *,
    action: str,
    speed: float | None = None,
    scenario: str | None = None,
    severity: str | None = None,
    patient_count: int | None = None,
    intervention_id: str | None = None,
) -> dict[str, Any]:
    current_state = get_simulation_state()
    scenario_name = scenario or current_state.get("active_scenario", "baseline")

    if action == "pause":
        update_simulation_state(is_paused=True, last_action="pause")
        append_simulation_event(
            {
                "event_type": "simulation",
                "severity": "warning",
                "title": "Simulation paused",
                "description": "Operator paused the twin to inspect ICU capacity and routing pressure.",
            }
        )
    elif action == "resume":
        update_simulation_state(is_paused=False, last_action="resume")
        append_simulation_event(
            {
                "event_type": "simulation",
                "severity": "normal",
                "title": "Simulation resumed",
                "description": "Realtime digital twin resumed normal event playback.",
            }
        )
    elif action == "set_speed":
        next_speed = float(speed or current_state.get("speed", 1.0))
        update_simulation_state(speed=next_speed, last_action="set_speed")
        append_simulation_event(
            {
                "event_type": "simulation",
                "severity": "warning" if next_speed > 1.5 else "normal",
                "title": f"Playback speed set to {next_speed:.1f}x",
                "description": "Command center updated the simulation speed to stress-test response timing.",
            }
        )
    elif action == "inject_crisis":
        severity_level, virtual_admissions, crisis_label = _scenario_defaults(
            scenario_name,
            severity or "major",
        )
        update_simulation_state(
            active_scenario=scenario_name,
            crisis_level=severity_level,
            crisis_label=crisis_label,
            virtual_admissions=virtual_admissions,
            last_action="inject_crisis",
        )

        patients = _decorate_patients(
            _load_patients(db),
            crisis_level=severity_level,
        )
        _inject_crisis_samples(
            db,
            patients,
            scenario=scenario_name,
            crisis_level=severity_level,
            patient_count=patient_count or min(4, len(patients)),
        )
        append_simulation_event(
            {
                "event_type": "crisis",
                "severity": "critical" if severity_level >= 2 else "warning",
                "title": crisis_label,
                "description": f"{crisis_label} injected into the ICU twin affecting {patient_count or min(4, len(patients))} live patients.",
            }
        )
    elif action == "apply_intervention":
        baseline_overview = get_operations_overview(db)
        baseline = _capture_intervention_baseline(
            summary=baseline_overview["summary"],
            resource_cards=baseline_overview["resource_cards"],
        )
        _apply_intervention(
            db,
            current_state=current_state,
            intervention_id=intervention_id or "",
            baseline=baseline,
        )
    else:
        reset_simulation_state()
        append_simulation_event(
            {
                "event_type": "simulation",
                "severity": "normal",
                "title": "Simulation reset",
                "description": "Digital twin returned to baseline hospital operations.",
            }
        )

    return get_operations_overview(db)
