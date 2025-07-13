from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    TextAreaField,
    FileField,
    BooleanField,
    DecimalField,
)
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
from functools import wraps
import stripe
import paypalrestsdk
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from cryptography.fernet import Fernet
import base64
from celery import Celery
import qrcode
from io import BytesIO

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///ltfpqrr.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize extensions
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Encryption key for storing sensitive data
encryption_key_str = os.environ.get("ENCRYPTION_KEY")
if not encryption_key_str:
    # Generate a new key if not provided
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning(
        "No ENCRYPTION_KEY provided, generated a new one. This should be set in production."
    )
else:
    # Convert string to bytes for Fernet
    ENCRYPTION_KEY = encryption_key_str.encode("utf-8")

cipher_suite = Fernet(ENCRYPTION_KEY)


# Helper function to decrypt gateway settings
def decrypt_value(encrypted_value):
    """Decrypt an encrypted value using the cipher suite."""
    if not encrypted_value:
        return None
    try:
        return cipher_suite.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        logger.error(f"Error decrypting value: {e}")
        return None


# Helper function to configure payment gateways from database
def configure_payment_gateways():
    """Configure payment gateways from database settings."""
    try:
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


# Configure payment gateways (will be reconfigured from database after app starts)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
paypalrestsdk.configure(
    {
        "mode": os.environ.get("PAYPAL_MODE", "sandbox"),
        "client_id": os.environ.get("PAYPAL_CLIENT_ID"),
        "client_secret": os.environ.get("PAYPAL_CLIENT_SECRET"),
    }
)

# Import models and forms
from models.models import (
    db,
    User,
    Role,
    Tag,
    Pet,
    Subscription,
    SearchLog,
    NotificationPreference,
    SystemSetting,
    PaymentGateway,
    PricingPlan,
    Payment,
)
from models.partner.partner import Partner, PartnerAccessRequest, PartnerSubscription
from forms import *

