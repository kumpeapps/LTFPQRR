#!/usr/bin/env python3

from app import app
from models.models import Payment, Subscription
from extensions import db
from sqlalchemy import func

with app.app_context():
    print('=== Checking for Duplicate Payment Intents ===')
    
    # Find payment intents that appear more than once
    duplicate_intents = db.session.query(
        Payment.payment_intent_id,
        func.count(Payment.id).label('count')
    ).group_by(Payment.payment_intent_id).having(func.count(Payment.id) > 1).all()
    
    if duplicate_intents:
        print('Found duplicate payment intents:')
        for intent_id, count in duplicate_intents:
            print(f'Payment Intent: {intent_id} appears {count} times')
            
            # Get the actual payments
            payments = Payment.query.filter_by(payment_intent_id=intent_id).all()
            for p in payments:
                print(f'  - Payment ID: {p.id}, User: {p.user_id}, Amount: ${p.amount}, Created: {p.created_at}')
            print()
    else:
        print('No duplicate payment intents found!')
    
    print()
    print('=== Checking for Multiple Subscriptions per User ===')
    
    # Find users with multiple active subscriptions
    user_sub_counts = db.session.query(
        Subscription.user_id,
        func.count(Subscription.id).label('count')
    ).filter(Subscription.status == 'active').group_by(Subscription.user_id).having(func.count(Subscription.id) > 1).all()
    
    if user_sub_counts:
        print('Users with multiple active subscriptions:')
        for user_id, count in user_sub_counts:
            print(f'User {user_id} has {count} active subscriptions')
            subs = Subscription.query.filter_by(user_id=user_id, status='active').all()
            for s in subs:
                print(f'  - Sub ID: {s.id}, Created: {s.created_at}')
            print()
    else:
        print('No users with multiple active subscriptions found!')
    
    print()
    print('=== Recent Application Activity ===')
    
    # Show recent payments and subscriptions with timestamps
    print('Last 5 payments:')
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    for p in recent_payments:
        print(f'  Payment ID: {p.id}, Intent: {p.payment_intent_id}, User: {p.user_id}, ${p.amount}, {p.created_at}')
    
    print()
    print('Last 5 subscriptions:')
    recent_subs = Subscription.query.order_by(Subscription.created_at.desc()).limit(5).all()
    for s in recent_subs:
        print(f'  Sub ID: {s.id}, User: {s.user_id}, Status: {s.status}, {s.created_at}')
