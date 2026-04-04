"""Development-only API helpers for demos and QA."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.alerts import PatientAlert
from app.models.identity import PatientAlias
from app.schemas.devtools import (
    TelemetrySimulationRequest,
    TelemetrySimulationResponse,
)
from app.services.alert_engine import process_vitals_for_alerts
from app.services.identity_reconciler import ensure_patient_aliases
from app.services.telemetry_writer import align_bpm_to_parity, insert_clean_sample

router = APIRouter()


@router.post(
    "/dev/simulate-telemetry",
    response_model=TelemetrySimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def simulate_telemetry(
    payload: TelemetrySimulationRequest,
    db: Session = Depends(get_db),
):
    """Insert one synthetic telemetry sample for a patient during local QA."""

    if settings.ENVIRONMENT.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Telemetry simulation is disabled in production.",
        )

    alias = (
        db.query(PatientAlias)
        .filter(PatientAlias.patient_id == payload.patient_id)
        .first()
    )
    if alias is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient alias not found.",
        )

    applied_bpm = align_bpm_to_parity(payload.bpm, alias.parity_flag)
    timestamp = datetime.utcnow()
    aliases_by_slot = ensure_patient_aliases(alias.patient_raw_id, db)
    target_slot = next(
        (
            slot
            for slot, mapped_alias in aliases_by_slot.items()
            if mapped_alias.patient_id == alias.patient_id
        ),
        1,
    )

    for slot in sorted(slot for slot in aliases_by_slot if slot < target_slot):
        companion_alias = aliases_by_slot[slot]
        insert_clean_sample(
            db,
            patient_raw_id=alias.patient_raw_id,
            parity_flag=companion_alias.parity_flag,
            bpm=76,
            oxygen=98,
            source_device=f"{payload.source_device}-COMPANION",
            timestamp=timestamp,
        )

    insert_clean_sample(
        db,
        patient_raw_id=alias.patient_raw_id,
        parity_flag=alias.parity_flag,
        bpm=payload.bpm,
        oxygen=payload.oxygen,
        source_device=payload.source_device,
        timestamp=timestamp,
    )

    process_vitals_for_alerts(payload.patient_id, applied_bpm, payload.oxygen, db)

    latest_alert = (
        db.query(PatientAlert)
        .filter(PatientAlert.patient_id == payload.patient_id)
        .order_by(PatientAlert.opened_at.desc())
        .first()
    )

    return TelemetrySimulationResponse(
        patient_id=payload.patient_id,
        patient_raw_id=alias.patient_raw_id,
        requested_bpm=payload.bpm,
        applied_bpm=applied_bpm,
        oxygen=payload.oxygen,
        parity_flag=alias.parity_flag,
        adjusted_for_identity=applied_bpm != payload.bpm,
        timestamp=timestamp,
        alert_status=latest_alert.status if latest_alert else None,
    )
