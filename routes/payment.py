"""
Payment processing routes
"""

from datetime import datetime, timedelta
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_login import login_required, current_user
from utils import get_enabled_payment_gateways, decrypt_value
from extensions import logger
from models.models import PaymentGateway
import stripe

payment = Blueprint("payment", __name__, url_prefix="/payment")


@payment.route("/tag")
@login_required
def tag_payment():
    """Tag payment page."""
    if "claiming_tag_id" not in session:
        flash("No tag selected for claiming.", "error")
        return redirect(url_for("tag.claim_tag"))

    tag_id = session["claiming_tag_id"]
    subscription_type = session["subscription_type"]

    # Define pricing
    pricing = {"monthly": 9.99, "yearly": 99.99, "lifetime": 199.99}

    amount = pricing.get(subscription_type, 9.99)

    # Get enabled payment gateways
    enabled_gateways, gateway_config = get_enabled_payment_gateways()

    # Check if any payment gateways are enabled
    if not enabled_gateways:
        flash(
            "No payment gateways are currently available. Please contact support.",
            "error",
        )
        return redirect(url_for("dashboard.customer_dashboard"))

    return render_template(
        "tag/payment.html",
        tag_id=tag_id,
        subscription_type=subscription_type,
        amount=amount,
        enabled_gateways=enabled_gateways,
        gateway_config=gateway_config,
    )


