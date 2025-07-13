#!/usr/bin/env python3
"""
Create test data for the updated system
"""

from app import app, db
from models.models import User, PricingPlan, Subscription, Role, Tag
from datetime import datetime, timedelta
import uuid

def create_test_data():
    with app.app_context():
        # Create partner pricing plans
        partner_plan = PricingPlan(
            name='Partner Starter',
            description='Basic partner plan with 5 tags',
            plan_type='partner',
            price=29.99,
            billing_period='monthly',
            max_tags=5,
            requires_approval=True,
            is_active=True
        )
        partner_plan.set_features_list([
            'Create up to 5 tags',
            'Tag activation control',
            'Partner dashboard',
            'Email support'
        ])
        
        partner_pro_plan = PricingPlan(
            name='Partner Pro',
            description='Professional partner plan with unlimited tags',
            plan_type='partner',
            price=99.99,
            billing_period='monthly',
            max_tags=0,  # Unlimited
            requires_approval=True,
            is_active=True,
            is_featured=True
        )
        partner_pro_plan.set_features_list([
            'Unlimited tags',
            'Tag activation control',
            'Partner dashboard',
            'Priority support',
            'Advanced analytics'
        ])
        
        # Create tag pricing plans
        tag_basic_plan = PricingPlan(
            name='Basic Tag',
            description='Individual tag subscription',
            plan_type='tag',
            price=4.99,
            billing_period='monthly',
            max_pets=1,
            requires_approval=False,
            is_active=True,
            show_on_homepage=True
        )
        tag_basic_plan.set_features_list([
            'QR tag generation',
            'Pet profile',
            'Lost pet alerts',
            'Basic support'
        ])
        
        db.session.add_all([partner_plan, partner_pro_plan, tag_basic_plan])
        
        # Create a test user for partner subscription
        test_user = User.query.filter_by(email='test@example.com').first()
        if test_user:
            # Create a pending partner subscription
            subscription = Subscription(
                user_id=test_user.id,
                pricing_plan_id=partner_plan.id,
                subscription_type='partner',
                status='pending',
                admin_approved=False,
                max_tags=5,
                amount=29.99,
                start_date=datetime.utcnow()
            )
            db.session.add(subscription)
        
        db.session.commit()
        print('Test data created successfully!')

if __name__ == '__main__':
    create_test_data()
