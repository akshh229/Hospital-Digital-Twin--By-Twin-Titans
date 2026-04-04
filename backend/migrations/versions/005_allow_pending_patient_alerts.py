"""Allow pending status for patient alerts

Revision ID: 005
Revises: 004
Create Date: 2026-03-29
"""

from alembic import op

# revision identifiers
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE patient_alerts
        DROP CONSTRAINT IF EXISTS ck_alert_status;

        ALTER TABLE patient_alerts
        ADD CONSTRAINT ck_alert_status
        CHECK (status IN ('pending', 'open', 'closed', 'acknowledged'));
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE patient_alerts
        DROP CONSTRAINT IF EXISTS ck_alert_status;

        ALTER TABLE patient_alerts
        ADD CONSTRAINT ck_alert_status
        CHECK (status IN ('open', 'closed', 'acknowledged'));
        """
    )
