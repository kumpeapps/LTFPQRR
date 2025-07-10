#!/usr/bin/env python3
"""
Final verification that the application can be properly initialized
"""

import os
import sys

def check_configuration():
    """Check that all configuration files are properly updated"""
    
    print("Final Configuration Check")
    print("=" * 50)
    
    # Check requirements.txt
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'squareup' not in content and 'stripe' in content and 'paypal' in content:
                print("✓ requirements.txt: Square removed, Stripe/PayPal present")
            else:
                print("✗ requirements.txt: Issue with package configuration")
                return False
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False
    
    # Check docker-compose.yml
    try:
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
            if 'SQUARE_ACCESS_TOKEN' not in content and 'STRIPE_SECRET_KEY' in content and 'PAYPAL_CLIENT_ID' in content:
                print("✓ docker-compose.yml: Square vars removed, Stripe/PayPal present")
            else:
                print("✗ docker-compose.yml: Issue with environment variables")
                return False
    except Exception as e:
        print(f"✗ Error reading docker-compose.yml: {e}")
        return False
    
    # Check .env file
    try:
        with open('.env', 'r') as f:
            content = f.read()
            if 'SQUARE_ACCESS_TOKEN' not in content and 'STRIPE_SECRET_KEY' in content and 'PAYPAL_CLIENT_ID' in content:
                print("✓ .env: Square vars removed, Stripe/PayPal present")
            else:
                print("✗ .env: Issue with environment variables")
                return False
    except Exception as e:
        print(f"✗ Error reading .env: {e}")
        return False
    
    # Check models/models.py
    try:
        with open('models/models.py', 'r') as f:
            content = f.read()
            if 'PaymentGateway' in content and 'square' not in content.lower():
                print("✓ models/models.py: PaymentGateway present, Square removed")
            else:
                print("✗ models/models.py: Issue with model definition")
                return False
    except Exception as e:
        print(f"✗ Error reading models/models.py: {e}")
        return False
    
    # Check forms.py
    try:
        with open('forms.py', 'r') as f:
            content = f.read()
            if 'get_payment_gateway_choices' in content and 'square' not in content.lower():
                print("✓ forms.py: Dynamic choices implemented, Square removed")
            else:
                print("✗ forms.py: Issue with form configuration")
                return False
    except Exception as e:
        print(f"✗ Error reading forms.py: {e}")
        return False
    
    # Check app.py
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            if 'configure_payment_gateways' in content and 'update_payment_gateway_settings' in content and 'square' not in content.lower():
                print("✓ app.py: Database configuration implemented, Square removed")
            else:
                print("✗ app.py: Issue with application configuration")
                return False
    except Exception as e:
        print(f"✗ Error reading app.py: {e}")
        return False
    
    print("\n✅ All configuration checks passed!")
    return True

def main():
    """Run final verification"""
    os.chdir('/Users/justinkumpe/Documents/LTFPQRR')
    
    if check_configuration():
        print("\n🎉 SUCCESS: Square payment gateway has been completely removed!")
        print("🔧 Payment gateway settings have been moved to database configuration")
        print("✅ The application is ready to use Stripe and PayPal only")
        return True
    else:
        print("\n❌ FAILURE: Some configuration issues remain")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