@payment.route("/success")
@login_required
def success():
    """Handle successful payment."""
    from models.models import Tag, Subscription, PartnerSubscription
    from extensions import db
    import logging

    logger = logging.getLogger(__name__)

    logger.info("=== Payment success handler called ===")
    logger.info(f"Session contents: {dict(session)}")
    logger.info(f"Current user: {current_user.username}")

    # Handle tag claim payments
    if "claiming_tag_id" in session:
        logger.info("Processing tag claim payment")
        tag_id = session.get("claiming_tag_id")
        subscription_type = session.get("subscription_type", "monthly")
        payment_method = session.get("payment_method", "unknown")
        
        # For Stripe payments, only process via webhook for security
        # The direct success page should only handle non-Stripe payments
        if payment_method == "stripe":
            logger.info("Stripe payment detected - deferring to webhook processing")
            # Don't process here, let webhook handle it
            # Just show success message and clean up session
            session.pop("claiming_tag_id", None)
            session.pop("subscription_type", None)
            session.pop("payment_method", None)
            flash("Payment successful! Your subscription will be activated shortly.", "success")
            return redirect(url_for("dashboard.customer_dashboard"))
        
        # Process non-Stripe payments immediately (PayPal, manual, etc.)
        logger.info(f"Processing non-Stripe payment method: {payment_method}")
        
        # Pop the session data for non-Stripe payments
        tag_id = session.pop("claiming_tag_id")
        subscription_type = session.pop("subscription_type", "monthly")
        session.pop("payment_method", None)

        # In a real implementation, you would verify the payment here
        # For now, we'll just create the subscription
        from sqlalchemy import func

        tag_obj = Tag.query.filter(func.upper(Tag.tag_id) == func.upper(tag_id)).first()
        if tag_obj:
            # More robust duplicate prevention using payment_id and tag_id
            existing_subscription = Subscription.query.filter(
                Subscription.user_id == current_user.id,
                Subscription.tag_id == tag_obj.id,
                Subscription.status.in_(['active', 'pending'])
            ).first()
            
            if existing_subscription:
                logger.warning(f"Subscription already exists for user {current_user.id} and tag {tag_obj.id}: {existing_subscription.id}")
                flash(f"You already have an active subscription for tag {tag_id}.", "info")
                return redirect(url_for("dashboard.customer_dashboard"))
            
            # Check if this payment_intent was already processed (prevent webhook duplicates)
            payment_intent_id = session.get('payment_intent_id')
            if payment_intent_id:
                existing_with_payment = Subscription.query.filter_by(
                    payment_id=payment_intent_id
                ).first()
                if existing_with_payment:
                    logger.warning(f"Payment {payment_intent_id} already processed for subscription {existing_with_payment.id}")
                    flash(f"Payment for tag {tag_id} has already been processed.", "info")
                    return redirect(url_for("dashboard.customer_dashboard"))
            
            # Use database transaction to prevent race conditions
            try:
                # Only update tag ownership if it's being claimed for the first time
                if not tag_obj.owner_id:
                    tag_obj.owner_id = current_user.id
                    tag_obj.status = "claimed"

                # Create subscription with unique payment identifier
                subscription = Subscription(
                    user_id=current_user.id,
                    tag_id=tag_obj.id,
                    subscription_type="tag",
                    status="active",
                    payment_method="stripe",  # default
                    payment_id=payment_intent_id,  # Use payment_intent_id for uniqueness
                    amount=(
                        9.99
                        if subscription_type == "monthly"
                        else (99.99 if subscription_type == "yearly" else 199.99)
                    ),
                    start_date=datetime.utcnow(),
                    end_date=(
                        datetime.utcnow() + timedelta(days=365)
                        if subscription_type == "yearly"
                        else (
                            datetime.utcnow() + timedelta(days=30)
                            if subscription_type == "monthly"
                            else None
                        )
                    ),
                    auto_renew=True if subscription_type in ['monthly', 'yearly'] else False,
                )
                db.session.add(subscription)
                db.session.commit()
                
                # Clear session data to prevent reprocessing
                session.pop('payment_intent_id', None)
                
                logger.info(f"Successfully created subscription {subscription.id} for user {current_user.id} and tag {tag_obj.id}")
                flash(f"Payment successful! Tag {tag_id} subscription has been activated.", "success")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating subscription: {str(e)}")
                flash("There was an error processing your payment. Please contact support.", "error")
                
            return redirect(url_for("dashboard.customer_dashboard"))

    # Handle partner subscription payments
    elif "partner_subscription_type" in session:
        logger.info("Processing partner subscription payment")
        subscription_type = session.pop("partner_subscription_type")
        partner_id = session.pop("partner_id", None)
        pricing_plan_id = session.pop("pricing_plan_id", None)

        # Get pricing plan to check if approval is required
        from models.models import PricingPlan

        pricing_plan = None
        if pricing_plan_id:
            pricing_plan = PricingPlan.query.get(pricing_plan_id)

        # Determine if approval is required
        requires_approval = pricing_plan.requires_approval if pricing_plan else False

        # Create partner subscription
        try:
            logger.info(
                f"Creating partner subscription for partner_id: {partner_id}, pricing_plan_id: {pricing_plan_id}"
            )

            # Calculate end date based on pricing plan
            start_date = datetime.utcnow()
            end_date = None
            if (
                pricing_plan
                and hasattr(pricing_plan, "duration_months")
                and pricing_plan.duration_months > 0
            ):
                end_date = start_date + timedelta(
                    days=pricing_plan.duration_months * 30
                )
            elif subscription_type == "yearly":
                end_date = start_date + timedelta(days=365)
            elif subscription_type == "monthly":
                end_date = start_date + timedelta(days=30)

            logger.info(f"Calculated dates - start: {start_date}, end: {end_date}")

            # Create a partner subscription record
            partner_subscription = PartnerSubscription(
                partner_id=partner_id,
                pricing_plan_id=pricing_plan_id,
                status="pending" if requires_approval else "active",
                admin_approved=not requires_approval,
                max_tags=pricing_plan.max_tags if pricing_plan else 0,
                payment_method="stripe",
                amount=(
                    pricing_plan.price
                    if pricing_plan
                    else (29.99 if subscription_type == "monthly" else 299.99)
                ),
                start_date=start_date,
                end_date=end_date,
                auto_renew=True,
            )

            logger.info(
                "Created PartnerSubscription object, attempting to save to database"
            )
            db.session.add(partner_subscription)
            db.session.commit()
            logger.info("Successfully saved partner subscription to database")

            # Send email notifications
            try:
                if requires_approval:
                    flash(
                        "Partner subscription request submitted for approval. You will receive an email when it's approved.",
                        "info",
                    )

                    # Try to send emails using enhanced email system
                    try:
                        from email_utils import (
                            send_partner_subscription_confirmation_email_enhanced,
                        )
                        from services.enhanced_email_service import EmailTemplateManager

                        # Send confirmation to partner
                        send_partner_subscription_confirmation_email_enhanced(
                            current_user, partner_subscription
                        )

                        # Send admin notification using enhanced template system
                        # The enhanced system will automatically load the model instances
                        admin_inputs = {
                            "subscription_id": partner_subscription.id,
                            "user_id": current_user.id,
                            "partner_id": (
                                partner_subscription.partner.id
                                if partner_subscription.partner
                                else None
                            ),
                        }

                        # Get admin users and send notifications
                        from models.models import User, Role

                        admin_role = Role.query.filter_by(name="admin").first()
                        if admin_role and admin_role.users:
                            for admin_user in admin_role.users:
                                # Add admin email to inputs for targeting
                                admin_inputs["admin_email"] = admin_user.email
                                admin_inputs["admin_user_id"] = admin_user.id

                                EmailTemplateManager.send_from_template(
                                    template_name="admin_partner_approval_notification",
                                    inputs=admin_inputs,
                                    email_type="admin_approval_notification",
                                    priority="high",
                                )

                    except Exception as email_error:
                        logger.error(
                            f"Error sending approval emails (non-critical): {email_error}"
                        )
                else:
                    flash("Partner subscription activated successfully!", "success")

                    # Try to send confirmation email using enhanced system
                    try:
                        from email_utils import (
                            send_partner_subscription_confirmation_email_enhanced,
                        )

                        send_partner_subscription_confirmation_email_enhanced(
                            current_user, partner_subscription
                        )
                    except Exception as email_error:
                        logger.error(
                            f"Error sending confirmation email (non-critical): {email_error}"
                        )
            except Exception as email_error:
                logger.error(f"Error in email notification flow: {email_error}")
                # Always show success message regardless of email issues
                if requires_approval:
                    flash(
                        "Partner subscription request submitted for approval. You will receive an email when it's approved.",
                        "info",
                    )
                else:
                    flash("Partner subscription activated successfully!", "success")

            if partner_id:
                return redirect(url_for("partner_dashboard"))
            else:
                return redirect(url_for("partner_dashboard"))

        except Exception as e:
            logger.error(f"Error creating partner subscription: {e}")
            flash(
                "Payment processed but there was an error setting up your subscription. Please contact support.",
                "error",
            )
            return redirect(url_for("partner.management_dashboard"))

    logger.info("Payment completed but no specific handler matched")
    flash("Payment completed successfully!", "success")
    return redirect(url_for("dashboard.dashboard"))


