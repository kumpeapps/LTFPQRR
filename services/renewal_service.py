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
        partner_renewed_count = (
            SubscriptionRenewalService.process_partner_subscription_renewals()
        )

        total_renewed = renewed_count + partner_renewed_count
        logger.info(
            f"Auto-renewal processing completed. Renewed {total_renewed} subscriptions ({renewed_count} tag, {partner_renewed_count} partner)"
        )

        return {
            "total_renewed": total_renewed,
            "tag_renewals": renewed_count,
            "partner_renewals": partner_renewed_count,
        }

    @staticmethod
    def process_subscription_renewals():
        """Process regular tag subscription renewals"""
        renewed_count = 0

        # Find subscriptions that need renewal (expire in next 24 hours and have auto_renew enabled)
        # Also include recently expired subscriptions (up to 24 hours ago) for retry attempts
        tomorrow = datetime.utcnow() + timedelta(days=1)
        yesterday = datetime.utcnow() - timedelta(days=1)

        subscriptions_to_renew = Subscription.query.filter(
            Subscription.auto_renew == True,
            Subscription.status.in_(["active", "expired"]),  # Include expired for retries
            Subscription.end_date <= tomorrow,
            Subscription.end_date
            >= yesterday,  # Allow recently expired (within 24 hours)
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
        # Include recently expired subscriptions (up to 24 hours ago) to handle missed renewals
        tomorrow = datetime.utcnow() + timedelta(days=1)
        yesterday = datetime.utcnow() - timedelta(days=1)

        subscriptions_to_renew = PartnerSubscription.query.filter(
            PartnerSubscription.auto_renew == True,
            PartnerSubscription.status.in_(["active", "expired"]),  # Include expired for retries
            PartnerSubscription.end_date <= tomorrow,
            PartnerSubscription.end_date
            >= yesterday,  # Allow recently expired (within 24 hours)
        ).all()

        logger.info(
            f"Found {len(subscriptions_to_renew)} partner subscriptions to renew"
        )

        for subscription in subscriptions_to_renew:
            try:
                if SubscriptionRenewalService.renew_partner_subscription(subscription):
                    renewed_count += 1
            except Exception as e:
                logger.error(
                    f"Error renewing partner subscription {subscription.id}: {e}"
                )

        return renewed_count

    @staticmethod
    def renew_subscription(subscription):
        """Renew a regular tag subscription with retry logic"""
        try:
            logger.info(
                f"Attempting renewal for tag subscription {subscription.id} for user {subscription.user.username} (attempt {subscription.renewal_attempts + 1})"
            )

            # Check if subscription has exceeded max retries
            if subscription.renewal_attempts >= 3:
                logger.error(f"Subscription {subscription.id} has exceeded max renewal attempts (3), cancelling auto-renewal")
                subscription.auto_renew = False
                subscription.status = 'cancelled'
                subscription.renewal_failure_reason = 'Maximum renewal attempts exceeded'
                db.session.commit()
                return False

            # Set subscription to expired if past end date during renewal attempts
            now = datetime.utcnow()
            if subscription.end_date < now and subscription.status == 'active':
                subscription.status = 'expired'
                logger.info(f"Setting subscription {subscription.id} status to expired during renewal process")

            # Get billing period from pricing plan if available
            if subscription.pricing_plan:
                billing_period = subscription.pricing_plan.billing_period
            else:
                # Fallback to subscription_type if no pricing plan
                billing_period = subscription.subscription_type

            # Calculate new end date based on billing period
            if billing_period == "monthly":
                new_end_date = subscription.end_date + timedelta(days=30)
            elif billing_period == "yearly":
                new_end_date = subscription.end_date + timedelta(days=365)
            elif billing_period == "lifetime":
                # Lifetime subscriptions don't need renewal
                logger.info(f"Skipping lifetime subscription {subscription.id}")
                return False
            else:
                error_msg = f"Unknown billing period {billing_period} for subscription {subscription.id}"
                logger.warning(error_msg)
                subscription.renewal_failure_reason = error_msg
                subscription.renewal_attempts += 1
                subscription.last_renewal_attempt = now
                db.session.commit()
                return False

            # Increment renewal attempt counter
            subscription.renewal_attempts += 1
            subscription.last_renewal_attempt = now

            # Try to process payment - PAYMENT IS REQUIRED
            payment_successful = False
            payment_error = None
            
            if subscription.payment_method == "stripe" and subscription.payment_id:
                try:
                    payment_successful = SubscriptionRenewalService.process_stripe_renewal_payment(subscription)
                except Exception as e:
                    payment_error = str(e)
                    logger.error(f"Payment processing error for subscription {subscription.id}: {e}")

            if not payment_successful:
                error_msg = f"Payment failed for subscription {subscription.id}: {payment_error or 'Payment processing failed'}"
                logger.error(error_msg)
                subscription.renewal_failure_reason = error_msg
                
                # Keep subscription expired until payment succeeds
                subscription.status = 'expired'
                db.session.commit()
                
                # Check if this was the final attempt
                if subscription.renewal_attempts >= 3:
                    logger.error(f"Final renewal attempt failed for subscription {subscription.id}, cancelling auto-renewal")
                    subscription.auto_renew = False
                    subscription.status = 'cancelled'
                    subscription.renewal_failure_reason = 'Payment failed after 3 attempts'
                    db.session.commit()
                
                return False

            # Payment successful - update subscription
            subscription.start_date = subscription.end_date  # New period starts when old one ends
            subscription.end_date = new_end_date
            subscription.status = 'active'  # Reactivate subscription
            subscription.updated_at = now
            subscription.renewal_attempts = 0  # Reset retry counter on success
            subscription.renewal_failure_reason = None  # Clear failure reason
            subscription.last_renewal_attempt = None  # Clear last attempt timestamp

            db.session.commit()

            # Send renewal notification email
            try:
                send_subscription_renewal_email(
                    subscription.user, subscription, subscription_type="tag"
                )
            except Exception as email_error:
                logger.warning(
                    f"Failed to send renewal email for subscription {subscription.id}: {email_error}"
                )

            logger.info(
                f"Successfully renewed tag subscription {subscription.id} until {new_end_date}"
            )
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error renewing subscription {subscription.id}: {e}")
            
            # Update failure tracking
            subscription.renewal_failure_reason = str(e)
            subscription.renewal_attempts = getattr(subscription, 'renewal_attempts', 0) + 1
            subscription.last_renewal_attempt = datetime.utcnow()
            
            if subscription.renewal_attempts >= 3:
                subscription.auto_renew = False
                subscription.status = 'cancelled'
                logger.error(f"Subscription {subscription.id} cancelled after {subscription.renewal_attempts} failed attempts")
            
            db.session.commit()
            return False

    @staticmethod
    def renew_partner_subscription(subscription):
        """Renew a partner subscription"""
        try:
            logger.info(
                f"Renewing partner subscription {subscription.id} for partner {subscription.partner.company_name}"
            )

            # Calculate new end date based on pricing plan
            if subscription.pricing_plan:
                if subscription.pricing_plan.billing_period == "monthly":
                    new_end_date = subscription.end_date + timedelta(days=30)
                elif subscription.pricing_plan.billing_period == "yearly":
                    new_end_date = subscription.end_date + timedelta(days=365)
                elif subscription.pricing_plan.billing_period == "lifetime":
                    # Lifetime subscriptions don't need renewal
                    logger.info(
                        f"Skipping lifetime partner subscription {subscription.id}"
                    )
                    return False
                else:
                    logger.warning(
                        f"Unknown billing period {subscription.pricing_plan.billing_period} for partner subscription {subscription.id}"
                    )
                    return False
            else:
                # Default to yearly for partner subscriptions without pricing plan
                new_end_date = subscription.end_date + timedelta(days=365)

            # Try to process payment if payment method is available
            payment_successful = True
            if subscription.payment_method == "stripe" and subscription.payment_id:
                payment_successful = (
                    SubscriptionRenewalService.process_stripe_renewal_payment(
                        subscription
                    )
                )

            if not payment_successful:
                logger.warning(
                    f"Payment failed for partner subscription {subscription.id}, cancelling auto-renewal"
                )
                subscription.auto_renew = False
                subscription.status = "expired"
                db.session.commit()
                return False

            # Update subscription dates
            subscription.start_date = (
                subscription.end_date
            )  # New period starts when old one ends
            subscription.end_date = new_end_date
            subscription.updated_at = datetime.utcnow()

            db.session.commit()

            # Send renewal notification email
            try:
                send_subscription_renewal_email(
                    subscription.user, subscription, subscription_type="partner"
                )
            except Exception as email_error:
                logger.warning(
                    f"Failed to send renewal email for partner subscription {subscription.id}: {email_error}"
                )

            logger.info(
                f"Successfully renewed partner subscription {subscription.id} until {new_end_date}"
            )
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error renewing partner subscription {subscription.id}: {e}")
            return False

    @staticmethod
    def process_stripe_renewal_payment(subscription):
        """Process payment for subscription renewal via Stripe"""
        try:
            from models.models import PaymentGateway
            from utils import decrypt_value

            # Get Stripe configuration from payment_gateways table
            stripe_gateway = PaymentGateway.query.filter_by(
                name="stripe", enabled=True
            ).first()
            
            if not stripe_gateway or not stripe_gateway.secret_key:
                logger.warning(
                    "Stripe payment gateway not configured or not enabled, skipping payment processing"
                )
                return True  # Continue with renewal but without payment

            # Decrypt the secret key
            secret_key = decrypt_value(stripe_gateway.secret_key)
            stripe.api_key = secret_key
            
            logger.info(f"Using Stripe key: {secret_key[:7]}... for renewal payment")

            # Check if subscription has a saved payment method/customer
            if not subscription.payment_id:
                logger.warning(
                    f"No payment method saved for subscription {subscription.id}, cannot process auto-renewal payment"
                )
                return False

            # Try to retrieve the original payment intent to get customer and payment method
            try:
                original_payment_intent = stripe.PaymentIntent.retrieve(
                    subscription.payment_id
                )
                customer_id = original_payment_intent.customer
                payment_method_id = original_payment_intent.payment_method

                if not customer_id or not payment_method_id:
                    error_msg = f"Incomplete payment setup for subscription {subscription.id}: customer={customer_id}, payment_method={payment_method_id}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            except Exception as e:
                logger.error(
                    f"Could not retrieve original payment intent for subscription {subscription.id}: {e}"
                )
                return False

            # Create a new payment intent for renewal using the saved payment method
            try:
                amount = int(
                    float(
                        subscription.pricing_plan.price
                        if subscription.pricing_plan
                        else subscription.amount
                    )
                    * 100
                )

                payment_intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency="usd",
                    customer=customer_id,
                    payment_method=payment_method_id,
                    confirmation_method="automatic",
                    confirm=True,  # Automatically confirm the payment
                    off_session=True,  # Indicate this is for a subscription renewal
                    metadata={
                        "subscription_id": subscription.id,
                        "subscription_type": subscription.subscription_type,
                        "renewal": "true",
                        "billing_period": (
                            subscription.pricing_plan.billing_period
                            if subscription.pricing_plan
                            else "monthly"
                        ),
                    },
                    description=f"Auto-renewal for {subscription.subscription_type} subscription",
                )

                logger.info(
                    f"Successfully charged ${amount/100:.2f} for subscription {subscription.id} renewal: {payment_intent.id}"
                )

                # Update payment ID for tracking
                subscription.payment_id = payment_intent.id

                return True

            except stripe.error.CardError as e:
                # Card was declined
                logger.error(
                    f"Card declined for subscription {subscription.id} renewal: {e.user_message}"
                )
                return False

            except stripe.error.AuthenticationError as e:
                logger.error(
                    f"Stripe authentication error for subscription {subscription.id}: {e}"
                )
                return False

            except Exception as e:
                logger.error(
                    f"Error processing Stripe payment for subscription {subscription.id}: {e}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Error in Stripe renewal payment processing for subscription {subscription.id}: {e}"
            )
            return False

    @staticmethod
    def get_subscriptions_expiring_soon(days=7):
        """Get subscriptions that will expire within the specified number of days"""
        cutoff_date = datetime.utcnow() + timedelta(days=days)

        expiring_subscriptions = Subscription.query.filter(
            Subscription.status == "active",
            Subscription.end_date <= cutoff_date,
            Subscription.end_date > datetime.utcnow(),
        ).all()

        expiring_partner_subscriptions = PartnerSubscription.query.filter(
            PartnerSubscription.status == "active",
            PartnerSubscription.end_date <= cutoff_date,
            PartnerSubscription.end_date > datetime.utcnow(),
        ).all()

        return {
            "tag_subscriptions": expiring_subscriptions,
            "partner_subscriptions": expiring_partner_subscriptions,
            "total_count": len(expiring_subscriptions)
            + len(expiring_partner_subscriptions),
        }

    @staticmethod
    def enable_auto_renewal_for_subscription(subscription_id, subscription_type="tag"):
        """Enable auto-renewal for a specific subscription"""
        try:
            if subscription_type == "tag":
                subscription = Subscription.query.get(subscription_id)
            elif subscription_type == "partner":
                subscription = PartnerSubscription.query.get(subscription_id)
            else:
                raise ValueError(f"Invalid subscription type: {subscription_type}")

            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")

            subscription.auto_renew = True
            subscription.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(
                f"Enabled auto-renewal for {subscription_type} subscription {subscription_id}"
            )
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error enabling auto-renewal for subscription {subscription_id}: {e}"
            )
            return False
