"""
Timezone-aware forms for user preferences
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from services.timezone_service import TimezoneService


class TimezonePreferenceForm(FlaskForm):
    """Form for user timezone preferences"""
    
    timezone = SelectField(
        'Timezone',
        choices=[],  # Will be populated dynamically
        validators=[DataRequired()],
        description='Select your preferred timezone for displaying dates and times'
    )
    
    submit = SubmitField('Update Timezone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate timezone choices
        self.timezone.choices = TimezoneService.get_timezone_choices()


class AdminTimezoneForm(FlaskForm):
    """Form for admin to set system-wide timezone defaults"""
    
    default_timezone = SelectField(
        'Default System Timezone',
        choices=[],
        validators=[DataRequired()],
        description='Default timezone for new users and system operations'
    )
    
    business_timezone = SelectField(
        'Business Hours Timezone',
        choices=[],
        validators=[DataRequired()],
        description='Timezone for business hours calculations'
    )
    
    submit = SubmitField('Update System Timezone Settings')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate with all available timezones for admin
        self.default_timezone.choices = TimezoneService.get_timezone_choices()
        self.business_timezone.choices = TimezoneService.get_timezone_choices()
