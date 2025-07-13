#!/usr/bin/env python3
"""
Create a partner subscription for testing purposes
"""

from app import app, db
from models.models import User, Subscription
from datetime import datetime, timedelta

def create_partner_subscription():
    with app.app_context():
        # Find the partner user
        user = User.query.filter_by(email='partner@example.com').first()
        if not user:
            print('Partner user not found')
            return

        # Check if subscription already exists
        existing_sub = Subscription.query.filter_by(
            user_id=user.id,
            subscription_type='partner'
        ).first()
        
        if existing_sub:
            print(f'Partner subscription already exists (status: {existing_sub.status})')
            return

        # Create a partner subscription
        subscription = Subscription(
            user_id=user.id,
            subscription_type='partner',
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),  # 1 year
            amount=99.99
        )

        db.session.add(subscription)
        db.session.commit()
        print('Partner subscription created successfully')

if __name__ == '__main__':
    create_partner_subscription()
