"""
Auto-renewal service for LTFPQRR subscriptions
"""
from datetime import datetime, timedelta
from extensions import db, logger
from models.models import Subscription, PartnerSubscription, User
from email_utils import send_subscription_renewal_email
import stripe


class SubscriptionRenewalService:
    """Service to handle automatic subscription renewals"""
    
    @staticmethod
    def process_all_renewals():
        """Process all subscriptions that need renewal"""
        logger.info("Starting auto-renewal processing...")
        
        # Process regular subscriptions
        renewed_count = SubscriptionRenewalService.process_subscription_renewals()
        
        # Process partner subscriptions  
        partner_renewed_count = SubscriptionRenewalService.process_partner_subscription_renewals()
        
        total_renewed = renewed_count + partner_renewed_count
        logger.info(f"Auto-renewal processing completed. Renewed {total_renewed} subscriptions ({renewed_count} tag, {partner_renewed_count} partner)")
        
        return {
            'total_renewed': total_renewed,
            'tag_renewals': renewed_count,
            'partner_renewals': partner_renewed_count
        }
    
    @staticmethod
    def process_subscription_renewals():
        """Process regular tag subscription renewals"""
        renewed_count = 0
        
        # Find subscriptions that need renewal (expire in next 24 hours and have auto_renew enabled)
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        subscriptions_to_renew = Subscription.query.filter(
            Subscription.auto_renew == True,
            Subscription.status == 'active',
            Subscription.end_date <= tomorrow,
            Subscription.end_date > datetime.utcnow()  # Not already expired
        ).all()
        
        logger.info(f"Found {len(subscriptions_to_renew)} tag subscriptions to renew")
        
        for subscription in subscriptions_to_renew:
            try:
                if SubscriptionRenewalService.renew_subscription(subscription):
                    renewed_count += 1
            except Exception as e:
                logger.error(f"Error renewing tag subscription {subscription.id}: {e}")
        
        return renewed_count
    
    @staticmethod
    def process_partner_subscription_renewals():
        """Process partner subscription renewals"""
        renewed_count = 0
        
        # Find partner subscriptions that need renewal
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        subscriptions_to_renew = PartnerSubscription.query.filter(
            PartnerSubscription.auto_renew == True,
            PartnerSubscription.status == 'active',
            PartnerSubscription.end_date <= tomorrow,
            PartnerSubscription.end_date > datetime.utcnow()  # Not already expired
        ).all()
        
        logger.info(f"Found {len(subscriptions_to_renew)} partner subscriptions to renew")
        
        for subscription in subscriptions_to_renew:
            try:
                if SubscriptionRenewalService.renew_partner_subscription(subscription):
                    renewed_count += 1
            except Exception as e:
                logger.error(f"Error renewing partner subscription {subscription.id}: {e}")
        
        return renewed_count
    
    @staticmethod
    def renew_subscription(subscription):
        """Renew a regular tag subscription"""
        try:
            logger.info(f"Renewing tag subscription {subscription.id} for user {subscription.user.username}")
            
            # Calculate new end date based on subscription type
            if subscription.subscription_type == 'monthly':
                new_end_date = subscription.end_date + timedelta(days=30)
            elif subscription.subscription_type == 'yearly':
                new_end_date = subscription.end_date + timedelta(days=365)
            elif subscription.subscription_type == 'lifetime':
                # Lifetime subscriptions don't need renewal
                logger.info(f"Skipping lifetime subscription {subscription.id}")
                return False
            else:
                logger.warning(f"Unknown subscription type {subscription.subscription_type} for subscription {subscription.id}")
                return False
            
            # Try to process payment if payment method is available
            payment_successful = True
            if subscription.payment_method == 'stripe' and subscription.payment_id:
                payment_successful = SubscriptionRenewalService.process_stripe_renewal_payment(subscription)
            
            if not payment_successful:
                logger.warning(f"Payment failed for subscription {subscription.id}, cancelling auto-renewal")
                subscription.auto_renew = False
                subscription.status = 'expired'
                db.session.commit()
                return False
            
            # Update subscription dates
            subscription.start_date = subscription.end_date  # New period starts when old one ends
            subscription.end_date = new_end_date
            subscription.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Send renewal notification email
            try:
                send_subscription_renewal_email(subscription.user, subscription)
            except Exception as email_error:
                logger.warning(f"Failed to send renewal email for subscription {subscription.id}: {email_error}")
            
            logger.info(f"Successfully renewed tag subscription {subscription.id} until {new_end_date}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error renewing subscription {subscription.id}: {e}")
            return False
    
    @staticmethod
    def renew_partner_subscription(subscription):
        """Renew a partner subscription"""
        try:
            logger.info(f"Renewing partner subscription {subscription.id} for partner {subscription.partner.company_name}")
            
            # Calculate new end date based on pricing plan
            if subscription.pricing_plan:
                if subscription.pricing_plan.billing_period == 'monthly':
                    new_end_date = subscription.end_date + timedelta(days=30)
                elif subscription.pricing_plan.billing_period == 'yearly':
                    new_end_date = subscription.end_date + timedelta(days=365)
                elif subscription.pricing_plan.billing_period == 'lifetime':
                    # Lifetime subscriptions don't need renewal
                    logger.info(f"Skipping lifetime partner subscription {subscription.id}")
                    return False
                else:
                    logger.warning(f"Unknown billing period {subscription.pricing_plan.billing_period} for partner subscription {subscription.id}")
                    return False
            else:
                # Default to yearly for partner subscriptions without pricing plan
                new_end_date = subscription.end_date + timedelta(days=365)
            
            # Try to process payment if payment method is available
            payment_successful = True
            if subscription.payment_method == 'stripe' and subscription.payment_id:
                payment_successful = SubscriptionRenewalService.process_stripe_renewal_payment(subscription)
            
            if not payment_successful:
                logger.warning(f"Payment failed for partner subscription {subscription.id}, cancelling auto-renewal")
                subscription.auto_renew = False
                subscription.status = 'expired'
                db.session.commit()
                return False
            
            # Update subscription dates
            subscription.start_date = subscription.end_date  # New period starts when old one ends
            subscription.end_date = new_end_date
            subscription.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Send renewal notification email
            try:
                send_subscription_renewal_email(subscription.user, subscription)
            except Exception as email_error:
                logger.warning(f"Failed to send renewal email for partner subscription {subscription.id}: {email_error}")
            
            logger.info(f"Successfully renewed partner subscription {subscription.id} until {new_end_date}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error renewing partner subscription {subscription.id}: {e}")
            return False
    
    @staticmethod
    def process_stripe_renewal_payment(subscription):
        """Process payment for subscription renewal via Stripe"""
        try:
            from models.models import SystemSetting
            
            # Get Stripe configuration
            stripe_key = SystemSetting.get_value('stripe_secret_key')
            if not stripe_key:
                logger.warning("No Stripe secret key configured, skipping payment processing")
                return True  # Continue with renewal but without payment
            
            stripe.api_key = stripe_key
            
            # Create a new payment intent for renewal
            payment_intent = stripe.PaymentIntent.create(
                amount=int(float(subscription.amount) * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'subscription_id': subscription.id,
                    'subscription_type': subscription.subscription_type,
                    'renewal': 'true'
                },
                description=f"Auto-renewal for {subscription.subscription_type} subscription"
            )
            
            # For auto-renewal, we would typically use a saved payment method
            # This is a simplified version - in production you'd want to:
            # 1. Save customer payment methods during initial subscription
            # 2. Use those saved methods for auto-renewal
            # 3. Handle failed payments with retry logic
            
            logger.info(f"Created Stripe payment intent for subscription {subscription.id}: {payment_intent.id}")
            
            # Update payment ID for tracking
            subscription.payment_id = payment_intent.id
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Stripe payment for subscription {subscription.id}: {e}")
            return False
    
    @staticmethod
    def get_subscriptions_expiring_soon(days=7):
        """Get subscriptions that will expire within the specified number of days"""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        expiring_subscriptions = Subscription.query.filter(
            Subscription.status == 'active',
            Subscription.end_date <= cutoff_date,
            Subscription.end_date > datetime.utcnow()
        ).all()
        
        expiring_partner_subscriptions = PartnerSubscription.query.filter(
            PartnerSubscription.status == 'active',
            PartnerSubscription.end_date <= cutoff_date,
            PartnerSubscription.end_date > datetime.utcnow()
        ).all()
        
        return {
            'tag_subscriptions': expiring_subscriptions,
            'partner_subscriptions': expiring_partner_subscriptions,
            'total_count': len(expiring_subscriptions) + len(expiring_partner_subscriptions)
        }
    
    @staticmethod
    def enable_auto_renewal_for_subscription(subscription_id, subscription_type='tag'):
        """Enable auto-renewal for a specific subscription"""
        try:
            if subscription_type == 'tag':
                subscription = Subscription.query.get(subscription_id)
            elif subscription_type == 'partner':
                subscription = PartnerSubscription.query.get(subscription_id)
            else:
                raise ValueError(f"Invalid subscription type: {subscription_type}")
            
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")
            
            subscription.auto_renew = True
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Enabled auto-renewal for {subscription_type} subscription {subscription_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error enabling auto-renewal for subscription {subscription_id}: {e}")
            return False
