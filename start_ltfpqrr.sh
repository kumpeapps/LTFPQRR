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
import sys
from app import app, db
from models.models import *

with app.app_context():
    # Check if alembic_version table exists
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    if 'alembic_version' in inspector.get_table_names():
        print('Running migrations...')
        import subprocess
        result = subprocess.run(['python', 'migrate.py', 'upgrade'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print('Migration errors:', result.stderr)
        if result.returncode != 0:
            print('Migration failed!')
            sys.exit(1)
        
        # Ensure roles exist even after migrations
        roles = ['user', 'admin', 'super-admin', 'partner']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name)
                db.session.add(role)
        db.session.commit()
    else:
        print('Creating fresh database schema...')
        db.create_all()
        
        # Create initial roles
        roles = ['user', 'admin', 'super-admin', 'partner']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name)
                db.session.add(role)
        
        db.session.commit()
        print('Database initialized successfully!')
        
        # Stamp with latest migration
        try:
            import subprocess
            result = subprocess.run(['python', 'migrate.py', 'stamp'], capture_output=True, text=True)
            print('Database stamped with latest migration')
            if result.returncode != 0:
                print('Warning: Could not stamp database:', result.stderr)
        except Exception as e:
            print(f'Warning: Could not stamp database: {e}')
"

# Initialize default settings and payment gateways
echo "Initializing system settings and payment gateways..."
python init_default_settings.py || echo "Warning: Failed to initialize default settings"

# Initialize system settings for email templates
echo "Initializing system settings for email templates..."
python init_system_settings.py || echo "Warning: Failed to initialize system settings"

# Initialize default email templates
echo "Initializing default email templates..."
python init_email_templates.py || echo "Warning: Failed to initialize email templates"

# Start the Flask application
echo "Starting Flask application..."
exec python app.py
