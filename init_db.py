#!/usr/bin/env python3
"""
Database initialization script for LTFPQRR
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, init_db

def main():
    """Initialize the database with default data"""
    print("Initializing LTFPQRR database...")
    
    with app.app_context():
        try:
            # Initialize database
            init_db()
            print("✓ Database initialized successfully!")
            print("✓ Default roles created")
            print("✓ System settings configured")
            print("✓ Payment gateways initialized")
            print("\nDatabase setup complete!")
            print("\nNext steps:")
            print("1. Run the application: python app.py")
            print("2. Register your first account (will get admin privileges)")
            print("3. Configure payment gateways in admin panel")
            
        except Exception as e:
            print(f"✗ Error initializing database: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
