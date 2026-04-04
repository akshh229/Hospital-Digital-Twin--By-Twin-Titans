"""
WebSocket server for patient vitals streaming.

The telemetry processor runs independently from the FastAPI process, so this
endpoint watches database state and emits deltas instead of depending on
in-memory broadcast helpers.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text

from app.config import settings
from app.database import SessionLocal
from app.services.recovery_projection import RECOVERY_CTES, hydrate_name_fields

router = APIRouter()


def _serialize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in mapping.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            serialized[key] = value
        elif hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = str(value)
    return serialized


def _snapshot_signature(snapshot: Any) -> str:
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"))


def _get_patient_snapshot(patient_id: str) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        row = (
            db.execute(
                text(
                    RECOVERY_CTES
                    + """
                    SELECT
                        pa.patient_id,
                        rd.name_cipher AS patient_name_cipher,
                        latest_vitals.bpm AS last_bpm,
                        latest_vitals.oxygen AS last_oxygen,
                        latest_vitals.timestamp AS last_vitals_timestamp,
                        EXISTS(
                            SELECT 1
                            FROM patient_alerts
                            WHERE patient_alerts.patient_id = pa.patient_id
                              AND status = 'open'
                        ) AS has_active_alert
                    FROM patient_alias pa
                    LEFT JOIN recovered_demographics rd
                        ON rd.patient_raw_id = pa.patient_raw_id
                       AND rd.parity_flag = pa.parity_flag
                    LEFT JOIN LATERAL (
                        SELECT bpm, oxygen, timestamp
                        FROM resolved_telemetry rt
                        WHERE rt.patient_raw_id = pa.patient_raw_id
                          AND rt.resolved_parity = pa.parity_flag
                        ORDER BY timestamp DESC, id DESC
                        LIMIT 1
                    ) latest_vitals ON true
                    WHERE pa.patient_id = :patient_id
                    """
                ),
                {"patient_id": patient_id},
            )
            .mappings()
            .first()
        )

        if row is None:
            return None

        snapshot = hydrate_name_fields(
            [dict(row)],
            cipher_key="patient_name_cipher",
            output_key="patient_name",
        )[0]
        timestamp = snapshot.get("last_vitals_timestamp")
        snapshot["last_vitals_timestamp"] = (
            timestamp.isoformat() if timestamp is not None else None
        )
        snapshot["has_active_alert"] = bool(snapshot.get("has_active_alert"))
        return snapshot
    finally:
        db.close()


def _get_patients_snapshot() -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
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
                ORDER BY has_active_alert DESC, rd.age ASC NULLS LAST, pa.patient_raw_id ASC, pa.parity_flag ASC
                LIMIT 100
                """
            )
        ).mappings()

        hydrated = hydrate_name_fields(
            [dict(row) for row in rows],
            cipher_key="name_cipher",
            output_key="name",
        )
        return [_serialize_mapping(row) for row in hydrated]
    finally:
        db.close()


def _get_alerts_snapshot() -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                RECOVERY_CTES
                + """
                SELECT
                    pa.id,
                    pa.patient_id,
                    pa.alert_type,
                    pa.opened_at,
                    pa.last_bpm,
                    pa.last_oxygen,
                    pa.status,
                    pa.consecutive_abnormal_count,
                    rd.name_cipher AS patient_name_cipher,
                    rd.age,
                    rd.ward
                FROM patient_alerts pa
                LEFT JOIN patient_alias paa ON pa.patient_id = paa.patient_id
                LEFT JOIN recovered_demographics rd
                  ON rd.patient_raw_id = paa.patient_raw_id
                 AND rd.parity_flag = paa.parity_flag
                WHERE pa.status = 'open'
                ORDER BY pa.opened_at DESC
                """
            )
        ).mappings()

        hydrated = hydrate_name_fields(
            [dict(row) for row in rows],
            cipher_key="patient_name_cipher",
            output_key="patient_name",
        )
        return [_serialize_mapping(row) for row in hydrated]
    finally:
        db.close()


