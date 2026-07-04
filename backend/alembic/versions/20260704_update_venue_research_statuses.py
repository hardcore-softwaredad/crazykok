"""rename venue research status values

Revision ID: f28b0a9d3e61
Revises: c41a9d738f10
Create Date: 2026-07-04 21:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f28b0a9d3e61"
down_revision = "c41a9d738f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE venues SET research_status = CASE research_status "
            "WHEN 'inventory' THEN 'identified' "
            "WHEN 'basic' THEN 'researched' "
            "ELSE research_status END "
            "WHERE research_status IN ('inventory', 'basic')"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE venues SET research_status = CASE research_status "
            "WHEN 'identified' THEN 'inventory' "
            "WHEN 'researched' THEN 'basic' "
            "ELSE research_status END "
            "WHERE research_status IN ('identified', 'researched')"
        )
    )
