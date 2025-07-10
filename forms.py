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
    account_type = SelectField('Account Type', choices=[('customer', 'Customer'), ('partner', 'Partner')], validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class PetForm(FlaskForm):
    name = StringField('Pet Name', validators=[DataRequired(), Length(max=100)])
    breed = StringField('Breed', validators=[Optional(), Length(max=100)])
    color = StringField('Color', validators=[Optional(), Length(max=50)])
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    vet_name = StringField('Veterinarian Name', validators=[Optional(), Length(max=100)])
    vet_phone = StringField('Veterinarian Phone', validators=[Optional(), Length(max=20)])
    vet_address = TextAreaField('Veterinarian Address', validators=[Optional()])
    groomer_name = StringField('Groomer Name', validators=[Optional(), Length(max=100)])
    groomer_phone = StringField('Groomer Phone', validators=[Optional(), Length(max=20)])
    groomer_address = TextAreaField('Groomer Address', validators=[Optional()])
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
        tag = Tag.query.filter_by(tag_id=field.data).first()
        if not tag:
            raise ValidationError('Tag not found.')
        if tag.status != 'available':
            raise ValidationError('Tag is not available for claiming.')

class TransferTagForm(FlaskForm):
    new_owner_username = StringField('New Owner Username', validators=[DataRequired(), Length(min=3, max=80)])
    
    def validate_new_owner_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError('User not found.')
        if user.account_type != 'customer':
            raise ValidationError('Tags can only be transferred to customer accounts.')

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
    api_key = StringField('API Key', validators=[Optional()])
    secret_key = StringField('Secret Key', validators=[Optional()])
    webhook_secret = StringField('Webhook Secret', validators=[Optional()])
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
