"""
Add timezone columns to user and partner tables
"""

import os
import sys
sys.path.append('/app')

from flask import Flask
from config import config
from extensions import db

def add_timezone_columns():
    """Add timezone columns to user and partner tables"""
    try:
        # Add timezone column to user table
        print("Adding timezone column to user table...")
        with db.engine.connect() as conn:
            conn.execute(db.text("""
                ALTER TABLE user 
                ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL
            """))
            conn.commit()
        print("✓ Added timezone column to user table")
        
        # Add timezone column to partner table  
        print("Adding timezone column to partner table...")
        with db.engine.connect() as conn:
            conn.execute(db.text("""
                ALTER TABLE partner 
                ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL
            """))
            conn.commit()
        print("✓ Added timezone column to partner table")
        
        print("✅ Successfully added timezone columns to both tables")
        return True
        
    except Exception as e:
        print(f"❌ Error adding timezone columns: {e}")
        return False

if __name__ == '__main__':
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config['default'])
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        add_timezone_columns()
