"""
Recovery projection helpers.

Builds parity-aware identity projections from the raw staging demographics and
the recovered clean telemetry stream. This lets the API expose two distinct
patients for a colliding raw ID without rewriting the storage schema.
"""

from collections.abc import Iterable

from app.services.name_decoder import decode_patient_name


RECOVERY_CTES = """
WITH telemetry_ranked AS (
    SELECT
        ct.id,
        ct.patient_raw_id,
        ct.timestamp,
        ct.bpm,
        ct.oxygen,
        ct.quality_flag,
        ct.parity_flag,
        ROW_NUMBER() OVER (
            PARTITION BY ct.patient_raw_id, ct.timestamp
            ORDER BY ct.id
        ) AS sample_slot
    FROM clean_telemetry ct
    WHERE ct.quality_flag = 'good'
),
slot_profiles AS (
    SELECT
        patient_raw_id,
        sample_slot,
        COUNT(*) AS sample_count,
        SUM(CASE WHEN parity_flag = 'even' THEN 1 ELSE 0 END) AS even_count,
        SUM(CASE WHEN parity_flag = 'odd' THEN 1 ELSE 0 END) AS odd_count
    FROM telemetry_ranked
    GROUP BY patient_raw_id, sample_slot
),
slot_ranked AS (
    SELECT
        sp.*,
        COUNT(*) OVER (PARTITION BY sp.patient_raw_id) AS slot_count,
        ROW_NUMBER() OVER (
            PARTITION BY sp.patient_raw_id
            ORDER BY (sp.even_count::float / NULLIF(sp.sample_count, 0)) DESC, sp.sample_slot ASC
        ) AS even_rank
    FROM slot_profiles sp
),
slot_assignments AS (
    SELECT
        patient_raw_id,
        sample_slot,
        sample_count,
        CASE
            WHEN slot_count = 1 THEN
                CASE WHEN even_count >= odd_count THEN 'even' ELSE 'odd' END
            WHEN even_rank = 1 THEN 'even'
            ELSE 'odd'
        END AS resolved_parity,
        CASE
            WHEN slot_count = 1 THEN
                ROUND(GREATEST(even_count, odd_count)::numeric / NULLIF(sample_count, 0), 2)
            WHEN even_rank = 1 THEN
                ROUND(even_count::numeric / NULLIF(sample_count, 0), 2)
            ELSE
                ROUND(odd_count::numeric / NULLIF(sample_count, 0), 2)
        END AS confidence_score
    FROM slot_ranked
),
resolved_telemetry AS (
    SELECT
        tr.id,
        tr.patient_raw_id,
        tr.timestamp,
        tr.bpm,
        tr.oxygen,
        tr.quality_flag,
        tr.parity_flag,
        tr.sample_slot,
        sa.resolved_parity,
        sa.sample_count AS identity_sample_count,
        sa.confidence_score
    FROM telemetry_ranked tr
    JOIN slot_assignments sa
      ON sa.patient_raw_id = tr.patient_raw_id
     AND sa.sample_slot = tr.sample_slot
),
ranked_demographics AS (
    SELECT
        sd.patient_raw_id,
        sd.name_cipher,
        sd.age,
        sd.ward_code,
        ROW_NUMBER() OVER (
            PARTITION BY sd.patient_raw_id
            ORDER BY sd.id
        ) AS demographic_rank,
        COUNT(*) OVER (PARTITION BY sd.patient_raw_id) AS demographic_count
    FROM stg_patient_demographics sd
),
recovered_demographics AS (
    SELECT
        rd.patient_raw_id,
        sa.resolved_parity AS parity_flag,
        rd.name_cipher,
        rd.age,
        rd.ward_code AS ward,
        rd.demographic_rank,
        rd.demographic_count
    FROM ranked_demographics rd
    LEFT JOIN slot_assignments sa
      ON sa.patient_raw_id = rd.patient_raw_id
     AND sa.sample_slot = rd.demographic_rank
    WHERE rd.demographic_count = 1 OR rd.demographic_rank <= 2
)
"""


def hydrate_name_fields(
    rows: Iterable[dict],
    *,
    cipher_key: str,
    output_key: str,
) -> list[dict]:
    """Decode name ciphers in SQL result payloads."""

    hydrated: list[dict] = []
    for row in rows:
        payload = dict(row)
        payload[output_key] = decode_patient_name(payload.pop(cipher_key, None))
        hydrated.append(payload)
    return hydrated
