#!/usr/bin/env python3
"""
Test script to add an email to the queue for testing the dashboard/queue fix
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.email_service import EmailManager, EmailPriority

def create_test_email():
    """Create a test email in the queue"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating test email in queue...")
            
            # Queue a test email
            queue_item = EmailManager.queue_email(
                to_email="test@example.com",
                subject="Test Email for Queue Testing",
                html_body="<h1>Test Email</h1><p>This is a test email to verify the queue system is working correctly.</p>",
                text_body="Test Email\n\nThis is a test email to verify the queue system is working correctly.",
                priority=EmailPriority.NORMAL,
                send_immediately=False  # Don't send immediately, just queue it
            )
            
            print(f"✅ Test email created successfully with ID: {queue_item.id}")
            print(f"   To: {queue_item.to_email}")
            print(f"   Subject: {queue_item.subject}")
            print(f"   Status: {queue_item.status.value}")
            print(f"   Priority: {queue_item.priority.value}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating test email: {e}")
            return False

if __name__ == '__main__':
    success = create_test_email()
    sys.exit(0 if success else 1)
