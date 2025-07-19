"""add_privacy_fields_to_pet

Revision ID: 8db23a4bc700
Revises: fd244cf70ecd
Create Date: 2025-07-18 23:27:43.473934

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8db23a4bc700'
down_revision = 'fd244cf70ecd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add privacy fields to pet table
    op.add_column('pet', sa.Column('vet_info_public', sa.Boolean(), nullable=True, default=False))
    op.add_column('pet', sa.Column('groomer_info_public', sa.Boolean(), nullable=True, default=False))
    op.add_column('pet', sa.Column('phone_public', sa.Boolean(), nullable=True, default=True))


def downgrade() -> None:
    # Remove privacy fields from pet table
    op.drop_column('pet', 'phone_public')
    op.drop_column('pet', 'groomer_info_public')
    op.drop_column('pet', 'vet_info_public')
