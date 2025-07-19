#!/usr/bin/env python3
"""
Check failed emails in the database
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.email.email_models import EmailQueue, EmailStatus
from sqlalchemy import desc

def check_failed_emails():
    app = create_app()
    with app.app_context():
        try:
            # Check current failed/retry emails
            failed_emails = EmailQueue.query.filter(
                EmailQueue.status.in_([EmailStatus.FAILED, EmailStatus.RETRY])
            ).order_by(desc(EmailQueue.created_at)).limit(10).all()

            print('Recent failed/retry emails:')
            for email in failed_emails:
                print(f'ID: {email.id}, Status: {email.status.value}, To: {email.to_email}')
                print(f'  Error: {email.last_error}')
                print(f'  Retry Count: {email.retry_count}/{email.max_retries}')
                print(f'  Scheduled: {email.scheduled_at}')
                print(f'  Can Retry: {email.can_retry()}')
                print('---')
                
            print(f'\nTotal failed/retry emails: {len(failed_emails)}')
            
            # Check all statuses
            all_statuses = db.session.query(EmailQueue.status, db.func.count(EmailQueue.id)).group_by(EmailQueue.status).all()
            print('\nEmail queue status summary:')
            for status, count in all_statuses:
                print(f'  {status.value}: {count}')
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_failed_emails()
