"""Add payment gateway fields for stripe

Revision ID: 7d8a9678f789
Revises: aa64826264b8
Create Date: 2025-07-11 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7d8a9678f789'
down_revision = 'aa64826264b8'
branch_labels = None
depends_on = None


def upgrade():
    # This migration was already applied manually
    pass


def downgrade():
    # This migration was already applied manually
    pass