@payment.route("/partner", methods=["POST"])
@payment.route("/partner/<int:partner_id>", methods=["POST"])
@login_required
def partner_subscription_payment(partner_id=None):
    """Process partner subscription payment."""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"=== Partner subscription payment initiated ===")
    logger.info(f"Partner ID: {partner_id}")
    logger.info(f"Form data: {dict(request.form)}")

    # Users can request partner subscriptions for specific partners
    subscription_type = request.form.get("subscription_type")
    pricing_plan_id = request.form.get("pricing_plan_id")

    logger.info(f"Subscription type: {subscription_type}")
    logger.info(f"Pricing plan ID: {pricing_plan_id}")

    # Get pricing plan from database
    from models.models import PricingPlan

    if pricing_plan_id:
        pricing_plan = PricingPlan.query.filter_by(
            id=pricing_plan_id,
            plan_type="partner",
            is_active=True,
        ).first()
    else:
        # Fallback to billing period lookup for backwards compatibility
        if subscription_type not in ["monthly", "yearly"]:
            flash("Invalid subscription type.", "error")
            return redirect(url_for("partner.subscription", partner_id=partner_id))

        pricing_plan = PricingPlan.query.filter_by(
            plan_type="partner",
            billing_period=subscription_type,
            is_active=True,
        ).first()

    if not pricing_plan:
        flash("Invalid subscription plan selected.", "error")
        return redirect(url_for("partner.subscription", partner_id=partner_id))

    # Update subscription_type from pricing plan if not provided
    if not subscription_type:
        subscription_type = pricing_plan.billing_period

    # If partner_id specified, validate access
    if partner_id:
        owned_partners = current_user.get_owned_partners()
        accessible_partners = current_user.get_accessible_partners()
        all_partners = owned_partners + accessible_partners
        partner_obj = next((p for p in all_partners if p.id == partner_id), None)
        if not partner_obj:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner.management_dashboard"))

        # Store partner info in session
        session["partner_id"] = partner_id

    # Store subscription info in session for payment processing
    session["partner_subscription_type"] = subscription_type
    session["pricing_plan_id"] = pricing_plan.id

    logger.info(f"Set session data - partner_subscription_type: {subscription_type}")
    logger.info(f"Set session data - pricing_plan_id: {pricing_plan.id}")
    logger.info(f"Session after setting: {dict(session)}")

    amount = float(pricing_plan.price)

    # Get enabled payment gateways
    enabled_gateways, gateway_config = get_enabled_payment_gateways()

    # Check if any payment gateways are enabled
    if not enabled_gateways:
        flash(
            "No payment gateways are currently available. Please contact support.",
            "error",
        )
        return redirect(url_for("partner.subscription", partner_id=partner_id))

    return render_template(
        "partner/payment.html",
        subscription_type=subscription_type,
        amount=amount,
        pricing_plan=pricing_plan,
        enabled_gateways=enabled_gateways,
        gateway_config=gateway_config,
        partner_id=partner_id,
    )


