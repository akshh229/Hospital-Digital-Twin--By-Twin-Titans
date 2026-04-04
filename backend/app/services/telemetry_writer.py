"""Helpers for writing alias-aware telemetry samples into staging and clean layers."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models.cleaned import CleanTelemetry
from app.models.staging import StgTelemetryLogs
from app.services.telemetry_decoder import encode_telemetry


def align_bpm_to_parity(bpm: int, parity_flag: str) -> int:
    """Adjust a BPM value so it matches the target alias parity."""

    wants_even = parity_flag == "even"
    is_even = bpm % 2 == 0

    if wants_even == is_even:
        return bpm

    if bpm < settings.BPM_MAX:
        return bpm + 1

    return bpm - 1


def insert_clean_sample(
    db: Session,
    *,
    patient_raw_id: str,
    parity_flag: str,
    bpm: int,
    oxygen: int,
    source_device: str,
    timestamp: datetime | None = None,
) -> CleanTelemetry:
    """Insert one telemetry sample into staging and clean tables."""

    sample_time = timestamp or datetime.utcnow()
    applied_bpm = align_bpm_to_parity(bpm, parity_flag)
    hex_payload = encode_telemetry(applied_bpm, oxygen)

    staging = StgTelemetryLogs(
        patient_raw_id=patient_raw_id,
        timestamp=sample_time,
        hex_payload=hex_payload,
        source_device=source_device,
    )
    db.add(staging)
    db.flush()

    clean = CleanTelemetry(
        staging_log_id=staging.id,
        patient_raw_id=patient_raw_id,
        timestamp=sample_time,
        hex_payload=hex_payload,
        bpm=applied_bpm,
        oxygen=oxygen,
        parity_flag=parity_flag,
        quality_flag="good",
    )
    db.add(clean)
    db.flush()
    return clean
