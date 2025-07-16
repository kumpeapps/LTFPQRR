#!/usr/bin/env python3
"""
Initialize default email templates for LTFPQRR
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.email_service import EmailTemplateManager
from extensions import logger


def create_default_templates():
    """Create default email templates"""
    app = create_app()
    
    with app.app_context():
        templates = [
            {
                'name': 'partner_subscription_confirmation',
                'subject': 'Partner Subscription Confirmed - {status}',
                'description': 'Confirmation email sent when a partner subscription is created',
                'variables': ['user_name', 'first_name', 'partner_name', 'plan_name', 'amount', 'start_date', 'max_tags', 'status'],
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LTFPQRR Partner Subscription Confirmation</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Hi {first_name},</h2>
        
        <p>Thank you for your partner subscription with LTFPQRR!</p>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 20px 0;">Subscription Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{partner_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{plan_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${amount}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{start_date}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{max_tags}</td></tr>
            </table>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #856404; margin: 0 0 10px 0;">Status: {status}</h3>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:8000/partner" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Access Partner Dashboard</a>
        </div>
        
        <p>If you have any questions, please contact us at <a href="mailto:support@ltfpqrr.com">support@ltfpqrr.com</a></p>
        <p>Thank you for choosing LTFPQRR!</p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {first_name},

Thank you for your partner subscription with LTFPQRR!

Subscription Details:
- Partner: {partner_name}
- Plan: {plan_name}
- Amount: ${amount}
- Start Date: {start_date}
- Max Tags: {max_tags}

Status: {status}

Access your partner dashboard: http://localhost:8000/partner

If you have any questions, please contact us at support@ltfpqrr.com

Thank you for choosing LTFPQRR!
                '''
            },
            {
                'name': 'partner_subscription_approved',
                'subject': 'Partner Subscription Approved - Welcome to LTFPQRR!',
                'description': 'Email sent when a partner subscription is approved by admin',
                'variables': ['user_name', 'first_name', 'partner_name', 'plan_name', 'amount', 'start_date', 'max_tags'],
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LTFPQRR Partner Subscription Approved</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Hi {first_name},</h2>
        
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #155724; margin: 0 0 10px 0;">🎉 Congratulations! Your Partner Subscription is Approved</h3>
            <p style="color: #155724; margin: 0;">Welcome to the LTFPQRR partner network!</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 20px 0;">Your Active Subscription</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{partner_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{plan_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${amount}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{start_date}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{max_tags}</td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:8000/partner" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Access Partner Dashboard</a>
        </div>
        
        <p>You can now start creating and managing QR tags for your partner business!</p>
        <p>If you have any questions, please contact us at <a href="mailto:support@ltfpqrr.com">support@ltfpqrr.com</a></p>
        <p>Thank you for choosing LTFPQRR!</p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {first_name},

🎉 Congratulations! Your Partner Subscription is Approved

Welcome to the LTFPQRR partner network!

Your Active Subscription:
- Partner: {partner_name}
- Plan: {plan_name}
- Amount: ${amount}
- Start Date: {start_date}
- Max Tags: {max_tags}

Access your partner dashboard: http://localhost:8000/partner

You can now start creating and managing QR tags for your partner business!

If you have any questions, please contact us at support@ltfpqrr.com

Thank you for choosing LTFPQRR!
                '''
            },
            {
                'name': 'partner_subscription_rejected',
                'subject': 'Partner Subscription Update - Request Not Approved',
                'description': 'Email sent when a partner subscription is rejected by admin',
                'variables': ['user_name', 'first_name', 'partner_name', 'plan_name', 'amount', 'start_date', 'refund_processed', 'refund_message'],
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LTFPQRR Partner Subscription Update</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Hi {first_name},</h2>
        
        <p>We regret to inform you that your partner subscription request could not be approved at this time.</p>
        
        <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h3 style="color: #721c24; margin: 0 0 15px 0;">Subscription Request Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{partner_name}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{plan_name}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">${amount}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Requested Date:</td><td style="padding: 8px;">{start_date}</td></tr>
            </table>
        </div>
        
        {% if refund_processed == 'Yes' %}
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h3 style="color: #155724; margin: 0 0 10px 0;">💰 Refund Processed</h3>
            <p style="color: #155724; margin: 0;">{refund_message}</p>
        </div>
        {% endif %}
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="mailto:support@ltfpqrr.com" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Contact Support</a>
        </div>
        
        <p>If you have questions about this decision or would like to reapply, please contact our support team at <a href="mailto:support@ltfpqrr.com">support@ltfpqrr.com</a>.</p>
        <p>Thank you for your interest in LTFPQRR.</p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {first_name},

We regret to inform you that your partner subscription request could not be approved at this time.

Subscription Request Details:
- Partner: {partner_name}
- Plan: {plan_name}
- Amount: ${amount}
- Requested Date: {start_date}

{% if refund_processed == 'Yes' %}
💰 Refund Processed: {refund_message}
{% endif %}

If you have questions about this decision or would like to reapply, please contact our support team:
support@ltfpqrr.com

Thank you for your interest in LTFPQRR.
                '''
            },
            {
                'name': 'admin_partner_approval_notification',
                'subject': 'New Partner Subscription Requires Approval',
                'description': 'Notification sent to admins when a partner subscription needs approval',
                'variables': ['partner_name', 'user_name', 'user_email', 'plan_name', 'amount', 'start_date', 'max_tags'],
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LTFPQRR Admin Notification</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Admin Notification</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Hello Admin,</h2>
        
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #856404; margin: 0 0 10px 0;">⚡ Action Required</h3>
            <p style="color: #856404; margin: 0;">A new partner subscription requires your approval.</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 20px 0;">Subscription Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{partner_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Owner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{user_name} ({user_email})</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{plan_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${amount}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{start_date}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{max_tags}</td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:8000/admin/partner-subscriptions" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Review Subscription</a>
        </div>
        
        <p>Please review and approve this subscription in the admin panel.</p>
        <p><small>This is an automated notification from the LTFPQRR system.</small></p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hello Admin,

⚡ Action Required: A new partner subscription requires your approval.

Subscription Details:
- Partner: {partner_name}
- Owner: {user_name} ({user_email})
- Plan: {plan_name}
- Amount: ${amount}
- Start Date: {start_date}
- Max Tags: {max_tags}

Please review and approve this subscription in the admin panel:
http://localhost:8000/admin/partner-subscriptions

This is an automated notification from the LTFPQRR system.
                '''
            }
        ]
        
        created_count = 0
        for template_data in templates:
            try:
                # Check if template already exists
                existing = EmailTemplateManager.get_template(name=template_data['name'])
                if existing:
                    print(f"Template '{template_data['name']}' already exists, skipping...")
                    continue
                
                # Create template
                template = EmailTemplateManager.create_template(
                    name=template_data['name'],
                    subject=template_data['subject'],
                    html_content=template_data['html_content'],
                    text_content=template_data['text_content'],
                    description=template_data['description'],
                    variables=template_data['variables']
                )
                
                print(f"Created template: {template_data['name']}")
                created_count += 1
                
            except Exception as e:
                print(f"Error creating template '{template_data['name']}': {e}")
                logger.error(f"Error creating template '{template_data['name']}': {e}")
        
        print(f"\nCreated {created_count} new email templates")
        return True


if __name__ == '__main__':
    create_default_templates()
