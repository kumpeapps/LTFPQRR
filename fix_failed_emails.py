#!/usr/bin/env python3
"""
Manually fix failed emails that should be retried
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.email.email_models import EmailQueue, EmailStatus
from sqlalchemy import desc
from datetime import datetime, timedelta

def fix_failed_emails():
    app = create_app()
    with app.app_context():
        try:
            # Get failed emails that can be retried
            failed_emails = EmailQueue.query.filter(
                EmailQueue.status == EmailStatus.FAILED,
                EmailQueue.retry_count < EmailQueue.max_retries,
                EmailQueue.expires_at > datetime.utcnow()
            ).all()
            
            print(f"Found {len(failed_emails)} failed emails that can be retried")
            
            for email in failed_emails:
                print(f"Fixing email ID {email.id}: {email.to_email}")
                # Reset to retry status with new schedule
                email.status = EmailStatus.RETRY
                delay_minutes = min(60, 5 * (2 ** (email.retry_count)))
                email.scheduled_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
                print(f"  Set to retry status, scheduled for: {email.scheduled_at}")
            
            if failed_emails:
                db.session.commit()
                print(f"Successfully updated {len(failed_emails)} emails to retry status")
            else:
                print("No failed emails found that can be retried")
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    fix_failed_emails()
