#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! python -c "
import os
from sqlalchemy import create_engine
import sys
import time

try:
    # Use SQLAlchemy to test database connection
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///ltfpqrr.db')
    engine = create_engine(db_url)
    conn = engine.connect()
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
"; do
    echo "Database not ready, retrying in 1 second..."
    sleep 1
done

echo "Database is ready!"

# Initialize database and run migrations
echo "Initializing database..."
python -c "
from app import app, db
from models.models import *

with app.app_context():
    # Check if alembic_version table exists
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    if 'alembic_version' in inspector.get_table_names():
        print('Running migrations...')
        import subprocess
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print('Migration errors:', result.stderr)
        if result.returncode != 0:
            print('Migration failed!')
            sys.exit(1)
    else:
        print('Creating fresh database schema...')
        db.create_all()
        
        # Create initial roles
        roles = ['user', 'admin', 'super-admin']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name)
                db.session.add(role)
        
        # Create system settings
        default_settings = {
            'registration_enabled': 'true',
            'site_name': 'LTFPQRR - Lost Then Found Pet QR Registry',
            'contact_email': 'admin@ltfpqrr.com',
            'paypal_enabled': 'true',
            'stripe_enabled': 'true',
            'square_enabled': 'true',
            'partner_monthly_price': '29.99',
            'partner_yearly_price': '299.99',
            'tag_monthly_price': '9.99',
            'tag_yearly_price': '99.99',
            'tag_lifetime_price': '199.99'
        }
        
        for key, value in default_settings.items():
            if not SystemSetting.query.filter_by(key=key).first():
                setting = SystemSetting(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        print('Database initialized successfully!')
        
        # Stamp with latest migration
        try:
            import subprocess
            result = subprocess.run(['alembic', 'stamp', 'head'], capture_output=True, text=True)
            print('Database stamped with latest migration')
            if result.returncode != 0:
                print('Warning: Could not stamp database:', result.stderr)
        except Exception as e:
            print(f'Warning: Could not stamp database: {e}')
"

# Start the Flask application
echo "Starting Flask application..."
exec python app.py
