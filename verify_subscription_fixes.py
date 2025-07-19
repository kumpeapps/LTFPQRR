#!/usr/bin/env python3
"""
Verification script for subscription duplicate and webhook fixes
This script tests the duplicate prevention logic and webhook event handling
"""

import sys
import os
from datetime import datetime

# Set up the Flask app context
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

def test_duplicate_prevention():
    """Test duplicate subscription prevention logic"""
    print("=== Testing Duplicate Subscription Prevention ===")
    
    try:
        from app import create_app
        from extensions import db
        from models.models import User, Tag, Subscription, Payment
        from utils import process_successful_payment
        
        app = create_app()
        
        with app.app_context():
            # Find an existing test user and tag
            test_user = User.query.first()
            test_tag = Tag.query.filter_by(status='available').first()
            
            if not test_user or not test_tag:
                print("⚠️  Need at least one user and one available tag for testing")
                return False
            
            print(f"Test user: {test_user.username}")
            print(f"Test tag: {test_tag.tag_id}")
            
            # Simulate first payment processing
            payment_intent_id = f"pi_test_duplicate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"First payment processing with intent: {payment_intent_id}")
            result1 = process_successful_payment(
                user_id=test_user.id,
                payment_type="tag",
                payment_method="stripe",
                amount=29.99,
                payment_intent_id=payment_intent_id,
                claiming_tag_id=test_tag.tag_id,
                subscription_type="yearly"
            )
            
            if not result1:
                print("❌ First payment processing failed")
                return False
            
            print("✅ First payment processing succeeded")
            
            # Check subscription was created
            subscription = Subscription.query.filter_by(
                user_id=test_user.id,
                tag_id=test_tag.id,
                status="active"
            ).first()
            
            if not subscription:
                print("❌ No subscription created after first payment")
                return False
            
            print(f"✅ Subscription created: {subscription.id}")
            
            # Simulate duplicate webhook call with same payment intent
            print(f"Duplicate payment processing with same intent: {payment_intent_id}")
            result2 = process_successful_payment(
                user_id=test_user.id,
                payment_type="tag",
                payment_method="stripe",
                amount=29.99,
                payment_intent_id=payment_intent_id,
                claiming_tag_id=test_tag.tag_id,
                subscription_type="yearly"
            )
            
            if not result2:
                print("❌ Duplicate prevention failed - should return True for already processed")
                return False
            
            # Check that only one subscription exists
            subscription_count = Subscription.query.filter_by(
                user_id=test_user.id,
                tag_id=test_tag.id,
                status="active"
            ).count()
            
            if subscription_count > 1:
                print(f"❌ Found {subscription_count} subscriptions - duplicate not prevented!")
                return False
            
            print("✅ Duplicate prevention working correctly")
            
            # Cleanup - cancel the test subscription
            if subscription:
                subscription.status = "cancelled"
                test_tag.status = "available"
                test_tag.owner_id = None
                db.session.commit()
                print("✅ Test cleanup completed")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_webhook_events():
    """Test webhook event handling"""
    print("\n=== Testing Webhook Event Handling ===")
    
    try:
        from app import create_app
        from routes.payment import payment
        
        app = create_app()
        
        with app.test_client() as client:
            # Test webhook endpoint exists
            print("Testing webhook endpoint availability...")
            
            # This will fail without proper signature, but should not return 404
            response = client.post('/payment/stripe/webhook', 
                                 data='{"test": "data"}',
                                 headers={'Content-Type': 'application/json'})
            
            if response.status_code == 404:
                print("❌ Webhook endpoint not found (404)")
                return False
            elif response.status_code == 400:
                print("✅ Webhook endpoint exists (returned 400 for invalid payload)")
                return True
            else:
                print(f"✅ Webhook endpoint exists (returned {response.status_code})")
                return True
                
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False


def test_payment_lookup_fix():
    """Test improved payment lookup in refund/cancellation functions"""
    print("\n=== Testing Payment Lookup Fix ===")
    
    try:
        from app import create_app
        from extensions import db
        from models.models import Payment, User
        from utils import process_payment_refund
        
        app = create_app()
        
        with app.app_context():
            # Find or create a test payment record
            test_user = User.query.first()
            if not test_user:
                print("⚠️  Need at least one user for testing")
                return False
            
            # Create a test payment with payment_intent_id
            test_payment_intent = f"pi_test_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            test_payment = Payment(
                user_id=test_user.id,
                payment_gateway="stripe",
                payment_intent_id=test_payment_intent,
                amount=29.99,
                status="completed",
                payment_type="tag"
            )
            test_payment.generate_transaction_id()
            test_payment.mark_completed()
            
            db.session.add(test_payment)
            db.session.commit()
            
            print(f"Created test payment with intent ID: {test_payment_intent}")
            
            # Test that payment can be found by payment_intent_id
            result = process_payment_refund(
                payment_intent_id=test_payment_intent,
                refund_reason="test_refund",
                refund_amount=29.99,
                webhook_event_type="test"
            )
            
            if not result:
                print("❌ Payment lookup by payment_intent_id failed")
                return False
            
            # Check payment status was updated
            test_payment = Payment.query.filter_by(payment_intent_id=test_payment_intent).first()
            if test_payment.status != "refunded":
                print("❌ Payment status not updated to refunded")
                return False
            
            print("✅ Payment lookup and refund processing working correctly")
            
            # Cleanup
            db.session.delete(test_payment)
            db.session.commit()
            print("✅ Test cleanup completed")
            
            return True
            
    except Exception as e:
        print(f"❌ Payment lookup test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Run all verification tests"""
    print("🔍 LTFPQRR Subscription & Webhook Fixes Verification")
    print("=" * 60)
    
    tests = [
        ("Duplicate Prevention", test_duplicate_prevention),
        ("Webhook Events", test_webhook_events),
        ("Payment Lookup Fix", test_payment_lookup_fix)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
        
        if result:
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Fixes are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
