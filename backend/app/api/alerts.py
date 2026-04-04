"""
Alerts API Endpoints
Critical vitals alerts management
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.alerts import PatientAlert
from app.schemas.alert import AlertResponse, AlertHistoryResponse
from app.services.alert_engine import get_patient_alert_history
from app.services.recovery_projection import RECOVERY_CTES, hydrate_name_fields

router = APIRouter()


@router.get("/alerts", response_model=List[AlertResponse])
async def list_active_alerts(db: Session = Depends(get_db)):
    """Get all currently open critical alerts."""
    query = text(
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

    result = db.execute(query)
    alerts = hydrate_name_fields(
        [dict(row._mapping) for row in result],
        cipher_key="patient_name_cipher",
        output_key="patient_name",
    )
    return alerts


@router.get("/alerts/history/{patient_id}", response_model=List[AlertHistoryResponse])
async def get_alert_history(patient_id: UUID, db: Session = Depends(get_db)):
    """Get alert history for a specific patient."""
    alerts = get_patient_alert_history(patient_id, db)

    return [
        {
            "id": a.id,
            "opened_at": a.opened_at,
            "closed_at": a.closed_at,
            "duration_minutes": int((a.closed_at - a.opened_at).total_seconds() / 60)
            if a.closed_at
            else None,
            "last_bpm": a.last_bpm,
            "last_oxygen": a.last_oxygen,
            "status": a.status,
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark alert as acknowledged by clinician."""
    alert = db.query(PatientAlert).filter(PatientAlert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    if alert.closed_at is None:
        alert.closed_at = datetime.utcnow()
    db.commit()

    return {"status": "acknowledged", "alert_id": alert_id}
