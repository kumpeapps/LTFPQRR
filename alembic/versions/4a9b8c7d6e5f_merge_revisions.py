"""Merge revisions

Revision ID: 4a9b8c7d6e5f
Revises: 22cb62fd5df0, 7d8a9678f789
Create Date: 2025-07-11 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4a9b8c7d6e5f'
down_revision = ('22cb62fd5df0', '7d8a9678f789')
branch_labels = None
depends_on = None


def upgrade():
    # Merge migration - no changes needed
    pass


def downgrade():
    # Merge migration - no changes needed
    pass
