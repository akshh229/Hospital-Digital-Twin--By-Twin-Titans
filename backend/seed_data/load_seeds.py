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
from app.models.identity import PatientAlias
from app.services.telemetry_decoder import decode_telemetry
from app.services.cipher import decrypt_medication
from app.services.identity_reconciler import ensure_patient_aliases
from app.services.name_decoder import decode_patient_name

BASE_DIR = Path(__file__).parent


def collect_seed_counts() -> dict[str, int]:
    """Return lightweight table counts so bootstrap logic can decide quickly."""

    db = SessionLocal()
    try:
        return {
            "staging_demographics": db.query(StgPatientDemographics).count(),
            "staging_telemetry": db.query(StgTelemetryLogs).count(),
            "staging_prescriptions": db.query(StgPrescriptionAudit).count(),
            "clean_telemetry": db.query(CleanTelemetry).count(),
            "clean_prescriptions": db.query(CleanPrescriptions).count(),
            "clean_demographics": db.query(CleanDemographics).count(),
            "patient_alias": db.query(PatientAlias).count(),
        }
    finally:
        db.close()


def seed_dataset_ready(counts: dict[str, int] | None = None) -> bool:
    """Return True when the core seeded dataset is already available."""

    snapshot = counts or collect_seed_counts()
    required_tables = (
        "staging_demographics",
        "staging_telemetry",
        "staging_prescriptions",
        "clean_telemetry",
        "clean_prescriptions",
        "clean_demographics",
        "patient_alias",
    )
    return all(snapshot.get(table_name, 0) > 0 for table_name in required_tables)


def _print_seed_counts(counts: dict[str, int]) -> None:
    print("Current seed state:")
    for table_name, count in counts.items():
        print(f"  - {table_name}: {count}")


def load_staging_data():
    """Load CSV files into staging tables using batch inserts"""
    db = SessionLocal()

    print("Loading patient demographics...")
    with open(BASE_DIR / "patient_demographics.csv") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row["age"] = int(row["age"])
            rows.append(row)

        existing_keys = {
            (patient_raw_id, name_cipher, age, ward_code)
            for patient_raw_id, name_cipher, age, ward_code in db.query(
                StgPatientDemographics.patient_raw_id,
                StgPatientDemographics.name_cipher,
                StgPatientDemographics.age,
                StgPatientDemographics.ward_code,
            ).all()
        }
        new_rows = []
        skipped = 0
        for row in rows:
            key = (
                row["patient_raw_id"],
                row["name_cipher"],
                row["age"],
                row["ward_code"],
            )
            if key in existing_keys:
                skipped += 1
                continue
            existing_keys.add(key)
            new_rows.append(row)

        if new_rows:
            db.bulk_save_objects([StgPatientDemographics(**row) for row in new_rows])
    db.commit()
    print(f"  Loaded {len(new_rows)} new records ({skipped} duplicates skipped)")

    print("Loading telemetry logs...")
    with open(BASE_DIR / "telemetry_logs.csv") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row["timestamp"] = datetime.fromisoformat(row["timestamp"])
            rows.append(row)

        existing_keys = {
            (patient_raw_id, timestamp, hex_payload, source_device)
            for patient_raw_id, timestamp, hex_payload, source_device in db.query(
                StgTelemetryLogs.patient_raw_id,
                StgTelemetryLogs.timestamp,
                StgTelemetryLogs.hex_payload,
                StgTelemetryLogs.source_device,
            ).all()
        }
        new_rows = []
        skipped = 0
        for row in rows:
            key = (
                row["patient_raw_id"],
                row["timestamp"],
                row["hex_payload"],
                row["source_device"],
            )
            if key in existing_keys:
                skipped += 1
                continue
            existing_keys.add(key)
            new_rows.append(row)

        batch_size = 1000
        for i in range(0, len(new_rows), batch_size):
            batch = new_rows[i : i + batch_size]
            db.bulk_save_objects([StgTelemetryLogs(**row) for row in batch])
            db.commit()
            print(f"  Loaded {min(i + batch_size, len(new_rows))}/{len(new_rows)} new records")
    print(f"  Done ({len(new_rows)} new, {skipped} duplicates skipped)")

    print("Loading prescriptions...")
    with open(BASE_DIR / "prescription_audit.csv") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row["timestamp"] = datetime.fromisoformat(row["timestamp"])
            row["age"] = int(row["age"])
            rows.append(row)

        existing_keys = {
            (patient_raw_id, timestamp, age, med_cipher_text, dosage, route)
            for patient_raw_id, timestamp, age, med_cipher_text, dosage, route in db.query(
                StgPrescriptionAudit.patient_raw_id,
                StgPrescriptionAudit.timestamp,
                StgPrescriptionAudit.age,
                StgPrescriptionAudit.med_cipher_text,
                StgPrescriptionAudit.dosage,
                StgPrescriptionAudit.route,
            ).all()
        }
        new_rows = []
        skipped = 0
        for row in rows:
            key = (
                row["patient_raw_id"],
                row["timestamp"],
                row["age"],
                row["med_cipher_text"],
                row["dosage"],
                row["route"],
            )
            if key in existing_keys:
                skipped += 1
                continue
            existing_keys.add(key)
            new_rows.append(row)

        if new_rows:
            db.bulk_save_objects([StgPrescriptionAudit(**row) for row in new_rows])
    db.commit()
    print(f"  Loaded {len(new_rows)} new records ({skipped} duplicates skipped)")

    db.close()


def process_telemetry():
    """Process staging telemetry into cleaned table"""
    db = SessionLocal()

    print("Processing telemetry...")
    staging = db.query(StgTelemetryLogs).all()
    existing_staging_ids = {
        staging_log_id
        for (staging_log_id,) in db.query(CleanTelemetry.staging_log_id)
        .filter(CleanTelemetry.staging_log_id.isnot(None))
        .all()
    }

    processed = 0
    skipped = 0
    for record in staging:
        if record.id in existing_staging_ids:
            skipped += 1
            continue

        decoded = decode_telemetry(record.hex_payload)
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
        existing_staging_ids.add(record.id)
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
    existing_keys = {
        (patient_raw_id, age, timestamp, med_cipher_text, dosage, route)
        for patient_raw_id, age, timestamp, med_cipher_text, dosage, route in db.query(
            CleanPrescriptions.patient_raw_id,
            CleanPrescriptions.age,
            CleanPrescriptions.timestamp,
            CleanPrescriptions.med_cipher_text,
            CleanPrescriptions.dosage,
            CleanPrescriptions.route,
        ).all()
    }

    processed = 0
    skipped = 0
    for record in staging:
        key = (
            record.patient_raw_id,
            record.age,
            record.timestamp,
            record.med_cipher_text,
            record.dosage,
            record.route,
        )
        if key in existing_keys:
            skipped += 1
            continue

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
        existing_keys.add(key)
        processed += 1

    db.commit()
    print(
        f"  Processed {len(staging)} records ({processed} new, {skipped} duplicates skipped)"
    )
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


def run_seed_pipeline():
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


if __name__ == "__main__":
    run_seed_pipeline()
