#!/usr/bin/env python3
"""
Database migration management script for LTFPQRR
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, upgrade, downgrade, stamp
from alembic import command
from alembic.config import Config
import argparse

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ltfpqrr.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    
    # Import models to register them
    from models.models import *
    
    return app, db, migrate

def main():
    parser = argparse.ArgumentParser(description='Database migration management')
    parser.add_argument('command', choices=['init', 'autogenerate', 'upgrade', 'downgrade', 'stamp', 'current', 'history'],
                       help='Migration command to run')
    parser.add_argument('--message', '-m', help='Migration message (for autogenerate)')
    parser.add_argument('--revision', '-r', help='Revision to upgrade/downgrade to')
    
    args = parser.parse_args()
    
    app, db, migrate_instance = create_app()
    
    with app.app_context():
        if args.command == 'init':
            print("Initializing migration repository...")
            init()
            print("Migration repository initialized!")
            
        elif args.command == 'autogenerate':
            if not args.message:
                print("Error: --message is required for autogenerate")
                sys.exit(1)
            print(f"Generating migration: {args.message}")
            migrate(message=args.message)
            print("Migration generated!")
            
        elif args.command == 'upgrade':
            revision = args.revision or 'head'
            print(f"Upgrading to revision: {revision}")
            upgrade(revision=revision)
            print("Upgrade completed!")
            
        elif args.command == 'downgrade':
            revision = args.revision or '-1'
            print(f"Downgrading to revision: {revision}")
            downgrade(revision=revision)
            print("Downgrade completed!")
            
        elif args.command == 'stamp':
            revision = args.revision or 'head'
            print(f"Stamping database with revision: {revision}")
            stamp(revision=revision)
            print("Database stamped!")
            
        elif args.command == 'current':
            from alembic import command
            from alembic.config import Config
            
            alembic_cfg = Config('alembic.ini')
            command.current(alembic_cfg, verbose=True)
            
        elif args.command == 'history':
            from alembic import command
            from alembic.config import Config
            
            alembic_cfg = Config('alembic.ini')
            command.history(alembic_cfg, verbose=True)

if __name__ == '__main__':
    main()
