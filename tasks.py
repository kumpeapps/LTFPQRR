"""
Celery tasks for LTFPQRR background processing
"""
from celery import Celery
from datetime import datetime
import os

# Initialize Celery
celery = Celery('ltfpqrr')

# Configure Celery
celery.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Schedule tasks
    beat_schedule={
        'process-subscription-renewals': {
            'task': 'tasks.process_subscription_renewals',
            'schedule': 3600.0,  # Run every hour
        },
        'send-renewal-reminders': {
            'task': 'tasks.send_renewal_reminders',
            'schedule': 86400.0,  # Run daily
        },
    },
)


@celery.task(name='tasks.process_subscription_renewals')
def process_subscription_renewals():
    """Celery task to process subscription renewals"""
    try:
        from services.renewal_service import SubscriptionRenewalService
        
        result = SubscriptionRenewalService.process_all_renewals()
        
        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'renewals_processed': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


@celery.task(name='tasks.send_renewal_reminders')
def send_renewal_reminders():
    """Celery task to send renewal reminder emails"""
    try:
        from services.renewal_service import SubscriptionRenewalService
        from email_utils import send_subscription_expiry_reminder
        
        # Get subscriptions expiring in 7 days
        expiring_soon = SubscriptionRenewalService.get_subscriptions_expiring_soon(days=7)
        
        reminder_count = 0
        
        # Send reminders for tag subscriptions
        for subscription in expiring_soon['tag_subscriptions']:
            try:
                send_subscription_expiry_reminder(subscription.user, subscription)
                reminder_count += 1
            except Exception as e:
                print(f"Error sending reminder for subscription {subscription.id}: {e}")
        
        # Send reminders for partner subscriptions
        for subscription in expiring_soon['partner_subscriptions']:
            try:
                send_subscription_expiry_reminder(subscription.user, subscription)
                reminder_count += 1
            except Exception as e:
                print(f"Error sending reminder for partner subscription {subscription.id}: {e}")
        
        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'reminders_sent': reminder_count,
            'total_expiring': expiring_soon['total_count']
        }
    except Exception as e:
        return {
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


@celery.task(name='tasks.cleanup_expired_subscriptions')
def cleanup_expired_subscriptions():
    """Celery task to cleanup expired subscriptions"""
    try:
        from extensions import db
        from models.payment.payment import Subscription
        from models.partner.partner import PartnerSubscription
        from datetime import datetime, timedelta
        
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
        
        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'expired_tag_subscriptions': expired_tag_count,
            'expired_partner_subscriptions': expired_partner_count,
            'total_expired': expired_tag_count + expired_partner_count
        }
    except Exception as e:
        db.session.rollback()
        return {
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


if __name__ == '__main__':
    # For development testing
    celery.start()
