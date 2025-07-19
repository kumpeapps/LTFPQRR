from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, DecimalField, DateField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo, ValidationError
from models.models import User, Tag

# Helper function to get payment gateway choices
def get_payment_gateway_choices():
    """Get payment gateway choices from the database."""
    try:
        from models.models import PaymentGateway
        gateways = PaymentGateway.query.filter_by(enabled=True).all()
        choices = []
        for gateway in gateways:
            if gateway.name == 'stripe':
                choices.append(('stripe', 'Credit Card (Stripe)'))
            elif gateway.name == 'paypal':
                choices.append(('paypal', 'PayPal'))
        return choices
    except Exception:
        # Fallback to default choices
        return [('stripe', 'Credit Card (Stripe)'), ('paypal', 'PayPal')]

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class PetForm(FlaskForm):
    """Pet registration form."""
    name = StringField('Pet Name', validators=[DataRequired()])
    species = SelectField('Species', choices=[
        ('', 'Select Species'),
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('hamster', 'Hamster'),
        ('fish', 'Fish'),
        ('reptile', 'Reptile'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    breed = StringField('Breed')
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    color = StringField('Color')
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    vet_name = StringField('Veterinarian Name', validators=[Optional(), Length(max=100)])
    vet_phone = StringField('Veterinarian Phone', validators=[Optional(), Length(max=20)])
    vet_address = TextAreaField('Veterinarian Address', validators=[Optional()])
    vet_info_public = BooleanField('Make veterinarian information public')
    groomer_name = StringField('Groomer Name', validators=[Optional(), Length(max=100)])
    groomer_phone = StringField('Groomer Phone', validators=[Optional(), Length(max=20)])
    groomer_address = TextAreaField('Groomer Address', validators=[Optional()])
    groomer_info_public = BooleanField('Make groomer information public')
    phone_public = BooleanField('Make my phone number public', default=True)
    tag_id = SelectField('Assign to Tag', coerce=int, validators=[Optional()])

class TagForm(FlaskForm):
    # Simple form for tag creation - tag_id is auto-generated
    pass

class ClaimTagForm(FlaskForm):
    tag_id = StringField('Tag ID', validators=[DataRequired(), Length(min=1, max=20)])
    subscription_type = SelectField('Subscription Type', 
                                  choices=[('monthly', 'Monthly ($9.99/month)'), 
                                          ('yearly', 'Yearly ($99.99/year)'), 
                                          ('lifetime', 'Lifetime ($199.99)')], 
                                  validators=[DataRequired()])
    
    def validate_tag_id(self, field):
        from sqlalchemy import func
        tag = Tag.query.filter(func.upper(Tag.tag_id) == func.upper(field.data)).first()
        if not tag:
            raise ValidationError('Tag not found.')
        if tag.status != 'available':
            raise ValidationError('Tag is not available for claiming.')

class PurchaseSubscriptionForm(FlaskForm):
    """Form for purchasing subscriptions on existing owned tags"""
    subscription_type = SelectField('Subscription Type', 
                                  choices=[('monthly', 'Monthly ($9.99/month)'), 
                                          ('yearly', 'Yearly ($99.99/year)'), 
                                          ('lifetime', 'Lifetime ($199.99)')], 
                                  validators=[DataRequired()])

class TransferTagForm(FlaskForm):
    new_owner_username = StringField('New Owner Username', validators=[DataRequired(), Length(min=3, max=80)])
    
    def validate_new_owner_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError('User not found.')
        if not user.has_role('user'):
            raise ValidationError('Tags can only be transferred to customer accounts.')

class BatchTagCreateForm(FlaskForm):
    quantity = IntegerField('Number of Tags to Create', validators=[DataRequired(), NumberRange(min=1, max=100)])
    partner_id = SelectField('Partner', coerce=int, validators=[DataRequired()])

class BatchTagActionForm(FlaskForm):
    selected_tags = HiddenField('Selected Tags', validators=[DataRequired()])
    action = SelectField('Action', choices=[
        ('activate', 'Activate Tags'),
        ('deactivate', 'Deactivate Tags'),
        ('download_qr', 'Download QR Codes')
    ], validators=[DataRequired()])

class ContactOwnerForm(FlaskForm):
    finder_name = StringField('Your Name', validators=[DataRequired(), Length(max=100)])
    finder_email = StringField('Your Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])

class AddSubscriptionForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    subscription_type = SelectField('Subscription Type', 
                                  choices=[('monthly', 'Monthly'), 
                                          ('yearly', 'Yearly'), 
                                          ('lifetime', 'Lifetime'),
                                          ('partner', 'Partner')], 
                                  validators=[DataRequired()])
    end_date = DateField('End Date (optional for lifetime)', validators=[Optional()])

class PaymentForm(FlaskForm):
    payment_method = SelectField('Payment Method', 
                                choices=[], 
                                validators=[DataRequired()])
    
    # Stripe fields
    stripe_token = HiddenField()
    
    # PayPal fields
    paypal_payment_id = HiddenField()
    
    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.payment_method.choices = get_payment_gateway_choices()

class SystemSettingForm(FlaskForm):
    key = StringField('Setting Key', validators=[DataRequired(), Length(max=100)])
    value = StringField('Setting Value', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])

class PaymentGatewayForm(FlaskForm):
    name = SelectField('Payment Gateway', 
                      choices=[('stripe', 'Stripe'), 
                              ('paypal', 'PayPal')], 
                      validators=[DataRequired()])
    enabled = BooleanField('Enabled')
    
    # Stripe fields
    publishable_key = StringField('Publishable Key (Stripe)', validators=[Optional()])
    secret_key = StringField('Secret Key (Stripe/PayPal Client Secret)', validators=[Optional()])
    webhook_secret = StringField('Webhook Secret (Stripe)', validators=[Optional()])
    
    # PayPal fields
    client_id = StringField('Client ID (PayPal)', validators=[Optional()])
    
    # Legacy field (keeping for backward compatibility)
    api_key = StringField('API Key (Legacy)', validators=[Optional()])
    
    environment = SelectField('Environment', 
                             choices=[('sandbox', 'Sandbox'), 
                                     ('production', 'Production')], 
                             validators=[DataRequired()])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    timezone = SelectField('Timezone', choices=[], validators=[DataRequired()])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])

class CancelSubscriptionForm(FlaskForm):
    reason = TextAreaField('Reason for Cancellation (optional)', validators=[Optional(), Length(max=500)])
    confirm = BooleanField('I confirm that I want to cancel this subscription', validators=[DataRequired()])

class PartnerSubscriptionForm(FlaskForm):
    subscription_type = SelectField('Subscription Type', 
                                  choices=[('monthly', 'Monthly Partner ($29.99/month)'), 
                                          ('yearly', 'Yearly Partner ($299.99/year)')], 
                                  validators=[DataRequired()])
    payment_method = SelectField('Payment Method', 
                                choices=[], 
                                validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(PartnerSubscriptionForm, self).__init__(*args, **kwargs)
        self.payment_method.choices = get_payment_gateway_choices()

class PricingPlanForm(FlaskForm):
    name = StringField('Plan Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    plan_type = SelectField('Plan Type', 
                           choices=[('tag', 'Tag Plan'), ('partner', 'Partner Plan')], 
                           validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    currency = SelectField('Currency', 
                          choices=[('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')], 
                          default='USD',
                          validators=[DataRequired()])
    billing_period = SelectField('Billing Period', 
                                choices=[('monthly', 'Monthly'), ('yearly', 'Yearly'), ('one-time', 'One-time')], 
                                default='monthly',
                                validators=[DataRequired()])
    features = TextAreaField('Features (one per line)', validators=[Optional()])
    max_tags = IntegerField('Max Tags', validators=[NumberRange(min=0)], default=1)
    max_pets = IntegerField('Max Pets', validators=[NumberRange(min=1)], default=1)
    requires_approval = BooleanField('Requires Admin Approval')
    is_active = BooleanField('Active', default=True)
    is_featured = BooleanField('Featured Plan')
    show_on_homepage = BooleanField('Show on Homepage')
    sort_order = IntegerField('Sort Order', validators=[NumberRange(min=0)], default=0)

    def validate_max_tags(self, field):
        """Custom validation for max_tags based on plan type"""
        if self.plan_type.data == 'partner':
            if field.data is None or field.data < 0:
                raise ValidationError('Partner plans must specify the maximum number of tags allowed per subscription period (0 = unlimited, 1+ = specific limit).')
        
    def validate_max_pets(self, field):
        """Custom validation for max_pets based on plan type"""
        if self.plan_type.data == 'tag':
            if not field.data or field.data < 1:
                raise ValidationError('Tag plans must specify the maximum number of pets per tag (minimum 1).')

class EditSubscriptionForm(FlaskForm):
    """Form for editing subscriptions in admin panel"""
    status = SelectField('Status', 
                        choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('pending', 'Pending')],
                        validators=[DataRequired()])
    auto_renew = BooleanField('Auto Renew')
    admin_approved = BooleanField('Admin Approved')
    max_tags = IntegerField('Max Tags', validators=[NumberRange(min=0)], default=0)
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[Optional()])
    amount = DecimalField('Amount', validators=[Optional(), NumberRange(min=0)], places=2)
    payment_method = SelectField('Payment Method',
                                choices=[('stripe', 'Stripe'), ('paypal', 'PayPal'), ('manual', 'Manual')],
                                validators=[Optional()])
    notes = TextAreaField('Admin Notes', validators=[Optional()])
