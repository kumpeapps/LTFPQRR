"""
Timezone-related routes for user preferences
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from forms.timezone_forms import TimezonePreferenceForm
from services.timezone_service import TimezoneService
from models.system.system import SystemSetting

timezone_bp = Blueprint('timezone', __name__, url_prefix='/timezone')


@timezone_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """User timezone preferences page"""
    form = TimezonePreferenceForm()
    
    if form.validate_on_submit():
        try:
            # Update user's timezone preference
            current_user.timezone = form.timezone.data
            db.session.commit()
            
            # Also update session
            TimezoneService.set_user_timezone(form.timezone.data)
            
            flash('Timezone preference updated successfully!', 'success')
            return redirect(url_for('timezone.preferences'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating timezone preference. Please try again.', 'error')
    
    # Pre-populate form with current timezone
    if current_user.timezone:
        form.timezone.data = current_user.timezone
    else:
        form.timezone.data = 'UTC'
    
    return render_template('timezone/preferences.html', form=form)


@timezone_bp.route('/set', methods=['POST'])
@login_required
def set_timezone():
    """AJAX endpoint to set timezone"""
    timezone = request.json.get('timezone') if request.is_json else request.form.get('timezone')
    
    if not timezone:
        return jsonify({'error': 'Timezone not provided'}), 400
    
    try:
        # Validate timezone
        if not TimezoneService.set_user_timezone(timezone):
            return jsonify({'error': 'Invalid timezone'}), 400
        
        # Update user preference if logged in
        if current_user.is_authenticated:
            current_user.timezone = timezone
            db.session.commit()
        
        return jsonify({'success': True, 'timezone': timezone})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update timezone'}), 500


@timezone_bp.route('/detect', methods=['POST'])
def detect_timezone():
    """AJAX endpoint to detect and set timezone from browser"""
    timezone = request.json.get('timezone') if request.is_json else request.form.get('timezone')
    
    if not timezone:
        return jsonify({'error': 'Timezone not provided'}), 400
    
    try:
        if TimezoneService.set_user_timezone(timezone):
            return jsonify({'success': True, 'timezone': timezone})
        else:
            return jsonify({'error': 'Invalid timezone'}), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to set timezone'}), 500


@timezone_bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Admin timezone settings page"""
    # Check if user is admin
    if not current_user.has_role('admin') and not current_user.has_role('super-admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    from forms.timezone_forms import AdminTimezoneForm
    form = AdminTimezoneForm()
    
    if form.validate_on_submit():
        try:
            # Update system timezone settings
            default_tz_setting = SystemSetting.query.filter_by(key='default_timezone').first()
            if not default_tz_setting:
                default_tz_setting = SystemSetting(
                    key='default_timezone',
                    value=form.default_timezone.data,
                    description='Default timezone for new users'
                )
                db.session.add(default_tz_setting)
            else:
                default_tz_setting.value = form.default_timezone.data
            
            business_tz_setting = SystemSetting.query.filter_by(key='business_timezone').first()
            if not business_tz_setting:
                business_tz_setting = SystemSetting(
                    key='business_timezone',
                    value=form.business_timezone.data,
                    description='Timezone for business hours calculations'
                )
                db.session.add(business_tz_setting)
            else:
                business_tz_setting.value = form.business_timezone.data
            
            db.session.commit()
            flash('System timezone settings updated successfully!', 'success')
            return redirect(url_for('timezone.admin_settings'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating timezone settings. Please try again.', 'error')
    
    # Pre-populate form with current settings
    default_tz = SystemSetting.get_value('default_timezone', 'UTC')
    business_tz = SystemSetting.get_value('business_timezone', 'UTC')
    
    form.default_timezone.data = default_tz
    form.business_timezone.data = business_tz
    
    return render_template('timezone/admin_settings.html', form=form)
