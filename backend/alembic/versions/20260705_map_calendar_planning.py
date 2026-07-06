"""add map and calendar planning data

Revision ID: f6a21c88d905
Revises: f28b0a9d3e61
Create Date: 2026-07-05 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a21c88d905"
down_revision = "f28b0a9d3e61"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.add_column(sa.Column("profit_score", sa.Float(), nullable=True))
        batch_op.create_index("ix_opportunities_profit_score", ["profit_score"])

    op.create_table(
        "operations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.Integer(),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="committed"),
        sa.Column("commitment_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_operations_opportunity_id", "operations", ["opportunity_id"])
    op.create_index("ix_operations_status", "operations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_operations_status", table_name="operations")
    op.drop_index("ix_operations_opportunity_id", table_name="operations")
    op.drop_table("operations")
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_index("ix_opportunities_profit_score")
        batch_op.drop_column("profit_score")
