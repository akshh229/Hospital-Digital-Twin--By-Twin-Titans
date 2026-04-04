"""Schemas for development-only QA helpers."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TelemetrySimulationRequest(BaseModel):
    patient_id: UUID
    bpm: int = Field(ge=20, le=220)
    oxygen: int = Field(ge=50, le=100)
    source_device: str = Field(default="DEV_PANEL", min_length=1, max_length=50)


class TelemetrySimulationResponse(BaseModel):
    patient_id: UUID
    patient_raw_id: str
    requested_bpm: int
    applied_bpm: int
    oxygen: int
    parity_flag: str
    adjusted_for_identity: bool
    timestamp: datetime
    alert_status: str | None = None
