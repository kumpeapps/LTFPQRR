"""
Add reply_to field to email_queue table using SQLAlchemy
"""

import os
import sys
sys.path.append('/app')

from flask import Flask
from config import config
from extensions import db
from sqlalchemy import text, inspect

def add_reply_to_field():
    """Add reply_to field to email_queue table"""
    try:
        # Check if the table exists
        inspector = inspect(db.engine)
        if 'email_queue' not in inspector.get_table_names():
            print("❌ email_queue table does not exist")
            return False
        
        # Check if reply_to column already exists
        columns = [col['name'] for col in inspector.get_columns('email_queue')]
        if 'reply_to' in columns:
            print("✓ reply_to column already exists in email_queue table")
            return True
        
        # Add reply_to column to email_queue table
        print("Adding reply_to column to email_queue table...")
        with db.engine.connect() as conn:
            # Use proper SQL syntax for MySQL/PostgreSQL
            conn.execute(text("""
                ALTER TABLE email_queue 
                ADD COLUMN reply_to VARCHAR(255)
            """))
            conn.commit()
        print("✓ Added reply_to column to email_queue table")
        
        print("✅ Successfully added reply_to field to email_queue table")
        return True
        
    except Exception as e:
        print(f"❌ Error adding reply_to field: {e}")
        return False

if __name__ == '__main__':
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config['default'])
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        add_reply_to_field()
