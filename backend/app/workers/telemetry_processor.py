"""
Telemetry Processor - Background worker that processes staging data into cleaned tables
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.staging import (
    StgTelemetryLogs,
    StgPrescriptionAudit,
    StgPatientDemographics,
)
from app.models.cleaned import CleanTelemetry, CleanPrescriptions, CleanDemographics
from app.services.telemetry_decoder import decode_telemetry
from app.services.cipher import decrypt_medication
from app.services.identity_reconciler import reconcile_patient_identity
from app.services.name_decoder import decode_patient_name
from app.services.alert_engine import process_vitals_for_alerts


def process_unprocessed_telemetry(db: Session = None):
    """Process all unprocessed telemetry from staging to cleaned."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        staging_records = db.query(StgTelemetryLogs).all()

        for record in staging_records:
            decoded = decode_telemetry(record.hex_payload)

            existing = (
                db.query(CleanTelemetry)
                .filter_by(staging_log_id=record.id)
                .first()
            )

            if not existing:
                clean = CleanTelemetry(
                    staging_log_id=record.id,
                    patient_raw_id=record.patient_raw_id,
                    timestamp=record.timestamp,
                    hex_payload=record.hex_payload,
                    bpm=decoded["bpm"],
                    oxygen=decoded["oxygen"],
                    parity_flag=decoded["parity_flag"],
                    quality_flag=decoded["quality_flag"],
                )
                db.add(clean)
                db.flush()

                if decoded["quality_flag"] == "good" and decoded["bpm"]:
                    try:
                        patient_id = reconcile_patient_identity(record.patient_raw_id, clean.id, db)
                        process_vitals_for_alerts(
                            patient_id, decoded["bpm"], decoded["oxygen"] or 0, db
                        )
                    except Exception:
                        pass

        db.commit()
        return len(staging_records)
    finally:
        if close_db:
            db.close()


def process_unprocessed_prescriptions(db: Session = None):
    """Process all unprocessed prescriptions from staging to cleaned."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        staging_records = db.query(StgPrescriptionAudit).all()

        for record in staging_records:
            decoded_name = decrypt_medication(record.med_cipher_text, record.age)

            clean = CleanPrescriptions(
                patient_raw_id=record.patient_raw_id,
                age=record.age,
                timestamp=record.timestamp,
                med_cipher_text=record.med_cipher_text,
                med_decoded_name=decoded_name,
                dosage=record.dosage,
                route=record.route,
            )
            db.add(clean)

        db.commit()
        return len(staging_records)
    finally:
        if close_db:
            db.close()


def process_unprocessed_demographics(db: Session = None):
    """Process all unprocessed demographics from staging to cleaned."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        staging_records = db.query(StgPatientDemographics).all()

        for record in staging_records:
            existing = (
                db.query(CleanDemographics)
                .filter_by(patient_raw_id=record.patient_raw_id)
                .first()
            )

            if existing:
                existing.name_cipher = record.name_cipher
                existing.decoded_name = decode_patient_name(record.name_cipher)
                existing.age = record.age
                existing.ward = record.ward_code
                continue

            clean = CleanDemographics(
                patient_raw_id=record.patient_raw_id,
                name_cipher=record.name_cipher,
                decoded_name=decode_patient_name(record.name_cipher),
                age=record.age,
                ward=record.ward_code,
            )
            db.add(clean)

        db.commit()
        return len(staging_records)
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    print("Running telemetry processor...")
    n = process_unprocessed_telemetry()
    print(f"  Processed {n} telemetry records")
    n = process_unprocessed_prescriptions()
    print(f"  Processed {n} prescription records")
    n = process_unprocessed_demographics()
    print(f"  Processed {n} demographic records")
    print("Done")
