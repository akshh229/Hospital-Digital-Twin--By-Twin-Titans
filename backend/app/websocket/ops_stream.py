"""WebSocket stream for the ICU operations dashboard."""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder

from app.config import settings
from app.database import SessionLocal
from app.services.operations_center import get_operations_overview

router = APIRouter()


def _get_ops_snapshot() -> dict:
    db = SessionLocal()
    try:
        return get_operations_overview(db)
    finally:
        db.close()


def _encode_snapshot(snapshot: dict) -> dict:
    return jsonable_encoder(snapshot)


def _snapshot_signature(snapshot: dict) -> str:
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"))


@router.websocket("/overview")
async def operations_overview_websocket(websocket: WebSocket):
    """Push command-center overview snapshots whenever operations state changes."""
    await websocket.accept()

    snapshot = _encode_snapshot(await run_in_threadpool(_get_ops_snapshot))
    signature = _snapshot_signature(snapshot)
    await websocket.send_json({"type": "ops_snapshot", "overview": snapshot})

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
                current_snapshot = _encode_snapshot(
                    await run_in_threadpool(_get_ops_snapshot)
                )
                current_signature = _snapshot_signature(current_snapshot)
                if current_signature != signature:
                    await websocket.send_json(
                        {"type": "ops_snapshot", "overview": current_snapshot}
                    )
                    snapshot = current_snapshot
                    signature = current_signature
    except WebSocketDisconnect:
        return
