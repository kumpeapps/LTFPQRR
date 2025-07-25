"""
Payment processing routes
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from utils import get_enabled_payment_gateways, decrypt_value
from extensions import logger
from models.models import PaymentGateway
import stripe

payment = Blueprint('payment', __name__, url_prefix='/payment')


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
    
    # Handle tag claim payments
    if "claiming_tag_id" in session:
        tag_id = session.pop("claiming_tag_id")
        subscription_type = session.pop("subscription_type", "monthly")

        # In a real implementation, you would verify the payment here
        # For now, we'll just create the subscription
        from sqlalchemy import func
        tag_obj = Tag.query.filter(func.upper(Tag.tag_id) == func.upper(tag_id)).first()
        if tag_obj:
            tag_obj.owner_id = current_user.id
            tag_obj.status = "claimed"

            # Create subscription
            subscription = Subscription(
                user_id=current_user.id,
                tag_id=tag_obj.id,
                subscription_type=subscription_type,
                status="active",
                payment_method="stripe",  # default
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
            )
            db.session.add(subscription)
            db.session.commit()

            flash(f"Payment successful! Tag {tag_id} has been claimed.", "success")
            return redirect(url_for("dashboard.customer_dashboard"))
    
    # Handle partner subscription payments
    elif "partner_subscription_type" in session:
        subscription_type = session.pop("partner_subscription_type")
        partner_id = session.pop("partner_id", None)
        
        # Create partner subscription
        try:
            # Create a partner subscription record
            partner_subscription = PartnerSubscription(
                partner_id=partner_id,
                status="pending" if not partner_id else "active",
                admin_approved=False if not partner_id else True,
                max_tags=0,
                payment_method="stripe",
                amount=29.99 if subscription_type == "monthly" else 299.99,
                start_date=datetime.utcnow(),
                end_date=(
                    datetime.utcnow() + timedelta(days=365)
                    if subscription_type == "yearly"
                    else datetime.utcnow() + timedelta(days=30)
                ),
                auto_renew=True
            )
            
            db.session.add(partner_subscription)
            db.session.commit()
            
            if partner_id:
                flash("Partner subscription activated successfully!", "success")
                return redirect(url_for("partner.dashboard", partner_id=partner_id))
            else:
                flash("Partner subscription request submitted for approval.", "info")
                return redirect(url_for("partner.management_dashboard"))
            
        except Exception as e:
            logger.error(f"Error creating partner subscription: {e}")
            flash("Payment processed but there was an error setting up your subscription. Please contact support.", "error")
            return redirect(url_for("partner.management_dashboard"))

    flash("Payment completed successfully!", "success")
    return redirect(url_for("dashboard.dashboard"))


@payment.route("/partner", methods=["POST"])
@payment.route("/partner/<int:partner_id>", methods=["POST"])
@login_required
def partner_subscription_payment(partner_id=None):
    """Process partner subscription payment."""
    # Users can request partner subscriptions for specific partners
    subscription_type = request.form.get("subscription_type")
    pricing_plan_id = request.form.get("pricing_plan_id")
    
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
        partner_id=partner_id
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


@payment.route("/stripe/create-intent", methods=["POST"])
@login_required
def create_stripe_payment_intent():
    """Create a Stripe payment intent for processing payments"""
    try:
        # Log request details for debugging
        logger.info(f"Stripe payment intent request - Content-Type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Try to get JSON data first, fall back to form data
        data = request.get_json()
        if not data:
            logger.info("No JSON data found, trying form data")
            # Fallback to form data
            data = {
                'amount': request.form.get('amount', 0),
                'currency': request.form.get('currency', 'usd'),
                'payment_type': request.form.get('payment_type', 'tag')
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
        stripe_gateway = PaymentGateway.query.filter_by(name="stripe", enabled=True).first()
        if not stripe_gateway or not stripe_gateway.secret_key:
            return jsonify({"error": "Stripe payment gateway not configured"}), 400
        
        # Decrypt keys
        secret_key = decrypt_value(stripe_gateway.secret_key)
        publishable_key = decrypt_value(stripe_gateway.publishable_key)
        
        # Configure Stripe API
        stripe.api_key = secret_key
        
        # Log for debugging (without exposing the full key)
        logger.info(f"Using Stripe key: {secret_key[:7]}... (environment: {stripe_gateway.environment})")
        
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
            amount=amount_cents,
            currency=currency,
            metadata=metadata
        )
        
        return jsonify({
            "client_secret": intent.client_secret,
            "publishable_key": publishable_key
        })
        
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
        stripe_gateway = PaymentGateway.query.filter_by(name="stripe", enabled=True).first()
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
            logger.info(f"Successfully processed payment {payment_intent_id} for user {user_id}")
            
            # Clear session data
            if payment_type == "tag":
                session.pop("claiming_tag_id", None)
                session.pop("subscription_type", None)
            elif payment_type == "partner":
                session.pop("partner_subscription_type", None)
                session.pop("partner_id", None)
            
            return jsonify({
                "status": "success",
                "message": "Payment processed successfully",
                "redirect_url": url_for("payment.success")
            })
        else:
            return jsonify({"error": "Failed to process payment"}), 500
            
    except Exception as e:
        logger.error(f"Error confirming Stripe payment: {e}")
        return jsonify({"error": "Payment confirmation failed"}), 500
