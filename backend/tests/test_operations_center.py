"""Tests for operations center helpers."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.services.operations_center import (
    _build_active_interventions,
    _build_bed_heatmap,
    _build_incident_handoff,
    _build_incident_replay_frames,
    _build_operator_activity,
    _build_operations_trust,
    _build_resource_panels,
    _build_recommended_actions,
    _build_scenario_comparison,
    apply_simulation_action,
    _build_timeline,
    _decorate_patients,
    calculate_risk_score,
    classify_risk,
    recommend_unit,
)


def test_risk_score_prefers_alerting_and_low_oxygen():
    patient = {
        "last_bpm": 138,
        "last_oxygen": 84,
        "has_active_alert": True,
        "prescription_count": 4,
    }

    score = calculate_risk_score(patient, crisis_level=2)

    assert score >= 80
    assert classify_risk(score) == "Critical"
    assert recommend_unit(score) == "ICU"


def test_risk_score_keeps_stable_patient_low():
    patient = {
        "last_bpm": 78,
        "last_oxygen": 98,
        "has_active_alert": False,
        "prescription_count": 1,
    }

    score = calculate_risk_score(patient, crisis_level=0)

    assert score < 40
    assert classify_risk(score) == "Stable"
    assert recommend_unit(score) == "Observation"


def test_decorated_patients_include_risk_reasons():
    decorated = _decorate_patients(
        [
            {
                "patient_id": "patient-1",
                "patient_raw_id": "P00001",
                "parity_flag": "even",
                "name": "John Smith",
                "age": 55,
                "ward": "ICU-1",
                "last_bpm": 138,
                "last_oxygen": 84,
                "last_vitals_timestamp": "2026-04-04T12:00:00+00:00",
                "quality_flag": "good",
                "prescription_count": 4,
                "has_active_alert": True,
            }
        ],
        crisis_level=2,
    )

    reasons = " ".join(decorated[0]["risk_reasons"]).lower()

    assert "alert" in reasons
    assert "oxygen" in reasons or "hypoxia" in reasons
    assert "tachy" in reasons or "heart rate" in reasons


def test_build_active_interventions_from_state_modifiers():
    interventions = _build_active_interventions(
        {
            "surge_bed_bonus": 4,
            "oxygen_reserve_bonus": 24,
            "staffing_support_bonus": 6,
        }
    )

    assert len(interventions) == 3
    assert interventions[0]["label"]
    assert any(item["id"] == "open-surge-beds" for item in interventions)
    assert any(item["value"] == "+4 beds" for item in interventions)
    assert any(item["value"] == "+24%" for item in interventions)
    assert all(item["can_clear"] is True for item in interventions)
    assert all(item["clear_label"] for item in interventions)
    assert all(item["can_step_down"] is True for item in interventions)
    assert all(item["step_down_label"] for item in interventions)


def test_build_operator_activity_uses_structured_event_metadata():
    with patch(
        "app.services.operations_center.get_simulation_events",
        return_value=[
            {
                "id": "evt-speed",
                "timestamp": "2026-04-05T09:02:00+00:00",
                "event_type": "simulation",
                "severity": "warning",
                "title": "Playback speed set to 2.0x",
                "description": "Command center updated the simulation speed to stress-test response timing.",
                "action_key": "set_speed",
                "speed": 2.0,
            },
            {
                "id": "evt-alert",
                "timestamp": "2026-04-05T09:01:00+00:00",
                "event_type": "alert",
                "severity": "critical",
                "title": "Telemetry breach",
                "description": "Not an operator event.",
            },
        ],
    ):
        activity = _build_operator_activity({"crisis_label": "Nominal operations"})

    assert len(activity) == 1
    assert activity[0]["action_key"] == "set_speed"
    assert activity[0]["action_label"] == "Set speed to 2.0x"
    assert activity[0]["speed"] == 2.0
    assert activity[0]["title"] == "Playback speed set to 2.0x"


def test_build_incident_handoff_packages_export_ready_summary():
    handoff = _build_incident_handoff(
        summary={
            "icu_occupied": 12,
            "icu_capacity": 14,
            "overflow_patients": 2,
            "active_alerts": 1,
            "attention_patients": 3,
        },
        simulation={
            "crisis_label": "Oxygen network degradation",
            "last_action_label": "Applied oxygen reserve protection",
            "last_action_at": datetime(2026, 4, 5, 9, 2, tzinfo=UTC),
        },
        trust={
            "confidence_label": "medium",
            "confidence_reason": "Telemetry is usable but slightly behind the ideal freshness window.",
            "telemetry_state": "watch",
        },
        resource_cards=[
            {
                "resource_key": "oxygen_network",
                "label": "Oxygen network",
                "available": 28,
                "capacity": 100,
                "unit": "%",
                "status": "critical",
                "trend": "falling",
            }
        ],
        recommended_actions=[
            {
                "title": "Open surge beds or accelerate step-down transfers",
                "owner": "Hospital ops lead",
            },
            {
                "title": "Rebalance nurse coverage",
                "owner": "Charge nurse",
            },
        ],
        active_interventions=[
            {
                "label": "Oxygen reserve buffer",
                "value": "+12%",
                "effect": "Respiratory reserve support is currently lifting the oxygen network model.",
            }
        ],
        operator_activity=[
            {
                "timestamp": datetime(2026, 4, 5, 9, 2, tzinfo=UTC),
                "action_label": "Applied oxygen reserve protection",
            }
        ],
        patients=[
            {
                "patient_raw_id": "P00001",
                "name": "John Smith",
                "risk_score": 88,
            }
        ],
    )

    assert handoff["status"] == "critical"
    assert handoff["status_label"] == "Critical pressure"
    assert handoff["command_snapshot"]
    assert any("oxygen" in risk.lower() for risk in handoff["immediate_risks"])
    assert handoff["active_interventions"]
    assert handoff["recent_actions"][0].endswith("Applied oxygen reserve protection")
    assert any("Hospital ops lead" in step for step in handoff["next_steps"])
    assert "## Recommended Next Steps" in handoff["markdown"]
    assert handoff["export_filename"].startswith("icu-incident-handoff-")


def test_bed_heatmap_supports_surge_bed_bonus():
    patients = [
        {
            "patient_id": f"patient-{index}",
            "patient_raw_id": f"P{index:05d}",
            "name": f"Patient {index}",
            "age": 40,
            "ward": "ICU-1",
            "parity_flag": "even",
            "last_bpm": 120,
            "last_oxygen": 90,
            "has_active_alert": index < 3,
            "risk_score": 70,
            "risk_label": "High",
            "recommended_unit": "ICU",
            "risk_reasons": ["Escalation"],
        }
        for index in range(14)
    ]

    base_beds, _, base_overflow = _build_bed_heatmap(
        patients,
        virtual_admissions=0,
        surge_bed_bonus=0,
    )
    surge_beds, _, surge_overflow = _build_bed_heatmap(
        patients,
        virtual_admissions=0,
        surge_bed_bonus=2,
    )

    assert len(base_beds) == 12
    assert len(surge_beds) == 14
    assert surge_overflow < base_overflow


def test_resource_panels_honor_oxygen_and_staffing_boosts():
    patients = [
        {
            "risk_score": 88,
        },
        {
            "risk_score": 74,
        },
        {
            "risk_score": 58,
        },
    ]

    base_cards, _ = _build_resource_panels(
        patients,
        crisis_level=2,
        speed=1.0,
        virtual_admissions=2,
        oxygen_reserve_bonus=0,
        staffing_support_bonus=0,
    )
    boosted_cards, _ = _build_resource_panels(
        patients,
        crisis_level=2,
        speed=1.0,
        virtual_admissions=2,
        oxygen_reserve_bonus=12,
        staffing_support_bonus=3,
    )

    base_by_key = {card["resource_key"]: card for card in base_cards}
    boosted_by_key = {card["resource_key"]: card for card in boosted_cards}

    assert boosted_by_key["oxygen_network"]["available"] > base_by_key["oxygen_network"]["available"]
    assert boosted_by_key["critical_care_nurses"]["available"] > base_by_key["critical_care_nurses"]["available"]


def test_trust_and_recommended_actions_capture_pressure_signals():
    patients = [
        {
            "patient_id": "patient-1",
            "patient_raw_id": "P00001",
            "name": "John Smith",
            "last_bpm": 132,
            "last_oxygen": 87,
            "last_vitals_timestamp": "2026-04-04T11:59:55+00:00",
            "has_active_alert": True,
            "risk_score": 86,
            "risk_label": "Critical",
            "recommended_unit": "ICU",
            "risk_reasons": ["Open telemetry alert", "Low oxygen reserve"],
        }
    ]
    resource_cards = [
        {
            "resource_key": "oxygen_network",
            "label": "Oxygen network",
            "available": 18,
            "capacity": 100,
            "unit": "%",
            "status": "critical",
            "trend": "falling",
        },
        {
            "resource_key": "critical_care_nurses",
            "label": "Critical care nurses",
            "available": 4,
            "capacity": 18,
            "unit": "staff",
            "status": "warning",
            "trend": "falling",
        },
    ]
    summary = {
        "overflow_patients": 3,
        "active_alerts": 1,
    }

    with patch(
        "app.services.operations_center._utcnow",
        return_value=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
    ):
        trust = _build_operations_trust(
            patients,
            state={
                "is_paused": False,
                "active_scenario": "oxygen_shortage",
                "crisis_level": 2,
            },
        )
        actions = _build_recommended_actions(
            summary=summary,
            resource_cards=resource_cards,
            trust=trust,
            state={"is_paused": False},
            patients=patients,
        )

    assert trust["telemetry_state"] == "live"
    assert trust["confidence_label"] in {"high", "medium"}
    assert "simulated" in trust["data_source"].lower()
    assert actions
    titles = " ".join(action["title"].lower() for action in actions)
    assert "surge" in titles or "step-down" in titles
    assert "oxygen" in titles
    assert all(action["projected_window_minutes"] == 30 for action in actions)
    assert any(action["projected_metrics"] for action in actions)
    assert any(action["action_type"] == "intervention" for action in actions)
    surge_action = next(
        action for action in actions if "surge" in action["title"].lower()
    )
    assert surge_action["state"] == "recommended"
    assert surge_action["can_apply"] is True
    assert any(
        metric["key"] == "overflow_patients" and metric["projected_value"] < metric["current_value"]
        for metric in surge_action["projected_metrics"]
    )
    oxygen_action = next(
        action for action in actions if "oxygen" in action["title"].lower()
    )
    assert oxygen_action["action_type"] == "intervention"
    assert any(
        metric["key"] == "oxygen_network" and metric["projected_value"] > metric["current_value"]
        for metric in oxygen_action["projected_metrics"]
    )


def test_recommended_actions_reflect_active_state_and_observed_metrics():
    patients = [
        {
            "patient_id": "patient-1",
            "patient_raw_id": "P00001",
            "name": "John Smith",
            "last_bpm": 132,
            "last_oxygen": 87,
            "last_vitals_timestamp": "2026-04-04T11:59:55+00:00",
            "has_active_alert": True,
            "risk_score": 86,
            "risk_label": "Critical",
            "recommended_unit": "ICU",
            "risk_reasons": ["Open telemetry alert", "Low oxygen reserve"],
        }
    ]
    resource_cards = [
        {
            "resource_key": "oxygen_network",
            "label": "Oxygen network",
            "available": 86,
            "capacity": 100,
            "unit": "%",
            "status": "normal",
            "trend": "stable",
        },
        {
            "resource_key": "critical_care_nurses",
            "label": "Critical care nurses",
            "available": 6,
            "capacity": 18,
            "unit": "staff",
            "status": "warning",
            "trend": "falling",
        },
    ]

    actions = _build_recommended_actions(
        summary={
            "overflow_patients": 6,
            "active_alerts": 1,
            "attention_patients": 3,
            "icu_capacity": 14,
        },
        resource_cards=resource_cards,
        trust={"telemetry_state": "live"},
        state={
            "is_paused": False,
            "surge_bed_bonus": 2,
            "oxygen_reserve_bonus": 0,
            "staffing_support_bonus": 0,
            "last_intervention_id": "open-surge-beds",
            "last_intervention_baseline": {
                "icu_capacity": 12,
                "overflow_patients": 8,
                "attention_patients": 4,
            },
        },
        patients=patients,
    )

    surge_action = next(action for action in actions if action["id"] == "open-surge-beds")

    assert surge_action["state"] == "active"
    assert surge_action["state_label"] == "2 surge beds active"
    assert surge_action["can_apply"] is True
    assert surge_action["apply_label"] == "Add 2 more surge beds"
    assert surge_action["observed_summary"] is not None
    assert any(
        metric["key"] == "icu_capacity"
        and metric["baseline_value"] == 12
        and metric["current_value"] == 14
        for metric in surge_action["observed_metrics"]
    )
    assert any(
        metric["key"] == "overflow_patients"
        and metric["baseline_value"] == 8
        and metric["current_value"] == 6
        for metric in surge_action["observed_metrics"]
    )


def test_recommended_actions_distinguish_control_and_advisory_guidance():
    actions = _build_recommended_actions(
        summary={
            "overflow_patients": 0,
            "active_alerts": 0,
            "attention_patients": 0,
            "icu_capacity": 12,
        },
        resource_cards=[
            {
                "resource_key": "oxygen_network",
                "label": "Oxygen network",
                "available": 92,
                "capacity": 100,
                "unit": "%",
                "status": "normal",
                "trend": "stable",
            },
            {
                "resource_key": "critical_care_nurses",
                "label": "Critical care nurses",
                "available": 9,
                "capacity": 18,
                "unit": "staff",
                "status": "normal",
                "trend": "stable",
            },
        ],
        trust={
            "telemetry_state": "watch",
            "confidence_reason": "Telemetry is outside the ideal freshness window.",
        },
        state={
            "is_paused": True,
        },
        patients=[],
    )

    validate_action = next(
        action for action in actions if action["id"] == "validate-telemetry-freshness"
    )
    resume_action = next(
        action for action in actions if action["id"] == "resume-simulator-when-ready"
    )

    assert validate_action["action_type"] == "advisory"
    assert validate_action["can_apply"] is False
    assert validate_action["apply_label"] is None
    assert validate_action["state_label"] == "Advisory guidance"
    assert resume_action["action_type"] == "control"
    assert resume_action["control_action"] == "resume"
    assert resume_action["can_apply"] is True
    assert resume_action["apply_label"] == "Resume twin"


def test_scenario_comparison_highlights_degraded_current_state():
    comparison = _build_scenario_comparison(
        baseline_summary={
            "icu_occupied": 10,
            "overflow_patients": 0,
            "active_alerts": 0,
            "average_risk_score": 34,
        },
        current_summary={
            "icu_occupied": 12,
            "overflow_patients": 3,
            "active_alerts": 2,
            "average_risk_score": 62,
        },
        baseline_resources=[
            {
                "resource_key": "oxygen_network",
                "label": "Oxygen network",
                "available": 74,
            }
        ],
        current_resources=[
            {
                "resource_key": "oxygen_network",
                "label": "Oxygen network",
                "available": 28,
            }
        ],
        state={"crisis_label": "Oxygen shortage"},
    )

    assert comparison["current_label"] == "Oxygen shortage"
    assert any(
        metric["key"] == "overflow_patients" and metric["status"] == "degraded"
        for metric in comparison["summary_metrics"]
    )
    assert any(
        metric["key"] == "oxygen_network" and metric["status"] == "degraded"
        for metric in comparison["resource_metrics"]
    )


def test_incident_replay_frames_create_checkpoint_story():
    timeline = [
        {
            "id": "overflow-3",
            "timestamp": datetime(2026, 4, 4, 12, 4, tzinfo=UTC),
            "event_type": "capacity",
            "severity": "critical",
            "title": "3 patients waiting for ICU routing",
            "description": "Overflow demand exceeds live bed capacity.",
            "patient_id": None,
            "bed_id": None,
        },
        {
            "id": "alert-1",
            "timestamp": datetime(2026, 4, 4, 12, 2, tzinfo=UTC),
            "event_type": "alert",
            "severity": "critical",
            "title": "Telemetry breach for John Smith",
            "description": "SpO2 and BPM require review.",
            "patient_id": "patient-1",
            "bed_id": None,
        },
    ]

    frames = _build_incident_replay_frames(
        timeline=timeline,
        summary={
            "icu_occupied": 12,
            "overflow_patients": 3,
            "active_alerts": 2,
            "attention_patients": 5,
        },
    )

    assert frames
    assert frames[0]["phase_label"] == "Current state"
    assert any(frame["overflow_patients"] < 3 for frame in frames[1:])
    assert any("overflow" in frame["focus_note"].lower() for frame in frames)


def test_apply_intervention_updates_state_and_emits_event():
    db = MagicMock()

    with patch(
        "app.services.operations_center.get_simulation_state",
        return_value={
            "is_paused": False,
            "speed": 1.0,
            "active_scenario": "baseline",
            "crisis_level": 0,
            "crisis_label": "Nominal operations",
            "virtual_admissions": 4,
            "surge_bed_bonus": 0,
            "oxygen_reserve_bonus": 0,
            "staffing_support_bonus": 0,
            "updated_at": "2026-04-05T09:00:00",
            "last_action": "reset",
        },
    ), patch(
        "app.services.operations_center.update_simulation_state"
    ) as update_state, patch(
        "app.services.operations_center.append_simulation_event"
    ) as append_event, patch(
        "app.services.operations_center.get_operations_overview",
        side_effect=[
            {
                "summary": {
                    "icu_capacity": 12,
                    "overflow_patients": 4,
                    "attention_patients": 2,
                    "active_alerts": 1,
                },
                "resource_cards": [
                    {"resource_key": "oxygen_network", "available": 72},
                    {"resource_key": "critical_care_nurses", "available": 4},
                ],
            },
            {"ok": True},
        ],
    ):
        result = apply_simulation_action(
            db,
            action="apply_intervention",
            intervention_id="open-surge-beds",
        )

    assert result == {"ok": True}
    update_state.assert_called_once()
    state_payload = update_state.call_args.kwargs
    assert state_payload["surge_bed_bonus"] == 2
    assert state_payload["virtual_admissions"] == 2
    assert state_payload["last_intervention_id"] == "open-surge-beds"
    assert state_payload["last_intervention_baseline"]["icu_capacity"] == 12
    assert state_payload["last_intervention_baseline"]["overflow_patients"] == 4
    assert state_payload["last_action_at"]
    append_event.assert_called_once()
    assert "surge beds" in append_event.call_args.args[0]["title"].lower()
    assert append_event.call_args.args[0]["action_key"] == "apply_intervention"
    assert append_event.call_args.args[0]["action_label"] == "Applied surge beds"


def test_step_down_intervention_updates_state_and_emits_event():
    db = MagicMock()

    with patch(
        "app.services.operations_center.get_simulation_state",
        return_value={
            "is_paused": False,
            "speed": 1.0,
            "active_scenario": "baseline",
            "crisis_level": 0,
            "crisis_label": "Nominal operations",
            "virtual_admissions": 0,
            "surge_bed_bonus": 4,
            "oxygen_reserve_bonus": 0,
            "staffing_support_bonus": 0,
            "updated_at": "2026-04-05T09:00:00",
            "last_action": "apply_intervention",
        },
    ), patch(
        "app.services.operations_center.update_simulation_state"
    ) as update_state, patch(
        "app.services.operations_center.append_simulation_event"
    ) as append_event, patch(
        "app.services.operations_center.get_operations_overview",
        side_effect=[
            {
                "summary": {
                    "icu_capacity": 16,
                    "overflow_patients": 0,
                    "attention_patients": 2,
                    "active_alerts": 0,
                },
                "resource_cards": [
                    {"resource_key": "oxygen_network", "available": 72},
                    {"resource_key": "critical_care_nurses", "available": 4},
                ],
            },
            {"ok": True},
        ],
    ):
        result = apply_simulation_action(
            db,
            action="step_down_intervention",
            intervention_id="open-surge-beds",
        )

    assert result == {"ok": True}
    update_state.assert_called_once()
    state_payload = update_state.call_args.kwargs
    assert state_payload["surge_bed_bonus"] == 2
    assert state_payload["virtual_admissions"] == 2
    assert state_payload["last_action"] == "step_down_intervention"
    assert state_payload["last_intervention_id"] == "open-surge-beds"
    assert state_payload["last_intervention_baseline"]["icu_capacity"] == 16
    assert state_payload["last_action_at"]
    append_event.assert_called_once()
    assert "stepped down" in append_event.call_args.args[0]["title"].lower()
    assert append_event.call_args.args[0]["action_key"] == "step_down_intervention"
    assert append_event.call_args.args[0]["action_label"] == "Stepped down surge beds"


def test_clear_intervention_updates_state_and_emits_event():
    db = MagicMock()

    with patch(
        "app.services.operations_center.get_simulation_state",
        return_value={
            "is_paused": False,
            "speed": 1.0,
            "active_scenario": "baseline",
            "crisis_level": 0,
            "crisis_label": "Nominal operations",
            "virtual_admissions": 1,
            "surge_bed_bonus": 0,
            "oxygen_reserve_bonus": 12,
            "staffing_support_bonus": 0,
            "updated_at": "2026-04-05T09:00:00",
            "last_action": "apply_intervention",
        },
    ), patch(
        "app.services.operations_center.update_simulation_state"
    ) as update_state, patch(
        "app.services.operations_center.append_simulation_event"
    ) as append_event, patch(
        "app.services.operations_center.get_operations_overview",
        side_effect=[
            {
                "summary": {
                    "icu_capacity": 12,
                    "overflow_patients": 1,
                    "attention_patients": 2,
                    "active_alerts": 1,
                },
                "resource_cards": [
                    {"resource_key": "oxygen_network", "available": 84},
                    {"resource_key": "critical_care_nurses", "available": 4},
                ],
            },
            {"ok": True},
        ],
    ):
        result = apply_simulation_action(
            db,
            action="clear_intervention",
            intervention_id="protect-oxygen-reserve",
        )

    assert result == {"ok": True}
    update_state.assert_called_once()
    state_payload = update_state.call_args.kwargs
    assert state_payload["oxygen_reserve_bonus"] == 0
    assert state_payload["last_action"] == "clear_intervention"
    assert state_payload["last_intervention_id"] == "protect-oxygen-reserve"
    assert state_payload["last_intervention_baseline"]["oxygen_network"] == 84
    assert state_payload["last_action_at"]
    append_event.assert_called_once()
    assert "cleared" in append_event.call_args.args[0]["title"].lower()
    assert append_event.call_args.args[0]["action_key"] == "clear_intervention"
    assert (
        append_event.call_args.args[0]["action_label"]
        == "Cleared oxygen reserve protection"
    )


def test_timeline_handles_mixed_naive_and_aware_timestamps():
    db = MagicMock()
    db.execute.return_value.mappings.return_value.all.return_value = [
        {
            "id": 1,
            "patient_id": "patient-1",
            "opened_at": datetime(2026, 4, 4, 12, 5, tzinfo=UTC),
            "last_bpm": 132,
            "last_oxygen": 88,
            "patient_name_cipher": "JOHNSMITH",
        }
    ]

    bed_tiles = [
        {
            "bed_id": "ICU-01",
            "patient": {
                "patient_id": "patient-2",
                "patient_raw_id": "P00002",
                "patient_name": "Jane Doe",
                "risk_score": 84,
                "recommended_unit": "ICU",
            },
        }
    ]

    with patch(
        "app.services.operations_center.get_simulation_events",
        return_value=[
            {
                "id": "sim-1",
                "timestamp": "2026-04-04T12:00:00",
                "event_type": "simulation",
                "severity": "normal",
                "title": "Simulation resumed",
                "description": "Baseline playback resumed.",
                "patient_id": None,
                "bed_id": None,
            }
        ],
    ):
        timeline = _build_timeline(
            db,
            bed_tiles=bed_tiles,
            overflow_count=1,
            state={"is_paused": True, "updated_at": "2026-04-04T12:10:00"},
        )

    assert timeline
    assert all(event["timestamp"].tzinfo is not None for event in timeline)
