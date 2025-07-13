"""migrate data from old tables to new plural named tables

Revision ID: aa64826264b8
Revises: effcb230d5db
Create Date: 2025-07-11 19:29:31.400237

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa64826264b8'
down_revision = 'effcb230d5db'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection and inspector to check table existence
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    metadata = sa.MetaData()
    
    # Define old tables
    old_pricing_plan = sa.Table('pricing_plan', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.DECIMAL(10, 2)),
        sa.Column('currency', sa.String(3)),
        sa.Column('billing_period', sa.String(20)),
        sa.Column('plan_type', sa.String(20)),
        sa.Column('max_tags', sa.Integer),
        sa.Column('features', sa.Text),
        sa.Column('is_active', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    old_payment_gateway = sa.Table('payment_gateway', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50)),
        sa.Column('api_key', sa.Text),
        sa.Column('secret_key', sa.Text),
        sa.Column('publishable_key', sa.Text),
        sa.Column('client_id', sa.Text),
        sa.Column('webhook_secret', sa.Text),
        sa.Column('environment', sa.String(20)),
        sa.Column('enabled', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    # Define new tables
    new_pricing_plans = sa.Table('pricing_plans', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.DECIMAL(10, 2)),
        sa.Column('currency', sa.String(3)),
        sa.Column('billing_period', sa.String(20)),
        sa.Column('plan_type', sa.String(20)),
        sa.Column('max_tags', sa.Integer),
        sa.Column('features', sa.JSON),
        sa.Column('is_active', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    new_payment_gateways = sa.Table('payment_gateways', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50)),
        sa.Column('api_key', sa.Text),
        sa.Column('secret_key', sa.Text),
        sa.Column('publishable_key', sa.Text),
        sa.Column('client_id', sa.Text),
        sa.Column('webhook_secret', sa.Text),
        sa.Column('environment', sa.String(20)),
        sa.Column('enabled', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    # Migrate pricing plan data if old table exists
    if 'pricing_plan' in existing_tables:
        try:
            old_plans = connection.execute(sa.select(old_pricing_plan)).fetchall()
            for plan in old_plans:
                # Check if record already exists in new table
                existing = connection.execute(
                    sa.select(new_pricing_plans).where(new_pricing_plans.c.id == plan.id)
                ).fetchone()
                
                if not existing:
                    # Convert features text to JSON
                    features = {}
                    if plan.features and plan.features.strip():
                        features = {'description': plan.features}
                    
                    connection.execute(
                        sa.insert(new_pricing_plans).values(
                            id=plan.id,
                            name=plan.name,
                            description=plan.description,
                            price=plan.price,
                            currency=plan.currency,
                            billing_period=plan.billing_period or 'monthly',
                            plan_type=plan.plan_type,
                            max_tags=plan.max_tags,
                            features=features,
                            is_active=plan.is_active,
                            created_at=plan.created_at,
                            updated_at=plan.updated_at,
                        )
                    )
        except Exception as e:
            print(f"Error migrating pricing_plan data: {e}")
    
    # Migrate payment gateway data if old table exists
    if 'payment_gateway' in existing_tables:
        try:
            old_gateways = connection.execute(sa.select(old_payment_gateway)).fetchall()
            for gateway in old_gateways:
                # Check if record already exists in new table
                existing = connection.execute(
                    sa.select(new_payment_gateways).where(new_payment_gateways.c.id == gateway.id)
                ).fetchone()
                
                if not existing:
                    connection.execute(
                        sa.insert(new_payment_gateways).values(
                            id=gateway.id,
                            name=gateway.name,
                            api_key=gateway.api_key,
                            secret_key=gateway.secret_key,
                            publishable_key=gateway.publishable_key,
                            client_id=gateway.client_id,
                            webhook_secret=gateway.webhook_secret,
                            environment=gateway.environment,
                            enabled=gateway.enabled,
                            created_at=gateway.created_at,
                            updated_at=gateway.updated_at,
                        )
                    )
        except Exception as e:
            print(f"Error migrating payment_gateway data: {e}")
    
    # Update foreign key constraint in subscription table
    if 'subscription' in existing_tables:
        try:
            with op.batch_alter_table('subscription') as batch_op:
                try:
                    batch_op.drop_constraint('subscription_ibfk_3', type_='foreignkey')
                except:
                    # Constraint might not exist or have a different name
                    pass
                batch_op.create_foreign_key(
                    'subscription_ibfk_3', 'pricing_plans',
                    ['pricing_plan_id'], ['id']
                )
        except Exception as e:
            print(f"Error updating foreign key constraint: {e}")
    
    # Drop old tables if they exist
    if 'pricing_plan' in existing_tables:
        op.drop_table('pricing_plan')
    if 'payment_gateway' in existing_tables:
        op.drop_table('payment_gateway')


def downgrade() -> None:
    # Recreate old tables
    op.create_table('pricing_plan',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.VARCHAR(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plan_type', sa.VARCHAR(length=20), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.VARCHAR(length=3), nullable=True),
        sa.Column('billing_period', sa.VARCHAR(length=20), nullable=True),
        sa.Column('features', sa.Text(), nullable=True),
        sa.Column('max_tags', sa.Integer(), nullable=True),
        sa.Column('max_pets', sa.Integer(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('show_on_homepage', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('payment_gateway',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.VARCHAR(length=50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('secret_key', sa.Text(), nullable=True),
        sa.Column('webhook_secret', sa.Text(), nullable=True),
        sa.Column('environment', sa.VARCHAR(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('publishable_key', sa.Text(), nullable=True),
        sa.Column('client_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data back using SQLAlchemy
    connection = op.get_bind()
    metadata = sa.MetaData()
    
    # Define table objects for data migration
    old_pricing_plan = sa.Table('pricing_plan', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.DECIMAL(10, 2)),
        sa.Column('currency', sa.String(3)),
        sa.Column('billing_period', sa.String(20)),
        sa.Column('plan_type', sa.String(20)),
        sa.Column('max_tags', sa.Integer),
        sa.Column('features', sa.Text),
        sa.Column('is_active', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    old_payment_gateway = sa.Table('payment_gateway', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50)),
        sa.Column('api_key', sa.Text),
        sa.Column('secret_key', sa.Text),
        sa.Column('publishable_key', sa.Text),
        sa.Column('client_id', sa.Text),
        sa.Column('webhook_secret', sa.Text),
        sa.Column('environment', sa.String(20)),
        sa.Column('enabled', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    new_pricing_plans = sa.Table('pricing_plans', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.DECIMAL(10, 2)),
        sa.Column('currency', sa.String(3)),
        sa.Column('billing_period', sa.String(20)),
        sa.Column('plan_type', sa.String(20)),
        sa.Column('max_tags', sa.Integer),
        sa.Column('features', sa.JSON),
        sa.Column('is_active', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    new_payment_gateways = sa.Table('payment_gateways', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50)),
        sa.Column('api_key', sa.Text),
        sa.Column('secret_key', sa.Text),
        sa.Column('publishable_key', sa.Text),
        sa.Column('client_id', sa.Text),
        sa.Column('webhook_secret', sa.Text),
        sa.Column('environment', sa.String(20)),
        sa.Column('enabled', sa.Boolean),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    # Migrate data back from new tables to old tables
    try:
        # Migrate pricing plans data back
        plans = connection.execute(sa.select(new_pricing_plans)).fetchall()
        for plan in plans:
            # Convert JSON features back to text
            features_text = None
            if plan.features and isinstance(plan.features, dict):
                features_text = plan.features.get('description', '')
            elif plan.features:
                features_text = str(plan.features)
            
            connection.execute(
                sa.insert(old_pricing_plan).values(
                    id=plan.id,
                    name=plan.name,
                    description=plan.description,
                    price=plan.price,
                    currency=plan.currency,
                    billing_period=plan.billing_period,
                    plan_type=plan.plan_type,
                    max_tags=plan.max_tags,
                    features=features_text,
                    is_active=plan.is_active,
                    created_at=plan.created_at,
                    updated_at=plan.updated_at,
                )
            )
        
        # Migrate payment gateways data back
        gateways = connection.execute(sa.select(new_payment_gateways)).fetchall()
        for gateway in gateways:
            connection.execute(
                sa.insert(old_payment_gateway).values(
                    id=gateway.id,
                    name=gateway.name,
                    api_key=gateway.api_key,
                    secret_key=gateway.secret_key,
                    publishable_key=gateway.publishable_key,
                    client_id=gateway.client_id,
                    webhook_secret=gateway.webhook_secret,
                    environment=gateway.environment,
                    enabled=gateway.enabled,
                    created_at=gateway.created_at,
                    updated_at=gateway.updated_at,
                )
            )
    except Exception as e:
        print(f"Error migrating data back: {e}")
    
    # Update foreign key constraint back to old table
    try:
        with op.batch_alter_table('subscription') as batch_op:
            try:
                batch_op.drop_constraint('subscription_ibfk_3', type_='foreignkey')
            except:
                pass
            batch_op.create_foreign_key(
                'subscription_ibfk_3', 'pricing_plan',
                ['pricing_plan_id'], ['id']
            )
    except Exception as e:
        print(f"Error updating foreign key constraint: {e}")
    
    # Drop new tables
    op.drop_table('pricing_plans')
    op.drop_table('payment_gateways')
