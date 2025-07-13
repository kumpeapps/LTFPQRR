#!/usr/bin/env python3
"""
Debug script to check pending partner subscriptions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.models import db, User, Subscription

def debug_pending_subscriptions():
    """Debug pending partner subscriptions"""
    with app.app_context():
        print("=== Debugging Pending Partner Subscriptions ===\n")
        
        # Check all users
        users = User.query.all()
        print(f"Found {len(users)} users in database\n")
        
        for user in users:
            print(f"User: {user.get_full_name()} ({user.email})")
            print(f"  - Has partner role: {user.has_partner_role()}")
            print(f"  - Has pending partner subscription: {user.has_pending_partner_subscription()}")
            print(f"  - Can access partner dashboard: {user.can_access_partner_dashboard()}")
            
            # Check all subscriptions for this user
            subscriptions = user.subscriptions.all()
            if subscriptions:
                print(f"  - Subscriptions ({len(subscriptions)}):")
                for sub in subscriptions:
                    print(f"    * {sub.subscription_type} - {sub.status} - ${sub.amount}")
                    if sub.subscription_type == 'partner':
                        print(f"      Admin approved: {sub.admin_approved}")
                        print(f"      Start date: {sub.start_date}")
                        if sub.pricing_plan:
                            print(f"      Plan: {sub.pricing_plan.name}")
            else:
                print("  - No subscriptions")
            
            print()
        
        # Check specifically for pending partner subscriptions
        pending_partner_subs = Subscription.query.filter_by(
            subscription_type='partner',
            status='pending'
        ).all()
        
        print(f"\n=== Pending Partner Subscriptions ===")
        print(f"Found {len(pending_partner_subs)} pending partner subscriptions")
        
        for sub in pending_partner_subs:
            print(f"Subscription ID: {sub.id}")
            print(f"  User: {sub.user.get_full_name()} ({sub.user.email})")
            print(f"  Amount: ${sub.amount}")
            print(f"  Status: {sub.status}")
            print(f"  Admin approved: {sub.admin_approved}")
            print(f"  Created: {sub.created_at}")
            print(f"  Start date: {sub.start_date}")
            if sub.pricing_plan:
                print(f"  Plan: {sub.pricing_plan.name}")
            print()

if __name__ == "__main__":
    debug_pending_subscriptions()
