"""${message}

Revision ID: 001
Revises:
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Staging tables
    op.create_table(
        "stg_patient_demographics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_raw_id", sa.String(50), nullable=False),
        sa.Column("name_cipher", sa.Text()),
        sa.Column("age", sa.Integer()),
        sa.Column("ward_code", sa.String(10)),
        sa.Column(
            "ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stg_demographics_raw_id", "stg_patient_demographics", ["patient_raw_id"]
    )

    op.create_table(
        "stg_telemetry_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_raw_id", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hex_payload", sa.Text(), nullable=False),
        sa.Column("source_device", sa.String(50)),
        sa.Column(
            "ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stg_telemetry_raw_id", "stg_telemetry_logs", ["patient_raw_id"])
    op.create_index("ix_stg_telemetry_timestamp", "stg_telemetry_logs", ["timestamp"])

    op.create_table(
        "stg_prescription_audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_raw_id", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("med_cipher_text", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100)),
        sa.Column("route", sa.String(50)),
        sa.Column(
            "ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stg_prescription_raw_id", "stg_prescription_audit", ["patient_raw_id"]
    )

    # Cleaned tables
    op.create_table(
        "clean_telemetry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_raw_id", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hex_payload", sa.Text()),
        sa.Column("bpm", sa.Integer()),
        sa.Column("oxygen", sa.Integer()),
        sa.Column("parity_flag", sa.String(4)),
        sa.Column("quality_flag", sa.String(10)),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "patient_raw_id", "timestamp", name="uq_clean_telemetry_patient_timestamp"
        ),
        sa.CheckConstraint("parity_flag IN ('even', 'odd')", name="ck_parity_flag"),
        sa.CheckConstraint(
            "quality_flag IN ('good', 'bad', 'missing')", name="ck_quality_flag"
        ),
    )
    op.create_index("ix_clean_telemetry_raw_id", "clean_telemetry", ["patient_raw_id"])
    op.create_index("ix_clean_telemetry_timestamp", "clean_telemetry", ["timestamp"])

    op.create_table(
        "clean_prescriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_raw_id", sa.String(50), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("med_cipher_text", sa.String(255), nullable=False),
        sa.Column("med_decoded_name", sa.String(255)),
        sa.Column("dosage", sa.String(100)),
        sa.Column("route", sa.String(50)),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clean_prescription_raw_id", "clean_prescriptions", ["patient_raw_id"]
    )

    op.create_table(
        "clean_demographics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_raw_id", sa.String(50), nullable=False),
        sa.Column("name_cipher", sa.Text()),
        sa.Column("decoded_name", sa.String(255)),
        sa.Column("age", sa.Integer()),
        sa.Column("ward", sa.String(50)),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clean_demographics_raw_id", "clean_demographics", ["patient_raw_id"]
    )

    # Identity tables
    op.create_table(
        "patient_alias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_raw_id", sa.String(50), nullable=False),
        sa.Column("parity_flag", sa.String(4), nullable=False),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("sample_count", sa.Integer(), default=1),
        sa.Column("confidence_score", sa.Numeric(3, 2), default=0.5),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "patient_raw_id", "parity_flag", name="uq_patient_alias_raw_parity"
        ),
        sa.UniqueConstraint("patient_id", name="uq_patient_alias_patient_id"),
        sa.CheckConstraint(
            "parity_flag IN ('even', 'odd')", name="ck_alias_parity_flag"
        ),
    )
    op.create_index("ix_patient_alias_patient_id", "patient_alias", ["patient_id"])

    op.create_table(
        "identity_audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("patient_raw_id", sa.String(50)),
        sa.Column("parity_flag", sa.String(4)),
        sa.Column("action", sa.String(50)),
        sa.Column("bpm_samples_used", sa.Integer()),
        sa.Column("decision_reason", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_identity_audit_patient_id", "identity_audit_log", ["patient_id"]
    )

    # Alert tables
    op.create_table(
        "patient_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(50), server_default="critical_vitals"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20)),
        sa.Column("last_bpm", sa.Integer()),
        sa.Column("last_oxygen", sa.Integer()),
        sa.Column("consecutive_abnormal_count", sa.Integer(), default=1),
        sa.Column("consecutive_normal_count", sa.Integer(), default=0),
        sa.Column("metadata", sa.JSON()),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('open', 'closed', 'acknowledged')", name="ck_alert_status"
        ),
    )
    op.create_index("ix_patient_alerts_patient_id", "patient_alerts", ["patient_id"])


def downgrade():
    op.drop_table("patient_alerts")
    op.drop_table("identity_audit_log")
    op.drop_table("patient_alias")
    op.drop_table("clean_demographics")
    op.drop_table("clean_prescriptions")
    op.drop_table("clean_telemetry")
    op.drop_table("stg_prescription_audit")
    op.drop_table("stg_telemetry_logs")
    op.drop_table("stg_patient_demographics")
