#!/usr/bin/env python3
"""
Debug retry logic for failed emails
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

def debug_retry_logic():
    app = create_app()
    with app.app_context():
        try:
            # Get a failed email to debug
            failed_email = EmailQueue.query.filter(EmailQueue.status == EmailStatus.FAILED).first()
            
            if not failed_email:
                print("No failed emails found")
                return
                
            print(f"Debugging email ID: {failed_email.id}")
            print(f"Status: {failed_email.status.value}")
            print(f"Retry count: {failed_email.retry_count}/{failed_email.max_retries}")
            print(f"Expires at: {failed_email.expires_at}")
            print(f"Current time: {datetime.utcnow()}")
            print(f"Has expired: {datetime.utcnow() >= failed_email.expires_at}")
            print(f"Can retry: {failed_email.can_retry()}")
            
            # Check each condition in can_retry
            print(f"\ncan_retry() conditions:")
            print(f"  status in [FAILED, RETRY]: {failed_email.status in [EmailStatus.FAILED, EmailStatus.RETRY]}")
            print(f"  retry_count < max_retries: {failed_email.retry_count} < {failed_email.max_retries} = {failed_email.retry_count < failed_email.max_retries}")
            print(f"  not expired: {datetime.utcnow()} < {failed_email.expires_at} = {datetime.utcnow() < failed_email.expires_at}")
            
            # Try to retry this email manually
            print(f"\nTesting mark_failed with retry logic...")
            original_retry_count = failed_email.retry_count
            
            # Reset the retry count to test the logic
            failed_email.retry_count = 0
            print(f"Reset retry count to: {failed_email.retry_count}")
            print(f"Can retry now: {failed_email.can_retry()}")
            
            # Call mark_failed to test the logic
            failed_email.mark_failed("Test error for retry logic")
            print(f"After mark_failed:")
            print(f"  Status: {failed_email.status.value}")
            print(f"  Retry count: {failed_email.retry_count}")
            print(f"  Scheduled at: {failed_email.scheduled_at}")
            
            # Don't commit the changes - this is just for testing
            db.session.rollback()
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_retry_logic()
