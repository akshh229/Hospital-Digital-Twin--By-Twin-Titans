"""Generate synthetic patient data for testing"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# Inline cipher functions (no app dependency needed for generation)
def encrypt_medication(plain_text: str, age: int) -> str:
    shift = age % 26
    result = []
    for char in plain_text.upper():
        if char.isalpha():
            pos = ord(char) - ord("A")
            new_pos = (pos + shift) % 26
            result.append(chr(ord("A") + new_pos))
        else:
            result.append(char)
    return "".join(result)


def encode_telemetry(bpm: int, spo2: int) -> str:
    bpm_bytes = bpm.to_bytes(2, byteorder="big")
    spo2_bytes = spo2.to_bytes(2, byteorder="big")
    return (bpm_bytes + spo2_bytes).hex()


BASE_DIR = Path(__file__).parent
PATIENTS = 20
COLLIDING_IDS = 5

MEDICATIONS = [
    "ASPIRIN",
    "INSULIN",
    "MORPHINE",
    "WARFARIN",
    "LISINOPRIL",
    "METFORMIN",
    "ATORVASTATIN",
    "AMLODIPINE",
    "OMEPRAZOLE",
    "GABAPENTIN",
]

WARDS = ["ICU-1", "ICU-2", "ICU-3", "Ward-4", "Ward-5", "ER"]

FIRST_NAMES = [
    "John",
    "Jane",
    "Robert",
    "Maria",
    "David",
    "Sarah",
    "Michael",
    "Emily",
    "James",
    "Linda",
    "William",
    "Patricia",
    "Richard",
    "Barbara",
    "Joseph",
    "Elizabeth",
    "Thomas",
    "Susan",
    "Charles",
    "Jessica",
]
LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
]


def generate_patients():
    """Generate patient demographics"""
    patients = []
    used_names = set()

    for i in range(PATIENTS):
        if i < COLLIDING_IDS * 2:
            raw_id = f"P{(i // 2) + 1:05d}"
        else:
            raw_id = f"P{i + 1:05d}"

        age = random.randint(18, 85)

        while True:
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            if name not in used_names:
                used_names.add(name)
                break

        name_cipher = name.upper().replace(" ", "")

        patients.append(
            {
                "patient_raw_id": raw_id,
                "name_cipher": name_cipher,
                "age": age,
                "ward_code": random.choice(WARDS),
            }
        )

    with open(BASE_DIR / "patient_demographics.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["patient_raw_id", "name_cipher", "age", "ward_code"]
        )
        writer.writeheader()
        writer.writerows(patients)

    return patients


def generate_telemetry(patients):
    """Generate telemetry logs - 1000 samples per patient over 24 hours"""
    telemetry = []
    start_time = datetime.now() - timedelta(hours=24)

    for patient in patients:
        patient_idx = int(patient["patient_raw_id"][1:]) - 1
        if patient_idx < COLLIDING_IDS * 2:
            if patient_idx % 2 == 0:
                base_bpm = 70  # Even parity patient
            else:
                base_bpm = 75  # Odd parity patient
        else:
            base_bpm = random.randint(60, 90)

        for j in range(1000):
            timestamp = start_time + timedelta(minutes=j * 1.44)

            bpm = base_bpm + random.randint(-10, 10)
            spo2 = random.randint(94, 100)

            # 5% corrupted samples
            if random.random() < 0.05:
                if random.random() < 0.5:
                    hex_payload = "DEADBEEF"
                else:
                    bpm = random.randint(250, 300)
                    hex_payload = encode_telemetry(bpm, spo2)
            else:
                hex_payload = encode_telemetry(bpm, spo2)

            telemetry.append(
                {
                    "patient_raw_id": patient["patient_raw_id"],
                    "timestamp": timestamp.isoformat(),
                    "hex_payload": hex_payload,
                    "source_device": f"MONITOR_{random.randint(1, 10)}",
                }
            )

    with open(BASE_DIR / "telemetry_logs.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["patient_raw_id", "timestamp", "hex_payload", "source_device"],
        )
        writer.writeheader()
        writer.writerows(telemetry)

    return telemetry


def generate_prescriptions(patients):
    """Generate prescriptions with age-encrypted medication names"""
    prescriptions = []

    for patient in patients:
        num_meds = random.randint(3, 8)

        for _ in range(num_meds):
            med_name = random.choice(MEDICATIONS)
            age = patient["age"]
            med_cipher = encrypt_medication(med_name, age)

            prescriptions.append(
                {
                    "patient_raw_id": patient["patient_raw_id"],
                    "timestamp": (
                        datetime.now() - timedelta(hours=random.randint(1, 72))
                    ).isoformat(),
                    "age": age,
                    "med_cipher_text": med_cipher,
                    "dosage": f"{random.choice([2, 5, 10, 25, 50, 100])}mg",
                    "route": random.choice(["PO", "IV", "SC", "IM"]),
                }
            )

    with open(BASE_DIR / "prescription_audit.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "patient_raw_id",
                "timestamp",
                "age",
                "med_cipher_text",
                "dosage",
                "route",
            ],
        )
        writer.writeheader()
        writer.writerows(prescriptions)

    return prescriptions


if __name__ == "__main__":
    print("Generating seed data...")

    patients = generate_patients()
    print(f"  Generated {len(patients)} patients")

    telemetry = generate_telemetry(patients)
    print(f"  Generated {len(telemetry)} telemetry samples")

    prescriptions = generate_prescriptions(patients)
    print(f"  Generated {len(prescriptions)} prescriptions")

    print("\nSeed data generated successfully!")
    print("  - patient_demographics.csv")
    print("  - telemetry_logs.csv")
    print("  - prescription_audit.csv")
