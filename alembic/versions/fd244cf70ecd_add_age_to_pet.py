"""add_date_of_birth_to_pet

Revision ID: fd244cf70ecd
Revises: 00fffe5aabfe
Create Date: 2025-07-18 01:05:40.214186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd244cf70ecd'
down_revision = '00fffe5aabfe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add date_of_birth column to pet table
    op.add_column('pet', sa.Column('date_of_birth', sa.Date(), nullable=True))


def downgrade() -> None:
    # Remove date_of_birth column from pet table
    op.drop_column('pet', 'date_of_birth')
