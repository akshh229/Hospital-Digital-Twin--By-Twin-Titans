"""Refresh patient_view for parity-safe identity recovery

Revision ID: 004
Revises: 003
Create Date: 2026-03-29
"""

from alembic import op

# revision identifiers
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DROP MATERIALIZED VIEW IF EXISTS patient_view CASCADE;

        CREATE MATERIALIZED VIEW patient_view AS
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
                tr.sample_slot,
                sa.resolved_parity
            FROM telemetry_ranked tr
            JOIN slot_assignments sa
              ON sa.patient_raw_id = tr.patient_raw_id
             AND sa.sample_slot = tr.sample_slot
        ),
        ranked_demographics AS (
            SELECT
                cd.id,
                cd.patient_raw_id,
                cd.decoded_name,
                cd.age,
                cd.ward,
                ROW_NUMBER() OVER (
                    PARTITION BY cd.patient_raw_id
                    ORDER BY cd.id
                ) AS demographic_rank,
                COUNT(*) OVER (PARTITION BY cd.patient_raw_id) AS demographic_count
            FROM clean_demographics cd
        ),
        recovered_demographics AS (
            SELECT
                rd.patient_raw_id,
                sa.resolved_parity AS parity_flag,
                rd.decoded_name,
                rd.age,
                rd.ward
            FROM ranked_demographics rd
            LEFT JOIN slot_assignments sa
              ON sa.patient_raw_id = rd.patient_raw_id
             AND sa.sample_slot = rd.demographic_rank
            WHERE rd.demographic_count = 1 OR rd.demographic_rank <= 2
        )
        SELECT
            pa.patient_id,
            pa.patient_raw_id,
            pa.parity_flag,
            rd.decoded_name,
            rd.age,
            rd.ward,
            latest_vitals.bpm AS last_bpm,
            latest_vitals.oxygen AS last_oxygen,
            latest_vitals.timestamp AS last_vitals_timestamp,
            latest_vitals.quality_flag,
            COALESCE(presc_count.cnt, 0) AS prescription_count,
            EXISTS(
                SELECT 1
                FROM patient_alerts
                WHERE patient_alerts.patient_id = pa.patient_id
                  AND patient_alerts.status = 'open'
            ) AS has_active_alert
        FROM patient_alias pa
        LEFT JOIN recovered_demographics rd
          ON rd.patient_raw_id = pa.patient_raw_id
         AND rd.parity_flag = pa.parity_flag
        LEFT JOIN LATERAL (
            SELECT bpm, oxygen, timestamp, quality_flag
            FROM resolved_telemetry rt
            WHERE rt.patient_raw_id = pa.patient_raw_id
              AND rt.resolved_parity = pa.parity_flag
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
        ) latest_vitals ON true
        LEFT JOIN (
            SELECT cp.patient_raw_id, rd_inner.parity_flag, COUNT(*) AS cnt
            FROM clean_prescriptions cp
            JOIN recovered_demographics rd_inner
              ON rd_inner.patient_raw_id = cp.patient_raw_id
             AND rd_inner.age = cp.age
            GROUP BY cp.patient_raw_id, rd_inner.parity_flag
        ) presc_count
          ON presc_count.patient_raw_id = pa.patient_raw_id
         AND presc_count.parity_flag = pa.parity_flag;

        CREATE UNIQUE INDEX idx_patient_view_id ON patient_view(patient_id);
        """
    )


def downgrade():
    op.execute(
        """
        DROP MATERIALIZED VIEW IF EXISTS patient_view CASCADE;

        CREATE MATERIALIZED VIEW patient_view AS
        SELECT
            pa.patient_id,
            pa.patient_raw_id,
            pa.parity_flag,
            cd.decoded_name,
            cd.age,
            cd.ward,
            latest_vitals.bpm AS last_bpm,
            latest_vitals.oxygen AS last_oxygen,
            latest_vitals.timestamp AS last_vitals_timestamp,
            latest_vitals.quality_flag,
            COALESCE(presc_count.cnt, 0) AS prescription_count,
            EXISTS(
                SELECT 1 FROM patient_alerts
                WHERE patient_alerts.patient_id = pa.patient_id
                AND patient_alerts.status = 'open'
            ) AS has_active_alert
        FROM patient_alias pa
        LEFT JOIN clean_demographics cd ON cd.patient_raw_id = pa.patient_raw_id
        LEFT JOIN LATERAL (
            SELECT bpm, oxygen, timestamp, quality_flag
            FROM clean_telemetry ct
            WHERE ct.patient_raw_id = pa.patient_raw_id
                AND ct.parity_flag = pa.parity_flag
                AND ct.quality_flag = 'good'
            ORDER BY timestamp DESC
            LIMIT 1
        ) latest_vitals ON true
        LEFT JOIN (
            SELECT patient_raw_id, COUNT(*) AS cnt
            FROM clean_prescriptions
            GROUP BY patient_raw_id
        ) presc_count ON presc_count.patient_raw_id = pa.patient_raw_id;

        CREATE UNIQUE INDEX idx_patient_view_id ON patient_view(patient_id);
        """
    )
