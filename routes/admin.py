"""
Admin routes
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils import admin_required, super_admin_required, update_payment_gateway_settings, configure_payment_gateways
from forms import PaymentGatewayForm, PricingPlanForm

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard."""
    from models.models import User, Tag, Subscription, Pet
    
    # Get statistics
    stats = {
        "total_users": User.query.count(),
        "total_tags": Tag.query.count(),
        "active_subscriptions": Subscription.query.filter_by(status="active").count(),
        "total_pets": Pet.query.count(),
    }

    return render_template("admin/dashboard.html", stats=stats)


@admin.route("/users")
@admin_required
def users():
    """Admin user management."""
    from models.models import User
    from extensions import db
    
    search = request.args.get("search", "")
    query = User.query

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(search_filter),
                User.email.ilike(search_filter),
                User.first_name.ilike(search_filter),
                User.last_name.ilike(search_filter),
            )
        )

    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, search=search)


@admin.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    """Edit a user."""
    from models.models import User, Role
    from extensions import db
    from forms import ProfileForm
    
    user = User.query.get_or_404(user_id)
    form = ProfileForm(obj=user)

    # Get all available roles
    all_roles = Role.query.all()

    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.address = form.address.data
        user.email = form.email.data
        user.updated_at = datetime.utcnow()
        
        # Handle role updates (super-admin only)
        if current_user.has_role('super-admin'):
            # Get selected role IDs from form
            selected_role_ids = request.form.getlist('roles')
            
            # Convert to integers
            try:
                selected_role_ids = [int(role_id) for role_id in selected_role_ids]
            except ValueError:
                flash("Invalid role selection.", "error")
                return render_template(
                    "admin/edit_user.html", form=form, user=user, all_roles=all_roles
                )
            
            # Get role objects
            selected_roles = Role.query.filter(Role.id.in_(selected_role_ids)).all()
            
            # Ensure at least one role is assigned (default to 'user' role)
            if not selected_roles:
                user_role = Role.query.filter_by(name='user').first()
                if user_role:
                    selected_roles = [user_role]
            
            # Update user roles
            user.roles = selected_roles
            
            flash(f"User {user.username} updated successfully with roles: {', '.join([r.name for r in selected_roles])}", "success")
        else:
            flash(f"User {user.username} updated successfully.", "success")
        
        db.session.commit()
        return redirect(url_for("admin.users"))

    return render_template(
        "admin/edit_user.html", form=form, user=user, all_roles=all_roles
    )


@admin.route("/users/delete/<int:user_id>", methods=["POST"])
@super_admin_required
def delete_user(user_id):
    """Delete a user."""
    from models.models import User
    from extensions import db
    
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.users"))

    # Check if user has any dependencies
    if user.pets.count() > 0 or user.owned_tags.count() > 0:
        flash("Cannot delete user with existing pets or tags.", "error")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()

    flash(f"User {user.username} deleted successfully.", "success")
    return redirect(url_for("admin.users"))


@admin.route("/subscriptions")
@admin_required
def subscriptions():
    """Admin subscription management."""
    from models.models import Subscription, User
    from extensions import db
    
    search = request.args.get("search", "")
    query = Subscription.query

    if search:
        search_filter = f"%{search}%"
        query = query.join(User).filter(
            db.or_(
                User.username.ilike(search_filter),
                User.email.ilike(search_filter),
                User.first_name.ilike(search_filter),
                User.last_name.ilike(search_filter),
                Subscription.subscription_type.ilike(search_filter),
                Subscription.status.ilike(search_filter),
                Subscription.payment_method.ilike(search_filter),
            )
        )

    subscriptions = query.order_by(Subscription.created_at.desc()).all()
    return render_template(
        "admin/subscriptions.html", subscriptions=subscriptions, search=search
    )


