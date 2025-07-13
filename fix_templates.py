#!/usr/bin/env python3
"""
Script to fix template URL references after blueprint refactoring.
"""

import os
import re
import glob

# Define the mapping of old endpoints to new blueprint endpoints
ENDPOINT_MAPPING = {
    # Public routes
    "url_for('index')": "url_for('public.index')",
    "url_for('contact')": "url_for('public.contact')",
    "url_for('privacy')": "url_for('public.privacy')",
    "url_for('found_index')": "url_for('public.found_index')",
    
    # Auth routes
    "url_for('login')": "url_for('auth.login')",
    "url_for('register')": "url_for('auth.register')",
    "url_for('logout')": "url_for('auth.logout')",
    
    # Dashboard routes
    "url_for('dashboard')": "url_for('dashboard_bp.dashboard')",
    "url_for('customer_dashboard')": "url_for('dashboard_bp.customer_dashboard')",
    
    # Partner routes
    "url_for('partner_dashboard')": "url_for('partner.dashboard')",
    "url_for('partner_management_dashboard')": "url_for('partner.management_dashboard')",
    "url_for('partner_detail')": "url_for('partner.detail')",
    "url_for('partner_subscription')": "url_for('partner.subscription')",
    "url_for('partner_subscription_detail')": "url_for('partner.subscription_detail')",
    
    # Tag routes
    "url_for('create_tag')": "url_for('tag.create_tag')",
    "url_for('activate_tag')": "url_for('tag.activate_tag')",
    "url_for('deactivate_tag')": "url_for('tag.deactivate_tag')",
    "url_for('claim_tag')": "url_for('tag.claim_tag')",
    "url_for('transfer_tag')": "url_for('tag.transfer_tag')",
    "url_for('found_pet')": "url_for('tag.found_pet')",
    "url_for('contact_owner')": "url_for('tag.contact_owner')",
    
    # Pet routes
    "url_for('create_pet')": "url_for('pet.create_pet')",
    "url_for('edit_pet')": "url_for('pet.edit_pet')",
    
    # Payment routes
    "url_for('tag_payment')": "url_for('payment.tag_payment')",
    "url_for('payment_success')": "url_for('payment.success')",
    "url_for('partner_subscription_payment')": "url_for('payment.partner_subscription_payment')",
    
    # Profile routes
    "url_for('profile')": "url_for('profile_bp.profile')",
    "url_for('edit_profile')": "url_for('profile_bp.edit_profile')",
    "url_for('change_password')": "url_for('profile_bp.change_password')",
    
    # Admin routes
    "url_for('admin_dashboard')": "url_for('admin.dashboard')",
    "url_for('admin_users')": "url_for('admin.users')",
    "url_for('admin_subscriptions')": "url_for('admin.subscriptions')",
    "url_for('admin_tags')": "url_for('admin.tags')",
    "url_for('admin_pricing')": "url_for('admin.pricing')",
    "url_for('admin_settings')": "url_for('admin.settings')",
    "url_for('payment_gateways')": "url_for('admin.payment_gateways')",
    "url_for('edit_payment_gateway')": "url_for('admin.edit_payment_gateway')",
    "url_for('create_pricing_plan')": "url_for('admin.create_pricing_plan')",
    "url_for('edit_pricing_plan')": "url_for('admin.edit_pricing_plan')",
    "url_for('delete_pricing_plan')": "url_for('admin.delete_pricing_plan')",
    
    # Settings routes
    "url_for('notification_settings')": "url_for('settings.notifications')",
    "url_for('toggle_notification')": "url_for('settings.toggle_notification')",
}

# Also update endpoint comparisons in templates
ENDPOINT_COMPARISON_MAPPING = {
    "request.endpoint == 'index'": "request.endpoint == 'public.index'",
    "request.endpoint == 'contact'": "request.endpoint == 'public.contact'",
    "request.endpoint == 'privacy'": "request.endpoint == 'public.privacy'",
    "request.endpoint == 'login'": "request.endpoint == 'auth.login'",
    "request.endpoint == 'register'": "request.endpoint == 'auth.register'",
    "request.endpoint == 'dashboard'": "request.endpoint == 'dashboard_bp.dashboard'",
    "request.endpoint == 'customer_dashboard'": "request.endpoint == 'dashboard_bp.customer_dashboard'",
    "request.endpoint == 'partner_dashboard'": "request.endpoint == 'partner.dashboard'",
    "request.endpoint == 'partner_subscription'": "request.endpoint == 'partner.subscription'",
}

def fix_template_file(filepath):
    """Fix URL references in a single template file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Apply URL mappings
    for old_url, new_url in ENDPOINT_MAPPING.items():
        content = content.replace(old_url, new_url)
    
    # Apply endpoint comparison mappings
    for old_comp, new_comp in ENDPOINT_COMPARISON_MAPPING.items():
        content = content.replace(old_comp, new_comp)
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    
    return False

def main():
    """Fix all template files."""
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        print(f"Template directory {template_dir} not found!")
        return
    
    # Find all HTML template files
    pattern = os.path.join(template_dir, '**', '*.html')
    template_files = glob.glob(pattern, recursive=True)
    
    fixed_count = 0
    for template_file in template_files:
        if fix_template_file(template_file):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} template files out of {len(template_files)} total.")

if __name__ == "__main__":
    main()
