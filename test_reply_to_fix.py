"""
Test script to verify pet owner contact email reply-to functionality
"""

import os
import sys
sys.path.append('/app')

from flask import Flask
from config import config
from extensions import db

def test_reply_to_functionality():
    """Test that pet contact emails include proper reply-to headers"""
    try:
        from models.models import User, Pet, Tag
        from utils import send_contact_email
        from models.email.email_models import EmailQueue
        
        print("🔍 Testing reply-to functionality...")
        
        # Find a test user and pet
        user = User.query.first()
        if not user:
            print("❌ No users found for testing")
            return False
            
        pet = Pet.query.filter_by(owner_id=user.id).first()
        if not pet:
            print("❌ No pets found for testing")
            return False
        
        # Test sending contact email
        finder_name = "Test Finder"
        finder_email = "finder@test.com"
        message = "I found your pet!"
        
        print(f"📧 Sending test contact email to {user.email}")
        print(f"   Finder: {finder_name} ({finder_email})")
        print(f"   Pet: {pet.name}")
        
        # Send the contact email
        success = send_contact_email(user, pet, finder_name, finder_email, message)
        
        if success:
            # Check the queued email for reply-to field
            latest_email = EmailQueue.query.filter_by(
                to_email=user.email,
                email_type="pet_found_contact"
            ).order_by(EmailQueue.created_at.desc()).first()
            
            if latest_email:
                print(f"✅ Email queued successfully")
                print(f"   To: {latest_email.to_email}")
                print(f"   Subject: {latest_email.subject}")
                print(f"   Reply-To: {latest_email.reply_to}")
                
                if latest_email.reply_to == finder_email:
                    print("✅ Reply-To field correctly set to finder's email!")
                    return True
                else:
                    print(f"❌ Reply-To field incorrect. Expected: {finder_email}, Got: {latest_email.reply_to}")
                    return False
            else:
                print("❌ No email found in queue")
                return False
        else:
            print("❌ Failed to send contact email")
            return False
            
    except Exception as e:
        print(f"❌ Error testing reply-to functionality: {e}")
        return False

if __name__ == '__main__':
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config['default'])
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        success = test_reply_to_functionality()
        if success:
            print("\n🎉 Reply-to functionality is working correctly!")
            print("   Pet owner contact emails will now reply directly to the finder.")
        else:
            print("\n💥 Reply-to functionality test failed!")
