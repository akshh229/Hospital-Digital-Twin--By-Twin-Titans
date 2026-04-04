"""
Vitals API Endpoints
Provides time-series vitals data for charts
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.identity import PatientAlias
from app.schemas.telemetry import VitalsTimeSeriesResponse
from app.services.recovery_projection import RECOVERY_CTES
from app.services.vitals_interpolator import interpolate_oxygen_series

router = APIRouter()


@router.get("/patients/{patient_id}/vitals", response_model=VitalsTimeSeriesResponse)
async def get_patient_vitals(
    patient_id: UUID,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """Get time-series vitals data for patient charts."""
    alias = db.query(PatientAlias).filter(PatientAlias.patient_id == patient_id).first()

    if not alias:
        raise HTTPException(status_code=404, detail="Patient not found")

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    vitals = db.execute(
        text(
            RECOVERY_CTES
            + """
            SELECT timestamp, bpm, oxygen, quality_flag
            FROM resolved_telemetry
            WHERE patient_raw_id = :patient_raw_id
              AND resolved_parity = :parity_flag
              AND timestamp >= :start_time
              AND timestamp <= :end_time
            ORDER BY timestamp ASC, id ASC
            """
        ),
        {
            "patient_raw_id": alias.patient_raw_id,
            "parity_flag": alias.parity_flag,
            "start_time": start_time,
            "end_time": end_time,
        },
    ).mappings()

    data_points = [
        {
            "timestamp": v["timestamp"],
            "bpm": v["bpm"],
            "oxygen": v["oxygen"],
            "quality_flag": v["quality_flag"],
        }
        for v in vitals
    ]
    data_points = interpolate_oxygen_series(data_points)

    return {
        "patient_id": patient_id,
        "start_time": start_time,
        "end_time": end_time,
        "data": data_points,
    }
