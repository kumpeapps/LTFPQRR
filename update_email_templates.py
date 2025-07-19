#!/usr/bin/env python3
"""
Update existing email templates to use new variable format
Replace legacy {variable} with new {{ model.field }} format while preserving HTML formatting
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.email.email_models import EmailTemplate
from extensions import db


def update_templates_to_new_format():
    """Update existing templates to use new variable format"""
    app = create_app()
    
    with app.app_context():
        # Variable mappings from legacy to new format
        variable_mappings = {
            # User variables
            '{user_name}': '{{ user.get_full_name() }}',
            '{first_name}': '{{ user.first_name }}',
            '{last_name}': '{{ user.last_name }}',
            '{user_email}': '{{ user.email }}',
            
            # Partner variables
            '{partner_name}': '{{ partner.company_name }}',
            '{partner_email}': '{{ partner.email }}',
            '{partner_phone}': '{{ partner.phone }}',
            '{partner_address}': '{{ partner.address }}',
            
            # Partner owner variables
            '{owner_name}': '{{ partner.owner.get_full_name() }}',
            '{owner_email}': '{{ partner.owner.email }}',
            '{owner_first_name}': '{{ partner.owner.first_name }}',
            '{owner_last_name}': '{{ partner.owner.last_name }}',
            
            # Subscription variables
            '{plan_name}': '{{ subscription.plan_name }}',
            '{amount}': '{{ subscription.amount }}',
            '{start_date}': '{{ subscription.start_date }}',
            '{end_date}': '{{ subscription.end_date }}',
            '{next_billing_date}': '{{ subscription.next_billing_date }}',
            '{max_tags}': '{{ subscription.max_tags }}',
            '{status}': '{{ subscription.status }}',
            
            # System variables
            '{app_name}': '{{ system.app_name }}',
            '{site_url}': '{{ system.site_url }}',
            '{support_email}': '{{ system.support_email }}',
            '{company_name}': '{{ system.app_name }}',
            
            # Payment variables
            '{refund_processed}': '{{ payment.refund_processed }}',
            '{refund_message}': '{{ payment.refund_message }}',
            '{payment_status}': '{{ payment.status }}',
            '{payment_method}': '{{ payment.method }}',
            
            # Pet/Tag variables
            '{pet_name}': '{{ pet.name }}',
            '{tag_id}': '{{ tag.id }}',
            '{tag_code}': '{{ tag.code }}',
            '{tag_url}': '{{ tag.url }}',
            
            # Found variables
            '{finder_name}': '{{ finder.name }}',
            '{finder_email}': '{{ finder.email }}',
            '{finder_phone}': '{{ finder.phone }}',
            '{found_location}': '{{ found.location }}',
            '{found_date}': '{{ found.date }}',
            '{found_message}': '{{ found.message }}'
        }
        
        # Get all existing templates
        templates = EmailTemplate.query.all()
        updated_count = 0
        
        print(f"Found {len(templates)} templates to update...")
        
        for template in templates:
            print(f"\nUpdating template: {template.name}")
            
            # Track if any changes were made
            changes_made = False
            
            # Update subject
            original_subject = template.subject
            new_subject = original_subject
            for old_var, new_var in variable_mappings.items():
                if old_var in new_subject:
                    new_subject = new_subject.replace(old_var, new_var)
                    changes_made = True
                    print(f"  Subject: {old_var} -> {new_var}")
            
            # Update HTML content
            original_html = template.html_content
            new_html = original_html
            for old_var, new_var in variable_mappings.items():
                if old_var in new_html:
                    new_html = new_html.replace(old_var, new_var)
                    changes_made = True
                    print(f"  HTML: {old_var} -> {new_var}")
            
            # Update text content
            original_text = template.text_content or ""
            new_text = original_text
            for old_var, new_var in variable_mappings.items():
                if old_var in new_text:
                    new_text = new_text.replace(old_var, new_var)
                    changes_made = True
                    print(f"  Text: {old_var} -> {new_var}")
            
            # Update template category if not set
            if not template.category:
                # Determine category based on template name
                if 'partner' in template.name.lower():
                    if 'subscription' in template.name.lower():
                        template.category = 'partner_subscription'
                    else:
                        template.category = 'partner_account'
                elif 'user' in template.name.lower():
                    template.category = 'user_account'
                elif 'found' in template.name.lower() or 'pet' in template.name.lower():
                    template.category = 'pet_found'
                elif 'admin' in template.name.lower():
                    template.category = 'admin_notification'
                else:
                    template.category = 'system_notification'
                
                print(f"  Set category: {template.category}")
                changes_made = True
            
            # Apply changes if any were made
            if changes_made:
                template.subject = new_subject
                template.html_content = new_html
                template.text_content = new_text
                updated_count += 1
                print(f"  ✅ Updated template: {template.name}")
            else:
                print(f"  ⏭️  No changes needed for: {template.name}")
        
        # Commit all changes
        if updated_count > 0:
            try:
                db.session.commit()
                print(f"\n✅ Successfully updated {updated_count} templates!")
                
                # Show sample of updated content
                print("\n📋 Sample updated template:")
                sample_template = templates[0] if templates else None
                if sample_template:
                    print(f"Template: {sample_template.name}")
                    print(f"Subject: {sample_template.subject[:100]}...")
                    print(f"HTML preview: {sample_template.html_content[:200]}...")
                
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error committing changes: {e}")
                return False
        else:
            print("\n⏭️  No templates needed updating")
        
        return True


def create_additional_default_templates():
    """Create additional default templates with new variable format"""
    app = create_app()
    
    with app.app_context():
        additional_templates = [
            {
                'name': 'user_registration_welcome',
                'subject': 'Welcome to {{ system.app_name }}!',
                'category': 'user_account',
                'description': 'Welcome email sent to new users',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to {{ system.app_name }}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{{ system.app_name }}</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Welcome {{ user.first_name }}!</h2>
        
        <p>Thank you for joining {{ system.app_name }}! We're excited to help you keep your pets safe.</p>
        
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h3 style="color: #155724; margin: 0 0 15px 0;">🎉 Your Account is Ready</h3>
            <p style="color: #155724; margin: 0;">You can now start creating QR tags for your pets!</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ system.site_url }}/dashboard" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Access Your Dashboard</a>
        </div>
        
        <p>If you have any questions, please contact us at <a href="mailto:{{ system.support_email }}">{{ system.support_email }}</a></p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Welcome {{ user.first_name }}!

Thank you for joining {{ system.app_name }}! We're excited to help you keep your pets safe.

🎉 Your Account is Ready
You can now start creating QR tags for your pets!

Access your dashboard: {{ system.site_url }}/dashboard

If you have any questions, please contact us at {{ system.support_email }}
                '''
            },
            {
                'name': 'pet_found_notification',
                'subject': 'Your pet {{ pet.name }} may have been found!',
                'category': 'pet_found',
                'description': 'Notification sent when someone scans a lost pet QR code',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Pet Found Notification</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
        <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{{ system.app_name }}</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Pet Found Alert</p>
    </div>
    
    <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin: 0 0 20px 0;">Great news {{ user.first_name }}!</h2>
        
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
            <h3 style="color: #155724; margin: 0 0 10px 0;">🐕 Someone found {{ pet.name }}!</h3>
            <p style="color: #155724; margin: 0;">A good Samaritan scanned your pet's QR tag.</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 20px 0;">Contact Information</h3>
            <p><strong>Finder:</strong> {{ finder.name }}</p>
            <p><strong>Phone:</strong> {{ finder.phone }}</p>
            <p><strong>Email:</strong> {{ finder.email }}</p>
            <p><strong>Location:</strong> {{ found.location }}</p>
            <p><strong>Found Date:</strong> {{ found.date }}</p>
            <p><strong>Message:</strong> {{ found.message }}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="tel:{{ finder.phone }}" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin: 5px;">Call Finder</a>
            <a href="mailto:{{ finder.email }}" style="background: linear-gradient(135deg, #007bff 0%, #6f42c1 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin: 5px;">Email Finder</a>
        </div>
        
        <p>Please contact the finder as soon as possible to arrange the safe return of {{ pet.name }}.</p>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Great news {{ user.first_name }}!

🐕 Someone found {{ pet.name }}!
A good Samaritan scanned your pet's QR tag.

Contact Information:
- Finder: {{ finder.name }}
- Phone: {{ finder.phone }}
- Email: {{ finder.email }}
- Location: {{ found.location }}
- Found Date: {{ found.date }}
- Message: {{ found.message }}

Please contact the finder as soon as possible to arrange the safe return of {{ pet.name }}.
                '''
            }
        ]
        
        from services.enhanced_email_service import EmailTemplateManager
        
        created_count = 0
        for template_data in additional_templates:
            try:
                # Check if template already exists
                existing = EmailTemplate.query.filter_by(name=template_data['name']).first()
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
                    category=template_data['category']
                )
                
                print(f"Created new template: {template_data['name']}")
                created_count += 1
                
            except Exception as e:
                print(f"Error creating template '{template_data['name']}': {e}")
        
        print(f"\nCreated {created_count} new templates with updated variable format")
        return True


if __name__ == '__main__':
    print("🔄 Updating email templates to new variable format...")
    print("=" * 60)
    
    # Update existing templates
    if update_templates_to_new_format():
        print("\n" + "=" * 60)
        print("✅ Template update completed successfully!")
        
        # Create additional templates
        print("\n🆕 Creating additional default templates...")
        create_additional_default_templates()
        
        print("\n" + "=" * 60)
        print("🎉 All template operations completed!")
        print("\n📋 Summary:")
        print("• Updated existing templates to use new {{ model.field }} format")
        print("• Preserved all HTML formatting and styling")
        print("• Added template categories for better organization")
        print("• Created additional default templates")
        print("\n💡 Templates now support:")
        print("• {{ user.first_name }}, {{ user.get_full_name() }}")
        print("• {{ partner.company_name }}, {{ partner.owner.email }}")
        print("• {{ subscription.plan_name }}, {{ subscription.amount }}")
        print("• {{ system.app_name }}, {{ system.site_url }}")
        print("• And many more model-based variables!")
    else:
        print("❌ Template update failed!")
        sys.exit(1)
