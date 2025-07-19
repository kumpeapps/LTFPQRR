#!/usr/bin/env python3
"""
Test the enhanced email template system
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from email_utils import send_test_email

def test_email_templates():
    """Test the enhanced email template system"""
    app = create_app()
    
    with app.app_context():
        print("Testing enhanced email template system...")
        
        # Test the test email template
        test_email = "test@example.com"
        result = send_test_email(test_email)
        
        if result:
            print(f"✅ Test email template sent successfully to {test_email}")
        else:
            print(f"❌ Failed to send test email template to {test_email}")
        
        return result

if __name__ == '__main__':
    test_email_templates()
