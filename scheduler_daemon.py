#!/usr/bin/env python3
"""
LTFPQRR Scheduler Daemon for Docker containers

This daemon runs scheduled tasks for subscription renewals, reminders, and cleanup
without requiring external cron or host-level scheduling.
"""

import os
import sys
import time
import signal
import threading
import logging
from datetime import datetime, timedelta
from flask import Flask
from extensions import db, logger

# Add app directory to path
sys.path.insert(0, '/app')

class SchedulerDaemon:
    """Docker-based scheduler for LTFPQRR background tasks"""
    
    def __init__(self):
        self.running = False
        self.threads = []
        self.app = None
        self.setup_logging()
        self.setup_signal_handlers()
        
    def setup_logging(self):
        """Setup logging for the scheduler"""
        os.makedirs('/app/logs', exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/logs/scheduler.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('scheduler')
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        
    def create_app(self):
        """Create Flask app for scheduler"""
        # Use the main app's create_app function to ensure proper model initialization
        from app import create_app as main_create_app
        
        # Create app using main configuration
        app = main_create_app('production')  # Use production config for scheduler
        
        return app
        
    def run_renewal_process(self):
        """Run subscription renewal processing"""
        with self.app.app_context():
            try:
                from services.renewal_service import SubscriptionRenewalService
                
                self.logger.info("Starting subscription renewal process...")
                result = SubscriptionRenewalService.process_all_renewals()
                
                if result['total_renewed'] > 0:
                    self.logger.info(f"Renewed {result['total_renewed']} subscriptions "
                                   f"({result['tag_renewals']} tag, {result['partner_renewals']} partner)")
                else:
                    self.logger.debug("No subscriptions needed renewal")
                    
            except Exception as e:
                self.logger.error(f"Error in renewal process: {e}")
                
    def run_reminder_process(self):
        """Send renewal reminder emails"""
        with self.app.app_context():
            try:
                from services.renewal_service import SubscriptionRenewalService
                from email_utils import send_subscription_expiry_reminder
                
                self.logger.info("Starting renewal reminder process...")
                
                # Get subscriptions expiring in 7 days
                expiring_soon = SubscriptionRenewalService.get_subscriptions_expiring_soon(days=7)
                
                reminder_count = 0
                
                # Send reminders for tag subscriptions
                for subscription in expiring_soon['tag_subscriptions']:
                    try:
                        if send_subscription_expiry_reminder(subscription.user, subscription):
                            reminder_count += 1
                    except Exception as e:
                        self.logger.error(f"Error sending reminder for tag subscription {subscription.id}: {e}")
                
                # Send reminders for partner subscriptions
                for subscription in expiring_soon['partner_subscriptions']:
                    try:
                        if send_subscription_expiry_reminder(subscription.user, subscription):
                            reminder_count += 1
                    except Exception as e:
                        self.logger.error(f"Error sending reminder for partner subscription {subscription.id}: {e}")
                
                if reminder_count > 0:
                    self.logger.info(f"Sent {reminder_count} renewal reminders")
                else:
                    self.logger.debug("No renewal reminders needed")
                    
            except Exception as e:
                self.logger.error(f"Error in reminder process: {e}")
                
    def run_cleanup_process(self):
        """Cleanup expired subscriptions"""
        with self.app.app_context():
            try:
                from models.models import Subscription, PartnerSubscription
                
                self.logger.info("Starting expired subscription cleanup...")
                
                # Mark subscriptions as expired if they're past their end date
                cutoff_date = datetime.utcnow()
                
                # Update tag subscriptions
                expired_tag_count = Subscription.query.filter(
                    Subscription.status == 'active',
                    Subscription.end_date < cutoff_date
                ).update({'status': 'expired'})
                
                # Update partner subscriptions
                expired_partner_count = PartnerSubscription.query.filter(
                    PartnerSubscription.status == 'active',
                    PartnerSubscription.end_date < cutoff_date
                ).update({'status': 'expired'})
                
                db.session.commit()
                
                total_expired = expired_tag_count + expired_partner_count
                if total_expired > 0:
                    self.logger.info(f"Marked {total_expired} subscriptions as expired "
                                   f"({expired_tag_count} tag, {expired_partner_count} partner)")
                else:
                    self.logger.debug("No subscriptions needed cleanup")
                    
            except Exception as e:
                db.session.rollback()
                self.logger.error(f"Error in cleanup process: {e}")
                
    def renewal_worker(self):
        """Worker thread for hourly subscription renewals"""
        self.logger.info("Renewal worker started")
        last_run = datetime.min
        
        while self.running:
            now = datetime.utcnow()
            
            # Run every hour
            if now - last_run >= timedelta(hours=1):
                self.run_renewal_process()
                last_run = now
                
            time.sleep(60)  # Check every minute
            
        self.logger.info("Renewal worker stopped")
        
    def reminder_worker(self):
        """Worker thread for daily reminder emails"""
        self.logger.info("Reminder worker started")
        last_run = datetime.min
        
        while self.running:
            now = datetime.utcnow()
            
            # Run daily at 9 AM UTC
            if (now.hour == 9 and now.minute < 5 and 
                now.date() != last_run.date()):
                self.run_reminder_process()
                last_run = now
                
            time.sleep(300)  # Check every 5 minutes
            
        self.logger.info("Reminder worker stopped")
        
    def cleanup_worker(self):
        """Worker thread for daily cleanup"""
        self.logger.info("Cleanup worker started")
        last_run = datetime.min
        
        while self.running:
            now = datetime.utcnow()
            
            # Run daily at midnight UTC
            if (now.hour == 0 and now.minute < 5 and 
                now.date() != last_run.date()):
                self.run_cleanup_process()
                last_run = now
                
            time.sleep(300)  # Check every 5 minutes
            
        self.logger.info("Cleanup worker stopped")
        
    def health_check_worker(self):
        """Worker thread to maintain health check file"""
        pid_file = '/app/logs/scheduler.pid'
        
        while self.running:
            try:
                with open(pid_file, 'w') as f:
                    f.write(str(os.getpid()))
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                self.logger.error(f"Error updating health check file: {e}")
                
        # Clean up pid file on shutdown
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except Exception:
            pass
            
    def email_queue_worker(self):
        """Worker thread for processing email queue"""
        self.logger.info("Email queue worker started")
        
        while self.running:
            try:
                with self.app.app_context():
                    # Import just what we need for email processing
                    from services.email_service import EmailManager
                    
                    # Process email queue every 30 seconds
                    stats = EmailManager.process_queue(limit=50)
                    
                    if stats.get('processed', 0) > 0:
                        self.logger.info(f"Email queue processed: {stats}")
                        
            except Exception as e:
                self.logger.error(f"Error processing email queue: {e}")
                
            time.sleep(30)  # Process every 30 seconds
            
        self.logger.info("Email queue worker stopped")
            
    def start(self):
        """Start the scheduler daemon"""
        self.logger.info("LTFPQRR Scheduler Daemon starting...")
        
        # Create Flask app
        self.app = self.create_app()
        
        # Test database connection
        with self.app.app_context():
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                self.logger.info("Database connection successful")
            except Exception as e:
                self.logger.error(f"Database connection failed: {e}")
                return False
        
        # Start worker threads
        self.running = True
        
        workers = [
            ('renewal', self.renewal_worker),
            ('reminder', self.reminder_worker),
            ('cleanup', self.cleanup_worker),
            ('health', self.health_check_worker),
            ('email_queue', self.email_queue_worker)
        ]
        
        for name, worker_func in workers:
            thread = threading.Thread(target=worker_func, name=f"{name}_worker")
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            self.logger.info(f"Started {name} worker thread")
        
        self.logger.info("All worker threads started, scheduler is running")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            
        self.stop()
        return True
        
    def stop(self):
        """Stop the scheduler daemon"""
        self.logger.info("Stopping scheduler daemon...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
            
        self.logger.info("Scheduler daemon stopped")


def main():
    """Main entry point"""
    daemon = SchedulerDaemon()
    
    # Wait for database to be ready
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            app = daemon.create_app()
            with app.app_context():
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
            break
        except Exception as e:
            retry_count += 1
            daemon.logger.info(f"Waiting for database... (attempt {retry_count}/{max_retries})")
            time.sleep(10)
    else:
        daemon.logger.error("Failed to connect to database after maximum retries")
        sys.exit(1)
    
    # Start the daemon
    daemon.start()


if __name__ == '__main__':
    main()
