"""Staging layer models - raw data, no transformations"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class StgPatientDemographics(Base):
    """Raw patient demographics - preserves all original data"""

    __tablename__ = "stg_patient_demographics"

    id = Column(Integer, primary_key=True, index=True)
    patient_raw_id = Column(String(50), nullable=False, index=True)
    name_cipher = Column(Text)
    age = Column(Integer)
    ward_code = Column(String(10))
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())


class StgTelemetryLogs(Base):
    """Raw telemetry logs - hex payloads untouched"""

    __tablename__ = "stg_telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_raw_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    hex_payload = Column(Text, nullable=False)
    source_device = Column(String(50))
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())


class StgPrescriptionAudit(Base):
    """Raw prescription audit - encrypted medication names"""

    __tablename__ = "stg_prescription_audit"

    id = Column(Integer, primary_key=True, index=True)
    patient_raw_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    age = Column(Integer, nullable=False)
    med_cipher_text = Column(String(255), nullable=False)
    dosage = Column(String(100))
    route = Column(String(50))
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
