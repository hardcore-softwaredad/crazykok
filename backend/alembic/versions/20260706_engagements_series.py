"""add engagements and opportunity series

Revision ID: 6b210a9ef307
Revises: f6a21c88d905
Create Date: 2026-07-06 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "6b210a9ef307"
down_revision = "f6a21c88d905"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunity_series",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opportunity_series_id", "opportunity_series", ["id"])
    op.create_index("ix_opportunity_series_name", "opportunity_series", ["name"], unique=True)
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.add_column(sa.Column("opportunity_series_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_opportunities_opportunity_series_id", "opportunity_series", ["opportunity_series_id"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_index("ix_opportunities_opportunity_series_id", ["opportunity_series_id"])

    op.rename_table("operations", "engagements")
    op.drop_index("ix_operations_opportunity_id", table_name="engagements")
    op.drop_index("ix_operations_status", table_name="engagements")
    op.create_index("ix_engagements_opportunity_id", "engagements", ["opportunity_id"])
    op.create_index("ix_engagements_status", "engagements", ["status"])

    with op.batch_alter_table("engagements") as batch_op:
        batch_op.add_column(sa.Column("pitch_number", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("setup_start_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("setup_end_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("teardown_start_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("teardown_end_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("arrival_plan", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("staffing_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("equipment_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("inventory_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("travel_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("calendar_visibility", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("attended", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("revenue_eur", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("costs_eur", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("profit_eur", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("weather_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("best_selling_items", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("operational_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("customer_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("rating", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("attend_again", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("lessons_learned", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("engagements") as batch_op:
        for column in (
            "lessons_learned", "attend_again", "rating", "customer_notes", "operational_notes", "best_selling_items",
            "weather_notes", "profit_eur", "costs_eur", "revenue_eur", "attended", "calendar_visibility", "travel_notes", "inventory_notes", "equipment_notes", "staffing_notes",
            "arrival_plan", "teardown_end_at", "teardown_start_at", "setup_end_at", "setup_start_at", "pitch_number",
        ):
            batch_op.drop_column(column)
    op.drop_index("ix_engagements_status", table_name="engagements")
    op.drop_index("ix_engagements_opportunity_id", table_name="engagements")
    op.rename_table("engagements", "operations")
    op.create_index("ix_operations_opportunity_id", "operations", ["opportunity_id"])
    op.create_index("ix_operations_status", "operations", ["status"])
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_index("ix_opportunities_opportunity_series_id")
        batch_op.drop_constraint("fk_opportunities_opportunity_series_id", type_="foreignkey")
        batch_op.drop_column("opportunity_series_id")
    op.drop_index("ix_opportunity_series_name", table_name="opportunity_series")
    op.drop_index("ix_opportunity_series_id", table_name="opportunity_series")
    op.drop_table("opportunity_series")