@payment.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        # Get Stripe configuration
        stripe_gateway = PaymentGateway.query.filter_by(
            name="stripe", enabled=True
        ).first()
        if not stripe_gateway or not stripe_gateway.webhook_secret:
            return jsonify({"error": "Webhook not configured"}), 400

        endpoint_secret = decrypt_value(stripe_gateway.webhook_secret)

        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

        # Handle the event
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]

            # Process the successful payment
            user_id = payment_intent["metadata"].get("user_id")
            payment_type = payment_intent["metadata"].get("payment_type")
            claiming_tag_id = payment_intent["metadata"].get("claiming_tag_id")
            subscription_type = payment_intent["metadata"].get("subscription_type")

            if user_id and payment_type:
                from utils import process_successful_payment

                process_successful_payment(
                    user_id=int(user_id),
                    payment_type=payment_type,
                    payment_method="stripe",
                    amount=payment_intent["amount"] / 100,  # Convert from cents
                    payment_intent_id=payment_intent["id"],
                    claiming_tag_id=claiming_tag_id,
                    subscription_type=subscription_type,
                )

        elif event["type"] == "charge.dispute.created":
            # Handle chargebacks/disputes
            charge = event["data"]["object"]
            payment_intent_id = charge.get("payment_intent")
            
            if payment_intent_id:
                from utils import process_payment_refund
                process_payment_refund(
                    payment_intent_id=payment_intent_id,
                    refund_reason="chargeback",
                    refund_amount=charge["amount"] / 100,
                    webhook_event_type="charge.dispute.created"
                )

        elif event["type"] in ["invoice.payment_failed", "payment_intent.payment_failed"]:
            # Handle failed payments for subscriptions
            payment_object = event["data"]["object"]
            payment_intent_id = payment_object.get("payment_intent") or payment_object.get("id")
            
            if payment_intent_id:
                from utils import process_payment_failure
                process_payment_failure(
                    payment_intent_id=payment_intent_id,
                    failure_reason=event["type"],
                    webhook_event_type=event["type"]
                )

        elif event["type"] == "charge.refunded":
            # Handle refunds
            charge = event["data"]["object"]
            payment_intent_id = charge.get("payment_intent")
            refund_amount = 0
            
            # Calculate total refunded amount
            for refund in charge.get("refunds", {}).get("data", []):
                refund_amount += refund["amount"] / 100
            
            if payment_intent_id:
                from utils import process_payment_refund
                process_payment_refund(
                    payment_intent_id=payment_intent_id,
                    refund_reason="merchant_refund",
                    refund_amount=refund_amount,
                    webhook_event_type="charge.refunded"
                )

        elif event["type"] == "refund.created":
            # Handle individual refund creation
            refund = event["data"]["object"]
            charge_id = refund.get("charge")
            
            # Get the charge to find the payment intent
            if charge_id:
                try:
                    import stripe
                    charge = stripe.Charge.retrieve(charge_id)
                    payment_intent_id = charge.get("payment_intent")
                    
                    if payment_intent_id:
                        from utils import process_payment_refund
                        process_payment_refund(
                            payment_intent_id=payment_intent_id,
                            refund_reason=refund.get("reason", "requested_by_customer"),
                            refund_amount=refund["amount"] / 100,
                            webhook_event_type="refund.created"
                        )
                except Exception as e:
                    logger.error(f"Error processing refund.created event: {str(e)}")

        elif event["type"] == "refund.updated":
            # Handle refund status updates (succeeded, failed, etc.)
            refund = event["data"]["object"]
            
            if refund["status"] == "succeeded":
                charge_id = refund.get("charge")
                
                if charge_id:
                    try:
                        import stripe
                        charge = stripe.Charge.retrieve(charge_id)
                        payment_intent_id = charge.get("payment_intent")
                        
                        if payment_intent_id:
                            from utils import process_payment_refund
                            process_payment_refund(
                                payment_intent_id=payment_intent_id,
                                refund_reason=refund.get("reason", "requested_by_customer"),
                                refund_amount=refund["amount"] / 100,
                                webhook_event_type="refund.updated"
                            )
                    except Exception as e:
                        logger.error(f"Error processing refund.updated event: {str(e)}")

        elif event["type"] == "customer.subscription.deleted":
            # Handle subscription cancellation in Stripe dashboard
            subscription_obj = event["data"]["object"]
            payment_intent_id = subscription_obj.get("latest_invoice", {}).get("payment_intent")
            
            if payment_intent_id:
                from utils import process_subscription_cancellation
                process_subscription_cancellation(
                    payment_intent_id=payment_intent_id,
                    webhook_event_type="customer.subscription.deleted"
                )

        elif event["type"] == "payment_intent.canceled":
            # Handle payment intent cancellation
            payment_intent = event["data"]["object"]
            payment_intent_id = payment_intent.get("id")
            
            if payment_intent_id:
                from utils import process_payment_cancellation
                process_payment_cancellation(
                    payment_intent_id=payment_intent_id,
                    webhook_event_type="payment_intent.canceled"
                )

        elif event["type"] == "invoice.payment_action_required":
            # Handle payment authentication required
            invoice = event["data"]["object"]
            payment_intent_id = invoice.get("payment_intent")
            
            if payment_intent_id:
                logger.info(f"Payment action required for intent {payment_intent_id}")
                # For now, just log. In the future, we could email the customer

        elif event["type"] == "payment_method.attached":
            # Handle payment method attachment for future use
            payment_method = event["data"]["object"]
            customer_id = payment_method.get("customer")
            logger.info(f"Payment method attached to customer {customer_id}")

        elif event["type"] == "customer.subscription.updated":
            # Handle subscription updates (like plan changes)
            subscription_obj = event["data"]["object"]
            logger.info(f"Subscription updated: {subscription_obj.get('id')}")
            # Could implement subscription modification logic here in the future

        else:
            logger.info(f"Unhandled Stripe webhook event type: {event['type']}")

        return jsonify({"status": "success"})

    except ValueError as e:
        logger.error(f"Invalid Stripe webhook payload: {str(e)}")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe webhook signature: {str(e)}")
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return jsonify({"error": "Webhook processing failed"}), 500


