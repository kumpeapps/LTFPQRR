#!/usr/bin/env python3
"""
Add sample search data for testing the admin search functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.models import Tag, User
from datetime import datetime

def create_sample_tags():
    """Create sample tags for testing search functionality"""
    with app.app_context():
        # Get the first user to use as creator
        user = User.query.first()
        if not user:
            print("No users found. Please create a user first.")
            return
        
        sample_tags = [
            "PET001", "PET002", "PET003", "DOG001", "CAT001",
            "RESCUE01", "BUDDY01", "FLUFFY01", "MAX001", "LUNA01"
        ]
        
        for tag_id in sample_tags:
            # Check if tag already exists
            existing = Tag.query.filter_by(tag_id=tag_id).first()
            if not existing:
                tag = Tag(
                    tag_id=tag_id,
                    status='available',
                    created_by=user.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(tag)
                print(f"Created tag: {tag_id}")
            else:
                print(f"Tag {tag_id} already exists")
        
        try:
            db.session.commit()
            print(f"Successfully created sample tags!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating tags: {e}")

if __name__ == "__main__":
    create_sample_tags()