@admin.route("/partner-subscriptions")
@admin_required
def partner_subscriptions():
    """Manage partner subscription requests."""
    from models.models import Subscription
    
    pending_subs = (
        Subscription.query.filter_by(subscription_type="partner", admin_approved=False)
        .order_by(Subscription.created_at.desc())
        .all()
    )

    approved_subs = (
        Subscription.query.filter_by(subscription_type="partner", admin_approved=True)
        .order_by(Subscription.created_at.desc())
        .all()
    )

    return render_template(
        "admin/partner_subscriptions.html",
        pending_subscriptions=pending_subs,
        approved_subscriptions=approved_subs,
    )


@admin.route("/partner-subscriptions/approve/<int:subscription_id>", methods=["POST"])
@admin_required
def approve_partner_subscription(subscription_id):
    """Approve a partner subscription."""
    from models.models import Subscription
    from extensions import db
    
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.subscription_type != "partner":
        flash("Invalid subscription type.", "error")
        return redirect(url_for("admin.partner_subscriptions"))

    if subscription.admin_approved:
        flash("Subscription is already approved.", "warning")
        return redirect(url_for("admin.partner_subscriptions"))

    try:
        subscription.approve(current_user)
        db.session.commit()
        
        # Send approval email to customer
        try:
            from email_utils import send_subscription_approved_email
            from extensions import logger
            send_subscription_approved_email(subscription.user, subscription)
        except Exception as email_error:
            from extensions import logger
            logger.error(f"Error sending approval email: {email_error}")
            # Don't fail the approval if email fails
        
        flash(
            f"Partner subscription for {subscription.partner.company_name} has been approved.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error approving subscription: {str(e)}", "error")

    return redirect(url_for("admin.partner_subscriptions"))


@admin.route("/partner-subscriptions/reject/<int:subscription_id>", methods=["POST"])
@admin_required
def reject_partner_subscription(subscription_id):
    """Reject a partner subscription."""
    from models.models import Subscription
    from extensions import db
    
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.subscription_type != "partner":
        flash("Invalid subscription type.", "error")
        return redirect(url_for("admin.partner_subscriptions"))

    try:
        subscription.status = "cancelled"
        db.session.commit()
        
        # Send rejection email to customer
        try:
            from email_utils import send_subscription_rejected_email
            from extensions import logger
            send_subscription_rejected_email(subscription.user, subscription)
        except Exception as email_error:
            logger.error(f"Error sending rejection email: {email_error}")
            # Don't fail the rejection if email fails
        
        flash(
            f"Partner subscription for {subscription.partner.company_name} has been rejected.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error rejecting subscription: {str(e)}", "error")

    return redirect(url_for("admin.partner_subscriptions"))


@admin.route("/payment-gateways")
@super_admin_required
def payment_gateways():
    """Payment gateway management."""
    from models.models import PaymentGateway
    
    gateways = PaymentGateway.query.all()
    return render_template("admin/payment_gateways.html", gateways=gateways)


@admin.route("/payment-gateways/edit/<int:gateway_id>", methods=["GET", "POST"])
@super_admin_required
def edit_payment_gateway(gateway_id):
    """Edit payment gateway settings."""
    from models.models import PaymentGateway
    
    gateway = PaymentGateway.query.get_or_404(gateway_id)
    form = PaymentGatewayForm(obj=gateway)

    if form.validate_on_submit():
        # Update gateway settings
        success = update_payment_gateway_settings(
            name=form.name.data,
            api_key=form.api_key.data if form.api_key.data else None,
            secret_key=form.secret_key.data if form.secret_key.data else None,
            publishable_key=(
                form.publishable_key.data if form.publishable_key.data else None
            ),
            client_id=form.client_id.data if form.client_id.data else None,
            webhook_secret=(
                form.webhook_secret.data if form.webhook_secret.data else None
            ),
            environment=form.environment.data,
            enabled=form.enabled.data,
        )

        if success:
            flash(
                f"{gateway.name.title()} payment gateway updated successfully!",
                "success",
            )
        else:
            flash("Error updating payment gateway settings.", "error")

        return redirect(url_for("admin.payment_gateways"))

    return render_template(
        "admin/edit_payment_gateway.html", form=form, gateway=gateway
    )


