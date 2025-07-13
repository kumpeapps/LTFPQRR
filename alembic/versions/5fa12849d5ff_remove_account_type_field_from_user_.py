"""Remove account_type field from user table

Revision ID: 5fa12849d5ff
Revises: 
Create Date: 2025-07-11 00:55:53.238482

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fa12849d5ff'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the account_type column from the user table
    op.drop_column('user', 'account_type')


def downgrade() -> None:
    # Add the account_type column back (for rollback purposes)
    op.add_column('user', sa.Column('account_type', sa.String(length=20), nullable=False, server_default='customer'))
