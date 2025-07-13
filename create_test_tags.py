#!/usr/bin/env python3
"""
Test script to create some test tags for the partner user
"""

from app import app, db
from models.models import User, Tag
import uuid

def create_test_tags():
    with app.app_context():
        # Find the partner user
        user = User.query.filter_by(email='partner@example.com').first()
        if not user:
            print('Partner user not found')
            return

        # Create a few test tags
        for i in range(3):
            tag = Tag(
                tag_id=str(uuid.uuid4())[:8].upper(),
                created_by=user.id,
                status='pending'
            )
            db.session.add(tag)
        
        db.session.commit()
        print('Test tags created successfully')

if __name__ == '__main__':
    create_test_tags()
