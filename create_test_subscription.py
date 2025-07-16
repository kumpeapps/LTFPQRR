#!/usr/bin/env python3
"""
Test subscription creation manually
"""
import sys
import os

# Set up the Flask app context
os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.models import User, Partner, PartnerSubscription, PricingPlan
from datetime import datetime, timedelta

def create_test_subscription():
    app = create_app()
    
    with app.app_context():
        print("=== Creating Test Subscription ===")
        
        # Get the existing partner and pricing plan
        partner = Partner.query.first()
        pricing_plan = PricingPlan.query.first()
        
        if not partner:
            print("❌ No partner found")
            return False
            
        if not pricing_plan:
            print("❌ No pricing plan found")
            return False
            
        print(f"Partner: {partner.company_name} (ID: {partner.id})")
        print(f"Partner Owner: {partner.owner.username}")
        print(f"Pricing Plan: {pricing_plan.name} (ID: {pricing_plan.id})")
        print(f"Requires Approval: {pricing_plan.requires_approval}")
        
        # Delete any existing subscriptions for this partner
        existing = PartnerSubscription.query.filter_by(partner_id=partner.id).first()
        if existing:
            print(f"Deleting existing subscription ID: {existing.id}")
            db.session.delete(existing)
            db.session.commit()
        
        # Create new subscription
        try:
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30)
            
            subscription = PartnerSubscription(
                partner_id=partner.id,
                pricing_plan_id=pricing_plan.id,
                status="active",  # Should be active since requires_approval=False
                admin_approved=True,  # Should be True since requires_approval=False
                max_tags=pricing_plan.max_tags,
                payment_method="test",
                amount=pricing_plan.price,
                start_date=start_date,
                end_date=end_date,
                auto_renew=True
            )
            
            print("Adding subscription to database...")
            db.session.add(subscription)
            db.session.commit()
            
            print(f"✅ Successfully created subscription ID: {subscription.id}")
            
            # Test the subscription
            print(f"Subscription status: {subscription.status}")
            print(f"Admin approved: {subscription.admin_approved}")
            print(f"Partner: {subscription.partner.company_name}")
            print(f"User (via partner.owner): {subscription.user.username}")
            
            # Test admin queries
            print("\n=== Testing Admin Queries ===")
            pending = PartnerSubscription.query.filter_by(admin_approved=False, status='pending').count()
            approved = PartnerSubscription.query.filter_by(admin_approved=True, status='active').count()
            print(f"Pending subscriptions: {pending}")
            print(f"Approved/Active subscriptions: {approved}")
            
            # Test user methods
            print("\n=== Testing User Methods ===")
            has_pending = partner.owner.has_pending_partner_subscription()
            print(f"User has pending subscription: {has_pending}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating subscription: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    create_test_subscription()
