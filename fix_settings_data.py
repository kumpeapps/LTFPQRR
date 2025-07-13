#!/usr/bin/env python3
"""
Script to fix corrupted system settings data.
Many text fields were set to 'false' because they were incorrectly treated as boolean checkboxes.
"""

from app import create_app
from models.system.system import SystemSetting
from extensions import db

def fix_settings_data():
    """Fix corrupted settings data by restoring proper default values."""
    
    app = create_app()
    with app.app_context():
        print("Fixing corrupted system settings data...")
        
        # Define proper default values for text fields that were corrupted
        default_values = {
            'site_name': 'LTFPQRR',
            'contact_email': 'admin@ltfpqrr.com',
            'site_description': 'Lost Tag Found Pet QR Registry & Recovery',
            'site_url': 'http://localhost:8000',
            'registration_type': 'open',
            'smtp_server': '',
            'smtp_port': '587',
            'smtp_username': '',
            'smtp_password': '',
            'smtp_from_email': '',
            'session_timeout': '30',
            'max_login_attempts': '5',
            'password_min_length': '8',
            'max_file_size': '5242880',  # 5MB in bytes
            'allowed_file_types': 'jpg,jpeg,png,gif,pdf',
            'maintenance_message': 'The site is temporarily down for maintenance. Please check back soon.'
        }
        
        fixed_count = 0
        for key, default_value in default_values.items():
            setting = SystemSetting.query.filter_by(key=key).first()
            if setting and setting.value == 'false':
                old_value = setting.value
                setting.value = default_value
                print(f"Fixed {key}: '{old_value}' -> '{default_value}'")
                fixed_count += 1
            elif setting:
                print(f"Skipped {key}: already has value '{setting.value}'")
            else:
                # Create the setting if it doesn't exist
                new_setting = SystemSetting(key=key, value=default_value)
                db.session.add(new_setting)
                print(f"Created {key}: '{default_value}'")
                fixed_count += 1
        
        # Commit all changes
        db.session.commit()
        print(f"\nFixed {fixed_count} settings.")
        
        # Show all settings after fix
        print("\nAll settings after fix:")
        settings = SystemSetting.query.all()
        for setting in settings:
            print(f"{setting.key}: {setting.value}")

if __name__ == '__main__':
    fix_settings_data()