def _has_vitals_changed(
    previous_snapshot: dict[str, Any] | None, current_snapshot: dict[str, Any]
) -> bool:
    if current_snapshot.get("last_vitals_timestamp") is None:
        return False

    if previous_snapshot is None:
        return True

    tracked_fields = ("last_vitals_timestamp", "last_bpm", "last_oxygen")
    return any(
        previous_snapshot.get(field) != current_snapshot.get(field)
        for field in tracked_fields
    )


def _build_vitals_message(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "vitals_update",
        "patient_id": str(snapshot["patient_id"]),
        "timestamp": snapshot["last_vitals_timestamp"],
        "bpm": snapshot["last_bpm"],
        "oxygen": snapshot["last_oxygen"],
    }


def _build_alert_message(
    previous_snapshot: dict[str, Any], current_snapshot: dict[str, Any]
) -> dict[str, Any] | None:
    if previous_snapshot.get("has_active_alert") == current_snapshot.get("has_active_alert"):
        return None

    if current_snapshot.get("has_active_alert"):
        return {
            "type": "alert_opened",
            "patient_id": str(current_snapshot["patient_id"]),
            "patient_name": current_snapshot.get("patient_name") or "Unknown",
            "last_bpm": current_snapshot.get("last_bpm"),
        }

    return {
        "type": "alert_closed",
        "patient_id": str(current_snapshot["patient_id"]),
    }


@router.websocket("/overview")
async def overview_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for dashboard-level patient and alert snapshots."""
    await websocket.accept()

    patients_snapshot = await run_in_threadpool(_get_patients_snapshot)
    alerts_snapshot = await run_in_threadpool(_get_alerts_snapshot)
    patients_signature = _snapshot_signature(patients_snapshot)
    alerts_signature = _snapshot_signature(alerts_snapshot)

    await websocket.send_json(
        {"type": "patients_snapshot", "patients": patients_snapshot}
    )
    await websocket.send_json({"type": "alerts_snapshot", "alerts": alerts_snapshot})

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WS_POLL_INTERVAL_SECONDS,
                )
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    continue

                if message.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )
            except asyncio.TimeoutError:
                current_patients = await run_in_threadpool(_get_patients_snapshot)
                current_alerts = await run_in_threadpool(_get_alerts_snapshot)
                current_patients_signature = _snapshot_signature(current_patients)
                current_alerts_signature = _snapshot_signature(current_alerts)

                if current_patients_signature != patients_signature:
                    await websocket.send_json(
                        {"type": "patients_snapshot", "patients": current_patients}
                    )
                    patients_snapshot = current_patients
                    patients_signature = current_patients_signature

                if current_alerts_signature != alerts_signature:
                    await websocket.send_json(
                        {"type": "alerts_snapshot", "alerts": current_alerts}
                    )
                    alerts_snapshot = current_alerts
                    alerts_signature = current_alerts_signature

    except WebSocketDisconnect:
        return


@router.websocket("/vitals/{patient_id}")
async def vitals_websocket_endpoint(websocket: WebSocket, patient_id: str):
    """
    WebSocket endpoint for patient vitals monitoring.

    The server emits vitals and alert deltas whenever database state changes.
    Clients may optionally send {"type": "ping"} heartbeats.
    """
    await websocket.accept()

    snapshot = await run_in_threadpool(_get_patient_snapshot, patient_id)
    if snapshot is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if _has_vitals_changed(None, snapshot):
        await websocket.send_json(_build_vitals_message(snapshot))

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WS_POLL_INTERVAL_SECONDS,
                )
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    continue

                if message.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )
            except asyncio.TimeoutError:
                current_snapshot = await run_in_threadpool(_get_patient_snapshot, patient_id)
                if current_snapshot is None:
                    await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                    return

                if _has_vitals_changed(snapshot, current_snapshot):
                    await websocket.send_json(_build_vitals_message(current_snapshot))

                alert_message = _build_alert_message(snapshot, current_snapshot)
                if alert_message is not None:
                    await websocket.send_json(alert_message)

                snapshot = current_snapshot

    except WebSocketDisconnect:
        return
