"""Create patient_view materialized view

Revision ID: 002
Revises: 001
Create Date: 2026-03-29
"""

from alembic import op

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
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
    """)


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS patient_view")
