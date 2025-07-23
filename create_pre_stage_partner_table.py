#!/usr/bin/env python3
"""
Create PreStagePartner table migration
"""

import os
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_pre_stage_partner_table():
    """Create the pre_stage_partner table using SQLAlchemy"""
    from app import app
    from extensions import db
    from models.models import PreStagePartner
    
    with app.app_context():
        try:
            print("Creating pre_stage_partner table...")
            
            # Check if table already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'pre_stage_partner' in existing_tables:
                print("Table 'pre_stage_partner' already exists.")
                return True
            
            # Create the table
            PreStagePartner.__table__.create(db.engine)
            print("Table 'pre_stage_partner' created successfully!")
            
            return True
            
        except Exception as e:
            print(f"Error creating pre_stage_partner table: {e}")
            return False

if __name__ == "__main__":
    success = create_pre_stage_partner_table()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
