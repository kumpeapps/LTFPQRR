#!/usr/bin/env python3
"""
Debug email queue processing
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.email.email_models import EmailQueue, EmailStatus
from sqlalchemy import desc
from datetime import datetime

def debug_queue_processing():
    app = create_app()
    with app.app_context():
        try:
            current_time = datetime.utcnow()
            print(f"Current UTC time: {current_time}")
            
            # Check retry emails
            retry_emails = EmailQueue.query.filter(EmailQueue.status == EmailStatus.RETRY).all()
            print(f"\nFound {len(retry_emails)} emails with retry status:")
            
            for email in retry_emails:
                print(f"  ID: {email.id}")
                print(f"  Status: {email.status.value}")
                print(f"  Scheduled at: {email.scheduled_at}")
                print(f"  Expires at: {email.expires_at}")
                print(f"  Ready to send: {email.scheduled_at <= current_time}")
                print(f"  Not expired: {email.expires_at > current_time}")
                print(f"  Should be processed: {email.scheduled_at <= current_time and email.expires_at > current_time}")
                print("---")
            
            # Check the exact query used by process_queue
            ready_emails = EmailQueue.query.filter(
                EmailQueue.status.in_([EmailStatus.PENDING, EmailStatus.RETRY]),
                EmailQueue.scheduled_at <= current_time,
                EmailQueue.expires_at > current_time
            ).order_by(
                EmailQueue.priority.desc(),
                EmailQueue.created_at.asc()
            ).all()
            
            print(f"\nEmails ready for processing (using same query as scheduler): {len(ready_emails)}")
            for email in ready_emails:
                print(f"  ID: {email.id}, Status: {email.status.value}, Scheduled: {email.scheduled_at}")
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_queue_processing()