@payment.route("/paypal/webhook", methods=["POST"])
def paypal_webhook():
    """Handle PayPal webhook events"""
    try:
        payload = request.get_json()
        
        # Get PayPal configuration
        paypal_gateway = PaymentGateway.query.filter_by(
            name="paypal", enabled=True
        ).first()
        
        if not paypal_gateway:
            return jsonify({"error": "PayPal webhook not configured"}), 400
        
        # TODO: Verify PayPal webhook signature for security
        # For now, we'll process the event but this should be implemented
        
        event_type = payload.get("event_type")
        resource = payload.get("resource", {})
        
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Handle successful PayPal payment
            # Extract metadata from PayPal custom fields or description
            custom_data = resource.get("custom_id", "")
            payment_id = resource.get("id")
            amount = float(resource.get("amount", {}).get("value", 0))
            
            # Process successful payment if we have the necessary metadata
            # This would need to be enhanced based on how you store metadata in PayPal
            logger.info(f"PayPal payment completed: {payment_id}, amount: ${amount}")
            
        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            # Handle PayPal refunds
            payment_id = resource.get("id")
            refund_amount = float(resource.get("amount", {}).get("value", 0))
            
            if payment_id:
                from utils import process_payment_refund
                process_payment_refund(
                    payment_intent_id=payment_id,
                    refund_reason="merchant_refund",
                    refund_amount=refund_amount,
                    webhook_event_type="PAYMENT.CAPTURE.REFUNDED"
                )
                
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            # Handle PayPal payment failures
            payment_id = resource.get("id")
            
            if payment_id:
                from utils import process_payment_failure
                process_payment_failure(
                    payment_intent_id=payment_id,
                    failure_reason="payment_denied",
                    webhook_event_type="PAYMENT.CAPTURE.DENIED"
                )
        
        else:
            logger.info(f"Unhandled PayPal webhook event type: {event_type}")
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        logger.error(f"PayPal webhook error: {str(e)}")
        return jsonify({"error": "Webhook processing failed"}), 500


