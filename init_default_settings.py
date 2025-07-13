#!/usr/bin/env python3
"""
Initialize default system settings and payment gateways
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.models import SystemSetting, PaymentGateway

def initialize_default_settings():
    """Initialize default system settings."""
    print("Initializing default system settings...")
    
    default_settings = [
        # General Settings
        ('site_name', 'LTFPQRR', 'Site name displayed in the header'),
        ('site_description', 'Lost Then Found Pet QR Registry', 'Site description for SEO'),
        ('site_url', 'http://localhost:8000', 'Base URL of the site'),
        ('registration_enabled', 'true', 'Allow new user registrations'),
        ('registration_type', 'open', 'Registration type: open, invite, approval'),
        ('email_verification_required', 'false', 'Require email verification for new accounts'),
        
        # SMTP Settings
        ('smtp_enabled', 'false', 'Enable email notifications'),
        ('smtp_server', '', 'SMTP server address (e.g., smtp.gmail.com)'),
        ('smtp_port', '587', 'SMTP server port'),
        ('smtp_username', '', 'SMTP username'),
        ('smtp_password', '', 'SMTP password or app password'),
        ('smtp_from_email', '', 'From email address for notifications'),
        ('smtp_use_tls', 'true', 'Use TLS encryption'),
        
        # Security Settings
        ('session_timeout', '3600', 'Session timeout in seconds'),
        ('max_login_attempts', '5', 'Maximum login attempts before lockout'),
        ('password_min_length', '6', 'Minimum password length'),
        
        # File Upload Settings
        ('max_file_size', '5242880', 'Maximum file upload size in bytes (5MB)'),
        ('allowed_file_types', 'jpg,jpeg,png,gif', 'Allowed file extensions'),
        
        # Maintenance
        ('maintenance_mode', 'false', 'Enable maintenance mode'),
        ('maintenance_message', 'Site is under maintenance. Please check back later.', 'Message shown during maintenance'),
    ]
    
    for key, value, description in default_settings:
        existing = SystemSetting.query.filter_by(key=key).first()
        if not existing:
            setting = SystemSetting(key=key, value=value, description=description)
            db.session.add(setting)
            print(f"  Added setting: {key} = {value}")
        else:
            print(f"  Setting already exists: {key}")
    
    db.session.commit()
    print("Default settings initialized!")

def initialize_payment_gateways():
    """Initialize default payment gateways."""
    print("Initializing payment gateways...")
    
    # Check if gateways already exist
    stripe_gateway = PaymentGateway.query.filter_by(name='stripe').first()
    if not stripe_gateway:
        stripe_gateway = PaymentGateway(
            name='stripe',
            enabled=False,
            environment='sandbox',
            publishable_key='',
            secret_key='',
            webhook_secret=''
        )
        db.session.add(stripe_gateway)
        print("  Added Stripe gateway")
    else:
        print("  Stripe gateway already exists")
    
    paypal_gateway = PaymentGateway.query.filter_by(name='paypal').first()
    if not paypal_gateway:
        paypal_gateway = PaymentGateway(
            name='paypal',
            enabled=False,
            environment='sandbox',
            client_id='',
            secret_key='',
            webhook_secret=''
        )
        db.session.add(paypal_gateway)
        print("  Added PayPal gateway")
    else:
        print("  PayPal gateway already exists")
    
    db.session.commit()
    print("Payment gateways initialized!")

def main():
    """Main function."""
    app = create_app()
    
    with app.app_context():
        try:
            initialize_default_settings()
            initialize_payment_gateways()
            print("\n✅ Successfully initialized default settings and payment gateways!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    main()