# Initialize db with app
db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role("admin"):
            flash("You need admin privileges to access this page.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role(
            "super-admin"
        ):
            flash("You need super-admin privileges to access this page.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
        broker=app.config.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# Configure Celery
app.config["CELERY_BROKER_URL"] = os.environ.get("REDIS_URL", "redis://redis:6379/0")
app.config["CELERY_RESULT_BACKEND"] = os.environ.get(
    "REDIS_URL", "redis://redis:6379/0"
)
celery = make_celery(app)


# Helper function to get enabled payment gateways
def get_enabled_payment_gateways():
    """Get a list of enabled payment gateways with configuration from the database."""
    try:
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


# Helper function to encrypt and store payment gateway settings
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
        gateway = PaymentGateway.query.filter_by(name=name).first()
        if not gateway:
            gateway = PaymentGateway(name=name)
            db.session.add(gateway)

        # Encrypt sensitive data before storing
        if api_key:
            gateway.api_key = cipher_suite.encrypt(api_key.encode()).decode()
        if secret_key:
            gateway.secret_key = cipher_suite.encrypt(secret_key.encode()).decode()
        if publishable_key:
            gateway.publishable_key = cipher_suite.encrypt(
                publishable_key.encode()
            ).decode()
        if client_id:
            gateway.client_id = cipher_suite.encrypt(client_id.encode()).decode()
        if webhook_secret:
            gateway.webhook_secret = cipher_suite.encrypt(
                webhook_secret.encode()
            ).decode()

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
        db.session.rollback()
        return False


# Routes
@app.route("/")
def index():
    # Handle tag search from homepage
    tag_id = request.args.get("tag_id")
    if tag_id:
        return redirect(url_for("found_pet", tag_id=tag_id))

    # Get pricing plans for homepage
    pricing_plans = (
        PricingPlan.query.filter_by(show_on_homepage=True, is_active=True)
        .order_by(PricingPlan.sort_order.asc())
        .all()
    )

    # Get stats for homepage
    total_pets = Pet.query.count()

    return render_template(
        "index.html", pricing_plans=pricing_plans, total_pets=total_pets
    )


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/found")
def found_index():
    """Found pet search page"""
    return render_template("found/index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Check if registration is enabled before processing
    registration_enabled = SystemSetting.get_value("registration_enabled", True)
    if not registration_enabled:
        flash(
            "Registration is currently disabled. Please contact an administrator.",
            "warning",
        )
        return redirect(url_for("login"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Double check registration is still enabled
        registration_enabled = SystemSetting.get_value("registration_enabled", True)
        if not registration_enabled:
            flash("Registration is currently disabled.", "error")
            return redirect(url_for("login"))

        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "error")
            return redirect(url_for("register"))

        # Create new user (all users are customers by default)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            address=form.address.data,
        )

        # First user gets admin roles
        if User.query.count() == 0:
            user.roles = [
                Role.query.filter_by(name="user").first(),
                Role.query.filter_by(name="admin").first(),
                Role.query.filter_by(name="super-admin").first(),
            ]
        else:
            user.roles = [Role.query.filter_by(name="user").first()]

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("auth/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("auth/login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    # Show unified dashboard selection for users with partner role
    if current_user.has_partner_role():
        owned_partners = current_user.get_owned_partners()
        accessible_partners = current_user.get_accessible_partners()
        
        # If no partners exist, show the partner management dashboard
        if not owned_partners and not accessible_partners:
            return redirect(url_for("partner_management_dashboard"))
        
        # Otherwise show partner dashboard
        return redirect(url_for("partner_dashboard"))
    else:
        return redirect(url_for("customer_dashboard"))


@app.route("/partner/management")
@login_required  
def partner_management_dashboard():
    """Partner management dashboard - allows creating and selecting partners"""
    if not current_user.has_partner_role():
        flash("Partner access required.", "error")
        return redirect(url_for("dashboard"))
    
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    return render_template(
        "partner/management.html",
        owned_partners=owned_partners,
        accessible_partners=accessible_partners
    )


@app.route("/partner/dashboard")
@login_required
def partner_dashboard():
    if not current_user.has_partner_role():
        flash("Partner access required.", "error")
        return redirect(url_for("dashboard"))

    # Get user's owned partners
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    # If user doesn't have any partners, redirect to management page
    if not owned_partners and not accessible_partners:
        flash("You need to create or have access to a partner account first.", "info")
        return redirect(url_for("partner_management_dashboard"))
    
    # If there are multiple partners, let user select one from query parameter
    partner_id = request.args.get('partner_id', type=int)
    if partner_id:
        all_partners = owned_partners + accessible_partners
        partner = next((p for p in all_partners if p.id == partner_id), None)
        if not partner:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner_management_dashboard"))
    else:
        # Default to first available partner
        partner = owned_partners[0] if owned_partners else accessible_partners[0]
    
    # Check if partner has active subscription
    subscription = partner.get_active_subscription()
    
    # Get partner's tags
    tags = partner.tags.all()

    return render_template(
        "partner/dashboard.html", 
        tags=tags, 
        subscription=subscription,
        partner=partner,
        owned_partners=owned_partners,
        accessible_partners=accessible_partners
    )


@app.route('/partner/<int:partner_id>')
@login_required
def partner_detail(partner_id):
    """View partner details and manage"""
    partner = Partner.query.get_or_404(partner_id)
    
    if not partner.user_has_access(current_user):
        flash('You do not have access to this partner.', 'error')
        return redirect(url_for('partner_management_dashboard'))
    
    user_role = partner.get_user_role(current_user)
    subscription = partner.get_active_subscription()
    
    # Check if we should prompt for subscription (new partner)
    prompt_subscription = request.args.get('prompt_subscription', False)
    
    return render_template('partner/detail.html', 
                         partner=partner,
                         user_role=user_role,
                         subscription=subscription,
                         prompt_subscription=prompt_subscription)


@app.route("/customer/dashboard")
@login_required
def customer_dashboard():
    # All users have customer access
    # Get customer's claimed tags and pets
    tags = Tag.query.filter_by(owner_id=current_user.id).all()
    pets = Pet.query.filter_by(owner_id=current_user.id).all()

    return render_template("customer/dashboard.html", tags=tags, pets=pets)


@app.route("/partner/subscription")
@app.route("/partner/<int:partner_id>/subscription")
@login_required
def partner_subscription(partner_id=None):
    # Show subscription info and allow managing partner subscriptions
    if not current_user.has_partner_role():
        flash("Partner access required to view subscriptions.", "error")
        return redirect(url_for("dashboard"))
    
    # Get user's partners
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    # If partner_id specified, show that specific partner's subscription
    if partner_id:
        all_partners = owned_partners + accessible_partners
        partner = next((p for p in all_partners if p.id == partner_id), None)
        if not partner:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner_management_dashboard"))
        
        subscription = partner.get_active_subscription()
        return render_template("partner/subscription.html", 
                             partner=partner,
                             subscription=subscription,
                             owned_partners=owned_partners,
                             accessible_partners=accessible_partners)
    
    # Otherwise show all partners and their subscriptions
    return render_template("partner/subscription.html", 
                         owned_partners=owned_partners,
                         accessible_partners=accessible_partners)


@app.route('/partner/<int:partner_id>/subscription', methods=['GET', 'POST'])
@login_required
def partner_subscription_detail(partner_id):
    """Manage partner subscription for specific partner"""
    partner = Partner.query.get_or_404(partner_id)
    
    if not partner.user_has_access(current_user):
        flash('You do not have access to this partner.', 'error')
        return redirect(url_for('partner_management_dashboard'))
    
    subscription = partner.get_active_subscription()
    
    return render_template('partner/subscription.html', 
                         partner=partner,
                         subscription=subscription)


@app.route("/tag/create", methods=["GET", "POST"])
@app.route("/tag/create/<int:partner_id>", methods=["GET", "POST"])
@login_required
def create_tag(partner_id=None):
    if not current_user.has_partner_role():
        flash("Partner access required to create tags.", "error")
        return redirect(url_for("dashboard"))

    # Get user's partners to choose from
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    if not owned_partners and not accessible_partners:
        flash("You need access to a partner account to create tags.", "error")
        return redirect(url_for("partner_management_dashboard"))

    # If partner_id provided, validate it
    selected_partner = None
    if partner_id:
        all_partners = owned_partners + accessible_partners
        selected_partner = next((p for p in all_partners if p.id == partner_id), None)
        if not selected_partner:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner_management_dashboard"))

    form = TagForm()
    if form.validate_on_submit():
        # Get partner_id from form, URL parameter, or use first available partner
        form_partner_id = request.form.get("partner_id")
        if form_partner_id:
            partner_id = int(form_partner_id)
        elif not partner_id and owned_partners:
            partner_id = owned_partners[0].id
        elif not partner_id and accessible_partners:
            partner_id = accessible_partners[0].id
            
        partner = Partner.query.get(partner_id)
        if not partner or not partner.user_has_access(current_user):
            flash("Invalid partner selected or you don't have access.", "error")
            return render_template("tag/create.html", form=form, 
                                 owned_partners=owned_partners,
                                 accessible_partners=accessible_partners,
                                 selected_partner=selected_partner)
        
        # Check if partner can create tags
        if not partner.can_create_tags():
            flash("This partner cannot create more tags. Check subscription limits.", "error")
            return render_template("tag/create.html", form=form,
                                 owned_partners=owned_partners,
                                 accessible_partners=accessible_partners,
                                 selected_partner=selected_partner)

        tag = Tag(
            tag_id=str(uuid.uuid4())[:8].upper(),
            created_by=current_user.id,
            partner_id=partner.id,
            status="pending",  # Tags start as pending, partners must activate them
        )
        db.session.add(tag)
        db.session.commit()

        flash(
            f"Tag {tag.tag_id} created successfully for {partner.company_name}! You can activate it from your partner dashboard.",
            "success",
        )
        return redirect(url_for("partner_dashboard", partner_id=partner.id))

    return render_template("tag/create.html", form=form,
                         owned_partners=owned_partners,
                         accessible_partners=accessible_partners,
                         selected_partner=selected_partner)


@app.route("/tag/activate/<int:tag_id>", methods=["POST"])
@login_required
def activate_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)

    # Check if current user has access to this tag's partner
    if tag.partner and not tag.partner.user_has_access(current_user):
        flash("You don't have access to this partner account.", "error")
        return redirect(url_for("partner_dashboard"))
    elif not tag.partner and tag.created_by != current_user.id:
        flash("You can only activate tags you created.", "error")
        return redirect(url_for("partner_dashboard"))

    # Check if partner can activate tags (has active subscription)
    if tag.partner and not tag.partner.has_active_subscription():
        flash("Partner needs an active subscription to activate tags.", "error")
        return redirect(url_for("partner_dashboard"))

    # Attempt to activate the tag
    if tag.activate_by_partner():
        db.session.commit()
        flash(
            f"Tag {tag.tag_id} has been activated and is now available for customers to claim!",
            "success",
        )
    else:
        flash(
            f"Unable to activate tag {tag.tag_id}. It may already be activated.",
            "error",
        )

    return redirect(url_for("partner_dashboard"))


@app.route("/tag/deactivate/<int:tag_id>", methods=["POST"])
@login_required
def deactivate_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)

    # Check if current user is the creator of the tag
    if tag.created_by != current_user.id:
        flash("You can only deactivate tags you created.", "error")
        return redirect(url_for("partner_dashboard"))

    # Only allow deactivation if tag is available (not claimed or active)
    if tag.status == "available":
        tag.status = "pending"
        tag.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f"Tag {tag.tag_id} has been deactivated.", "success")
    else:
        flash(
            f"Cannot deactivate tag {tag.tag_id}. It may be claimed or already in use.",
            "error",
        )

    return redirect(url_for("partner_dashboard"))


@app.route("/tag/claim", methods=["GET", "POST"])
@login_required
def claim_tag():
    # All users can claim tags (customer access)
    form = ClaimTagForm()
    if form.validate_on_submit():
        tag = Tag.query.filter_by(tag_id=form.tag_id.data).first()

        if not tag:
            flash("Tag not found.", "error")
            return redirect(url_for("claim_tag"))

        if tag.status != "available":
            flash("Tag is not available for claiming.", "error")
            return redirect(url_for("claim_tag"))

        # Store tag_id and subscription_type in session for payment
        session["claiming_tag_id"] = tag.tag_id
        session["subscription_type"] = form.subscription_type.data

        return redirect(url_for("tag_payment"))

    return render_template("tag/claim.html", form=form)


@app.route("/tag/payment")
@login_required
def tag_payment():
    if "claiming_tag_id" not in session:
        flash("No tag selected for claiming.", "error")
        return redirect(url_for("claim_tag"))

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
        return redirect(url_for("customer_dashboard"))

    return render_template(
        "tag/payment.html",
        tag_id=tag_id,
        subscription_type=subscription_type,
        amount=amount,
        enabled_gateways=enabled_gateways,
        gateway_config=gateway_config,
    )


