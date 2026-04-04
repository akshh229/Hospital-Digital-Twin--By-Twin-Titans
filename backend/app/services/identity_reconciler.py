"""Identity reconciliation helpers for parity-derived patient aliases."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.identity import IdentityAuditLog, PatientAlias


SLOT_PROFILES_QUERY = text(
    """
    WITH ranked_samples AS (
        SELECT
            ct.id,
            ct.patient_raw_id,
            ct.timestamp,
            ct.parity_flag,
            ROW_NUMBER() OVER (
                PARTITION BY ct.patient_raw_id, ct.timestamp
                ORDER BY ct.id
            ) AS sample_slot
        FROM clean_telemetry ct
        WHERE ct.patient_raw_id = :patient_raw_id
          AND ct.quality_flag = 'good'
    )
    SELECT
        sample_slot,
        COUNT(*) AS sample_count,
        SUM(CASE WHEN parity_flag = 'even' THEN 1 ELSE 0 END) AS even_count,
        SUM(CASE WHEN parity_flag = 'odd' THEN 1 ELSE 0 END) AS odd_count
    FROM ranked_samples
    GROUP BY sample_slot
    ORDER BY sample_slot
    """
)

ROW_SLOT_QUERY = text(
    """
    WITH ranked_samples AS (
        SELECT
            ct.id,
            ROW_NUMBER() OVER (
                PARTITION BY ct.patient_raw_id, ct.timestamp
                ORDER BY ct.id
            ) AS sample_slot
        FROM clean_telemetry ct
        WHERE ct.patient_raw_id = :patient_raw_id
          AND ct.quality_flag = 'good'
    )
    SELECT sample_slot
    FROM ranked_samples
    WHERE id = :telemetry_id
    """
)


def _build_slot_profiles(patient_raw_id: str, db: Session) -> list[dict]:
    rows = db.execute(
        SLOT_PROFILES_QUERY, {"patient_raw_id": patient_raw_id}
    ).mappings()

    profiles = []
    for row in rows:
        sample_count = int(row["sample_count"])
        even_count = int(row["even_count"] or 0)
        odd_count = int(row["odd_count"] or 0)
        profiles.append(
            {
                "sample_slot": int(row["sample_slot"]),
                "sample_count": sample_count,
                "even_count": even_count,
                "odd_count": odd_count,
                "even_share": (even_count / sample_count) if sample_count else 0.0,
                "odd_share": (odd_count / sample_count) if sample_count else 0.0,
            }
        )
    return profiles


def _assign_slot_parities(profiles: list[dict]) -> dict[int, dict]:
    if not profiles:
        return {}

    if len(profiles) == 1:
        profile = profiles[0]
        parity = "even" if profile["even_count"] >= profile["odd_count"] else "odd"
        confidence = round(
            max(profile["even_share"], profile["odd_share"]),
            2,
        )
        return {
            profile["sample_slot"]: {
                "parity_flag": parity,
                "sample_count": profile["sample_count"],
                "confidence_score": confidence,
            }
        }

    assignments: dict[int, dict] = {}
    sorted_by_even = sorted(
        profiles,
        key=lambda profile: (profile["even_share"], -profile["sample_slot"]),
        reverse=True,
    )

    even_profile = sorted_by_even[0]
    assignments[even_profile["sample_slot"]] = {
        "parity_flag": "even",
        "sample_count": even_profile["sample_count"],
        "confidence_score": round(even_profile["even_share"], 2),
    }

    for profile in sorted_by_even[1:]:
        assignments[profile["sample_slot"]] = {
            "parity_flag": "odd",
            "sample_count": profile["sample_count"],
            "confidence_score": round(profile["odd_share"], 2),
        }

    return assignments


def _upsert_alias(
    patient_raw_id: str,
    parity_flag: str,
    sample_count: int,
    confidence_score: float,
    db: Session,
) -> PatientAlias:
    alias = (
        db.query(PatientAlias)
        .filter_by(patient_raw_id=patient_raw_id, parity_flag=parity_flag)
        .first()
    )

    if alias is not None:
        alias.sample_count = sample_count
        alias.confidence_score = confidence_score
        return alias

    alias = PatientAlias(
        patient_raw_id=patient_raw_id,
        parity_flag=parity_flag,
        sample_count=sample_count,
        confidence_score=confidence_score,
    )
    db.add(alias)
    db.flush()

    audit = IdentityAuditLog(
        patient_id=alias.patient_id,
        patient_raw_id=patient_raw_id,
        parity_flag=parity_flag,
        action="created",
        bpm_samples_used=sample_count,
        decision_reason=(
            f"Recovered slot mapped to {parity_flag} identity "
            f"({confidence_score:.0%} confidence from {sample_count} samples)"
        ),
    )
    db.add(audit)
    return alias


def ensure_patient_aliases(patient_raw_id: str, db: Session) -> dict[int, PatientAlias]:
    """Create or refresh parity aliases for a raw ID based on telemetry slot profiles."""

    profiles = _build_slot_profiles(patient_raw_id, db)
    slot_assignments = _assign_slot_parities(profiles)

    aliases_by_slot: dict[int, PatientAlias] = {}
    if not slot_assignments:
        return aliases_by_slot

    try:
        for sample_slot, assignment in slot_assignments.items():
            aliases_by_slot[sample_slot] = _upsert_alias(
                patient_raw_id=patient_raw_id,
                parity_flag=assignment["parity_flag"],
                sample_count=assignment["sample_count"],
                confidence_score=assignment["confidence_score"],
                db=db,
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        for sample_slot, assignment in slot_assignments.items():
            alias = (
                db.query(PatientAlias)
                .filter_by(
                    patient_raw_id=patient_raw_id,
                    parity_flag=assignment["parity_flag"],
                )
                .first()
            )
            if alias is None:
                raise
            alias.sample_count = assignment["sample_count"]
            alias.confidence_score = assignment["confidence_score"]
            aliases_by_slot[sample_slot] = alias
        db.commit()

    return aliases_by_slot


def reconcile_patient_identity(patient_raw_id: str, telemetry_id: int, db: Session) -> UUID:
    """
    Resolve one telemetry sample to the correct reconstructed patient identity.

    Samples are first grouped into per-timestamp slots, then those slots are
    assigned to even/odd identities based on their long-run parity bias.
    """

    aliases_by_slot = ensure_patient_aliases(patient_raw_id, db)
    if not aliases_by_slot:
        raise ValueError(f"No telemetry slots found for {patient_raw_id}")

    row = db.execute(
        ROW_SLOT_QUERY,
        {"patient_raw_id": patient_raw_id, "telemetry_id": telemetry_id},
    ).first()
    if row is None:
        raise ValueError(f"Telemetry row {telemetry_id} not found for {patient_raw_id}")

    sample_slot = int(row[0])
    alias = aliases_by_slot.get(sample_slot)
    if alias is None:
        raise ValueError(
            f"No alias assignment found for {patient_raw_id} sample slot {sample_slot}"
        )

    return alias.patient_id
