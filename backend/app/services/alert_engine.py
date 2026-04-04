"""
Alert Engine - Debounced critical vitals monitoring
"""

from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.alerts import PatientAlert
from app.config import settings


def process_vitals_for_alerts(patient_id: UUID, bpm: int, oxygen: int, db: Session):
    """
    Check vitals and manage alert lifecycle with debouncing.

    Rules:
    - Open alert: Requires 2 consecutive abnormal samples
    - Close alert: Requires 2 consecutive normal samples
    - Abnormal: BPM < 60 or BPM > 100
    """
    is_abnormal = bpm < settings.ALERT_BPM_LOW or bpm > settings.ALERT_BPM_HIGH

    open_alert = (
        db.query(PatientAlert)
        .filter_by(patient_id=patient_id, status="open")
        .order_by(PatientAlert.opened_at.desc())
        .first()
    )

    if is_abnormal:
        if open_alert:
            open_alert.last_bpm = bpm
            open_alert.last_oxygen = oxygen
            open_alert.consecutive_abnormal_count += 1
            open_alert.consecutive_normal_count = 0
        else:
            recent_closed = (
                db.query(PatientAlert)
                .filter_by(patient_id=patient_id)
                .filter(PatientAlert.status.in_(["closed", "pending"]))
                .order_by(PatientAlert.opened_at.desc())
                .first()
            )

            if (
                recent_closed
                and recent_closed.consecutive_abnormal_count
                < settings.ALERT_DEBOUNCE_COUNT
            ):
                recent_closed.status = "open"
                recent_closed.closed_at = None
                recent_closed.consecutive_abnormal_count += 1
                recent_closed.last_bpm = bpm
                recent_closed.last_oxygen = oxygen
            else:
                alert = PatientAlert(
                    patient_id=patient_id,
                    status="pending",
                    opened_at=datetime.utcnow(),
                    last_bpm=bpm,
                    last_oxygen=oxygen,
                    consecutive_abnormal_count=1,
                    consecutive_normal_count=0,
                )
                db.add(alert)
    else:
        if open_alert:
            open_alert.consecutive_normal_count += 1
            open_alert.consecutive_abnormal_count = 0

            if open_alert.consecutive_normal_count >= settings.ALERT_DEBOUNCE_COUNT:
                open_alert.status = "closed"
                open_alert.closed_at = datetime.utcnow()

    db.commit()


def get_open_alerts(db: Session):
    """Get all currently open alerts"""
    return (
        db.query(PatientAlert)
        .filter_by(status="open")
        .order_by(PatientAlert.opened_at.desc())
        .all()
    )


def get_patient_alert_history(patient_id: UUID, db: Session):
    """Get alert history for a patient"""
    return (
        db.query(PatientAlert)
        .filter_by(patient_id=patient_id)
        .filter(PatientAlert.status.in_(["closed", "acknowledged"]))
        .order_by(PatientAlert.closed_at.desc())
        .limit(20)
        .all()
    )