@app.route("/pet/create", methods=["GET", "POST"])
@login_required
def create_pet():
    # All users can create pets (customer access)
    form = PetForm()

    # Get user's available tags
    available_tags = Tag.query.filter_by(owner_id=current_user.id, pet_id=None).all()
    form.tag_id.choices = [(tag.id, tag.tag_id) for tag in available_tags]

    if form.validate_on_submit():
        # Handle file upload
        photo_filename = None
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_filename = f"{uuid.uuid4()}_{photo_filename}"
            form.photo.data.save(
                os.path.join(app.config["UPLOAD_FOLDER"], photo_filename)
            )

        pet = Pet(
            name=form.name.data,
            breed=form.breed.data,
            color=form.color.data,
            photo=photo_filename,
            vet_name=form.vet_name.data,
            vet_phone=form.vet_phone.data,
            vet_address=form.vet_address.data,
            groomer_name=form.groomer_name.data,
            groomer_phone=form.groomer_phone.data,
            groomer_address=form.groomer_address.data,
            owner_id=current_user.id,
        )

        db.session.add(pet)
        db.session.commit()

        # Assign tag to pet
        if form.tag_id.data:
            tag = Tag.query.get(form.tag_id.data)
            if tag and tag.owner_id == current_user.id:
                tag.pet_id = pet.id
                db.session.commit()

        flash("Pet created successfully!", "success")
        return redirect(url_for("customer_dashboard"))

    return render_template("pet/create.html", form=form)


@app.route("/pet/edit/<int:pet_id>", methods=["GET", "POST"])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)

    if pet.owner_id != current_user.id:
        flash("You can only edit your own pets.", "error")
        return redirect(url_for("customer_dashboard"))

    # Check if pet is on a lifetime subscription and restrictions apply
    tag = Tag.query.filter_by(pet_id=pet.id).first()
    if tag:
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            tag_id=tag.id,
            subscription_type="lifetime",
            status="active",
        ).first()

        if subscription and subscription.restrictions_active:
            flash(
                "Pet name and details cannot be changed on active lifetime subscription.",
                "warning",
            )
            return redirect(url_for("customer_dashboard"))

    form = PetForm(obj=pet)

    if form.validate_on_submit():
        # Handle file upload
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_filename = f"{uuid.uuid4()}_{photo_filename}"
            form.photo.data.save(
                os.path.join(app.config["UPLOAD_FOLDER"], photo_filename)
            )

            # Delete old photo if it exists
            if pet.photo:
                old_photo_path = os.path.join(app.config["UPLOAD_FOLDER"], pet.photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)

            pet.photo = photo_filename

        pet.name = form.name.data
        pet.breed = form.breed.data
        pet.color = form.color.data
        pet.vet_name = form.vet_name.data
        pet.vet_phone = form.vet_phone.data
        pet.vet_address = form.vet_address.data
        pet.groomer_name = form.groomer_name.data
        pet.groomer_phone = form.groomer_phone.data
        pet.groomer_address = form.groomer_address.data

        db.session.commit()

        flash("Pet updated successfully!", "success")
        return redirect(url_for("customer_dashboard"))

    return render_template("pet/edit.html", form=form, pet=pet)


@app.route("/found/<tag_id>")
def found_pet(tag_id):
    tag = Tag.query.filter_by(tag_id=tag_id).first()

    if not tag:
        return render_template("found/invalid_tag.html", tag_id=tag_id)

    if not tag.pet_id:
        return render_template("found/not_registered.html", tag_id=tag_id)

    pet = Pet.query.get(tag.pet_id)
    owner = User.query.get(pet.owner_id)

    # Log the search
    search_log = SearchLog(
        tag_id=tag.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
    )
    db.session.add(search_log)
    db.session.commit()

    # Check if owner wants notifications
    notification_pref = NotificationPreference.query.filter_by(
        user_id=owner.id, notification_type="tag_search"
    ).first()

    if notification_pref and notification_pref.enabled:
        send_notification_email(owner, tag, pet)

    return render_template("found/pet_info.html", pet=pet, owner=owner, tag=tag)


@app.route("/found/<tag_id>/contact", methods=["GET", "POST"])
def contact_owner(tag_id):
    tag = Tag.query.filter_by(tag_id=tag_id).first()

    if not tag:
        return render_template("found/invalid_tag.html", tag_id=tag_id)

    if not tag.pet_id:
        flash("This tag is not registered to a pet.", "error")
        return redirect(url_for("found_pet", tag_id=tag_id))

    pet = Pet.query.get(tag.pet_id)
    owner = User.query.get(pet.owner_id)

    form = ContactOwnerForm()
    if form.validate_on_submit():
        # Send email to owner
        send_contact_email(
            owner, pet, form.finder_name.data, form.finder_email.data, form.message.data
        )

        flash("Your message has been sent to the pet owner.", "success")
        return redirect(url_for("found_pet", tag_id=tag_id))

    return render_template("found/contact.html", form=form, pet=pet, tag=tag)


@app.route("/tag/transfer/<int:tag_id>", methods=["GET", "POST"])
@login_required
def transfer_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)

    if tag.owner_id != current_user.id:
        flash("You can only transfer tags you own.", "error")
        return redirect(url_for("customer_dashboard"))

    form = TransferTagForm()
    if form.validate_on_submit():
        new_owner = User.query.filter_by(username=form.new_owner_username.data).first()

        if not new_owner:
            flash("User not found.", "error")
            return redirect(url_for("transfer_tag", tag_id=tag_id))

        # Check if user has the 'user' role (which means they're a customer)
        if not new_owner.has_role("user"):
            flash("Tags can only be transferred to customer accounts.", "error")
            return redirect(url_for("transfer_tag", tag_id=tag_id))

        # Transfer the tag
        tag.owner_id = new_owner.id
        db.session.commit()

        flash(
            f"Tag {tag.tag_id} transferred to {new_owner.username} successfully!",
            "success",
        )
        return redirect(url_for("customer_dashboard"))

    return render_template("tag/transfer.html", form=form, tag=tag)


@app.route("/settings/notifications")
@login_required
def notification_settings():
    preferences = NotificationPreference.query.filter_by(user_id=current_user.id).all()
    return render_template("settings/notifications.html", preferences=preferences)


