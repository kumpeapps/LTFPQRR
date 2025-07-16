#!/usr/bin/env python3
"""
Email queue processing script for LTFPQRR
Can be run as a scheduled task to process pending emails
"""
import sys
import os
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.email_service import EmailManager
from extensions import logger


def process_email_queue(limit=50, verbose=False):
    """Process pending emails in the queue"""
    app = create_app()
    
    with app.app_context():
        try:
            print(f"Starting email queue processing at {datetime.now()}")
            
            # Process the queue
            stats = EmailManager.process_queue(limit=limit)
            
            if 'error' in stats:
                print(f"ERROR: {stats['error']}")
                return False
            
            print(f"Queue processing complete:")
            print(f"  - Processed: {stats['processed']}")
            print(f"  - Sent: {stats['sent']}")
            print(f"  - Failed: {stats['failed']}")
            print(f"  - Expired: {stats['expired']}")
            
            if verbose:
                # Get current queue stats
                queue_stats = EmailManager.get_queue_stats()
                print(f"\nCurrent queue status:")
                for status, count in queue_stats.get('queue', {}).items():
                    print(f"  - {status}: {count}")
            
            return True
            
        except Exception as e:
            print(f"ERROR processing email queue: {e}")
            logger.error(f"Email queue processing error: {e}")
            return False


def cleanup_old_emails(days=30, verbose=False):
    """Clean up old email logs and queue items"""
    app = create_app()
    
    with app.app_context():
        try:
            print(f"Starting email cleanup (older than {days} days) at {datetime.now()}")
            
            result = EmailManager.cleanup_old_emails(days=days)
            
            if 'error' in result:
                print(f"ERROR: {result['error']}")
                return False
            
            print(f"Cleanup complete:")
            print(f"  - Logs deleted: {result['logs_deleted']}")
            print(f"  - Queue items deleted: {result['queue_deleted']}")
            
            return True
            
        except Exception as e:
            print(f"ERROR cleaning up emails: {e}")
            logger.error(f"Email cleanup error: {e}")
            return False


def get_queue_status():
    """Get and display current queue status"""
    app = create_app()
    
    with app.app_context():
        try:
            stats = EmailManager.get_queue_stats()
            
            print(f"Email Queue Status at {datetime.now()}:")
            print("=" * 50)
            
            print("\nQueue by Status:")
            for status, count in stats.get('queue', {}).items():
                print(f"  {status.title()}: {count}")
            
            print(f"\nPending emails: {stats.get('pending_count', 0)}")
            
            print("\nLast 24 Hours:")
            for status, count in stats.get('recent_24h', {}).items():
                print(f"  {status.title()}: {count}")
            
            print(f"\nFailure rate: {stats.get('failure_rate', 0):.1f}%")
            
            return True
            
        except Exception as e:
            print(f"ERROR getting queue status: {e}")
            logger.error(f"Queue status error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='LTFPQRR Email Queue Management')
    parser.add_argument('action', choices=['process', 'cleanup', 'status'], 
                       help='Action to perform')
    parser.add_argument('--limit', type=int, default=50, 
                       help='Maximum number of emails to process (default: 50)')
    parser.add_argument('--days', type=int, default=30, 
                       help='Days of data to keep during cleanup (default: 30)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.action == 'process':
        success = process_email_queue(limit=args.limit, verbose=args.verbose)
    elif args.action == 'cleanup':
        success = cleanup_old_emails(days=args.days, verbose=args.verbose)
    elif args.action == 'status':
        success = get_queue_status()
    else:
        print(f"Unknown action: {args.action}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
