"""
Utility functions and decorators.
"""
import os
import logging
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from extensions import logger, get_cipher_suite
import stripe
import paypalrestsdk

# Get cipher suite for encryption/decryption
cipher_suite = None


def init_utils(app):
    """Initialize utilities with app context."""
    global cipher_suite
    cipher_suite = get_cipher_suite(app)


def decrypt_value(encrypted_value):
    """Decrypt an encrypted value using the cipher suite."""
    if not encrypted_value or not cipher_suite:
        return None
    try:
        return cipher_suite.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        logger.error(f"Error decrypting value: {e}")
        return None


def encrypt_value(value):
    """Encrypt a value using the cipher suite."""
    if not value or not cipher_suite:
        return None
    try:
        return cipher_suite.encrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Error encrypting value: {e}")
        return None


def configure_payment_gateways():
    """Configure payment gateways from database settings."""
    try:
        from models.models import PaymentGateway
        
        # Configure Stripe
        stripe_gateway = PaymentGateway.query.filter_by(
            name="stripe", enabled=True
        ).first()
        if stripe_gateway and stripe_gateway.secret_key:
            stripe.api_key = decrypt_value(stripe_gateway.secret_key)

        # Configure PayPal
        paypal_gateway = PaymentGateway.query.filter_by(
            name="paypal", enabled=True
        ).first()
        if paypal_gateway and paypal_gateway.api_key and paypal_gateway.secret_key:
            paypalrestsdk.configure(
                {
                    "mode": paypal_gateway.environment,
                    "client_id": decrypt_value(paypal_gateway.api_key),
                    "client_secret": decrypt_value(paypal_gateway.secret_key),
                }
            )
    except Exception as e:
        logger.error(f"Error configuring payment gateways: {e}")
        # Fallback to environment variables if database configuration fails
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
        paypalrestsdk.configure(
            {
                "mode": os.environ.get("PAYPAL_MODE", "sandbox"),
                "client_id": os.environ.get("PAYPAL_CLIENT_ID"),
                "client_secret": os.environ.get("PAYPAL_CLIENT_SECRET"),
            }
        )


def get_enabled_payment_gateways():
    """Get a list of enabled payment gateways with configuration from the database."""
    try:
        from models.models import PaymentGateway
        
        gateways = PaymentGateway.query.filter_by(enabled=True).all()
        enabled_gateways = []
        gateway_config = {}

        for gateway in gateways:
            # Only include gateways that have the necessary configuration
            if (
                gateway.name == "stripe"
                and gateway.secret_key
                and gateway.publishable_key
            ):
                enabled_gateways.append("stripe")
                gateway_config["stripe"] = {
                    "publishable_key": (
                        decrypt_value(gateway.publishable_key)
                        if gateway.publishable_key
                        else ""
                    ),
                    "enabled": True,
                }
            elif gateway.name == "paypal" and gateway.client_id and gateway.secret_key:
                enabled_gateways.append("paypal")
                gateway_config["paypal"] = {
                    "client_id": (
                        decrypt_value(gateway.client_id) if gateway.client_id else ""
                    ),
                    "enabled": True,
                }

        return enabled_gateways, gateway_config
    except Exception as e:
        logger.error("Error getting enabled payment gateways: %s", str(e))
        # Return empty configuration if there's an error
        return [], {}


def update_payment_gateway_settings(
    name,
    api_key=None,
    secret_key=None,
    publishable_key=None,
    client_id=None,
    webhook_secret=None,
    environment="sandbox",
    enabled=True,
):
    """Update payment gateway settings in the database."""
    try:
        from models.models import PaymentGateway
        from extensions import db
        from datetime import datetime
        
        gateway = PaymentGateway.query.filter_by(name=name).first()
        if not gateway:
            gateway = PaymentGateway(name=name)
            db.session.add(gateway)

        # Encrypt sensitive data before storing
        if api_key:
            gateway.api_key = encrypt_value(api_key)
        if secret_key:
            gateway.secret_key = encrypt_value(secret_key)
        if publishable_key:
            gateway.publishable_key = encrypt_value(publishable_key)
        if client_id:
            gateway.client_id = encrypt_value(client_id)
        if webhook_secret:
            gateway.webhook_secret = encrypt_value(webhook_secret)

        gateway.environment = environment
        gateway.enabled = enabled
        gateway.updated_at = datetime.utcnow()

        db.session.commit()

        # Reconfigure payment gateways after update
        configure_payment_gateways()

        logger.info("Payment gateway %s updated successfully", name)
        return True
    except Exception as e:
        logger.error("Error updating payment gateway %s: %s", name, str(e))
        from extensions import db
        db.session.rollback()
        return False


