"""Alert system models"""

from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class PatientAlert(Base):
    """Critical vitals alerts with debouncing logic"""

    __tablename__ = "patient_alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    alert_type = Column(String(50), default="critical_vitals")
    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True))
    status = Column(String(20))
    last_bpm = Column(Integer)
    last_oxygen = Column(Integer)
    consecutive_abnormal_count = Column(Integer, default=1)
    consecutive_normal_count = Column(Integer, default=0)
    alert_metadata = Column("metadata", JSONB)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'open', 'closed', 'acknowledged')",
            name="ck_alert_status",
        ),
    )
