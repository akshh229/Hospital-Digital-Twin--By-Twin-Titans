"""Track telemetry rows by staging source id

Revision ID: 003
Revises: 002
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "clean_telemetry",
        sa.Column("staging_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_clean_telemetry_staging_log_id",
        "clean_telemetry",
        ["staging_log_id"],
        unique=False,
    )
    op.drop_constraint(
        "uq_clean_telemetry_patient_timestamp",
        "clean_telemetry",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_clean_telemetry_staging_log_id",
        "clean_telemetry",
        ["staging_log_id"],
    )


def downgrade():
    op.drop_constraint(
        "uq_clean_telemetry_staging_log_id",
        "clean_telemetry",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_clean_telemetry_patient_timestamp",
        "clean_telemetry",
        ["patient_raw_id", "timestamp"],
    )
    op.drop_index("ix_clean_telemetry_staging_log_id", table_name="clean_telemetry")
    op.drop_column("clean_telemetry", "staging_log_id")
