"""
Live Simulator - Generates fake telemetry every 5 seconds for demo purposes
Run this alongside the backend to make the dashboard feel alive.
"""

import time
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.identity import PatientAlias
from app.services.alert_engine import process_vitals_for_alerts
from app.services.identity_reconciler import ensure_patient_aliases
from app.services.telemetry_writer import insert_clean_sample


def get_active_patient_raw_ids(db: Session):
    """Get list of patient raw IDs that currently have aliases."""

    patients = db.query(PatientAlias.patient_raw_id).distinct().all()
    return [p[0] for p in patients]


def simulate_vitals_batch(db: Session, patient_raw_ids: list[str]):
    """Generate one batch of new vitals for all patients."""
    for raw_id in patient_raw_ids:
        aliases_by_slot = ensure_patient_aliases(raw_id, db)
        if not aliases_by_slot:
            continue

        now = datetime.utcnow()
        for _, alias in sorted(aliases_by_slot.items()):
            if random.random() < 0.1:
                bpm = random.choice(
                    [
                        random.randint(40, 58),
                        random.randint(102, 145),
                    ]
                )
            else:
                bpm = random.randint(60, 100)

            spo2 = random.randint(94, 100)
            clean = insert_clean_sample(
                db,
                patient_raw_id=raw_id,
                parity_flag=alias.parity_flag,
                bpm=bpm,
                oxygen=spo2,
                source_device="SIMULATOR",
                timestamp=now,
            )

            process_vitals_for_alerts(alias.patient_id, clean.bpm, clean.oxygen, db)

    db.commit()


def run_simulator(interval: float = 5.0):
    """Main simulator loop."""
    print("=" * 60)
    print(" LAZARUS Live Simulator")
    print(f" Generating telemetry every {interval} seconds")
    print(" Press Ctrl+C to stop")
    print("=" * 60)
    print()

    db = SessionLocal()
    patients = get_active_patient_raw_ids(db)

    if not patients:
        print("No patients found in database.")
        print("Run seed data loader first: python seed_data/load_seeds.py")
        return

    print(f"Simulating vitals for {len(patients)} patients...")
    print()

    batch = 0
    try:
        while True:
            batch += 1
            simulate_vitals_batch(db, patients)
            print(
                f"  Batch {batch}: Generated vitals for {len(patients)} patients at {datetime.utcnow().strftime('%H:%M:%S')}"
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
    finally:
        db.close()


if __name__ == "__main__":
    run_simulator()
