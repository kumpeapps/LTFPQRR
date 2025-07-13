#!/usr/bin/env python3
"""
Debug script to check payment records for partner subscriptions.
"""
import sys
sys.path.append('.')

from app import create_app
from models.models import Payment, PartnerSubscription, Partner
from extensions import db

def debug_payment_records():
    """Debug payment records for partner subscriptions."""
    app = create_app()
    
    with app.app_context():
        print("🔍 Debugging Payment Records for Partner Subscriptions")
        print("=" * 60)
        
        # Get all partner subscriptions
        partner_subs = PartnerSubscription.query.all()
        print(f"\n📋 Found {len(partner_subs)} partner subscriptions:")
        
        for sub in partner_subs:
            print(f"\n🏢 Partner Subscription ID: {sub.id}")
            print(f"   Company: {sub.partner.company_name}")
            print(f"   Owner ID: {sub.partner.owner_id}")
            print(f"   Status: {sub.status}")
            print(f"   Admin Approved: {sub.admin_approved}")
            print(f"   Amount: ${sub.amount}")
            print(f"   Created: {sub.created_at}")
            
            # Look for payments for this partner's owner
            payments = Payment.query.filter_by(
                user_id=sub.partner.owner_id
            ).all()
            
            print(f"   💳 Payments for owner ID {sub.partner.owner_id}: {len(payments)}")
            
            for payment in payments:
                print(f"      - Payment ID: {payment.id}")
                print(f"        Type: {payment.payment_type}")
                print(f"        Status: {payment.status}")
                print(f"        Amount: ${payment.amount}")
                print(f"        Gateway: {payment.payment_gateway}")
                print(f"        Intent ID: {payment.payment_intent_id}")
                print(f"        Created: {payment.created_at}")
                print(f"        Metadata: {payment.payment_metadata}")
                print()
        
        # Check all payments with type "partner"
        print("\n💰 All Partner-type Payments:")
        print("-" * 40)
        
        partner_payments = Payment.query.filter_by(payment_type="partner").all()
        
        for payment in partner_payments:
            print(f"Payment ID: {payment.id}")
            print(f"User ID: {payment.user_id}")
            print(f"Status: {payment.status}")
            print(f"Amount: ${payment.amount}")
            print(f"Gateway: {payment.payment_gateway}")
            print(f"Intent ID: {payment.payment_intent_id}")
            print(f"Created: {payment.created_at}")
            print(f"Metadata: {payment.payment_metadata}")
            print("-" * 20)

if __name__ == "__main__":
    debug_payment_records()
