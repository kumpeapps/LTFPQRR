"""Add partner models and partner access system

Revision ID: 3f8c7b6a5d92
Revises: 7d8a9678f789
Create Date: 2025-07-11 23:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3f8c7b6a5d92'
down_revision = '4a9b8c7d6e5f'
branch_labels = None
depends_on = None


def upgrade():
    # Create partner table
    op.create_table('partner',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create partner_users association table
    op.create_table('partner_users',
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=True, default='member'),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['partner_id'], ['partner.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('partner_id', 'user_id')
    )
    
    # Create partner_access_request table
    op.create_table('partner_access_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(120), nullable=True),
        sa.Column('business_description', sa.Text(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, default='pending'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reviewed_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create partner_subscription table
    op.create_table('partner_subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('pricing_plan_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('admin_approved', sa.Boolean(), nullable=True, default=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('max_tags', sa.Integer(), nullable=True, default=0),
        sa.Column('payment_method', sa.String(20), nullable=True),
        sa.Column('payment_id', sa.String(100), nullable=True),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=True, default=False),
        sa.Column('cancellation_requested', sa.Boolean(), nullable=True, default=False),
        sa.ForeignKeyConstraint(['approved_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['partner_id'], ['partner.id'], ),
        sa.ForeignKeyConstraint(['pricing_plan_id'], ['pricing_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add partner_id to tag table
    op.add_column('tag', sa.Column('partner_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'tag', 'partner', ['partner_id'], ['id'])


def downgrade():
    # Remove partner_id from tag table
    op.drop_constraint(None, 'tag', type_='foreignkey')
    op.drop_column('tag', 'partner_id')
    
    # Drop partner-related tables
    op.drop_table('partner_subscription')
    op.drop_table('partner_access_request')
    op.drop_table('partner_users')
    op.drop_table('partner')