@payment.route("/stripe/create-intent", methods=["POST"])
@login_required
def create_stripe_payment_intent():
    """Create a Stripe payment intent for processing payments"""
    try:
        # Log request details for debugging
        logger.info(
            f"Stripe payment intent request - Content-Type: {request.content_type}"
        )
        logger.info(f"Request headers: {dict(request.headers)}")

        # Try to get JSON data first, fall back to form data
        data = request.get_json()
        if not data:
            logger.info("No JSON data found, trying form data")
            # Fallback to form data
            data = {
                "amount": request.form.get("amount", 0),
                "currency": request.form.get("currency", "usd"),
                "payment_type": request.form.get("payment_type", "tag"),
            }
            logger.info(f"Form data extracted: {data}")
        else:
            logger.info(f"JSON data received: {data}")

        amount = data.get("amount", 0)
        currency = data.get("currency", "usd")
        payment_type = data.get("payment_type", "tag")

        # Convert amount to cents for Stripe (multiply by 100)
        amount_cents = int(float(amount) * 100)

        # Get Stripe configuration
        stripe_gateway = PaymentGateway.query.filter_by(
            name="stripe", enabled=True
        ).first()
        if not stripe_gateway or not stripe_gateway.secret_key:
            return jsonify({"error": "Stripe payment gateway not configured"}), 400

        # Decrypt keys
        secret_key = decrypt_value(stripe_gateway.secret_key)
        publishable_key = decrypt_value(stripe_gateway.publishable_key)

        # Configure Stripe API
        stripe.api_key = secret_key

        # Log for debugging (without exposing the full key)
        logger.info(
            f"Using Stripe key: {secret_key[:7]}... (environment: {stripe_gateway.environment})"
        )

        # Get metadata from session
        metadata = {
            "user_id": current_user.id,
            "payment_type": payment_type,
        }

        # Add specific metadata based on payment type
        if payment_type == "tag":
            metadata["claiming_tag_id"] = session.get("claiming_tag_id", "")
            metadata["subscription_type"] = session.get("subscription_type", "")
        elif payment_type == "partner":
            metadata["subscription_type"] = session.get("partner_subscription_type", "")
            metadata["partner_id"] = session.get("partner_id", "")

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents, currency=currency, metadata=metadata
        )
        
        # Store payment method and intent ID in session for duplicate prevention
        session["payment_method"] = "stripe"
        session["payment_intent_id"] = intent.id

        return jsonify(
            {"client_secret": intent.client_secret, "publishable_key": publishable_key}
        )

    except Exception as e:
        logger.error(f"Error creating Stripe payment intent: {e}")
        return jsonify({"error": "Failed to create payment intent"}), 500


@payment.route("/stripe/confirm", methods=["POST"])
@login_required
def confirm_stripe_payment():
    """Confirm and process a successful Stripe payment (for local testing without webhooks)"""
    try:
        data = request.get_json()
        payment_intent_id = data.get("payment_intent_id")

        if not payment_intent_id:
            return jsonify({"error": "Payment intent ID required"}), 400

        # Configure Stripe
        stripe_gateway = PaymentGateway.query.filter_by(
            name="stripe", enabled=True
        ).first()
        if not stripe_gateway:
            return jsonify({"error": "Stripe not configured"}), 400

        stripe.api_key = decrypt_value(stripe_gateway.secret_key)

        # Retrieve payment intent from Stripe to verify it succeeded
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status != "succeeded":
            return jsonify({"error": "Payment not successful"}), 400

        # Extract metadata
        metadata = payment_intent.metadata
        user_id = int(metadata.get("user_id"))
        payment_type = metadata.get("payment_type")
        claiming_tag_id = metadata.get("claiming_tag_id")
        subscription_type = metadata.get("subscription_type")

        # Verify user matches current user
        if user_id != current_user.id:
            return jsonify({"error": "Payment user mismatch"}), 400

        # Process the payment using our existing function
        from utils import process_successful_payment

        success = process_successful_payment(
            user_id=user_id,
            payment_type=payment_type,
            payment_method="stripe",
            amount=payment_intent.amount / 100,  # Convert from cents
            payment_intent_id=payment_intent_id,
            claiming_tag_id=claiming_tag_id,
            subscription_type=subscription_type,
        )

        if success:
            logger.info(
                f"Successfully processed payment {payment_intent_id} for user {user_id}"
            )

            # Clear session data
            if payment_type == "tag":
                session.pop("claiming_tag_id", None)
                session.pop("subscription_type", None)
            elif payment_type == "partner":
                session.pop("partner_subscription_type", None)
                session.pop("partner_id", None)

            return jsonify(
                {
                    "status": "success",
                    "message": "Payment processed successfully",
                    "redirect_url": url_for("payment.success"),
                }
            )
        else:
            return jsonify({"error": "Failed to process payment"}), 500

    except Exception as e:
        logger.error(f"Error confirming Stripe payment: {e}")
        return jsonify({"error": "Payment confirmation failed"}), 500
