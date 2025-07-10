from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FileField, BooleanField, DecimalField
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
from flask_migrate import Migrate
from cryptography.fernet import Fernet
import base64
from celery import Celery
import qrcode
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ltfpqrr.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Encryption key for storing sensitive data
encryption_key_str = os.environ.get('ENCRYPTION_KEY')
if not encryption_key_str:
    # Generate a new key if not provided
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning("No ENCRYPTION_KEY provided, generated a new one. This should be set in production.")
else:
    # Convert string to bytes for Fernet
    ENCRYPTION_KEY = encryption_key_str.encode('utf-8')

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
        stripe_gateway = PaymentGateway.query.filter_by(name='stripe', enabled=True).first()
        if stripe_gateway and stripe_gateway.secret_key:
            stripe.api_key = decrypt_value(stripe_gateway.secret_key)
        
        # Configure PayPal
        paypal_gateway = PaymentGateway.query.filter_by(name='paypal', enabled=True).first()
        if paypal_gateway and paypal_gateway.api_key and paypal_gateway.secret_key:
            paypalrestsdk.configure({
                "mode": paypal_gateway.environment,
                "client_id": decrypt_value(paypal_gateway.api_key),
                "client_secret": decrypt_value(paypal_gateway.secret_key)
            })
    except Exception as e:
        logger.error(f"Error configuring payment gateways: {e}")
        # Fallback to environment variables if database configuration fails
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        paypalrestsdk.configure({
            "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),
            "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
            "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET')
        })

# Configure payment gateways (will be reconfigured from database after app starts)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
paypalrestsdk.configure({
    "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET')
})

# Import models and forms
from models.models import db, User, Role, Tag, Pet, Subscription, SearchLog, NotificationPreference, SystemSetting, PaymentGateway
from forms import *

# Initialize db with app
db.init_app(app)
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('admin'):
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('super-admin'):
            flash('You need super-admin privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Configure Celery
app.config['CELERY_BROKER_URL'] = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
celery = make_celery(app)

# Helper function to get enabled payment gateways
def get_enabled_payment_gateways():
    """Get a list of enabled payment gateways from the database."""
    try:
        gateways = PaymentGateway.query.filter_by(enabled=True).all()
        return [(gateway.name, gateway.name.title()) for gateway in gateways]
    except Exception as e:
        logger.error("Error getting enabled payment gateways: %s", str(e))
        # Fallback to default gateways
        return [('stripe', 'Stripe'), ('paypal', 'PayPal')]

# Helper function to encrypt and store payment gateway settings
def update_payment_gateway_settings(name, api_key=None, secret_key=None, webhook_secret=None, environment='sandbox', enabled=True):
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
        if webhook_secret:
            gateway.webhook_secret = cipher_suite.encrypt(webhook_secret.encode()).decode()
        
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
@app.route('/')
def index():
    # Handle tag search from homepage
    tag_id = request.args.get('tag_id')
    if tag_id:
        return redirect(url_for('found_pet', tag_id=tag_id))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if registration is enabled
        registration_enabled = SystemSetting.get_value('registration_enabled', True)
        if not registration_enabled:
            flash('Registration is currently disabled.', 'error')
            return redirect(url_for('login'))
        
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            address=form.address.data,
            account_type=form.account_type.data
        )
        
        # First user gets admin roles
        if User.query.count() == 0:
            user.roles = [
                Role.query.filter_by(name='user').first(),
                Role.query.filter_by(name='admin').first(),
                Role.query.filter_by(name='super-admin').first()
            ]
        else:
            user.roles = [Role.query.filter_by(name='user').first()]
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        
        flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.account_type == 'partner':
        return redirect(url_for('partner_dashboard'))
    else:
        return redirect(url_for('customer_dashboard'))

