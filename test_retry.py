#!/usr/bin/env python3
"""
Test retry processing by setting one email to immediate retry
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.email.email_models import EmailQueue, EmailStatus
from datetime import datetime, timedelta

def test_retry_processing():
    app = create_app()
    with app.app_context():
        try:
            # Get one retry email and set it to process immediately
            retry_email = EmailQueue.query.filter(EmailQueue.status == EmailStatus.RETRY).first()
            
            if retry_email:
                print(f"Setting email ID {retry_email.id} to process immediately")
                retry_email.scheduled_at = datetime.utcnow() - timedelta(minutes=1)
                db.session.commit()
                print(f"Email ID {retry_email.id} scheduled for: {retry_email.scheduled_at}")
                
                # Test the manual retry processing
                from services.email_service import EmailManager
                
                print("Processing the email manually...")
                success = EmailManager.process_queue_item(retry_email)
                print(f"Processing result: {success}")
                print(f"Email status after processing: {retry_email.status.value}")
                
            else:
                print("No retry emails found")
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    test_retry_processing()
