#!/usr/bin/env python3
"""
Initialize default email templates for LTFPQRR
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.enhanced_email_service import EmailTemplateManager
from models.email.email_models import EmailTemplate
from extensions import logger


def create_default_templates():
    """Create default email templates"""
    app = create_app()
    
    with app.app_context():
        templates = [
            {
                'name': 'partner_subscription_confirmation',
                'subject': 'Partner Subscription Confirmed - {{ subscription.status }}',
                'description': 'Confirmation email sent when a partner subscription is created',
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
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{{ system.app_name }}</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Hi {{ user.first_name }},</h2>
        
        <p>Thank you for your partner subscription with {{ system.app_name }}!</p>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 20px 0;">Subscription Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{ partner.company_name }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{ subscription.pricing_plan.name }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${{ subscription.amount }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{{ subscription.start_date.strftime('%B %d, %Y') }}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{{ subscription.max_tags if subscription.max_tags > 0 else 'Unlimited' }}</td></tr>
            </table>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #856404; margin: 0 0 10px 0;">Status: {{ subscription.status.title() }}</h3>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ system.site_url }}/partner" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Access Partner Dashboard</a>
        </div>
        
        <p>If you have any questions, please contact us at <a href="mailto:{{ system.support_email }}">{{ system.support_email }}</a></p>
        <p>Thank you for choosing {{ system.app_name }}!</p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {{ user.first_name }},

Thank you for your partner subscription with {{ system.app_name }}!

Subscription Details:
- Partner: {{ partner.company_name }}
- Plan: {{ subscription.pricing_plan.name }}
- Amount: ${{ subscription.amount }}
- Start Date: {{ subscription.start_date.strftime('%B %d, %Y') }}
- Max Tags: {{ subscription.max_tags if subscription.max_tags > 0 else 'Unlimited' }}

Status: {{ subscription.status.title() }}

Access your partner dashboard: {{ system.site_url }}/partner

If you have any questions, please contact us at {{ system.support_email }}

Thank you for choosing {{ system.app_name }}!
                '''
            },
            {
                'name': 'partner_subscription_approved',
                'subject': 'Partner Subscription Approved - Welcome to LTFPQRR!',
                'description': 'Email sent when a partner subscription is approved by admin',
                'category': 'partner_subscription',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ system.app_name }} Partner Subscription Approved</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">{{ system.app_name }}</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Hi {{ user.first_name }},</h2>
        
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #155724; margin: 0 0 10px 0;">🎉 Congratulations! Your Partner Subscription is Approved</h3>
            <p style="color: #155724; margin: 0;">Welcome to the {{ system.app_name }} partner network!</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 20px 0;">Your Active Subscription</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{ partner.company_name }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{ subscription.pricing_plan.name }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${{ subscription.amount }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{{ subscription.start_date.strftime('%B %d, %Y') }}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{{ subscription.max_tags if subscription.max_tags > 0 else 'Unlimited' }}</td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ system.site_url }}/partner" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Access Partner Dashboard</a>
        </div>
        
        <p>You can now start creating and managing QR tags for your partner business!</p>
        <p>If you have any questions, please contact us at <a href="mailto:{{ system.support_email }}">{{ system.support_email }}</a></p>
        <p>Thank you for choosing {{ system.app_name }}!</p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {{ user.first_name }},

🎉 Congratulations! Your Partner Subscription is Approved

Welcome to the {{ system.app_name }} partner network!

Your Active Subscription:
- Partner: {{ partner.company_name }}
- Plan: {{ subscription.pricing_plan.name }}
- Amount: ${{ subscription.amount }}
- Start Date: {{ subscription.start_date.strftime('%B %d, %Y') }}
- Max Tags: {{ subscription.max_tags if subscription.max_tags > 0 else 'Unlimited' }}

Access your partner dashboard: {{ system.site_url }}/partner

You can now start creating and managing QR tags for your partner business!

If you have any questions, please contact us at {{ system.support_email }}

Thank you for choosing {{ system.app_name }}!
                '''
            },
            {
                'name': 'partner_subscription_rejected',
                'subject': 'Partner Subscription Update - Request Not Approved',
                'description': 'Email sent when a partner subscription is rejected by admin',
                'category': 'partner_subscription',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ system.app_name }} Partner Subscription Update</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Hi {{ user.first_name }},</h2>
        
        <p>We regret to inform you that your partner subscription request could not be approved at this time.</p>
        
        <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h3 style="color: #721c24; margin: 0 0 15px 0;">Subscription Request Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{{ partner.company_name }}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{{ subscription.pricing_plan.name }}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">${{ subscription.amount }}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Requested Date:</td><td style="padding: 8px;">{{ subscription.start_date.strftime('%B %d, %Y') }}</td></tr>
            </table>
        </div>
        
        {% if refund_processed %}
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h3 style="color: #155724; margin: 0 0 10px 0;">💰 Refund Processed</h3>
            <p style="color: #155724; margin: 0;">{{ refund_message | default('Your payment has been refunded to your original payment method.') }}</p>
        </div>
        {% endif %}
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="mailto:{{ system.support_email }}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Contact Support</a>
        </div>
        
        <p>If you have questions about this decision or would like to reapply, please contact our support team at <a href="mailto:{{ system.support_email }}">{{ system.support_email }}</a>.</p>
        <p>Thank you for your interest in LTFPQRR.</p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {{ user.first_name }},

We regret to inform you that your partner subscription request could not be approved at this time.

Subscription Request Details:
- Partner: {{ partner.company_name }}
- Plan: {{ subscription.pricing_plan.name }}
- Amount: ${{ subscription.amount }}
- Requested Date: {{ subscription.start_date.strftime('%B %d, %Y') }}

{% if refund_processed %}
💰 Refund Processed: {{ refund_message | default('Your payment has been refunded to your original payment method.') }}
{% endif %}

If you have questions about this decision or would like to reapply, please contact our support team:
{{ system.support_email }}

Thank you for your interest in {{ system.app_name }}.
                '''
            },
            {
                'name': 'admin_partner_approval_notification',
                'subject': 'New Partner Subscription Requires Approval',
                'description': 'Notification sent to admins when a partner subscription needs approval',
                'category': 'system_admin',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ system.app_name }} Admin Notification</title>
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
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{ partner.company_name }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Owner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{{ partner.owner.get_full_name() }} ({{ user.email }})</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{{ subscription.pricing_plan.name }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${{ subscription.amount }}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{{ subscription.start_date.strftime('%B %d, %Y') }}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{{ subscription.max_tags if subscription.max_tags > 0 else 'Unlimited' }}</td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ system.site_url }}/admin/partner-subscriptions" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Review Subscription</a>
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
- Partner: {{ partner.company_name }}
- Owner: {{ partner.owner.get_full_name() }} ({{ user.email }})
- Plan: {{ subscription.pricing_plan.name }}
- Amount: ${{ subscription.amount }}
- Start Date: {{ subscription.start_date.strftime('%B %d, %Y') }}
- Max Tags: {{ subscription.max_tags if subscription.max_tags > 0 else 'Unlimited' }}

Please review and approve this subscription in the admin panel:
{{ system.site_url }}/admin/partner-subscriptions

This is an automated notification from the {{ system.app_name }} system.
                '''
            },
            {
                'name': 'pet_search_notification',
                'subject': '🐾 Someone Found Your Pet {{ pet_name }}!',
                'description': 'Notification sent when someone scans a pet\'s QR tag',
                'category': 'user_notification',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ system.app_name }} - Pet Found Notification</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{{ system.app_name }}</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #28a745; margin: 0 0 20px 0;">🎉 Great News! Someone Found Your Pet!</h2>
        
        <p>Hi {{ owner_name }},</p>
        
        <p>Someone just scanned the QR code for <strong>{{ pet_name }}</strong>{% if tag_id %} (Tag ID: {{ tag_id }}){% endif %}!</p>
        
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #155724; margin: 0 0 10px 0;">🐾 {{ pet_name }} May Be Safe!</h3>
            <p style="color: #155724; margin: 0;">Someone is looking out for your pet right now.</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 20px 0;">What This Means</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>Someone found your pet and scanned their QR tag</li>
                <li>They now have access to your contact information</li>
                <li>They may reach out to you soon through our contact system</li>
                <li>Check your email for any direct messages from the finder</li>
            </ul>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h3 style="color: #856404; margin: 0 0 10px 0;">⚡ Next Steps</h3>
            <p style="color: #856404; margin: 0;">If {{ pet_name }} is missing, be ready to coordinate pickup. If they're safe at home, no action needed!</p>
        </div>
        
        {% if search_timestamp %}
        <p style="font-size: 14px; color: #666;">Scan detected at: {{ search_timestamp }}</p>
        {% endif %}
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ system.site_url }}/dashboard/customer" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">View Dashboard</a>
        </div>
        
        <p>We hope you're reunited with {{ pet_name }} soon!</p>
        
        <hr style="margin: 30px 0;">
        <p style="font-size: 12px; color: #666; text-align: center;">
            This is an automated notification from {{ system.app_name }}.<br>
            If you have questions, please contact us at <a href="mailto:{{ system.support_email }}">{{ system.support_email }}</a>
        </p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {{ owner_name }},

🎉 Great News! Someone Found Your Pet!

Someone just scanned the QR code for {{ pet_name }}{% if tag_id %} (Tag ID: {{ tag_id }}){% endif %}!

🐾 {{ pet_name }} May Be Safe!
Someone is looking out for your pet right now.

What This Means:
- Someone found your pet and scanned their QR tag
- They now have access to your contact information
- They may reach out to you soon through our contact system
- Check your email for any direct messages from the finder

⚡ Next Steps:
If {{ pet_name }} is missing, be ready to coordinate pickup. If they're safe at home, no action needed!

{% if search_timestamp %}
Scan detected at: {{ search_timestamp }}
{% endif %}

We hope you're reunited with {{ pet_name }} soon!

View your dashboard: {{ system.site_url }}/dashboard/customer

---
This is an automated notification from {{ system.app_name }}.
If you have questions, please contact us at {{ system.support_email }}
                '''
            },
            {
                'name': 'pet_found_contact',
                'subject': '🐾 Message About Your Pet {{ pet_name }} from {{ finder_name }}',
                'description': 'Contact message sent when someone finds a pet and wants to reach the owner',
                'category': 'user_notification',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ system.app_name }} - Pet Found Message</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{{ system.app_name }}</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #28a745; margin: 0 0 20px 0;">🎉 Someone Has a Message About Your Pet!</h2>
        
        <p>Hi {{ owner_name }},</p>
        
        <p>Someone who found <strong>{{ pet_name }}</strong> has sent you a message:</p>
        
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h3 style="color: #155724; margin: 0 0 15px 0;">📧 Contact Information</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; color: #666;">From:</td><td style="padding: 8px;"><strong>{{ finder_name }}</strong></td></tr>
                <tr><td style="padding: 8px; color: #666;">Email:</td><td style="padding: 8px;"><strong>{{ finder_email }}</strong></td></tr>
            </table>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 15px 0;">💬 Their Message</h3>
            <div style="background: white; padding: 15px; border-left: 4px solid #28a745; border-radius: 4px;">
                {{ message | replace('\n', '<br>') | safe }}
            </div>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #856404; margin: 0 0 10px 0;">📞 Reply Directly</h3>
            <p style="color: #856404; margin: 0;"><strong>You can reply directly to this email to contact {{ finder_name }}.</strong></p>
        </div>
        
        <div style="background: #e9ecef; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 15px 0;">🐾 Pet Information</h3>
            <p><strong>Name:</strong> {{ pet_name }}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="mailto:{{ finder_email }}" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Reply to {{ finder_name }}</a>
        </div>
        
        <p><strong>Please coordinate with {{ finder_name }} to safely retrieve your pet. We hope you're reunited soon!</strong></p>
        
        <hr style="margin: 30px 0;">
        <p style="font-size: 12px; color: #666; text-align: center;">
            This message was sent through {{ system.app_name }}.<br>
            Reply directly to this email to contact the finder, or email <a href="mailto:{{ system.support_email }}">{{ system.support_email }}</a> for support.
        </p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Hi {{ owner_name }},

🎉 Someone Has a Message About Your Pet!

Someone who found {{ pet_name }} has sent you a message:

📧 Contact Information:
- From: {{ finder_name }}
- Email: {{ finder_email }}

💬 Their Message:
{{ message }}

📞 Reply Directly:
You can reply directly to this email to contact {{ finder_name }}.

🐾 Pet Information:
- Name: {{ pet_name }}

Please coordinate with {{ finder_name }} to safely retrieve your pet. We hope you're reunited soon!

Reply to them: {{ finder_email }}

---
This message was sent through {{ system.app_name }}.
Reply directly to this email to contact the finder, or email {{ system.support_email }} for support.
                '''
            }
        ]
        
        created_count = 0
        for template_data in templates:
            try:
                # Check if template already exists
                existing = EmailTemplate.query.filter_by(name=template_data['name']).first()
                if existing:
                    print(f"Template '{template_data['name']}' already exists, skipping...")
                    continue
                
                # Create template using enhanced manager
                template = EmailTemplateManager.create_template(
                    name=template_data['name'],
                    subject=template_data['subject'],
                    html_content=template_data['html_content'],
                    text_content=template_data['text_content'],
                    description=template_data['description'],
                    category=template_data['category']
                )
                
                print(f"Created template: {template_data['name']} (category: {template_data['category']})")
                created_count += 1
                
            except Exception as e:
                print(f"Error creating template '{template_data['name']}': {e}")
                logger.error(f"Error creating template '{template_data['name']}': {e}")
        
        print(f"\nCreated {created_count} new email templates with enhanced variable system")
        return True


if __name__ == '__main__':
    create_default_templates()