@app.route("/settings/notifications/toggle/<notification_type>")
@login_required
def toggle_notification(notification_type):
    preference = NotificationPreference.query.filter_by(
        user_id=current_user.id, notification_type=notification_type
    ).first()

    if not preference:
        preference = NotificationPreference(
            user_id=current_user.id, notification_type=notification_type, enabled=True
        )
        db.session.add(preference)
    else:
        preference.enabled = not preference.enabled

    db.session.commit()

    flash(f"Notification preference updated.", "success")
    return redirect(url_for("notification_settings"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    # Get statistics
    stats = {
        "total_users": User.query.count(),
        "total_tags": Tag.query.count(),
        "active_subscriptions": Subscription.query.filter_by(status="active").count(),
        "total_pets": Pet.query.count(),
    }

    return render_template("admin/dashboard.html", stats=stats)


@app.route("/admin/users")
@admin_required
def admin_users():
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


@app.route("/admin/subscriptions")
@admin_required
def admin_subscriptions():
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


@app.route("/admin/partner-subscriptions")
@admin_required
def admin_partner_subscriptions():
    """Manage partner subscription requests"""
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


@app.route(
    "/admin/partner-subscriptions/approve/<int:subscription_id>", methods=["POST"]
)
@admin_required
def approve_partner_subscription(subscription_id):
    """Approve a partner subscription"""
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.subscription_type != "partner":
        flash("This is not a partner subscription.", "error")
        return redirect(url_for("admin_partner_subscriptions"))

    if subscription.admin_approved:
        flash("Subscription is already approved.", "warning")
        return redirect(url_for("admin_partner_subscriptions"))

    try:
        subscription.approve(current_user)
        db.session.commit()
        flash(
            f"Partner subscription for {subscription.user.get_full_name()} has been approved.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error approving subscription: {str(e)}", "error")

    return redirect(url_for("admin_partner_subscriptions"))


@app.route(
    "/admin/partner-subscriptions/reject/<int:subscription_id>", methods=["POST"]
)
@admin_required
def reject_partner_subscription(subscription_id):
    """Reject a partner subscription"""
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.subscription_type != "partner":
        flash("This is not a partner subscription.", "error")
        return redirect(url_for("admin_partner_subscriptions"))

    try:
        subscription.status = "cancelled"
        db.session.commit()
        flash(
            f"Partner subscription for {subscription.user.get_full_name()} has been rejected.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error rejecting subscription: {str(e)}", "error")

    return redirect(url_for("admin_partner_subscriptions"))


@app.route("/admin/payment-gateways")
@super_admin_required
def payment_gateways():
    gateways = PaymentGateway.query.all()
    return render_template("admin/payment_gateways.html", gateways=gateways)


@app.route("/admin/payment-gateways/edit/<int:gateway_id>", methods=["GET", "POST"])
@super_admin_required
def edit_payment_gateway(gateway_id):
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

        return redirect(url_for("payment_gateways"))

    return render_template(
        "admin/edit_payment_gateway.html", form=form, gateway=gateway
    )


# Tag Management Routes
@app.route("/admin/tags")
@admin_required
def admin_tags():
    """Admin tag management page"""
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


@app.route("/admin/tags/create", methods=["GET", "POST"])
@admin_required
def admin_create_tag():
    """Create a new tag"""
    if request.method == "POST":
        tag_id = request.form.get("tag_id", "").strip().upper()

        if not tag_id:
            flash("Tag ID is required.", "error")
            return redirect(url_for("admin_create_tag"))

        # Check if tag already exists
        existing_tag = Tag.query.filter_by(tag_id=tag_id).first()
        if existing_tag:
            flash(f"Tag {tag_id} already exists.", "error")
            return redirect(url_for("admin_create_tag"))

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
            return redirect(url_for("admin_tags"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating tag: {str(e)}", "error")
            return redirect(url_for("admin_create_tag"))

    return render_template("admin/create_tag.html")


@app.route("/admin/tags/activate/<int:tag_id>", methods=["POST"])
@admin_required
def admin_activate_tag(tag_id):
    """Activate a pending tag"""
    tag = Tag.query.get_or_404(tag_id)

    if tag.status != "pending":
        flash(f"Tag {tag.tag_id} is not in pending status.", "error")
        return redirect(url_for("admin_tags"))

    try:
        tag.status = "available"
        tag.updated_at = datetime.utcnow()
        db.session.commit()

        flash(f"Tag {tag.tag_id} has been activated and is now available.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error activating tag: {str(e)}", "error")

    return redirect(url_for("admin_tags"))


@app.route("/admin/tags/deactivate/<int:tag_id>", methods=["POST"])
@admin_required
def admin_deactivate_tag(tag_id):
    """Deactivate an available tag"""
    tag = Tag.query.get_or_404(tag_id)

    if tag.status not in ["available", "active"]:
        flash(f"Tag {tag.tag_id} cannot be deactivated in its current status.", "error")
        return redirect(url_for("admin_tags"))

    try:
        tag.status = "pending"
        tag.updated_at = datetime.utcnow()
        db.session.commit()

        flash(f"Tag {tag.tag_id} has been deactivated.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deactivating tag: {str(e)}", "error")

    return redirect(url_for("admin_tags"))


# Pricing Management Routes
@app.route("/admin/pricing")
@admin_required
def admin_pricing():
    """Admin pricing management page"""
    plans = PricingPlan.query.order_by(PricingPlan.sort_order.asc()).all()
    return render_template("admin/pricing.html", plans=plans)


@app.route("/admin/pricing/create", methods=["GET", "POST"])
@admin_required
def create_pricing_plan():
    """Create new pricing plan"""
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
            return redirect(url_for("admin_pricing"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating pricing plan: {str(e)}", "error")

    return render_template("admin/create_pricing_plan.html", form=form)


@app.route("/admin/pricing/edit/<int:plan_id>", methods=["GET", "POST"])
@admin_required
def edit_pricing_plan(plan_id):
    """Edit pricing plan"""
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
            return redirect(url_for("admin_pricing"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating pricing plan: {str(e)}", "error")

    return render_template("admin/edit_pricing_plan.html", form=form, plan=plan)


@app.route("/admin/pricing/delete/<int:plan_id>", methods=["POST"])
@admin_required
def delete_pricing_plan(plan_id):
    """Delete pricing plan"""
    plan = PricingPlan.query.get_or_404(plan_id)

    try:
        db.session.delete(plan)
        db.session.commit()
        flash("Pricing plan deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting pricing plan: {str(e)}", "error")

    return redirect(url_for("admin_pricing"))


@app.route("/admin/pricing/toggle-homepage/<int:plan_id>", methods=["POST"])
@admin_required
def toggle_pricing_homepage(plan_id):
    """Toggle pricing plan visibility on homepage"""
    plan = PricingPlan.query.get_or_404(plan_id)

    try:
        plan.show_on_homepage = not plan.show_on_homepage
        db.session.commit()

        status = "shown on" if plan.show_on_homepage else "hidden from"
        flash(f'Pricing plan "{plan.name}" is now {status} homepage.', "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating pricing plan: {str(e)}", "error")

    return redirect(url_for("admin_pricing"))


@app.route("/payment/success")
@login_required
def payment_success():
    """Handle successful payment"""
    # Handle tag claim payments
    if "claiming_tag_id" in session:
        tag_id = session.pop("claiming_tag_id")
        subscription_type = session.pop("subscription_type", "monthly")

        # In a real implementation, you would verify the payment here
        # For now, we'll just create the subscription
        tag = Tag.query.filter_by(tag_id=tag_id).first()
        if tag:
            tag.owner_id = current_user.id
            tag.status = "claimed"

            # Create subscription
            subscription = Subscription(
                user_id=current_user.id,
                tag_id=tag.id,
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
            return redirect(url_for("customer_dashboard"))
    
    # Handle partner subscription payments
    elif "partner_subscription_type" in session:
        subscription_type = session.pop("partner_subscription_type")
        partner_id = session.pop("partner_id", None)
        
        # Create partner subscription
        try:
            # Create a partner subscription record
            partner_subscription = PartnerSubscription(
                partner_id=partner_id,  # Associate with specific partner if provided
                status="pending" if not partner_id else "active",  # Active if partner exists
                admin_approved=False if not partner_id else True,  # Auto-approve if partner exists
                max_tags=0,  # Unlimited for now
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
                flash("Payment successful! Your partner subscription is now active.", "success")
                return redirect(url_for("partner_dashboard", partner_id=partner_id))
            else:
                flash("Payment successful! Your partner subscription is pending admin approval.", "success")
                return redirect(url_for("partner_management_dashboard"))
            
        except Exception as e:
            logger.error(f"Error creating partner subscription: {e}")
            flash("Payment processed but there was an error setting up your subscription. Please contact support.", "error")
            return redirect(url_for("partner_management_dashboard"))

    flash("Payment completed successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/partner/subscription/payment", methods=["POST"])
@app.route("/partner/<int:partner_id>/subscription/payment", methods=["POST"])
@login_required
def partner_subscription_payment(partner_id=None):
    # Users can request partner subscriptions for specific partners
    subscription_type = request.form.get("subscription_type")
    if subscription_type not in ["monthly", "yearly"]:
        flash("Invalid subscription type.", "error")
        return redirect(url_for("partner_subscription", partner_id=partner_id))

    # If partner_id specified, validate access
    if partner_id:
        owned_partners = current_user.get_owned_partners()
        accessible_partners = current_user.get_accessible_partners()
        all_partners = owned_partners + accessible_partners
        partner = next((p for p in all_partners if p.id == partner_id), None)
        if not partner:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner_management_dashboard"))
        
        # Store partner info in session
        session["partner_id"] = partner_id

    # Store subscription info in session for payment processing
    session["partner_subscription_type"] = subscription_type

    # Define pricing for partner subscriptions
    partner_pricing = {"monthly": 29.99, "yearly": 299.99}

    amount = partner_pricing.get(subscription_type, 29.99)

    # Get enabled payment gateways
    enabled_gateways, gateway_config = get_enabled_payment_gateways()

    # Check if any payment gateways are enabled
    if not enabled_gateways:
        flash(
            "No payment gateways are currently available. Please contact support.",
            "error",
        )
        return redirect(url_for("partner_subscription", partner_id=partner_id))

    return render_template(
        "partner/payment.html",
        subscription_type=subscription_type,
        amount=amount,
        enabled_gateways=enabled_gateways,
        gateway_config=gateway_config,
        partner_id=partner_id
    )


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != current_user.id:
            flash("Email already in use by another account.", "error")
            return render_template("profile/edit.html", form=form)

        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.email = form.email.data
        current_user.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile/edit.html", form=form)


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not check_password_hash(
            current_user.password_hash, form.current_password.data
        ):
            flash("Current password is incorrect.", "error")
            return render_template("profile/change_password.html", form=form)

        current_user.password_hash = generate_password_hash(form.new_password.data)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Password changed successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile/change_password.html", form=form)


@app.route("/admin/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
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

        # Handle role updates (only for super-admin)
        if current_user.has_role("super-admin"):
            selected_role_ids = request.form.getlist("roles")
            new_roles = []

            for role_id in selected_role_ids:
                role = Role.query.get(int(role_id))
                if role:
                    new_roles.append(role)

            # Ensure at least the 'user' role is assigned
            if not new_roles:
                user_role = Role.query.filter_by(name="user").first()
                if user_role:
                    new_roles.append(user_role)

            # Prevent users from removing their own admin privileges (safety check)
            if user.id == current_user.id:
                current_has_admin = any(
                    role.name in ["admin", "super-admin"] for role in user.roles
                )
                new_has_admin = any(
                    role.name in ["admin", "super-admin"] for role in new_roles
                )

                if current_has_admin and not new_has_admin:
                    flash(
                        "Warning: You cannot remove your own admin privileges. Admin role retained.",
                        "warning",
                    )
                    admin_role = Role.query.filter_by(name="admin").first()
                    if admin_role and admin_role not in new_roles:
                        new_roles.append(admin_role)

            user.roles = new_roles

        db.session.commit()
        flash(f"User {user.username} updated successfully!", "success")
        return redirect(url_for("admin_users"))

    return render_template(
        "admin/edit_user.html", form=form, user=user, all_roles=all_roles
    )


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@super_admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin_users"))

    # Check if user has any dependencies
    if user.pets.count() > 0 or user.owned_tags.count() > 0:
        flash(
            "Cannot delete user with existing pets or tags. Transfer ownership first.",
            "error",
        )
        return redirect(url_for("admin_users"))

    db.session.delete(user)
    db.session.commit()

    flash(f"User {user.username} deleted successfully.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/settings/add", methods=["POST"])
@super_admin_required
def add_setting():
    key = request.form.get("key")
    value = request.form.get("value")
    description = request.form.get("description")

    if not key or not value:
        flash("Key and value are required.", "error")
        return redirect(url_for("admin_settings"))

    # Check if setting already exists
    existing = SystemSetting.query.filter_by(key=key).first()
    if existing:
        flash("Setting already exists.", "error")
        return redirect(url_for("admin_settings"))

    setting = SystemSetting(key=key, value=value, description=description)
    db.session.add(setting)
    db.session.commit()

    flash("Setting added successfully!", "success")
    return redirect(url_for("admin_settings"))


@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    """System settings management"""
    if request.method == "POST":
        gateway_updated = False

        # Get all boolean settings that might not be in form data when unchecked
        # Include common boolean setting patterns
        boolean_settings = ["smtp_enabled", "smtp_use_tls", "registration_enabled"]

        # Also check for any settings that look like booleans from the form
        for key in request.form.keys():
            if key.startswith("setting_"):
                setting_key = key.replace("setting_", "")
                if (
                    setting_key.endswith("_enabled")
                    or setting_key.endswith("_allow")
                    or setting_key.endswith("_disable")
                    or "enabled" in setting_key.lower()
                    or "allow" in setting_key.lower()
                    or "disable" in setting_key.lower()
                ):
                    if setting_key not in boolean_settings:
                        boolean_settings.append(setting_key)

        # Handle system settings updates
        processed_settings = set()
        for key, value in request.form.items():
            if key.startswith("setting_"):
                setting_key = key.replace("setting_", "")
                setting = SystemSetting.query.filter_by(key=setting_key).first()
                if setting:
                    # For boolean settings, ensure we handle the actual checkbox value
                    if setting_key in boolean_settings:
                        # If this is the hidden field with value 'false', check if checkbox is also present
                        if (
                            value == "false"
                            and f"setting_{setting_key}" not in processed_settings
                        ):
                            # Check if the checkbox version exists in form
                            checkbox_values = request.form.getlist(
                                f"setting_{setting_key}"
                            )
                            setting.value = (
                                "true" if "true" in checkbox_values else "false"
                            )
                        elif value == "true":
                            setting.value = "true"
                    else:
                        setting.value = value
                    setting.updated_at = datetime.utcnow()
                    processed_settings.add(f"setting_{setting_key}")
            elif key.startswith("gateway_"):
                # Handle payment gateway enable/disable
                gateway_name = key.replace("gateway_", "")
                gateway = PaymentGateway.query.filter_by(name=gateway_name).first()
                if gateway:
                    old_enabled = gateway.enabled
                    gateway.enabled = value == "true"
                    gateway.updated_at = datetime.utcnow()
                    if old_enabled != gateway.enabled:
                        gateway_updated = True

        db.session.commit()

        # Reconfigure payment gateways if any were updated
        if gateway_updated:
            configure_payment_gateways()

        flash("Settings updated successfully!", "success")
        return redirect(url_for("admin_settings"))

    settings = SystemSetting.query.all()
    gateways = PaymentGateway.query.all()
    return render_template("admin/settings.html", settings=settings, gateways=gateways)


@app.route("/admin/subscriptions/edit/<int:subscription_id>", methods=["GET", "POST"])
@super_admin_required
def edit_subscription(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)
    form = AddSubscriptionForm(obj=subscription)

    # Populate user choices
    users = User.query.all()
    form.user_id.choices = [(u.id, f"{u.username} ({u.email})") for u in users]

    if form.validate_on_submit():
        subscription.subscription_type = form.subscription_type.data
        subscription.end_date = form.end_date.data
        subscription.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Subscription updated successfully!", "success")
        return redirect(url_for("admin_subscriptions"))

    return render_template(
        "admin/edit_subscription.html", form=form, subscription=subscription
    )


@app.route("/admin/subscriptions/cancel/<int:subscription_id>", methods=["POST"])
@super_admin_required
def cancel_subscription_admin(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)

    subscription.status = "cancelled"
    subscription.updated_at = datetime.utcnow()
    db.session.commit()

    flash("Subscription cancelled successfully.", "success")
    return redirect(url_for("admin_subscriptions"))


@app.route("/customer/subscriptions")
@login_required
def customer_subscriptions():
    """Customer subscription management page"""
    subscriptions = (
        Subscription.query.filter_by(user_id=current_user.id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    return render_template("customer/subscriptions.html", subscriptions=subscriptions)


@app.route("/customer/subscriptions/cancel/<int:subscription_id>", methods=["POST"])
@login_required
def cancel_subscription(subscription_id):
    """Request cancellation of a subscription"""
    subscription = Subscription.query.filter_by(
        id=subscription_id, user_id=current_user.id
    ).first_or_404()

    if not subscription.can_be_cancelled():
        flash("This subscription cannot be cancelled at this time.", "error")
        return redirect(url_for("customer_subscriptions"))

    try:
        subscription.request_cancellation()
        db.session.commit()

        flash(
            "Your subscription cancellation has been requested. Your subscription will remain active until the end of the current billing period.",
            "info",
        )

        # TODO: Send cancellation confirmation email

    except Exception as e:
        db.session.rollback()
        flash("Error processing cancellation request. Please try again.", "error")
        logger.error(f"Error cancelling subscription {subscription_id}: {str(e)}")

    return redirect(url_for("customer_subscriptions"))


@app.route("/customer/subscriptions/reactivate/<int:subscription_id>", methods=["POST"])
@login_required
def reactivate_subscription(subscription_id):
    """Reactivate a cancelled subscription"""
    subscription = Subscription.query.filter_by(
        id=subscription_id, user_id=current_user.id
    ).first_or_404()

    if not subscription.cancellation_requested or subscription.status != "active":
        flash("This subscription cannot be reactivated.", "error")
        return redirect(url_for("customer_subscriptions"))

    try:
        subscription.cancellation_requested = False
        subscription.auto_renew = True
        subscription.updated_at = datetime.utcnow()
        db.session.commit()

        flash(
            "Your subscription has been reactivated and will continue to auto-renew.",
            "success",
        )

    except Exception as e:
        db.session.rollback()
        flash("Error reactivating subscription. Please try again.", "error")
        logger.error(f"Error reactivating subscription {subscription_id}: {str(e)}")

    return redirect(url_for("customer_subscriptions"))


# Payment transaction views
@app.route("/customer/payments")
@login_required
def customer_payments():
    """Customer payment history page"""
    payments = (
        Payment.query.filter_by(user_id=current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return render_template("customer/payments.html", payments=payments)


# Admin payment management
@app.route("/admin/payments")
@admin_required
def admin_payments():
    """Admin payment management page"""
    search = request.args.get("search", "")
    query = Payment.query

    if search:
        search_filter = f"%{search}%"
        query = query.join(User).filter(
            db.or_(
                User.username.ilike(search_filter),
                User.email.ilike(search_filter),
                Payment.transaction_id.ilike(search_filter),
                Payment.payment_intent_id.ilike(search_filter),
                Payment.status.ilike(search_filter),
            )
        )

    payments = query.order_by(Payment.created_at.desc()).all()
    return render_template("admin/payments.html", payments=payments, search=search)


# Admin subscription management improvements
@app.route("/admin/subscriptions/manage")
@admin_required
def admin_subscriptions_manage():
    """Admin manage subscriptions page"""
    subscriptions = Subscription.query.order_by(Subscription.created_at.desc()).all()
    return render_template(
        "admin/manage_subscriptions.html", subscriptions=subscriptions
    )


@app.route("/admin/subscriptions/<int:subscription_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_subscription(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)
    form = EditSubscriptionForm(obj=subscription)

    if form.validate_on_submit():
        subscription.status = form.status.data
        subscription.end_date = form.end_date.data
        subscription.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Subscription updated successfully!", "success")
        return redirect(url_for("admin_subscriptions_manage"))

    return render_template(
        "admin/edit_subscription.html", form=form, subscription=subscription
    )


@app.route("/admin/subscriptions/<int:subscription_id>/cancel", methods=["POST"])
@admin_required
def admin_cancel_subscription(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.status == "cancelled":
        flash("Subscription is already cancelled.", "info")
        return redirect(url_for("admin_subscriptions_manage"))

    try:
        subscription.status = "cancelled"
        subscription.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Subscription cancelled successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling subscription: {str(e)}", "error")

    return redirect(url_for("admin_subscriptions_manage"))


@app.route("/admin/subscriptions/<int:subscription_id>/reactivate", methods=["POST"])
@admin_required
def admin_reactivate_subscription(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.status == "active":
        flash("Subscription is already active.", "info")
        return redirect(url_for("admin_subscriptions_manage"))

    try:
        subscription.status = "active"
        subscription.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Subscription reactivated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error reactivating subscription: {str(e)}", "error")

    return redirect(url_for("admin_subscriptions_manage"))


@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection using SQLAlchemy text() function
        from sqlalchemy import text

        db.session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500


def get_smtp_settings():
    """Get SMTP settings from database"""
    try:
        settings = {}
        smtp_keys = [
            "smtp_enabled",
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email",
            "smtp_use_tls",
        ]

        for key in smtp_keys:
            setting = SystemSetting.get_value(key)
            if setting is not None:
                settings[key] = setting

        return settings
    except Exception as e:
        logger.error(f"Failed to get SMTP settings: {str(e)}")
        return {}


def send_notification_email(owner, tag, pet):
    """Send notification email when tag is searched"""
    try:
        # Get SMTP settings from database
        smtp_settings = get_smtp_settings()

        # Check if SMTP is enabled
        if not smtp_settings.get("smtp_enabled", False):
            logger.info("SMTP is disabled, skipping email notification")
            return

        # Validate required settings
        required_fields = [
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email",
        ]
        for field in required_fields:
            if not smtp_settings.get(field):
                logger.error(f"SMTP setting {field} is not configured")
                return

        msg = MIMEMultipart()
        msg["From"] = smtp_settings["smtp_from_email"]
        msg["To"] = owner.email
        msg["Subject"] = f"Your pet {pet.name}'s tag was searched"

        body = f"""
        Hello {owner.first_name},
        
        Your pet {pet.name}'s tag ({tag.tag_id}) was searched on our website.
        
        This could mean someone found your pet! Check your dashboard for more details.
        
        Best regards,
        LTFPQRR Team
        """

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(
            smtp_settings["smtp_server"], int(smtp_settings["smtp_port"])
        )
        if smtp_settings.get("smtp_use_tls", True):
            server.starttls()
        server.login(smtp_settings["smtp_username"], smtp_settings["smtp_password"])
        server.send_message(msg)
        server.quit()

    except Exception as e:
        logger.error(f"Failed to send notification email: {str(e)}")


def send_contact_email(owner, pet, finder_name, finder_email, message):
    """Send contact email from finder to owner"""
    try:
        # Get SMTP settings from database
        smtp_settings = get_smtp_settings()

        # Check if SMTP is enabled
        if not smtp_settings.get("smtp_enabled", False):
            logger.info("SMTP is disabled, skipping contact email")
            return

        # Validate required settings
        required_fields = [
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email",
        ]
        for field in required_fields:
            if not smtp_settings.get(field):
                logger.error(f"SMTP setting {field} is not configured")
                return

        msg = MIMEMultipart()
        msg["From"] = smtp_settings["smtp_from_email"]
        msg["To"] = owner.email
        msg["Subject"] = f"Someone found your pet {pet.name}!"

        body = f"""
        Hello {owner.first_name},
        
        Someone found your pet {pet.name} and sent you a message:
        
        Finder: {finder_name}
        Email: {finder_email}
        Message: {message}
        
        Please contact them as soon as possible!
        
        Best regards,
        LTFPQRR Team
        """

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(
            smtp_settings["smtp_server"], int(smtp_settings["smtp_port"])
        )
        if smtp_settings.get("smtp_use_tls", True):
            server.starttls()
        server.login(smtp_settings["smtp_username"], smtp_settings["smtp_password"])
        server.send_message(msg)
        server.quit()

    except Exception as e:
        logger.error(f"Failed to send contact email: {str(e)}")


def init_db():
    """Initialize database with roles and system settings"""
    db.create_all()

    # Create roles
    roles = ["user", "admin", "super-admin"]
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name)
            db.session.add(role)

    # Create system settings
    default_settings = {
        "registration_enabled": "true",
        "site_name": "LTFPQRR - Lost Then Found Pet QR Registry",
        "contact_email": "admin@ltfpqrr.com",
        # SMTP Email Settings
        "smtp_enabled": "false",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": "587",
        "smtp_username": "",
        "smtp_password": "",
        "smtp_from_email": "",
        "smtp_use_tls": "true",
    }

    for key, value in default_settings.items():
        if not SystemSetting.query.filter_by(key=key).first():
            setting = SystemSetting(key=key, value=value)
            db.session.add(setting)

    # Initialize payment gateways
    gateways = [
        {"name": "stripe", "enabled": False, "environment": "sandbox"},
        {"name": "paypal", "enabled": False, "environment": "sandbox"},
    ]

    for gateway_data in gateways:
        if not PaymentGateway.query.filter_by(name=gateway_data["name"]).first():
            gateway = PaymentGateway(
                name=gateway_data["name"],
                enabled=gateway_data["enabled"],
                environment=gateway_data["environment"],
            )
            db.session.add(gateway)

    db.session.commit()

    # Configure payment gateways from database
    configure_payment_gateways()


def generate_qr_code(tag_id, size=(200, 200)):
    """Generate QR code for a tag ID"""
    try:
        # Create the URL that the QR code will point to
        base_url = os.environ.get("BASE_URL", "http://localhost:8000")
        qr_url = f"{base_url}/found/{tag_id}"

        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Add data to QR code
        qr.add_data(qr_url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize(size)

        # Save to BytesIO
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        return img_buffer.getvalue()
    except Exception as e:
        app.logger.error(f"Error generating QR code: {str(e)}")
        return None


@app.route("/tag/<tag_id>/qr")
def tag_qr_code(tag_id):
    """Generate and serve QR code for a tag"""
    tag = Tag.query.filter_by(tag_id=tag_id).first()
    if not tag:
        flash("Tag not found", "error")
        return redirect(url_for("index"))

    # Check if user has permission to view this QR code
    if not current_user.is_authenticated:
        flash("Please log in to view QR codes", "error")
        return redirect(url_for("login"))

    if tag.partner_id != current_user.id and not current_user.has_role("admin"):
        if not tag.pet or tag.pet.owner_id != current_user.id:
            flash("You do not have permission to view this QR code", "error")
            return redirect(url_for("dashboard"))

    # Generate QR code
    qr_data = generate_qr_code(tag_id)
    if not qr_data:
        flash("Error generating QR code", "error")
        return redirect(url_for("dashboard"))

    return app.response_class(qr_data, mimetype="image/png")


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("404.html"), 500


@app.route("/admin/test-email", methods=["POST"])
@admin_required
def test_email():
    """Send a test email to verify SMTP settings"""
    try:
        test_email_address = request.form.get("test_email")
        if not test_email_address:
            flash("Please provide a test email address.", "error")
            return redirect(url_for("admin_settings"))

        # Get SMTP settings from database
        smtp_settings = get_smtp_settings()

        # Check if SMTP is enabled
        if not smtp_settings.get("smtp_enabled", False):
            flash("SMTP is disabled. Please enable it first.", "error")
            return redirect(url_for("admin_settings"))

        # Validate required settings
        required_fields = [
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email",
        ]
        for field in required_fields:
            if not smtp_settings.get(field):
                flash(f"SMTP setting {field} is not configured.", "error")
                return redirect(url_for("admin_settings"))

        # Create test email
        msg = MIMEMultipart()
        msg["From"] = smtp_settings["smtp_from_email"]
        msg["To"] = test_email_address
        msg["Subject"] = "LTFPQRR SMTP Test Email"

        body = f"""
        Hello,
        
        This is a test email from your LTFPQRR application to verify that your SMTP settings are working correctly.
        
        SMTP Configuration:
        - Server: {smtp_settings['smtp_server']}
        - Port: {smtp_settings['smtp_port']}
        - TLS: {'Enabled' if smtp_settings.get('smtp_use_tls', False) else 'Disabled'}
        - From Email: {smtp_settings['smtp_from_email']}
        
        If you received this email, your SMTP configuration is working properly!
        
        Best regards,
        LTFPQRR System
        """

        msg.attach(MIMEText(body, "plain"))

        # Send email
        server = smtplib.SMTP(
            smtp_settings["smtp_server"], int(smtp_settings["smtp_port"])
        )
        if smtp_settings.get("smtp_use_tls", False):
            server.starttls()
        server.login(smtp_settings["smtp_username"], smtp_settings["smtp_password"])
        server.send_message(msg)
        server.quit()

        flash(f"Test email sent successfully to {test_email_address}!", "success")

    except Exception as e:
        flash(f"Failed to send test email: {str(e)}", "error")

    return redirect(url_for("admin_settings"))


# Stripe Payment Processing Routes
@app.route("/payment/stripe/create-intent", methods=["POST"])
@login_required
def create_stripe_payment_intent():
    """Create a Stripe payment intent for processing payments"""
    try:
        data = request.get_json()
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
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata={
                "user_id": current_user.id,
                "payment_type": payment_type,
                "subscription_type": session.get("partner_subscription_type", ""),
                "claiming_tag_id": session.get("claiming_tag_id", "")
            }
        )
        
        return jsonify({
            "client_secret": intent.client_secret,
            "publishable_key": publishable_key
        })
        
    except Exception as e:
        logger.error(f"Error creating Stripe payment intent: {e}")
        return jsonify({"error": "Failed to create payment intent"}), 500


@app.route("/payment/paypal/create-order", methods=["POST"])
@login_required
def create_paypal_order():
    """Create a PayPal order for processing payments"""
    try:
        data = request.get_json()
        amount = data.get("amount", 0)
        currency = data.get("currency", "USD")
        payment_type = data.get("payment_type", "tag")
        
        # Get PayPal configuration
        paypal_gateway = PaymentGateway.query.filter_by(name="paypal", enabled=True).first()
        if not paypal_gateway or not paypal_gateway.client_id:
            return jsonify({"error": "PayPal payment gateway not configured"}), 400
        
        # Configure PayPal
        paypalrestsdk.configure({
            "mode": paypal_gateway.environment,
            "client_id": decrypt_value(paypal_gateway.client_id),
            "client_secret": decrypt_value(paypal_gateway.secret_key)
        })
        
        # Create PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": url_for("payment_success", _external=True),
                "cancel_url": url_for("partner_subscription", _external=True)
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"{payment_type.title()} Subscription",
                        "sku": f"{payment_type}_{session.get('partner_subscription_type', 'monthly')}",
                        "price": str(amount),
                        "currency": currency,
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(amount),
                    "currency": currency
                },
                "description": f"LTFPQRR {payment_type.title()} Subscription"
            }]
        })
        
        if payment.create():
            # Store payment ID in session
            session["paypal_payment_id"] = payment.id
            
            # Get approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            return jsonify({
                "payment_id": payment.id,
                "approval_url": approval_url
            })
        else:
            logger.error(f"PayPal payment creation failed: {payment.error}")
            return jsonify({"error": "Failed to create PayPal order"}), 500
        
    except Exception as e:
        logger.error(f"Error creating PayPal order: {e}")
        return jsonify({"error": "Failed to create PayPal order"}), 500


@app.route("/payment/stripe/webhook", methods=["POST"])
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


# PayPal Payment Processing Routes
@app.route("/payment/paypal/execute")
@login_required
def paypal_execute():
    """Execute PayPal payment after user approval"""
    try:
        payment_id = request.args.get("paymentId")
        payer_id = request.args.get("PayerID")

        if not payment_id or not payer_id:
            flash("Payment verification failed.", "error")
            return redirect(url_for("dashboard"))

        # Get PayPal configuration
        paypal_gateway = PaymentGateway.query.filter_by(
            name="paypal", enabled=True
        ).first()
        if not paypal_gateway:
            flash("PayPal not configured.", "error")
            return redirect(url_for("dashboard"))

        paypalrestsdk.configure(
            {
                "mode": paypal_gateway.environment,
                "client_id": decrypt_value(paypal_gateway.client_id),
                "client_secret": decrypt_value(paypal_gateway.secret_key),
            }
        )

        # Execute the payment
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            # Payment successful
            payment_type = session.get("paypal_payment_type")
            amount = session.get("paypal_amount")

            if payment_type and amount:
                process_successful_payment(
                    user_id=current_user.id,
                    payment_type=payment_type,
                    payment_method="paypal",
                    amount=float(amount),
                    payment_intent_id=payment_id,
                    claiming_tag_id=session.get("claiming_tag_id"),
                    subscription_type=session.get("subscription_type")
                    or session.get("partner_subscription_type"),
                )

            # Clean up session
            for key in ["paypal_payment_id", "paypal_payment_type", "paypal_amount"]:
                session.pop(key, None)

            return redirect(url_for("payment_success"))
        else:
            logger.error(f"PayPal payment execution failed: {payment.error}")
            flash("Payment execution failed.", "error")
            return redirect(url_for("dashboard"))

    except Exception as e:
        logger.error(f"PayPal payment execution failed: {str(e)}")
        flash("Payment processing failed.", "error")
        return redirect(url_for("dashboard"))


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
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found for payment processing")
            return False

        # Create payment record first
        payment = Payment(
            user_id=user_id,
            payment_gateway=payment_method,
            payment_intent_id=payment_intent_id,
            amount=amount,
            status="completed",
            payment_type=payment_type,
            metadata={
                "claiming_tag_id": claiming_tag_id,
                "subscription_type": subscription_type,
            },
        )
        payment.generate_transaction_id()
        payment.mark_completed()
        db.session.add(payment)
        db.session.flush()  # Get payment ID

        if payment_type == "tag" and claiming_tag_id:
            # Process tag subscription
            tag = Tag.query.filter_by(tag_id=claiming_tag_id).first()
            if tag:
                tag.owner_id = user_id
                tag.status = "claimed"

                # Find appropriate pricing plan
                pricing_plan = PricingPlan.query.filter_by(
                    subscription_type="tag",
                    billing_period=subscription_type,
                    enabled=True,
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

        elif payment_type == "partner":
            # Find appropriate pricing plan
            pricing_plan = PricingPlan.query.filter_by(
                subscription_type="partner",
                billing_period=subscription_type,
                enabled=True,
            ).first()

            # Process partner subscription
            subscription = Subscription(
                user_id=user_id,
                pricing_plan_id=pricing_plan.id if pricing_plan else None,
                subscription_type="partner",
                status="pending",  # Partner subscriptions need admin approval
                payment_method=payment_method,
                payment_id=payment_intent_id,
                amount=amount,
                start_date=datetime.utcnow(),
                auto_renew=True,
                max_tags=pricing_plan.max_tags if pricing_plan else 0,
            )

            # Set end date
            if subscription_type == "yearly":
                subscription.end_date = datetime.utcnow() + timedelta(days=365)
            else:  # monthly
                subscription.end_date = datetime.utcnow() + timedelta(days=30)

            db.session.add(subscription)
            db.session.flush()  # Get subscription ID

            # Link payment to subscription
            payment.subscription_id = subscription.id

            # Add partner role if not already present (pending approval)
            partner_role = Role.query.filter_by(name="partner").first()
            if partner_role and partner_role not in user.roles:
                user.roles.append(partner_role)

        db.session.commit()
        logger.info(
            f"Payment processed successfully for user {user_id}, type {payment_type}, amount ${amount}, transaction_id: {payment.transaction_id}"
        )
        return True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing payment: {str(e)}")
        raise
        return False


# Partner routes will be integrated directly into app.py to avoid conflicts


@app.route("/partner/create", methods=["GET", "POST"])
@login_required
def create_partner():
    if not current_user.has_partner_role():
        flash("Partner access required to create partner accounts.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        # Get form data
        company_name = request.form.get("company_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        
        # Validate required fields
        if not company_name or not email:
            flash("Company name and email are required.", "error")
            return render_template("partner/create.html")
        
        # Check if partner with this company name already exists
        existing_partner = Partner.query.filter_by(company_name=company_name).first()
        if existing_partner:
            flash("A partner with this company name already exists.", "error")
            return render_template("partner/create.html")
        
        # Create new partner
        try:
            partner = Partner(
                company_name=company_name,
                email=email,
                phone=phone,
                address=address,
                owner_id=current_user.id
            )
            db.session.add(partner)
            db.session.commit()
            
            flash(f"Partner '{company_name}' created successfully!", "success")
            # Redirect to partner dashboard with subscription prompt
            return redirect(url_for("partner_dashboard", partner_id=partner.id, prompt_subscription=1))
            
        except Exception as e:
            db.session.rollback()
            flash("Error creating partner. Please try again.", "error")
            return render_template("partner/create.html")
    
    return render_template("partner/create.html")


@app.route("/admin/partners")
@admin_required
def admin_partners():
    """Admin partner management page"""
    search = request.args.get("search", "")
    query = Partner.query
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                Partner.company_name.ilike(search_filter),
                Partner.email.ilike(search_filter),
                Partner.phone.ilike(search_filter)
            )
        )
    
    partners = query.order_by(Partner.created_at.desc()).all()
    return render_template("admin/partners.html", partners=partners, search=search)


@app.route("/admin/partners/<int:partner_id>")
@admin_required  
def admin_partner_detail(partner_id):
    """Admin view of partner details"""
    partner = Partner.query.get_or_404(partner_id)
    subscription = partner.get_active_subscription()
    tags = partner.tags.all()
    
    return render_template("admin/partner_detail.html", 
                         partner=partner, 
                         subscription=subscription,
                         tags=tags)


@app.route("/admin/partners/<int:partner_id>/suspend", methods=["POST"])
@admin_required
def admin_suspend_partner(partner_id):
    """Suspend/unsuspend a partner"""
    partner = Partner.query.get_or_404(partner_id)
    
    # Toggle suspended status
    partner.is_suspended = not getattr(partner, 'is_suspended', False)
    
    try:
        db.session.commit()
        status = "suspended" if partner.is_suspended else "reactivated"
        flash(f"Partner '{partner.company_name}' has been {status}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating partner status: {str(e)}", "error")
    
    return redirect(url_for("admin_partner_detail", partner_id=partner_id))

if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=False)
    