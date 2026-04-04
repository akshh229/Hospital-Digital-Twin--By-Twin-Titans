"""Shared simulation state store for the ICU operations center."""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime
from threading import Lock
from typing import Any
from uuid import uuid4

import redis

from app.config import settings


SIMULATION_STATE_KEY = "ops:simulation_state"
SIMULATION_EVENTS_KEY = "ops:simulation_events"
SIMULATION_EVENT_LIMIT = 80

_DEFAULT_STATE = {
    "is_paused": False,
    "speed": 1.0,
    "active_scenario": "baseline",
    "crisis_level": 0,
    "crisis_label": "Nominal operations",
    "virtual_admissions": 0,
    "surge_bed_bonus": 0,
    "oxygen_reserve_bonus": 0,
    "staffing_support_bonus": 0,
    "last_intervention_id": None,
    "last_intervention_at": None,
    "last_intervention_baseline": {},
    "updated_at": "",
    "last_action": "initialize",
}

_redis_client: redis.Redis | None = None
_redis_checked = False
_local_lock = Lock()
_local_state: dict[str, Any] | None = None
_local_events: deque[dict[str, Any]] = deque(maxlen=SIMULATION_EVENT_LIMIT)


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _normalize_state(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    state = dict(_DEFAULT_STATE)
    if payload:
        state.update(payload)

    if not state.get("updated_at"):
        state["updated_at"] = _now_iso()
    return state


def _get_redis_client() -> redis.Redis | None:
    global _redis_client, _redis_checked

    if _redis_checked:
        return _redis_client

    _redis_checked = True
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=0.5,
            socket_connect_timeout=0.5,
        )
        client.ping()
        _redis_client = client
    except Exception:
        _redis_client = None

    return _redis_client


def get_simulation_state() -> dict[str, Any]:
    client = _get_redis_client()
    if client is not None:
        raw = client.get(SIMULATION_STATE_KEY)
        if raw:
            return _normalize_state(json.loads(raw))

        state = _normalize_state()
        client.set(SIMULATION_STATE_KEY, json.dumps(state))
        return state

    global _local_state
    with _local_lock:
        if _local_state is None:
            _local_state = _normalize_state()
        return dict(_local_state)


def update_simulation_state(**updates: Any) -> dict[str, Any]:
    current_state = get_simulation_state()
    current_state.update(updates)
    current_state["updated_at"] = _now_iso()

    client = _get_redis_client()
    if client is not None:
        client.set(SIMULATION_STATE_KEY, json.dumps(current_state))
        return current_state

    global _local_state
    with _local_lock:
        _local_state = dict(current_state)
    return current_state


def reset_simulation_state() -> dict[str, Any]:
    state = _normalize_state()
    state["last_action"] = "reset"

    client = _get_redis_client()
    if client is not None:
        client.set(SIMULATION_STATE_KEY, json.dumps(state))
        client.delete(SIMULATION_EVENTS_KEY)
        return state

    global _local_state
    with _local_lock:
        _local_state = dict(state)
        _local_events.clear()
    return state


def append_simulation_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event)
    payload.setdefault("id", f"evt-{uuid4().hex[:10]}")
    payload.setdefault("timestamp", _now_iso())

    client = _get_redis_client()
    if client is not None:
        client.lpush(SIMULATION_EVENTS_KEY, json.dumps(payload))
        client.ltrim(SIMULATION_EVENTS_KEY, 0, SIMULATION_EVENT_LIMIT - 1)
        return payload

    with _local_lock:
        _local_events.appendleft(payload)
    return payload


def get_simulation_events(limit: int = 25) -> list[dict[str, Any]]:
    client = _get_redis_client()
    if client is not None:
        rows = client.lrange(SIMULATION_EVENTS_KEY, 0, max(limit - 1, 0))
        return [json.loads(row) for row in rows]

    with _local_lock:
        return list(_local_events)[:limit]