@app.route('/partner/dashboard')
@login_required
def partner_dashboard():
    if current_user.account_type != 'partner':
        flash('Partner access required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if partner has active subscription
    subscription = Subscription.query.filter_by(
        user_id=current_user.id,
        subscription_type='partner',
        status='active'
    ).first()
    
    if not subscription:
        flash('Active partner subscription required to create tags.', 'warning')
        return redirect(url_for('partner_subscription'))
    
    # Get partner's tags
    tags = Tag.query.filter_by(created_by=current_user.id).all()
    
    return render_template('partner/dashboard.html', tags=tags, subscription=subscription)

@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.account_type != 'customer':
        flash('Customer access required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get customer's claimed tags and pets
    tags = Tag.query.filter_by(owner_id=current_user.id).all()
    pets = Pet.query.filter_by(owner_id=current_user.id).all()
    
    return render_template('customer/dashboard.html', tags=tags, pets=pets)

@app.route('/partner/subscription')
@login_required
def partner_subscription():
    if current_user.account_type != 'partner':
        flash('Partner access required.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('partner/subscription.html')

@app.route('/tag/create', methods=['GET', 'POST'])
@login_required
def create_tag():
    if current_user.account_type != 'partner':
        flash('Partner access required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if partner has active subscription
    subscription = Subscription.query.filter_by(
        user_id=current_user.id,
        subscription_type='partner',
        status='active'
    ).first()
    
    if not subscription:
        flash('Active partner subscription required to create tags.', 'error')
        return redirect(url_for('partner_subscription'))
    
    form = TagForm()
    if form.validate_on_submit():
        tag = Tag(
            tag_id=str(uuid.uuid4())[:8].upper(),
            created_by=current_user.id,
            status='available'
        )
        db.session.add(tag)
        db.session.commit()
        
        flash(f'Tag {tag.tag_id} created successfully!', 'success')
        return redirect(url_for('partner_dashboard'))
    
    return render_template('tag/create.html', form=form)

@app.route('/tag/claim', methods=['GET', 'POST'])
@login_required
def claim_tag():
    if current_user.account_type != 'customer':
        flash('Customer access required.', 'error')
        return redirect(url_for('dashboard'))
    
    form = ClaimTagForm()
    if form.validate_on_submit():
        tag = Tag.query.filter_by(tag_id=form.tag_id.data).first()
        
        if not tag:
            flash('Tag not found.', 'error')
            return redirect(url_for('claim_tag'))
        
        if tag.status != 'available':
            flash('Tag is not available for claiming.', 'error')
            return redirect(url_for('claim_tag'))
        
        # Store tag_id and subscription_type in session for payment
        session['claiming_tag_id'] = tag.tag_id
        session['subscription_type'] = form.subscription_type.data
        
        return redirect(url_for('tag_payment'))
    
    return render_template('tag/claim.html', form=form)

@app.route('/tag/payment')
@login_required
def tag_payment():
    if 'claiming_tag_id' not in session:
        flash('No tag selected for claiming.', 'error')
        return redirect(url_for('claim_tag'))
    
    tag_id = session['claiming_tag_id']
    subscription_type = session['subscription_type']
    
    # Define pricing
    pricing = {
        'monthly': 9.99,
        'yearly': 99.99,
        'lifetime': 199.99
    }
    
    amount = pricing.get(subscription_type, 9.99)
    
    return render_template('tag/payment.html', 
                         tag_id=tag_id, 
                         subscription_type=subscription_type,
                         amount=amount)

@app.route('/pet/create', methods=['GET', 'POST'])
@login_required
def create_pet():
    if current_user.account_type != 'customer':
        flash('Customer access required.', 'error')
        return redirect(url_for('dashboard'))
    
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
            form.photo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
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
            owner_id=current_user.id
        )
        
        db.session.add(pet)
        db.session.commit()
        
        # Assign tag to pet
        if form.tag_id.data:
            tag = Tag.query.get(form.tag_id.data)
            if tag and tag.owner_id == current_user.id:
                tag.pet_id = pet.id
                db.session.commit()
        
        flash('Pet created successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('pet/create.html', form=form)

@app.route('/pet/edit/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    
    if pet.owner_id != current_user.id:
        flash('You can only edit your own pets.', 'error')
        return redirect(url_for('customer_dashboard'))
    
    # Check if pet is on a lifetime subscription and restrictions apply
    tag = Tag.query.filter_by(pet_id=pet.id).first()
    if tag:
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            tag_id=tag.id,
            subscription_type='lifetime',
            status='active'
        ).first()
        
        if subscription and subscription.restrictions_active:
            flash('Pet name and details cannot be changed on active lifetime subscription.', 'warning')
            return redirect(url_for('customer_dashboard'))
    
    form = PetForm(obj=pet)
    
    if form.validate_on_submit():
        # Handle file upload
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_filename = f"{uuid.uuid4()}_{photo_filename}"
            form.photo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            
            # Delete old photo if it exists
            if pet.photo:
                old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], pet.photo)
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
        
        flash('Pet updated successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('pet/edit.html', form=form, pet=pet)

@app.route('/found/<tag_id>')
def found_pet(tag_id):
    tag = Tag.query.filter_by(tag_id=tag_id).first_or_404()
    
    if not tag.pet_id:
        return render_template('found/not_registered.html', tag_id=tag_id)
    
    pet = Pet.query.get(tag.pet_id)
    owner = User.query.get(pet.owner_id)
    
    # Log the search
    search_log = SearchLog(
        tag_id=tag.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(search_log)
    db.session.commit()
    
    # Check if owner wants notifications
    notification_pref = NotificationPreference.query.filter_by(
        user_id=owner.id,
        notification_type='tag_search'
    ).first()
    
    if notification_pref and notification_pref.enabled:
        send_notification_email(owner, tag, pet)
    
    return render_template('found/pet_info.html', pet=pet, owner=owner, tag=tag)

@app.route('/found/<tag_id>/contact', methods=['GET', 'POST'])
def contact_owner(tag_id):
    tag = Tag.query.filter_by(tag_id=tag_id).first_or_404()
    
    if not tag.pet_id:
        flash('This tag is not registered to a pet.', 'error')
        return redirect(url_for('found_pet', tag_id=tag_id))
    
    pet = Pet.query.get(tag.pet_id)
    owner = User.query.get(pet.owner_id)
    
    form = ContactOwnerForm()
    if form.validate_on_submit():
        # Send email to owner
        send_contact_email(owner, pet, form.finder_name.data, 
                          form.finder_email.data, form.message.data)
        
        flash('Your message has been sent to the pet owner.', 'success')
        return redirect(url_for('found_pet', tag_id=tag_id))
    
    return render_template('found/contact.html', form=form, pet=pet, tag=tag)

@app.route('/tag/transfer/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def transfer_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    if tag.owner_id != current_user.id:
        flash('You can only transfer tags you own.', 'error')
        return redirect(url_for('customer_dashboard'))
    
    form = TransferTagForm()
    if form.validate_on_submit():
        new_owner = User.query.filter_by(username=form.new_owner_username.data).first()
        
        if not new_owner:
            flash('User not found.', 'error')
            return redirect(url_for('transfer_tag', tag_id=tag_id))
        
        if new_owner.account_type != 'customer':
            flash('Tags can only be transferred to customer accounts.', 'error')
            return redirect(url_for('transfer_tag', tag_id=tag_id))
        
        # Transfer the tag
        tag.owner_id = new_owner.id
        db.session.commit()
        
        flash(f'Tag {tag.tag_id} transferred to {new_owner.username} successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('tag/transfer.html', form=form, tag=tag)

@app.route('/settings/notifications')
@login_required
def notification_settings():
    preferences = NotificationPreference.query.filter_by(user_id=current_user.id).all()
    return render_template('settings/notifications.html', preferences=preferences)

@app.route('/settings/notifications/toggle/<notification_type>')
@login_required
def toggle_notification(notification_type):
    preference = NotificationPreference.query.filter_by(
        user_id=current_user.id,
        notification_type=notification_type
    ).first()
    
    if not preference:
        preference = NotificationPreference(
            user_id=current_user.id,
            notification_type=notification_type,
            enabled=True
        )
        db.session.add(preference)
    else:
        preference.enabled = not preference.enabled
    
    db.session.commit()
    
    flash(f'Notification preference updated.', 'success')
    return redirect(url_for('notification_settings'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_tags': Tag.query.count(),
        'active_subscriptions': Subscription.query.filter_by(status='active').count(),
        'total_pets': Pet.query.count()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/subscriptions')
@admin_required
def admin_subscriptions():
    subscriptions = Subscription.query.all()
    return render_template('admin/subscriptions.html', subscriptions=subscriptions)

@app.route('/admin/subscription/add', methods=['GET', 'POST'])
@super_admin_required
def add_subscription():
    form = AddSubscriptionForm()
    
    # Populate user choices
    users = User.query.all()
    form.user_id.choices = [(u.id, f"{u.username} ({u.email})") for u in users]
    
    if form.validate_on_submit():
        subscription = Subscription(
            user_id=form.user_id.data,
            subscription_type=form.subscription_type.data,
            status='active',
            start_date=datetime.utcnow(),
            end_date=form.end_date.data if form.end_date.data else None
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        flash('Subscription added successfully!', 'success')
        return redirect(url_for('admin_subscriptions'))
    
    return render_template('admin/add_subscription.html', form=form)

@app.route('/admin/settings')
@super_admin_required
def admin_settings():
    settings = SystemSetting.query.all()
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/settings/update', methods=['POST'])
@super_admin_required
def update_settings():
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            setting = SystemSetting.query.filter_by(key=setting_key).first()
            if setting:
                setting.value = value
                db.session.commit()
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/admin/payment-gateways')
@super_admin_required
def payment_gateways():
    gateways = PaymentGateway.query.all()
    return render_template('admin/payment_gateways.html', gateways=gateways)

@app.route('/admin/payment-gateways/edit/<int:gateway_id>', methods=['GET', 'POST'])
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
            webhook_secret=form.webhook_secret.data if form.webhook_secret.data else None,
            environment=form.environment.data,
            enabled=form.enabled.data
        )
        
        if success:
            flash(f'{gateway.name.title()} payment gateway updated successfully!', 'success')
        else:
            flash('Error updating payment gateway settings.', 'error')
        
        return redirect(url_for('payment_gateways'))
    
    return render_template('admin/edit_payment_gateway.html', form=form, gateway=gateway)

@app.route('/payment/success')
@login_required
def payment_success():
    """Handle successful payment"""
    if 'claiming_tag_id' in session:
        tag_id = session.pop('claiming_tag_id')
        subscription_type = session.pop('subscription_type', 'monthly')
        
        # In a real implementation, you would verify the payment here
        # For now, we'll just create the subscription
        tag = Tag.query.filter_by(tag_id=tag_id).first()
        if tag:
            tag.owner_id = current_user.id
            tag.status = 'claimed'
            
            # Create subscription
            subscription = Subscription(
                user_id=current_user.id,
                tag_id=tag.id,
                subscription_type=subscription_type,
                status='active',
                payment_method='stripe',  # default
                amount=9.99 if subscription_type == 'monthly' else (99.99 if subscription_type == 'yearly' else 199.99),
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365) if subscription_type == 'yearly' else (
                    datetime.utcnow() + timedelta(days=30) if subscription_type == 'monthly' else None
                )
            )
            db.session.add(subscription)
            db.session.commit()
            
            flash(f'Payment successful! Tag {tag_id} has been claimed.', 'success')
            return redirect(url_for('customer_dashboard'))
    
    flash('Payment completed successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/partner/subscription/payment', methods=['POST'])
@login_required
def partner_subscription_payment():
    if current_user.account_type != 'partner':
        flash('Partner access required.', 'error')
        return redirect(url_for('dashboard'))
    
    subscription_type = request.form.get('subscription_type')
    if subscription_type not in ['monthly', 'yearly']:
        flash('Invalid subscription type.', 'error')
        return redirect(url_for('partner_subscription'))
    
    # Store subscription info in session for payment processing
    session['partner_subscription_type'] = subscription_type
    
    # Define pricing for partner subscriptions
    partner_pricing = {
        'monthly': 29.99,
        'yearly': 299.99
    }
    
    amount = partner_pricing.get(subscription_type, 29.99)
    
    return render_template('partner/payment.html',
                         subscription_type=subscription_type,
                         amount=amount)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile/profile.html', user=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Email already in use by another account.', 'error')
            return render_template('profile/edit.html', form=form)
        
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.email = form.email.data
        current_user.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile/edit.html', form=form)

@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('profile/change_password.html', form=form)
        
        current_user.password_hash = generate_password_hash(form.new_password.data)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile/change_password.html', form=form)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = ProfileForm(obj=user)
    
    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.address = form.address.data
        user.email = form.email.data
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@super_admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    # Check if user has any dependencies
    if user.pets.count() > 0 or user.owned_tags.count() > 0:
        flash('Cannot delete user with existing pets or tags. Transfer ownership first.', 'error')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/settings/add', methods=['POST'])
@super_admin_required
def add_setting():
    key = request.form.get('key')
    value = request.form.get('value')
    description = request.form.get('description')
    
    if not key or not value:
        flash('Key and value are required.', 'error')
        return redirect(url_for('admin_settings'))
    
    # Check if setting already exists
    existing = SystemSetting.query.filter_by(key=key).first()
    if existing:
        flash('Setting already exists.', 'error')
        return redirect(url_for('admin_settings'))
    
    setting = SystemSetting(key=key, value=value, description=description)
    db.session.add(setting)
    db.session.commit()
    
    flash('Setting added successfully!', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/admin/subscriptions/edit/<int:subscription_id>', methods=['GET', 'POST'])
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
        flash('Subscription updated successfully!', 'success')
        return redirect(url_for('admin_subscriptions'))
    
    return render_template('admin/edit_subscription.html', form=form, subscription=subscription)

@app.route('/admin/subscriptions/cancel/<int:subscription_id>', methods=['POST'])
@super_admin_required
def cancel_subscription_admin(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)
    
    subscription.status = 'cancelled'
    subscription.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Subscription cancelled successfully.', 'success')
    return redirect(url_for('admin_subscriptions'))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection using SQLAlchemy text() function
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500

def send_notification_email(owner, tag, pet):
    """Send notification email when tag is searched"""
    try:
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('SMTP_FROM_EMAIL')
        msg['To'] = owner.email
        msg['Subject'] = f"Your pet {pet.name}'s tag was searched"
        
        body = f"""
        Hello {owner.first_name},
        
        Your pet {pet.name}'s tag ({tag.tag_id}) was searched on our website.
        
        This could mean someone found your pet! Check your dashboard for more details.
        
        Best regards,
        LTFPQRR Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(os.environ.get('SMTP_SERVER', 'localhost'), 587)
        server.starttls()
        server.login(os.environ.get('SMTP_USERNAME'), os.environ.get('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        logger.error(f"Failed to send notification email: {str(e)}")

def send_contact_email(owner, pet, finder_name, finder_email, message):
    """Send contact email from finder to owner"""
    try:
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('SMTP_FROM_EMAIL')
        msg['To'] = owner.email
        msg['Subject'] = f"Someone found your pet {pet.name}!"
        
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
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(os.environ.get('SMTP_SERVER', 'localhost'), 587)
        server.starttls()
        server.login(os.environ.get('SMTP_USERNAME'), os.environ.get('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        logger.error(f"Failed to send contact email: {str(e)}")

def init_db():
    """Initialize database with roles and system settings"""
    db.create_all()
    
    # Create roles
    roles = ['user', 'admin', 'super-admin']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name)
            db.session.add(role)
    
    # Create system settings
    default_settings = {
        'registration_enabled': 'true',
        'site_name': 'LTFPQRR - Lost Then Found Pet QR Registry',
        'contact_email': 'admin@ltfpqrr.com'
    }
    
    for key, value in default_settings.items():
        if not SystemSetting.query.filter_by(key=key).first():
            setting = SystemSetting(key=key, value=value)
            db.session.add(setting)
    
    # Initialize payment gateways
    gateways = [
        {'name': 'stripe', 'enabled': True, 'environment': 'sandbox'},
        {'name': 'paypal', 'enabled': True, 'environment': 'sandbox'}
    ]
    
    for gateway_data in gateways:
        if not PaymentGateway.query.filter_by(name=gateway_data['name']).first():
            gateway = PaymentGateway(
                name=gateway_data['name'],
                enabled=gateway_data['enabled'],
                environment=gateway_data['environment']
            )
            db.session.add(gateway)
    
    db.session.commit()
    
    # Configure payment gateways from database
    configure_payment_gateways()

def generate_qr_code(tag_id, size=(200, 200)):
    """Generate QR code for a tag ID"""
    try:
        # Create the URL that the QR code will point to
        base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
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
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
    except Exception as e:
        app.logger.error(f"Error generating QR code: {str(e)}")
        return None

@app.route('/tag/<tag_id>/qr')
def tag_qr_code(tag_id):
    """Generate and serve QR code for a tag"""
    tag = Tag.query.filter_by(tag_id=tag_id).first()
    if not tag:
        flash('Tag not found', 'error')
        return redirect(url_for('index'))
    
    # Check if user has permission to view this QR code
    if not current_user.is_authenticated:
        flash('Please log in to view QR codes', 'error')
        return redirect(url_for('login'))
    
    if tag.partner_id != current_user.id and not current_user.has_role('admin'):
        if not tag.pet or tag.pet.owner_id != current_user.id:
            flash('You do not have permission to view this QR code', 'error')
            return redirect(url_for('dashboard'))
    
    # Generate QR code
    qr_data = generate_qr_code(tag_id)
    if not qr_data:
        flash('Error generating QR code', 'error')
        return redirect(url_for('dashboard'))
    
    return app.response_class(qr_data, mimetype='image/png')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
