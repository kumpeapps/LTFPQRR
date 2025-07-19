#!/usr/bin/env python3
"""
Initialize system settings for email templates
"""
from models.models import SystemSetting
from extensions import db

def initialize_system_settings():
    """Initialize basic system settings for email templates"""
    
    settings = [
        {
            'key': 'site_url',
            'value': 'https://www.lostthenfound.pet',
            'description': 'Main website URL'
        },
        {
            'key': 'app_name',
            'value': 'Lost Then Found Pet QR Registry',
            'description': 'Application name'
        },
        {
            'key': 'support_email',
            'value': 'support@lostthenfound.pet',
            'description': 'Support email address'
        },
        {
            'key': 'company_name',
            'value': 'Lost Then Found Pet QR Registry',
            'description': 'Company name'
        }
    ]
    
    for setting_data in settings:
        # Check if setting already exists
        existing = SystemSetting.query.filter_by(key=setting_data['key']).first()
        if not existing:
            setting = SystemSetting(
                key=setting_data['key'],
                value=setting_data['value'],
                description=setting_data['description']
            )
            db.session.add(setting)
            print(f"Added system setting: {setting_data['key']} = {setting_data['value']}")
        else:
            print(f"System setting already exists: {setting_data['key']} = {existing.value}")
    
    try:
        db.session.commit()
        print("System settings initialized successfully!")
    except Exception as e:
        print(f"Error initializing system settings: {e}")
        db.session.rollback()

if __name__ == '__main__':
    from app import app
    with app.app_context():
        initialize_system_settings()
