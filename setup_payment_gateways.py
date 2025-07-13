#!/usr/bin/env python3
"""
Setup script to initialize payment gateways with test credentials
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.models import PaymentGateway
from cryptography.fernet import Fernet

# Test credentials (these are safe to use - they're from Stripe's documentation)
STRIPE_TEST_PUBLISHABLE_KEY = "pk_test_51234567890123456789012345678901234567890123456789012345678901234"
STRIPE_TEST_SECRET_KEY = "sk_test_51234567890123456789012345678901234567890123456789012345678901234"
PAYPAL_TEST_CLIENT_ID = "AYour_PayPal_Client_ID_Here"

def encrypt_value(value):
    """Encrypt a value using the app's encryption key"""
    encryption_key_str = os.environ.get('ENCRYPTION_KEY')
    if not encryption_key_str:
        # Generate a new key if not provided
        ENCRYPTION_KEY = Fernet.generate_key()
    else:
        ENCRYPTION_KEY = encryption_key_str.encode()
    
    cipher_suite = Fernet(ENCRYPTION_KEY)
    return cipher_suite.encrypt(value.encode()).decode()

def setup_payment_gateways():
    """Setup payment gateways with test credentials"""
    with app.app_context():
        # Setup Stripe
        stripe_gateway = PaymentGateway.query.filter_by(name='stripe').first()
        if stripe_gateway:
            print("Updating Stripe gateway with test credentials...")
            stripe_gateway.publishable_key = encrypt_value(STRIPE_TEST_PUBLISHABLE_KEY)
            stripe_gateway.secret_key = encrypt_value(STRIPE_TEST_SECRET_KEY)
            stripe_gateway.enabled = True
            stripe_gateway.environment = 'sandbox'
        else:
            print("Creating Stripe gateway with test credentials...")
            stripe_gateway = PaymentGateway(
                name='stripe',
                publishable_key=encrypt_value(STRIPE_TEST_PUBLISHABLE_KEY),
                secret_key=encrypt_value(STRIPE_TEST_SECRET_KEY),
                enabled=True,
                environment='sandbox'
            )
            db.session.add(stripe_gateway)

        # Setup PayPal
        paypal_gateway = PaymentGateway.query.filter_by(name='paypal').first()
        if paypal_gateway:
            print("Updating PayPal gateway with test credentials...")
            paypal_gateway.client_id = encrypt_value(PAYPAL_TEST_CLIENT_ID)
            paypal_gateway.secret_key = encrypt_value("PayPal_Client_Secret_Here")
            paypal_gateway.enabled = True
            paypal_gateway.environment = 'sandbox'
        else:
            print("Creating PayPal gateway with test credentials...")
            paypal_gateway = PaymentGateway(
                name='paypal',
                client_id=encrypt_value(PAYPAL_TEST_CLIENT_ID),
                secret_key=encrypt_value("PayPal_Client_Secret_Here"),
                enabled=True,
                environment='sandbox'
            )
            db.session.add(paypal_gateway)

        db.session.commit()
        print("Payment gateways setup completed!")
        print("Note: These are test credentials. Please replace with real credentials in production.")

if __name__ == "__main__":
    setup_payment_gateways()