# Tag Management Routes
@admin.route("/tags")
@admin_required
def tags():
    """Admin tag management page."""
    from models.models import Tag, User
    from extensions import db
    
    search = request.args.get("search", "")
    query = Tag.query

    if search:
        search_filter = f"%{search}%"
        # Create aliases for the User table to handle creator and owner joins
        creator = db.aliased(User)
        owner = db.aliased(User)

        query = (
            query.outerjoin(creator, Tag.created_by == creator.id)
            .outerjoin(owner, Tag.owner_id == owner.id)
            .filter(
                db.or_(
                    Tag.tag_id.ilike(search_filter),
                    Tag.status.ilike(search_filter),
                    creator.username.ilike(search_filter),
                    creator.email.ilike(search_filter),
                    owner.username.ilike(search_filter),
                    owner.email.ilike(search_filter),
                )
            )
        )

    tags = query.order_by(Tag.created_at.desc()).all()
    return render_template("admin/tags.html", tags=tags, search=search)


@admin.route("/tags/create", methods=["GET", "POST"])
@admin_required
def create_tag():
    """Create a new tag."""
    from models.models import Tag
    from extensions import db
    
    if request.method == "POST":
        tag_id = request.form.get("tag_id", "").strip().upper()

        if not tag_id:
            flash("Tag ID is required.", "error")
            return redirect(url_for("admin.create_tag"))

        # Check if tag already exists (case-insensitive)
        from sqlalchemy import func
        existing_tag = Tag.query.filter(func.upper(Tag.tag_id) == func.upper(tag_id)).first()
        if existing_tag:
            flash(f"Tag {tag_id} already exists.", "error")
            return redirect(url_for("admin.create_tag"))

        try:
            # Create new tag
            new_tag = Tag(
                tag_id=tag_id,
                status="available",  # Admin-created tags are immediately available
                created_by=current_user.id,
            )
            db.session.add(new_tag)
            db.session.commit()

            flash(f"Tag {tag_id} created successfully!", "success")
            return redirect(url_for("admin.tags"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating tag: {str(e)}", "error")
            return redirect(url_for("admin.create_tag"))

    return render_template("admin/create_tag.html")


@admin.route("/tags/activate/<int:tag_id>", methods=["POST"])
@admin_required
def activate_tag(tag_id):
    """Activate a pending tag."""
    from models.models import Tag
    from extensions import db
    
    tag_obj = Tag.query.get_or_404(tag_id)

    if tag_obj.status != "pending":
        flash(f"Tag {tag_obj.tag_id} is not in pending status.", "error")
        return redirect(url_for("admin.tags"))

    try:
        tag_obj.status = "available"
        tag_obj.updated_at = datetime.utcnow()
        db.session.commit()

        flash(f"Tag {tag_obj.tag_id} has been activated and is now available.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error activating tag: {str(e)}", "error")

    return redirect(url_for("admin.tags"))


@admin.route("/tags/deactivate/<int:tag_id>", methods=["POST"])
@admin_required
def deactivate_tag(tag_id):
    """Deactivate an available tag."""
    from models.models import Tag
    from extensions import db
    
    tag_obj = Tag.query.get_or_404(tag_id)

    if tag_obj.status not in ["available", "active"]:
        flash(f"Tag {tag_obj.tag_id} cannot be deactivated in its current status.", "error")
        return redirect(url_for("admin.tags"))

    try:
        tag_obj.status = "pending"
        tag_obj.updated_at = datetime.utcnow()
        db.session.commit()

        flash(f"Tag {tag_obj.tag_id} has been deactivated.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deactivating tag: {str(e)}", "error")

    return redirect(url_for("admin.tags"))


# Pricing Management Routes
@admin.route("/pricing")
@admin_required
def pricing():
    """Admin pricing management page."""
    from models.models import PricingPlan
    
    plans = PricingPlan.query.order_by(PricingPlan.sort_order.asc()).all()
    return render_template("admin/pricing.html", plans=plans)


@admin.route("/pricing/create", methods=["GET", "POST"])
@admin_required
def create_pricing_plan():
    """Create new pricing plan."""
    from models.models import PricingPlan
    from extensions import db
    
    form = PricingPlanForm()

    if form.validate_on_submit():
        try:
            # Get features as a list
            features_list = (
                [f.strip() for f in form.features.data.split("\n") if f.strip()]
                if form.features.data
                else []
            )

            plan = PricingPlan(
                name=form.name.data,
                description=form.description.data,
                plan_type=form.plan_type.data,
                price=form.price.data,
                currency=form.currency.data,
                billing_period=form.billing_period.data,
                max_tags=form.max_tags.data,
                max_pets=form.max_pets.data,
                requires_approval=form.requires_approval.data,
                is_active=form.is_active.data,
                is_featured=form.is_featured.data,
                show_on_homepage=form.show_on_homepage.data,
                sort_order=form.sort_order.data,
            )
            plan.set_features_list(features_list)

            db.session.add(plan)
            db.session.commit()

            flash("Pricing plan created successfully!", "success")
            return redirect(url_for("admin.pricing"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating pricing plan: {str(e)}", "error")

    return render_template("admin/create_pricing_plan.html", form=form)


@admin.route("/pricing/edit/<int:plan_id>", methods=["GET", "POST"])
@admin_required
def edit_pricing_plan(plan_id):
    """Edit pricing plan."""
    from models.models import PricingPlan
    from extensions import db
    
    plan = PricingPlan.query.get_or_404(plan_id)
    form = PricingPlanForm(obj=plan)

    # Set form features from plan
    if plan.features:
        form.features.data = "\n".join(plan.get_features_list())

    if form.validate_on_submit():
        try:
            # Get features as a list
            features_list = (
                [f.strip() for f in form.features.data.split("\n") if f.strip()]
                if form.features.data
                else []
            )

            plan.name = form.name.data
            plan.description = form.description.data
            plan.plan_type = form.plan_type.data
            plan.price = form.price.data
            plan.currency = form.currency.data
            plan.billing_period = form.billing_period.data
            plan.max_tags = form.max_tags.data
            plan.max_pets = form.max_pets.data
            plan.requires_approval = form.requires_approval.data
            plan.is_active = form.is_active.data
            plan.is_featured = form.is_featured.data
            plan.show_on_homepage = form.show_on_homepage.data
            plan.sort_order = form.sort_order.data
            plan.set_features_list(features_list)

            db.session.commit()

            flash("Pricing plan updated successfully!", "success")
            return redirect(url_for("admin.pricing"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating pricing plan: {str(e)}", "error")

    return render_template("admin/edit_pricing_plan.html", form=form, plan=plan)


@admin.route("/pricing/delete/<int:plan_id>", methods=["POST"])
@admin_required
def delete_pricing_plan(plan_id):
    """Delete pricing plan."""
    from models.models import PricingPlan
    from extensions import db
    
    plan = PricingPlan.query.get_or_404(plan_id)

    try:
        db.session.delete(plan)
        db.session.commit()
        flash("Pricing plan deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting pricing plan: {str(e)}", "error")

    return redirect(url_for("admin.pricing"))


@admin.route("/pricing/toggle-homepage/<int:plan_id>", methods=["POST"])
@admin_required
def toggle_pricing_homepage(plan_id):
    """Toggle pricing plan visibility on homepage."""
    from models.models import PricingPlan
    from extensions import db
    
    plan = PricingPlan.query.get_or_404(plan_id)

    try:
        plan.show_on_homepage = not plan.show_on_homepage
        db.session.commit()

        status = "shown on" if plan.show_on_homepage else "hidden from"
        flash(f'Pricing plan "{plan.name}" is now {status} homepage.', "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating pricing plan: {str(e)}", "error")

    return redirect(url_for("admin.pricing"))


@admin.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    """Admin settings management."""
    from models.models import SystemSetting, PaymentGateway
    from extensions import db
    
    # Filter out pricing-related and payment gateway settings (these should be managed through their respective sections)
    excluded_keys = [
        'partner_monthly_price', 'partner_yearly_price', 
        'tag_monthly_price', 'tag_yearly_price', 'tag_lifetime_price',
        'paypal_enabled', 'stripe_enabled', 'square_enabled'
    ]
    settings = SystemSetting.query.filter(~SystemSetting.key.in_(excluded_keys)).all()
    
    # Get payment gateways
    gateways = PaymentGateway.query.all()
    
    if request.method == "POST":
        # Define which fields are actually boolean checkboxes
        boolean_fields = ['registration_enabled', 'email_verification_required', 'maintenance_mode', 'smtp_enabled', 'smtp_use_tls']
        
        # Handle setting updates - support both key-based and id-based field names
        for setting in settings:
            # Try key-based field name first (from template)
            field_name = f"setting_{setting.key}"
            values = request.form.getlist(field_name)
            
            if values:
                if setting.key in boolean_fields:
                    # For boolean checkboxes, we get both hidden field (false) and checkbox (true) values
                    # The checkbox value (true) should take precedence
                    if 'true' in values:
                        new_value = 'true'
                    else:
                        new_value = 'false'
                else:
                    # For text fields, take the single value
                    new_value = values[0] if values[0] else setting.value
            else:
                # Fallback to id-based field name
                field_name = f"setting_{setting.id}"
                values = request.form.getlist(field_name)
                if values:
                    if setting.key in boolean_fields:
                        if 'true' in values:
                            new_value = 'true'
                        else:
                            new_value = 'false'
                    else:
                        new_value = values[0] if values[0] else setting.value
                else:
                    new_value = None
            
            if new_value is not None:
                setting.value = new_value
                setting.updated_at = datetime.utcnow()
        
        # Handle payment gateway updates
        for gateway in gateways:
            # Use getlist to handle hidden input + checkbox pattern
            values = request.form.getlist(f"gateway_{gateway.name}")
            if values:
                # For checkboxes, we get both hidden field (false) and checkbox (true) values
                # The checkbox value (true) should take precedence
                gateway.enabled = 'true' in values
            else:
                # If no values found, keep current state
                pass
        
        db.session.commit()
        flash("Settings updated successfully!", "success")
        return redirect(url_for("admin.settings"))
    
    return render_template("admin/settings.html", settings=settings, gateways=gateways)


@admin.route("/settings/add", methods=["POST"])
@super_admin_required
def add_setting():
    """Add a new system setting."""
    from models.models import SystemSetting
    from extensions import db
    
    key = request.form.get("key")
    value = request.form.get("value")
    description = request.form.get("description")

    if not key or not value:
        flash("Key and value are required.", "error")
        return redirect(url_for("admin.settings"))

    # Check if setting already exists
    existing = SystemSetting.query.filter_by(key=key).first()
    if existing:
        flash("Setting with this key already exists.", "error")
        return redirect(url_for("admin.settings"))

    setting = SystemSetting(key=key, value=value, description=description)
    db.session.add(setting)
    db.session.commit()

    flash("Setting added successfully!", "success")
    return redirect(url_for("admin.settings"))

@admin.route("/settings/test-email", methods=["POST"])
@admin_required
def test_email():
    """Send a test email to verify SMTP configuration."""
    from models.models import SystemSetting
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    test_email_address = request.form.get("test_email")
    if not test_email_address:
        flash("Please provide a test email address.", "error")
        return redirect(url_for("admin.settings"))
    
    try:
        # Get SMTP settings
        smtp_enabled = SystemSetting.get_value('smtp_enabled', False)
        if not smtp_enabled:
            flash("SMTP is not enabled. Please enable SMTP first.", "error")
            return redirect(url_for("admin.settings"))
        
        smtp_server = SystemSetting.get_value('smtp_server')
        smtp_port = int(SystemSetting.get_value('smtp_port', '587'))
        smtp_username = SystemSetting.get_value('smtp_username')
        smtp_password = SystemSetting.get_value('smtp_password')
        smtp_from_email = SystemSetting.get_value('smtp_from_email')
        smtp_use_tls = SystemSetting.get_value('smtp_use_tls', True)
        
        if not all([smtp_server, smtp_username, smtp_password, smtp_from_email]):
            flash("SMTP configuration is incomplete. Please check all required fields.", "error")
            return redirect(url_for("admin.settings"))
        
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = smtp_from_email
        msg['To'] = test_email_address
        msg['Subject'] = "LTFPQRR Test Email"
        
        body = f"""
        This is a test email from LTFPQRR.
        
        If you received this email, your SMTP configuration is working correctly.
        
        Configuration details:
        - SMTP Server: {smtp_server}
        - SMTP Port: {smtp_port}
        - From Email: {smtp_from_email}
        - TLS Enabled: {smtp_use_tls}
        
        Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        if smtp_use_tls:
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        flash(f"Test email sent successfully to {test_email_address}!", "success")
        
    except Exception as e:
        flash(f"Failed to send test email: {str(e)}", "error")
    
    return redirect(url_for("admin.settings"))

@admin.route("/partners")
@admin_required
def partners():
    """View and manage all partners."""
    from models.models import Partner
    from sqlalchemy import or_
    
    search = request.args.get("search", "").strip()
    
    # Build query
    query = Partner.query
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Partner.company_name.ilike(search_filter),
                Partner.email.ilike(search_filter),
                Partner.phone.ilike(search_filter),
            )
        )
    
    partners = query.order_by(Partner.created_at.desc()).all()
    return render_template("admin/partners.html", partners=partners, search=search)


@admin.route("/partner-subscriptions/cancel/<int:subscription_id>", methods=["POST"])
@admin_required
def cancel_partner_subscription(subscription_id):
    """Cancel a partner subscription."""
    from models.models import Subscription
    from extensions import db
    
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.subscription_type != "partner":
        flash("Invalid subscription type.", "error")
        return redirect(url_for("admin.partner_subscriptions"))

    try:
        subscription.status = "cancelled"
        subscription.end_date = datetime.utcnow()
        db.session.commit()
        
        # Send cancellation email to customer
        try:
            from email_utils import send_subscription_cancelled_email
            from extensions import logger
            send_subscription_cancelled_email(subscription.user, subscription, refunded=False)
        except Exception as email_error:
            logger.error(f"Error sending cancellation email: {email_error}")
            # Don't fail the cancellation if email fails
        
        flash(
            f"Partner subscription for {subscription.partner.company_name} has been cancelled.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling subscription: {str(e)}", "error")

    return redirect(url_for("admin.partner_subscriptions"))


@admin.route("/partner-subscriptions/refund/<int:subscription_id>", methods=["POST"])
@admin_required
def refund_partner_subscription(subscription_id):
    """Process a refund for a partner subscription."""
    from models.models import Subscription, Payment
    from extensions import db, logger
    import stripe
    
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.subscription_type != "partner":
        flash("Invalid subscription type.", "error")
        return redirect(url_for("admin.partner_subscriptions"))

    try:
        # Configure payment gateways to ensure Stripe is properly set up
        configure_payment_gateways()
        
        # Find associated payment record using the subscription link
        payment = Payment.query.filter_by(subscription_id=subscription.id).first()
        
        stripe_refund_successful = False
        
        if payment and payment.payment_intent_id:
            try:
                # Process Stripe refund
                refund = stripe.Refund.create(
                    payment_intent=payment.payment_intent_id,
                    reason='requested_by_customer'
                )
                
                if refund.status == 'succeeded':
                    stripe_refund_successful = True
                    logger.info(f"Stripe refund successful for payment {payment.payment_intent_id}: {refund.id}")
                    
                    # Mark payment as refunded with Stripe refund ID
                    payment.status = "refunded"
                    payment.updated_at = datetime.utcnow()
                    if not payment.payment_metadata:
                        payment.payment_metadata = {}
                    payment.payment_metadata['stripe_refund_id'] = refund.id
                    payment.payment_metadata['refund_date'] = datetime.utcnow().isoformat()
                    
                else:
                    logger.error(f"Stripe refund failed for payment {payment.payment_intent_id}: {refund.status}")
                    
            except stripe.error.StripeError as stripe_error:
                logger.error(f"Stripe refund error for payment {payment.payment_intent_id}: {str(stripe_error)}")
                flash(f"Stripe refund failed: {str(stripe_error)}", "error")
                return redirect(url_for("admin.partner_subscriptions"))
            except Exception as e:
                logger.error(f"Unexpected error during Stripe refund: {str(e)}")
                flash(f"Refund processing error: {str(e)}", "error")
                return redirect(url_for("admin.partner_subscriptions"))
        else:
            logger.warning(f"No payment record found for subscription {subscription_id} or missing payment_intent_id")
        
        # Cancel the subscription regardless of Stripe refund status
        subscription.status = "refunded"
        subscription.end_date = datetime.utcnow()
        
        db.session.commit()
        
        # Send cancellation email to customer
        try:
            from email_utils import send_subscription_cancelled_email
            from extensions import logger
            send_subscription_cancelled_email(subscription.user, subscription, refunded=stripe_refund_successful)
        except Exception as email_error:
            logger.error(f"Error sending cancellation email: {email_error}")
            # Don't fail the refund if email fails
        
        if stripe_refund_successful:
            flash(
                f"Partner subscription for {subscription.partner.company_name} has been successfully refunded through Stripe and cancelled.",
                "success",
            )
        else:
            flash(
                f"Partner subscription for {subscription.partner.company_name} has been cancelled. No Stripe payment found to refund.",
                "warning",
            )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing refund for subscription {subscription_id}: {str(e)}")
        flash(f"Error processing refund: {str(e)}", "error")

    return redirect(url_for("admin.partner_subscriptions"))


@admin.route("/partner-subscriptions/extend/<int:subscription_id>", methods=["GET", "POST"])
@admin_required
def extend_partner_subscription(subscription_id):
    """Extend or modify the expiration date of a partner subscription."""
    from models.models import Subscription
    from extensions import db
    from datetime import datetime, timedelta
    
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.subscription_type != "partner":
        flash("Invalid subscription type.", "error")
        return redirect(url_for("admin.partner_subscriptions"))
    
    if request.method == "POST":
        try:
            action = request.form.get("action")
            
            if action == "extend_month":
                if subscription.end_date:
                    subscription.end_date += timedelta(days=30)
                else:
                    subscription.end_date = datetime.utcnow() + timedelta(days=30)
            elif action == "extend_year":
                if subscription.end_date:
                    subscription.end_date += timedelta(days=365)
                else:
                    subscription.end_date = datetime.utcnow() + timedelta(days=365)
            elif action == "set_custom":
                custom_date = request.form.get("custom_date")
                if custom_date:
                    subscription.end_date = datetime.strptime(custom_date, "%Y-%m-%d")
            elif action == "set_unlimited":
                subscription.end_date = None
                
            db.session.commit()
            flash(
                f"Subscription expiration updated for {subscription.partner.company_name}.",
                "success",
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating subscription: {str(e)}", "error")
            
        return redirect(url_for("admin.partner_subscriptions"))
    
    # GET request - show form
    return render_template(
        "admin/extend_subscription.html",
        subscription=subscription
    )
