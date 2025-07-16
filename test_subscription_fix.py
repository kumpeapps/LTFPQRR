#!/usr/bin/env python3
"""
Test partner subscription creation without approval required
"""
import sys
import os

# Set up the Flask app context
os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.models import User, Partner, PartnerSubscription, PricingPlan, Role
from datetime import datetime, timedelta

def test_subscription_flow():
    # Create the Flask app and set up the context
    app = create_app()
    
    with app.app_context():
        print("=== Testing Partner Subscription Flow ===")
        
        # Test existing data first
        print(f"Total partners in database: {Partner.query.count()}")
        print(f"Total users in database: {User.query.count()}")
        print(f"Total pricing plans: {PricingPlan.query.count()}")
        print(f"Total partner subscriptions: {PartnerSubscription.query.count()}")
        
        # List existing partner subscriptions
        existing_subs = PartnerSubscription.query.all()
        print(f"\n=== Existing Partner Subscriptions ===")
        for sub in existing_subs:
            print(f"Sub ID: {sub.id}")
            print(f"  Partner: {sub.partner.company_name if sub.partner else 'MISSING'}")
            print(f"  Partner Owner: {sub.partner.owner.username if sub.partner and sub.partner.owner else 'MISSING'}")
            print(f"  Status: {sub.status}")
            print(f"  Admin Approved: {sub.admin_approved}")
            if sub.pricing_plan:
                print(f"  Pricing Plan: {sub.pricing_plan.name} (requires_approval: {sub.pricing_plan.requires_approval})")
            else:
                print(f"  Pricing Plan: MISSING")
            print()
        
        # Test admin dashboard queries
        print("\n=== Testing Admin Dashboard Queries ===")
        
        pending_subs = PartnerSubscription.query.filter_by(admin_approved=False, status='pending').all()
        print(f"Pending subscriptions (admin_approved=False, status='pending'): {len(pending_subs)}")
        for sub in pending_subs:
            print(f"  - ID: {sub.id}, Partner: {sub.partner.company_name}")
        
        approved_subs = PartnerSubscription.query.filter_by(admin_approved=True, status='active').all()
        print(f"Approved/Active subscriptions (admin_approved=True, status='active'): {len(approved_subs)}")
        for sub in approved_subs:
            print(f"  - ID: {sub.id}, Partner: {sub.partner.company_name}")
        
        all_active_subs = PartnerSubscription.query.filter_by(status='active').all()
        print(f"All active subscriptions (any admin_approved, status='active'): {len(all_active_subs)}")
        for sub in all_active_subs:
            print(f"  - ID: {sub.id}, Partner: {sub.partner.company_name}, Admin Approved: {sub.admin_approved}")
        
        # Test partner dashboard logic for each partner owner
        print("\n=== Testing Partner Dashboard Logic ===")
        partners = Partner.query.all()
        for partner in partners:
            if partner.owner:
                has_pending = partner.owner.has_pending_partner_subscription()
                can_access = partner.owner.can_access_partner_dashboard()
                print(f"Partner: {partner.company_name}")
                print(f"  Owner: {partner.owner.username}")
                print(f"  Has pending subscription: {has_pending}")
                print(f"  Can access dashboard: {can_access}")
                
                # Check what subscription methods return
                active_sub = partner.get_active_subscription()
                pending_sub = partner.get_pending_subscription()
                print(f"  Active subscription: {active_sub.id if active_sub else 'None'}")
                print(f"  Pending subscription: {pending_sub.id if pending_sub else 'None'}")
                print()
        
        # Check pricing plans
        print("\n=== Pricing Plans ===")
        plans = PricingPlan.query.all()
        for plan in plans:
            print(f"Plan: {plan.name}")
            print(f"  Requires approval: {plan.requires_approval}")
            print(f"  Active: {plan.is_active}")
            print(f"  Plan type: {plan.plan_type}")
            print()
        
        print("\n✅ Analysis completed!")
        return True

if __name__ == '__main__':
    test_subscription_flow()
