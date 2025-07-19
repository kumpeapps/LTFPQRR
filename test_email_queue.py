#!/usr/bin/env python3
"""
Test script for pet email notifications
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.email_service import EmailManager
from extensions import logger


def test_email_queue():
    """Test the email queue processing"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Testing email queue processing...")
            
            # Check queue stats
            from models.email.email_models import EmailQueue, EmailStatus
            pending_count = EmailQueue.query.filter_by(status=EmailStatus.PENDING).count()
            print(f"Pending emails in queue: {pending_count}")
            
            if pending_count > 0:
                # Process the queue
                stats = EmailManager.process_queue(limit=10)
                print(f"Queue processing results: {stats}")
            else:
                print("No pending emails to process")
            
            return True
            
        except Exception as e:
            print(f"ERROR testing email queue: {e}")
            return False


if __name__ == '__main__':
    test_email_queue()
