"""Cleaned layer models - decoded and validated data"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from app.database import Base


class CleanTelemetry(Base):
    """Decoded telemetry with BPM, SpO2, and quality flags"""

    __tablename__ = "clean_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    patient_raw_id = Column(String(50), nullable=False, index=True)
    staging_log_id = Column(Integer, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    hex_payload = Column(Text)
    bpm = Column(Integer)
    oxygen = Column(Integer)
    parity_flag = Column(String(4))
    quality_flag = Column(String(10))
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("staging_log_id", name="uq_clean_telemetry_staging_log_id"),
        CheckConstraint("parity_flag IN ('even', 'odd')", name="ck_parity_flag"),
        CheckConstraint(
            "quality_flag IN ('good', 'bad', 'missing')", name="ck_quality_flag"
        ),
    )


class CleanPrescriptions(Base):
    """Decoded prescriptions with decrypted medication names"""

    __tablename__ = "clean_prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_raw_id = Column(String(50), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    med_cipher_text = Column(String(255), nullable=False)
    med_decoded_name = Column(String(255))
    dosage = Column(String(100))
    route = Column(String(50))
    processed_at = Column(DateTime(timezone=True), server_default=func.now())


class CleanDemographics(Base):
    """Decoded patient demographics"""

    __tablename__ = "clean_demographics"

    id = Column(Integer, primary_key=True, index=True)
    patient_raw_id = Column(String(50), nullable=False, index=True)
    name_cipher = Column(Text)
    decoded_name = Column(String(255))
    age = Column(Integer)
    ward = Column(String(50))
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
