#!/usr/bin/env python3

from app import app
from models.models import Payment, Subscription, User, Tag
from extensions import db
from utils import process_successful_payment
import threading
import time

def test_concurrent_payments():
    """Test concurrent payment processing to reproduce the duplicate issue"""
    
    with app.app_context():
        # Get a test user and tag
        user = User.query.first()
        tag = Tag.query.filter_by(status='available').first()
        
        if not user or not tag:
            print("Need at least one user and one available tag for testing")
            return
            
        print(f"Testing with user {user.id} and tag {tag.tag_id}")
        
        # Same payment intent ID for both concurrent requests
        payment_intent_id = "pi_test_duplicate_" + str(int(time.time()))
        print(f"Using payment intent ID: {payment_intent_id}")
        
        results = []
        
        def concurrent_payment(thread_id):
            """Simulate concurrent payment processing"""
            with app.app_context():
                try:
                    print(f"Thread {thread_id} starting payment processing...")
                    result = process_successful_payment(
                        user_id=user.id,
                        payment_type="tag",
                        payment_method="stripe", 
                        amount=9.99,
                        payment_intent_id=payment_intent_id,
                        claiming_tag_id=tag.tag_id,
                        subscription_type="monthly"
                    )
                    results.append((thread_id, result))
                    print(f"Thread {thread_id} completed with result: {result}")
                except Exception as e:
                    results.append((thread_id, f"ERROR: {e}"))
                    print(f"Thread {thread_id} failed with error: {e}")
        
        # Create two threads to simulate concurrent processing
        thread1 = threading.Thread(target=concurrent_payment, args=(1,))
        thread2 = threading.Thread(target=concurrent_payment, args=(2,))
        
        # Start both threads nearly simultaneously
        thread1.start()
        thread2.start()
        
        # Wait for both to complete
        thread1.join()
        thread2.join()
        
        print(f"\nResults: {results}")
        
        # Check what was actually created BEFORE cleanup
        payments = Payment.query.filter_by(payment_intent_id=payment_intent_id).all()
        subscriptions = Subscription.query.filter_by(user_id=user.id, tag_id=tag.id).all()
        
        print(f"\nPayments created: {len(payments)}")
        for p in payments:
            print(f"  Payment ID: {p.id}, Status: {p.status}, Intent: {p.payment_intent_id}")
            
        print(f"Subscriptions created: {len(subscriptions)}")
        for s in subscriptions:
            print(f"  Subscription ID: {s.id}, Status: {s.status}, Payment ID: {s.payment_id}")
            
        # Record duplicate status before cleanup
        duplicate_found = len(payments) > 1 or len(subscriptions) > 1
        
        # Clean up test data
        for s in subscriptions:
            db.session.delete(s)
        for p in payments:
            db.session.delete(p)
        tag.status = 'available'
        tag.owner_id = None
        tag.pet_id = None  # Remove pet association when releasing tag
        db.session.commit()
        
        print(f"\nTest completed. Found {len(payments)} payments and {len(subscriptions)} subscriptions")
        return duplicate_found

if __name__ == "__main__":
    print("Testing duplicate payment scenario...")
    duplicate_found = test_concurrent_payments()
    print(f"Duplicate issue reproduced: {duplicate_found}")
