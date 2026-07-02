"""create initial tables

Revision ID: 52d7c0a57cb7
Revises: 
Create Date: 2026-07-02 17:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '52d7c0a57cb7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('organizer', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('expected_revenue', sa.Integer(), nullable=True),
        sa.Column('expected_attendance', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_name'), 'events', ['name'], unique=False)

    op.create_table(
        'organizers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_organizers_id'), 'organizers', ['id'], unique=False)
    op.create_index(op.f('ix_organizers_name'), 'organizers', ['name'], unique=False)

    op.create_table(
        'venues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_venues_id'), 'venues', ['id'], unique=False)
    op.create_index(op.f('ix_venues_name'), 'venues', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_venues_name'), table_name='venues')
    op.drop_index(op.f('ix_venues_id'), table_name='venues')
    op.drop_table('venues')
    op.drop_index(op.f('ix_organizers_name'), table_name='organizers')
    op.drop_index(op.f('ix_organizers_id'), table_name='organizers')
    op.drop_table('organizers')
    op.drop_index(op.f('ix_events_name'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')
