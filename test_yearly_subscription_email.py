#!/usr/bin/env python3
"""
Test yearly subscription email to verify billing period display
"""
import sys
import os

# Set up the Flask app context
os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.models import User, Tag
from models.payment.payment import Subscription
from email_utils import send_subscription_confirmation_email
from datetime import datetime, timedelta

def test_yearly_subscription_email():
    app = create_app()
    
    with app.app_context():
        print("=== Testing Yearly Subscription Email ===")
        
        # Get a test user
        user = User.query.first()
        if not user:
            print("❌ No user found in database")
            return False
            
        print(f"Test user: {user.username} ({user.email})")
        
        # Get a test tag
        tag = Tag.query.first()
        if not tag:
            print("❌ No tag found in database")
            return False
            
        print(f"Test tag: {tag.tag_id}")
        
        # Create a test yearly subscription (like the ones created in routes/payment.py line 92)
        test_subscription = Subscription(
            user_id=user.id,
            tag_id=tag.id,
            subscription_type="yearly",  # This is the key field for billing period
            status="active",
            payment_method="test",
            amount=99.99,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),
            # Note: pricing_plan_id is not set, just like in real tag subscriptions
        )
        
        print(f"Created test subscription:")
        print(f"  - Type: {test_subscription.subscription_type}")
        print(f"  - Amount: ${test_subscription.amount}")
        print(f"  - Pricing Plan: {test_subscription.pricing_plan}")
        print(f"  - Has pricing_plan: {test_subscription.pricing_plan is not None}")
        
        # Test the billing period logic that was just fixed
        if test_subscription.pricing_plan:
            billing_period = test_subscription.pricing_plan.billing_period.title()
        elif hasattr(test_subscription, 'subscription_type') and test_subscription.subscription_type in ['monthly', 'yearly', 'lifetime']:
            billing_period = test_subscription.subscription_type.title()
        else:
            billing_period = 'One-time'
            
        print(f"  - Calculated billing period: {billing_period}")
        
        # Test sending the actual email
        print("\n=== Sending Test Email ===")
        try:
            success = send_subscription_confirmation_email(user, test_subscription)
            if success:
                print("✅ Email sent successfully!")
                print(f"📧 Check {user.email} for confirmation email with 'Yearly' billing period")
            else:
                print("❌ Failed to send email")
                
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
        
        # Also test other subscription types for completeness
        print("\n=== Testing Other Subscription Types ===")
        
        test_cases = [
            ("monthly", 9.99, 30),
            ("lifetime", 199.99, None)
        ]
        
        for sub_type, amount, days in test_cases:
            print(f"\nTesting {sub_type} subscription:")
            
            end_date = datetime.utcnow() + timedelta(days=days) if days else None
            
            test_sub = Subscription(
                user_id=user.id,
                tag_id=tag.id,
                subscription_type=sub_type,
                status="active",
                payment_method="test",
                amount=amount,
                start_date=datetime.utcnow(),
                end_date=end_date
            )
            
            # Calculate billing period
            if test_sub.pricing_plan:
                billing_period = test_sub.pricing_plan.billing_period.title()
            elif hasattr(test_sub, 'subscription_type') and test_sub.subscription_type in ['monthly', 'yearly', 'lifetime']:
                billing_period = test_sub.subscription_type.title()
            else:
                billing_period = 'One-time'
                
            print(f"  - Subscription type: {test_sub.subscription_type}")
            print(f"  - Calculated billing period: {billing_period}")
            
            expected = sub_type.title()
            if billing_period == expected:
                print(f"  ✅ Correct: {billing_period} == {expected}")
            else:
                print(f"  ❌ Wrong: {billing_period} != {expected}")
        
        return True

if __name__ == '__main__':
    test_yearly_subscription_email()
