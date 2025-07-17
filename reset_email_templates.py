#!/usr/bin/env python3
"""
Reset and recreate email templates with new format
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.enhanced_email_service import EmailTemplateManager
from models.email.email_models import EmailTemplate
from extensions import db, logger


def reset_templates():
    """Delete and recreate templates"""
    app = create_app()
    
    with app.app_context():
        # Delete existing templates
        template_names = [
            'partner_subscription_confirmation',
            'partner_subscription_approved', 
            'partner_subscription_rejected',
            'admin_partner_approval_notification'
        ]
        
        for name in template_names:
            existing = EmailTemplate.query.filter_by(name=name).first()
            if existing:
                print(f"Deleting existing template: {name}")
                db.session.delete(existing)
        
        db.session.commit()
        print("Deleted old templates")
        
        # Now run the init script
        from init_email_templates import create_default_templates
        print("Creating new templates...")
        create_default_templates()


if __name__ == '__main__':
    reset_templates()
