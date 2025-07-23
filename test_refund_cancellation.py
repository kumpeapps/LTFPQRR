#!/usr/bin/env python3
"""
Test script to verify Stripe refund properly cancels and expires subscriptions
"""

import sys
import os
from datetime import datetime, timedelta

# Set up the Flask app context
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

def test_refund_subscription_cancellation():
    """Test that refunds properly cancel and expire subscriptions"""
    print("=== Testing Stripe Refund Subscription Cancellation ===")
    
    try:
        from app import create_app
        from extensions import db
        from models.models import User, Tag, Subscription, Payment, PricingPlan
        from utils import process_payment_refund, process_successful_payment
        
        app = create_app()
        
        with app.app_context():
            # Find test data
            test_user = User.query.first()
            test_tag = Tag.query.filter_by(status='available').first()
            
            if not test_user or not test_tag:
                print("⚠️  Need at least one user and one available tag for testing")
                return False
            
            print(f"Test user: {test_user.username}")
            print(f"Test tag: {test_tag.tag_id}")
            
            # Create a test subscription
            payment_intent_id = f"pi_refund_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print("Step 1: Creating test subscription...")
            result = process_successful_payment(
                user_id=test_user.id,
                payment_type="tag",
                payment_method="stripe",
                amount=29.99,
                payment_intent_id=payment_intent_id,
                claiming_tag_id=test_tag.tag_id,
                subscription_type="yearly"
            )
            
            if not result:
                print("❌ Failed to create test subscription")
                return False
            
            # Verify subscription was created
            subscription = Subscription.query.filter_by(
                user_id=test_user.id,
                tag_id=test_tag.id,
                status="active"
            ).first()
            
            if not subscription:
                print("❌ No active subscription found after payment")
                return False
            
            print(f"✅ Created subscription {subscription.id}")
            print(f"   Status: {subscription.status}")
            print(f"   Auto-renew: {subscription.auto_renew}")
            print(f"   End date: {subscription.end_date}")
            
            # Verify tag was claimed
            test_tag = Tag.query.get(test_tag.id)  # Refresh
            if test_tag.status != "claimed" or test_tag.owner_id != test_user.id:
                print("❌ Tag was not properly claimed")
                return False
            
            print(f"✅ Tag {test_tag.tag_id} properly claimed by user")
            
            print("\nStep 2: Processing refund...")
            
            # Process refund
            refund_result = process_payment_refund(
                payment_intent_id=payment_intent_id,
                refund_reason="requested_by_customer",
                refund_amount=29.99,
                webhook_event_type="charge.refunded"
            )
            
            if not refund_result:
                print("❌ Refund processing failed")
                return False
            
            print("✅ Refund processed successfully")
            
            # Verify subscription was cancelled and expired
            subscription = Subscription.query.get(subscription.id)  # Refresh
            
            print(f"\nSubscription after refund:")
            print(f"   Status: {subscription.status}")
            print(f"   Cancellation requested: {subscription.cancellation_requested}")
            print(f"   Auto-renew: {subscription.auto_renew}")
            print(f"   End date: {subscription.end_date}")
            print(f"   Updated at: {subscription.updated_at}")
            
            # Check all expected changes
            checks = [
                (subscription.status == "cancelled", "Subscription status set to cancelled"),
                (subscription.cancellation_requested == True, "Cancellation requested flag set"),
                (subscription.auto_renew == False, "Auto-renewal disabled"),
                (subscription.end_date <= datetime.utcnow(), "End date set to past/now"),
            ]
            
            all_passed = True
            for check_result, description in checks:
                if check_result:
                    print(f"✅ {description}")
                else:
                    print(f"❌ {description}")
                    all_passed = False
            
            # Verify tag was released
            test_tag = Tag.query.get(test_tag.id)  # Refresh
            tag_checks = [
                (test_tag.status == "available", "Tag status set to available"),
                (test_tag.owner_id is None, "Tag owner cleared"),
            ]
            
            for check_result, description in tag_checks:
                if check_result:
                    print(f"✅ {description}")
                else:
                    print(f"❌ {description}")
                    all_passed = False
            
            # Verify payment was marked as refunded
            payment = Payment.query.filter_by(payment_intent_id=payment_intent_id).first()
            if payment and payment.status == "refunded":
                print("✅ Payment status set to refunded")
            else:
                print("❌ Payment status not properly updated")
                all_passed = False
            
            # Cleanup - remove test data
            print("\nStep 3: Cleaning up test data...")
            if subscription:
                db.session.delete(subscription)
            if payment:
                db.session.delete(payment)
            
            # Reset tag to available state
            test_tag.status = "available"
            test_tag.owner_id = None
            test_tag.pet_id = None  # Remove pet association when releasing tag
            
            db.session.commit()
            print("✅ Test cleanup completed")
            
            return all_passed
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Run refund cancellation test"""
    print("🧪 LTFPQRR Stripe Refund Subscription Cancellation Test")
    print("=" * 65)
    
    result = test_refund_subscription_cancellation()
    
    print("\n" + "=" * 65)
    if result:
        print("🎉 All refund cancellation tests PASSED!")
        print("✅ Stripe refunds properly cancel and expire subscriptions")
        return 0
    else:
        print("⚠️  Some refund cancellation tests FAILED!")
        print("❌ Please review the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
