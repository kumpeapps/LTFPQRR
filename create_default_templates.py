#!/usr/bin/env python3
"""
Create default email templates with the new variable system
"""
from models.email.email_models import EmailTemplate
from extensions import db

def create_partner_subscription_template():
    """Create partner subscription approved email template"""
    
    # Check if template already exists
    existing = EmailTemplate.query.filter_by(name='partner_subscription_approved').first()
    if existing:
        print("Partner subscription approved template already exists")
        return
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{system.app_name}} - Partner Subscription Approved</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{{system.app_name}}</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    <div style="background: white; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="margin-bottom: 30px;">
            <h2 style="color: #333; margin: 0 0 10px 0; font-size: 1.8rem;">Hi {{user.first_name}},</h2>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <h3 style="color: #28a745; margin: 0 0 10px 0; font-size: 1.5rem;">Congratulations! Your Partner Subscription is Approved</h3>
            <p style="color: #666; margin: 0; font-size: 1.1rem;">Great news! Your partner subscription has been approved by our admin team. Welcome to the {{system.app_name}} partner network!</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h4 style="color: #333; margin: 0 0 20px 0; font-size: 1.3rem; text-align: center;">Subscription Details</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{partner.company_name}}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{subscription.plan_name}}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${{subscription.amount}}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{{subscription.start_date}}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Status:</td><td style="padding: 8px;"><strong>{{subscription.status}}</strong></td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{system.site_url}}/partner" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 1.1rem;">Access Partner Dashboard</a>
        </div>
        
        <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px; color: #666; font-size: 0.9rem; text-align: center;">
            <p>You can now start creating and managing QR tags for your partner business!</p>
            <p>If you have any questions, please contact us at <a href="mailto:{{system.support_email}}">{{system.support_email}}</a></p>
        </div>
    </div>
</body>
</html>"""

    text_content = """Hi {{user.first_name}},

Congratulations! Your Partner Subscription is Approved

Great news! Your partner subscription has been approved by our admin team. Welcome to the {{system.app_name}} partner network!

Subscription Details:
Partner: {{partner.company_name}}
Plan: {{subscription.plan_name}}
Amount: ${{subscription.amount}}
Start Date: {{subscription.start_date}}
Status: {{subscription.status}}

You can now access your partner dashboard and start creating and managing QR tags for your partner business!

Visit: {{system.site_url}}/partner

If you have any questions, please contact us at {{system.support_email}}

Best regards,
{{system.app_name}} Team"""

    template = EmailTemplate(
        name='partner_subscription_approved',
        subject='Partner Subscription Approved - Welcome to {{system.app_name}}!',
        html_content=html_content,
        text_content=text_content,
        description='Email sent when a partner subscription is approved by admin',
        variables=['user_name', 'first_name'],  # Legacy variables for backward compatibility
        is_active=True
    )
    
    db.session.add(template)
    
    try:
        db.session.commit()
        print("Partner subscription approved template created successfully!")
    except Exception as e:
        print(f"Error creating template: {e}")
        db.session.rollback()

if __name__ == '__main__':
    from app import app
    with app.app_context():
        create_partner_subscription_template()
