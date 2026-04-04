"""Identity reconciliation models"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Numeric,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class PatientAlias(Base):
    """Maps (raw_id, parity) to unique patient_id"""

    __tablename__ = "patient_alias"

    id = Column(Integer, primary_key=True, index=True)
    patient_raw_id = Column(String(50), nullable=False)
    parity_flag = Column(String(4), nullable=False)
    patient_id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sample_count = Column(Integer, default=1)
    confidence_score = Column(Numeric(3, 2), default=0.5)

    __table_args__ = (
        UniqueConstraint(
            "patient_raw_id", "parity_flag", name="uq_patient_alias_raw_parity"
        ),
        CheckConstraint("parity_flag IN ('even', 'odd')", name="ck_alias_parity_flag"),
    )


class IdentityAuditLog(Base):
    """Audit trail for identity reconciliation decisions"""

    __tablename__ = "identity_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_raw_id = Column(String(50))
    parity_flag = Column(String(4))
    action = Column(String(50))
    bpm_samples_used = Column(Integer)
    decision_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
