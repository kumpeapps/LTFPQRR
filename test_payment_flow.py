#!/usr/bin/env python3
"""
Test the complete payment flow for partner subscriptions
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

def test_payment_flow():
    app = create_app()
    
    with app.app_context():
        print("=== Testing Payment Flow Simulation ===")
        
        # Get existing data
        partner = Partner.query.first()
        pricing_plan = PricingPlan.query.first()
        
        if not partner or not pricing_plan:
            print("❌ Missing partner or pricing plan")
            return False
            
        print(f"Partner: {partner.company_name}")
        print(f"Pricing Plan: {pricing_plan.name}")
        print(f"Requires Approval: {pricing_plan.requires_approval}")
        
        # Clear any existing subscriptions
        PartnerSubscription.query.filter_by(partner_id=partner.id).delete()
        db.session.commit()
        print("Cleared existing subscriptions")
        
        # Simulate the exact payment flow logic
        print("\n=== Simulating Payment Success Handler ===")
        
        subscription_type = "monthly"  # or whatever is typical
        partner_id = partner.id
        pricing_plan_id = pricing_plan.id
        
        # Get pricing plan to check if approval is required (same as payment route)
        requires_approval = pricing_plan.requires_approval if pricing_plan else False
        print(f"Requires approval: {requires_approval}")
        
        # Create partner subscription (same logic as payment route)
        try:
            # Calculate end date based on pricing plan
            start_date = datetime.utcnow()
            end_date = None
            if pricing_plan and hasattr(pricing_plan, 'duration_months') and pricing_plan.duration_months > 0:
                end_date = start_date + timedelta(days=pricing_plan.duration_months * 30)
            elif subscription_type == "yearly":
                end_date = start_date + timedelta(days=365)
            elif subscription_type == "monthly":
                end_date = start_date + timedelta(days=30)
            
            print(f"Calculated dates - start: {start_date}, end: {end_date}")
            
            # Create a partner subscription record (exactly like payment route)
            partner_subscription = PartnerSubscription(
                partner_id=partner_id,
                pricing_plan_id=pricing_plan_id,
                status="pending" if requires_approval else "active",
                admin_approved=not requires_approval,
                max_tags=pricing_plan.max_tags if pricing_plan else 0,
                payment_method="stripe",
                amount=pricing_plan.price if pricing_plan else (29.99 if subscription_type == "monthly" else 299.99),
                start_date=start_date,
                end_date=end_date,
                auto_renew=True
            )
            
            print("Created PartnerSubscription object, attempting to save to database")
            db.session.add(partner_subscription)
            db.session.commit()
            print("Successfully saved partner subscription to database")
            
            # Check the subscription
            print(f"✅ Subscription ID: {partner_subscription.id}")
            print(f"   Status: {partner_subscription.status}")
            print(f"   Admin Approved: {partner_subscription.admin_approved}")
            print(f"   Amount: {partner_subscription.amount}")
            
            # Test what the admin dashboard would see
            print("\n=== Testing Admin Dashboard Queries ===")
            pending_subs = PartnerSubscription.query.filter_by(admin_approved=False, status='pending').all()
            approved_subs = PartnerSubscription.query.filter_by(admin_approved=True, status='active').all()
            
            print(f"Pending subscriptions: {len(pending_subs)}")
            print(f"Approved/Active subscriptions: {len(approved_subs)}")
            
            if approved_subs:
                for sub in approved_subs:
                    print(f"  - ID: {sub.id}, Partner: {sub.partner.company_name}")
            
            # Test what the partner dashboard would see
            print("\n=== Testing Partner Dashboard Logic ===")
            user = partner.owner
            has_pending = user.has_pending_partner_subscription()
            print(f"User has pending subscription: {has_pending}")
            
            active_sub = partner.get_active_subscription()
            pending_sub = partner.get_pending_subscription()
            print(f"Partner active subscription: {active_sub.id if active_sub else 'None'}")
            print(f"Partner pending subscription: {pending_sub.id if pending_sub else 'None'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in payment flow: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    test_payment_flow()
