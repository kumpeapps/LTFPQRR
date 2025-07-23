#!/usr/bin/env python3
"""
Script to force update existing email templates with the new logo content.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from extensions import db
from models.email.email_models import EmailTemplate

def update_templates_with_logo():
    """Update existing email templates with logo content"""
    
    # Read the template data directly from the file
    templates = [
        {
            'name': 'partner_subscription_confirmation',
            'subject': 'LTFPQRR Partner Subscription Confirmation',
            'description': 'Email sent when a partner submits a subscription request',
            'category': 'partner_subscription',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LTFPQRR Partner Subscription Confirmation</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <div style="margin-bottom: 20px;">
            <img src="cid:logo" alt="{{ system.app_name }} Logo" style="max-width: 80px; height: auto; border-radius: 8px;">
        </div>
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{{ system.app_name }}</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
'''
        }
    ]
    
    # For a simpler approach, let's just run a SQL update
    try:
        from sqlalchemy import text
        
        # Update all email templates to add logo to their HTML content
        updated_count = db.session.execute(text("""
            UPDATE email_template 
            SET html_content = REPLACE(
                html_content, 
                '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">',
                '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <div style="margin-bottom: 20px;">
            <img src="cid:logo" alt="{{ system.app_name }} Logo" style="max-width: 80px; height: auto; border-radius: 8px;">
        </div>'
            )
            WHERE html_content NOT LIKE '%cid:logo%'
        """)).rowcount
        
        db.session.commit()
        print(f"\nSuccessfully updated {updated_count} email templates with embedded logos!")
        return True
        
    except Exception as e:
        print(f"Error updating templates: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("Updating email templates with embedded logos...")
    
    # Initialize app context
    from app import app
    with app.app_context():
        success = update_templates_with_logo()
        if success:
            print("Email template update completed successfully!")
        else:
            print("Email template update failed!")
