#!/usr/bin/env python3
"""
Database migration management script for LTFPQRR
Uses pure Alembic for all database migrations
"""

import os
import sys
from alembic import command
from alembic.config import Config
import argparse

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_alembic_config():
    """Get Alembic configuration"""
    config = Config('alembic.ini')
    return config

def main():
    parser = argparse.ArgumentParser(description='Database migration management using Alembic')
    parser.add_argument('command', choices=['revision', 'upgrade', 'downgrade', 'stamp', 'current', 'history'],
                       help='Alembic command to run')
    parser.add_argument('--message', '-m', help='Migration message (for revision)')
    parser.add_argument('--autogenerate', action='store_true', help='Autogenerate migration (for revision)')
    parser.add_argument('--revision', '-r', help='Revision to upgrade/downgrade to', default='head')
    
    args = parser.parse_args()
    
    alembic_cfg = get_alembic_config()
    
    try:
        if args.command == 'revision':
            if not args.message:
                print("Error: --message is required for revision")
                sys.exit(1)
            print(f"Generating migration: {args.message}")
            if args.autogenerate:
                command.revision(alembic_cfg, message=args.message, autogenerate=True)
            else:
                command.revision(alembic_cfg, message=args.message)
            print("Migration generated!")
            
        elif args.command == 'upgrade':
            print(f"Upgrading to revision: {args.revision}")
            command.upgrade(alembic_cfg, args.revision)
            print("Upgrade completed!")
            
        elif args.command == 'downgrade':
            revision = args.revision if args.revision != 'head' else '-1'
            print(f"Downgrading to revision: {revision}")
            command.downgrade(alembic_cfg, revision)
            print("Downgrade completed!")
            
        elif args.command == 'stamp':
            print(f"Stamping database with revision: {args.revision}")
            command.stamp(alembic_cfg, args.revision)
            print("Database stamped!")
            
        elif args.command == 'current':
            print("Current database revision:")
            command.current(alembic_cfg, verbose=True)
            
        elif args.command == 'history':
            print("Migration history:")
            command.history(alembic_cfg, verbose=True)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
