"""Load seed data into database"""

import csv
from pathlib import Path
from datetime import datetime

from sqlalchemy import text

from app.database import SessionLocal
from app.models.staging import (
    StgPatientDemographics,
    StgTelemetryLogs,
    StgPrescriptionAudit,
)
from app.models.cleaned import CleanTelemetry, CleanPrescriptions, CleanDemographics
from app.services.telemetry_decoder import decode_telemetry
from app.services.cipher import decrypt_medication
from app.services.identity_reconciler import ensure_patient_aliases
from app.services.name_decoder import decode_patient_name

BASE_DIR = Path(__file__).parent


def load_staging_data():
    """Load CSV files into staging tables using batch inserts"""
    db = SessionLocal()

    print("Loading patient demographics...")
    with open(BASE_DIR / "patient_demographics.csv") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        db.bulk_save_objects([StgPatientDemographics(**row) for row in rows])
    db.commit()
    print(f"  Loaded {len(rows)} records")

    print("Loading telemetry logs...")
    with open(BASE_DIR / "telemetry_logs.csv") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row["timestamp"] = datetime.fromisoformat(row["timestamp"])
            rows.append(row)
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            db.bulk_save_objects([StgTelemetryLogs(**row) for row in batch])
            db.commit()
            print(f"  Loaded {min(i + batch_size, len(rows))}/{len(rows)}")
    print(f"  Done ({len(rows)} total)")

    print("Loading prescriptions...")
    with open(BASE_DIR / "prescription_audit.csv") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row["timestamp"] = datetime.fromisoformat(row["timestamp"])
            row["age"] = int(row["age"])
            rows.append(row)
        db.bulk_save_objects([StgPrescriptionAudit(**row) for row in rows])
    db.commit()
    print(f"  Loaded {len(rows)} records")

    db.close()


def process_telemetry():
    """Process staging telemetry into cleaned table"""
    db = SessionLocal()

    print("Processing telemetry...")
    staging = db.query(StgTelemetryLogs).all()

    processed = 0
    skipped = 0
    for record in staging:
        decoded = decode_telemetry(record.hex_payload)

        existing = (
            db.query(CleanTelemetry)
            .filter_by(staging_log_id=record.id)
            .first()
        )
        if existing:
            skipped += 1
            continue

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
        processed += 1

    db.commit()
    print(
        f"  Processed {len(staging)} records ({processed} new, {skipped} duplicates skipped)"
    )
    db.close()


def process_prescriptions():
    """Process staging prescriptions into cleaned table"""
    db = SessionLocal()

    print("Processing prescriptions...")
    staging = db.query(StgPrescriptionAudit).all()

    for record in staging:
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
    print(f"  Processed {len(staging)} records")
    db.close()

def process_demographics():
    """Process staging demographics into cleaned table"""
    db = SessionLocal()

    print("Processing demographics...")
    staging = db.query(StgPatientDemographics).all()

    for record in staging:
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
    print(f"  Processed {len(staging)} records")
    db.close()


def reconcile_identities():
    """Create patient aliases using telemetry slot parity recovery."""
    db = SessionLocal()

    print("Reconciling patient identities...")
    raw_ids = [row[0] for row in db.query(CleanTelemetry.patient_raw_id).distinct().all()]

    for raw_id in raw_ids:
        aliases = ensure_patient_aliases(raw_id, db)
        for alias in aliases.values():
            print(f"  {raw_id}/{alias.parity_flag} -> {alias.patient_id}")

    print("  Done")
    db.close()


def refresh_materialized_view():
    """Refresh patient view"""
    db = SessionLocal()
    db.execute(text("REFRESH MATERIALIZED VIEW patient_view"))
    db.commit()
    print("Refreshed materialized view")
    db.close()


if __name__ == "__main__":
    print("=" * 60)
    print(" LAZARUS - Seed Data Loader")
    print("=" * 60)
    print()

    load_staging_data()
    process_telemetry()
    process_prescriptions()
    process_demographics()
    reconcile_identities()
    refresh_materialized_view()

    print()
    print("Seed data loaded successfully!")
    print("  1. Start backend: uvicorn app.main:app --reload")
    print("  2. API docs: http://localhost:8000/docs")
    print("  3. Test: http://localhost:8000/api/patients")