# Decorators
def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role("admin"):
            flash("You need admin privileges to access this page.", "error")
            return redirect(url_for("public.index"))
        return f(*args, **kwargs)

    return decorated_function


def super_admin_required(f):
    """Decorator to require super-admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role(
            "super-admin"
        ):
            flash("You need super-admin privileges to access this page.", "error")
            return redirect(url_for("public.index"))
        return f(*args, **kwargs)

    return decorated_function


def send_notification_email(owner, tag, pet):
    """Queue notification email to pet owner when someone views their pet."""
    try:
        from extensions import logger
        from services.email_service import EmailManager
        from models.email.email_models import EmailPriority
        from datetime import datetime
        
        subject = f"🐾 Someone Found Your Pet {pet.name}!"
        
        # Queue the email for background processing
        queue_item = EmailManager.queue_email(
            to_email=owner.email,
            subject=subject,
            html_body="",  # Will be populated by template
            text_body="",  # Will be populated by template
            priority=EmailPriority.HIGH,
            user_id=owner.id,
            email_type="pet_search_notification",
            metadata={
                'pet_id': pet.id,
                'pet_name': pet.name,
                'tag_id': tag.tag_id,
                'owner_name': owner.first_name,
                'search_timestamp': datetime.utcnow().isoformat()
            },
            send_immediately=False  # Queue for background processing
        )
        
        logger.info(f"Pet search notification email queued for {owner.email} for pet {pet.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error queueing pet search notification email: {e}")
        return False


def send_contact_email(owner, pet, finder_name, finder_email, message):
    """Queue contact email from finder to pet owner."""
    try:
        from extensions import logger
        from services.email_service import EmailManager
        from models.email.email_models import EmailPriority
        
        subject = f"🐾 Message About Your Pet {pet.name} from {finder_name}"
        
        # Queue the email for background processing
        queue_item = EmailManager.queue_email(
            to_email=owner.email,
            subject=subject,
            html_body="",  # Will be populated by template
            text_body="",  # Will be populated by template
            reply_to=finder_email,  # Set finder's email as reply-to
            priority=EmailPriority.HIGH,
            user_id=owner.id,
            email_type="pet_found_contact",
            metadata={
                'pet_id': pet.id,
                'pet_name': pet.name,
                'owner_name': owner.first_name,
                'finder_name': finder_name,
                'finder_email': finder_email,
                'message': message
            },
            send_immediately=False  # Queue for background processing
        )
        
        logger.info(f"Pet found contact email queued for {owner.email} from {finder_name} about pet {pet.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error queueing pet found contact email: {e}")
        return False


def process_successful_payment(
    user_id,
    payment_type,
    payment_method,
    amount,
    payment_intent_id,
    claiming_tag_id=None,
    subscription_type=None,
):
    """Process a successful payment and create/update subscriptions"""
    from models.models import User, Tag, Subscription, Payment, PricingPlan, Role
    from extensions import db, logger
    from datetime import datetime, timedelta
    
    logger.info(f"Processing payment: user_id={user_id}, payment_type={payment_type}, amount=${amount}, payment_intent_id={payment_intent_id}")
    
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found for payment processing")
            return False

        logger.info(f"Found user: {user.username}")

        # Create payment record first
        payment = Payment(
            user_id=user_id,
            payment_gateway=payment_method,
            payment_intent_id=payment_intent_id,
            amount=amount,
            status="completed",
            payment_type=payment_type,
            payment_metadata={
                "claiming_tag_id": claiming_tag_id,
                "subscription_type": subscription_type,
            },
        )
        payment.generate_transaction_id()
        payment.mark_completed()
        db.session.add(payment)
        db.session.flush()  # Get payment ID
        
        logger.info(f"Created payment record with ID: {payment.id}, transaction_id: {payment.transaction_id}")

        if payment_type == "tag" and claiming_tag_id:
            logger.info(f"Processing tag subscription for tag {claiming_tag_id}")
            # Process tag subscription
            tag = Tag.query.filter_by(tag_id=claiming_tag_id).first()
            if tag:
                tag.owner_id = user_id
                tag.status = "claimed"

                # Find appropriate pricing plan
                pricing_plan = PricingPlan.query.filter_by(
                    plan_type="tag",
                    billing_period=subscription_type,
                    is_active=True,
                ).first()

                # Create subscription
                subscription = Subscription(
                    user_id=user_id,
                    tag_id=tag.id,
                    pricing_plan_id=pricing_plan.id if pricing_plan else None,
                    subscription_type="tag",
                    status="active",
                    payment_method=payment_method,
                    payment_id=payment_intent_id,
                    amount=amount,
                    start_date=datetime.utcnow(),
                    auto_renew=(
                        True if subscription_type in ["monthly", "yearly"] else False
                    ),
                )

                # Set end date based on subscription type
                if subscription_type == "yearly":
                    subscription.end_date = datetime.utcnow() + timedelta(days=365)
                elif subscription_type == "monthly":
                    subscription.end_date = datetime.utcnow() + timedelta(days=30)
                else:  # lifetime
                    subscription.end_date = None  # No end date for lifetime

                db.session.add(subscription)
                db.session.flush()  # Get subscription ID

                # Link payment to subscription
                payment.subscription_id = subscription.id
                logger.info(f"Created tag subscription with ID: {subscription.id}")

        elif payment_type == "partner":
            logger.info(f"Processing partner subscription for user {user_id}")
            
            # Import Flask session to access session data
            from flask import session
            
            # Get partner and pricing plan from session
            partner_id = session.get("partner_id")
            pricing_plan_id = session.get("pricing_plan_id")
            
            logger.info(f"Partner ID from session: {partner_id}")
            logger.info(f"Pricing plan ID from session: {pricing_plan_id}")
            
            if not partner_id or not pricing_plan_id:
                logger.error("Missing partner_id or pricing_plan_id in session")
                return False
            
            # Get the partner and pricing plan
            from models.models import Partner, PartnerSubscription
            partner = Partner.query.get(partner_id)
            pricing_plan = PricingPlan.query.get(pricing_plan_id)
            
            if not partner or not pricing_plan:
                logger.error(f"Partner ({partner_id}) or pricing plan ({pricing_plan_id}) not found")
                return False
                
            logger.info(f"Found partner: {partner.company_name}")
            logger.info(f"Found pricing plan: {pricing_plan.name}, requires_approval: {pricing_plan.requires_approval}")
            
            # Check if approval is required
            requires_approval = pricing_plan.requires_approval if pricing_plan else False
            
            # Create partner subscription record
            start_date = datetime.utcnow()
            end_date = None
            if pricing_plan and hasattr(pricing_plan, 'duration_months') and pricing_plan.duration_months > 0:
                end_date = start_date + timedelta(days=pricing_plan.duration_months * 30)
            elif subscription_type == "yearly":
                end_date = start_date + timedelta(days=365)
            elif subscription_type == "monthly":
                end_date = start_date + timedelta(days=30)
            
            partner_subscription = PartnerSubscription(
                partner_id=partner_id,
                pricing_plan_id=pricing_plan_id,
                status="pending" if requires_approval else "active",
                admin_approved=not requires_approval,
                max_tags=pricing_plan.max_tags if pricing_plan else 0,
                payment_method=payment_method,
                payment_id=payment_intent_id,
                amount=amount,
                start_date=start_date,
                end_date=end_date,
                auto_renew=True
            )
            
            db.session.add(partner_subscription)
            db.session.flush()
            
            # Link payment to partner subscription
            payment.partner_subscription_id = partner_subscription.id
            logger.info(f"Linked payment {payment.id} to partner subscription {partner_subscription.id}")
            
            logger.info(f"Created partner subscription with ID: {partner_subscription.id}")
            logger.info(f"Status: {partner_subscription.status}, Admin approved: {partner_subscription.admin_approved}")
            
            # Send email notifications
            try:
                if requires_approval:
                    logger.info("Sending approval notification emails")
                    from email_utils import send_partner_subscription_confirmation_email, send_partner_admin_approval_notification
                    send_partner_subscription_confirmation_email(user, partner_subscription)
                    send_partner_admin_approval_notification(partner_subscription)
                else:
                    logger.info("Sending confirmation email for auto-approved subscription")
                    from email_utils import send_partner_subscription_confirmation_email
                    send_partner_subscription_confirmation_email(user, partner_subscription)
            except Exception as email_error:
                logger.error(f"Error sending partner subscription emails: {email_error}")
                # Don't fail the payment for email issues

            # Add partner role if not already present
            partner_role = Role.query.filter_by(name="partner").first()
            if partner_role and partner_role not in user.roles:
                user.roles.append(partner_role)
                logger.info(f"Added partner role to user {user.username}")

        db.session.commit()
        
        # Send appropriate emails after successful commit (for tag subscriptions only)
        try:
            if payment_type == "tag" and 'subscription' in locals():
                from email_utils import send_subscription_confirmation_email
                send_subscription_confirmation_email(user, subscription)
                logger.info(f"Sent tag subscription confirmation email to {user.email}")
                
        except Exception as email_error:
            logger.error(f"Error sending emails: {email_error}")
            # Don't fail the payment processing if email fails
        
        logger.info(
            f"Payment processed successfully for user {user_id}, type {payment_type}, amount ${amount}, transaction_id: {payment.transaction_id}"
        )
        return True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing payment: {str(e)}")
        logger.error(f"Exception details: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise  # Re-raise the exception so it's not ignored
