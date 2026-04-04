"""
Live Simulator - Generates fake telemetry every 5 seconds for demo purposes
Run this alongside the backend to make the dashboard feel alive.
"""

import time
import random
from datetime import UTC, datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.identity import PatientAlias
from app.services.alert_engine import process_vitals_for_alerts
from app.services.identity_reconciler import ensure_patient_aliases
from app.services.ops_store import get_simulation_state
from app.services.telemetry_writer import insert_clean_sample


def get_active_patient_raw_ids(db: Session):
    """Get list of patient raw IDs that currently have aliases."""

    patients = db.query(PatientAlias.patient_raw_id).distinct().all()
    return [p[0] for p in patients]


def simulate_vitals_batch(
    db: Session,
    patient_raw_ids: list[str],
    *,
    simulation_state: dict | None = None,
):
    """Generate one batch of new vitals for all patients."""
    state = simulation_state or {}
    crisis_level = int(state.get("crisis_level", 0))
    active_scenario = str(state.get("active_scenario", "baseline"))
    abnormal_probability = min(0.1 + crisis_level * 0.08, 0.55)

    for raw_id in patient_raw_ids:
        aliases_by_slot = ensure_patient_aliases(raw_id, db)
        if not aliases_by_slot:
            continue

        now = datetime.now(UTC)
        for _, alias in sorted(aliases_by_slot.items()):
            if random.random() < abnormal_probability:
                bpm = random.choice(
                    [
                        random.randint(max(35, 40 - crisis_level * 2), 58),
                        random.randint(102 + crisis_level * 4, 145 + crisis_level * 6),
                    ]
                )
            else:
                bpm = random.randint(60, min(108 + crisis_level * 3, 130))

            if active_scenario == "oxygen_shortage":
                spo2 = random.randint(max(80, 90 - crisis_level * 3), 97)
            elif active_scenario == "acuity_cluster":
                spo2 = random.randint(max(84, 91 - crisis_level * 2), 98)
            else:
                spo2 = random.randint(max(88, 94 - crisis_level), 100)

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


def run_simulator(interval: float | None = None):
    """Main simulator loop."""
    base_interval = float(interval or settings.SIMULATOR_INTERVAL_SECONDS)

    print("=" * 60)
    print(" LAZARUS Live Simulator")
    print(f" Generating telemetry every {base_interval} seconds")
    print(" Press Ctrl+C to stop")
    print("=" * 60)
    print()

    batch = 0
    waiting_for_patients = False
    try:
        while True:
            simulation_state = get_simulation_state()
            speed = float(simulation_state.get("speed", 1.0) or 1.0)
            effective_interval = max(1.0, base_interval / max(speed, 0.5))

            if simulation_state.get("is_paused"):
                print("  Simulation paused. Waiting for resume signal...")
                time.sleep(1.0)
                continue

            try:
                db = SessionLocal()
                try:
                    patients = get_active_patient_raw_ids(db)
                    if not patients:
                        if not waiting_for_patients:
                            print("No patients found yet. Waiting for seed bootstrap to finish...")
                            waiting_for_patients = True
                        time.sleep(2.0)
                        continue

                    if waiting_for_patients:
                        print(f"Simulating vitals for {len(patients)} patients...")
                        print()
                        waiting_for_patients = False

                    batch += 1
                    simulate_vitals_batch(
                        db,
                        patients,
                        simulation_state=simulation_state,
                    )
                finally:
                    db.close()

                print(
                    "  Batch "
                    f"{batch}: Generated vitals for {len(patients)} patients at "
                    f"{datetime.now(UTC).strftime('%H:%M:%S')} "
                    f"(speed={speed:.1f}x, scenario={simulation_state.get('active_scenario', 'baseline')})"
                )
                time.sleep(effective_interval)
            except SQLAlchemyError as exc:
                print(f"Database error in simulator loop: {exc}. Retrying in 3 seconds...")
                time.sleep(3.0)
            except Exception as exc:  # noqa: BLE001 - keep demo worker resilient
                print(f"Simulator loop error: {exc}. Retrying in 3 seconds...")
                time.sleep(3.0)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    run_simulator()
