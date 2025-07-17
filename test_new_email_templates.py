#!/usr/bin/env python3
"""
Test script to verify the new email template system works with enhanced variables
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.enhanced_email_service import EmailTemplateManager
from models.email.email_models import EmailTemplate
from extensions import logger


def test_template_rendering():
    """Test template rendering with new variable system"""
    app = create_app()
    
    with app.app_context():
        # Test partner subscription confirmation template
        template = EmailTemplate.query.filter_by(name='partner_subscription_confirmation').first()
        
        if template:
            print(f"Testing template: {template.name}")
            print(f"Category: {template.category}")
            print(f"Required inputs: {template.required_inputs}")
            
            # Test variables in the template
            sample_variables = {
                'user': {'first_name': 'John', 'email': 'john@example.com'},
                'partner': {'company_name': 'Test Company'},
                'subscription': {
                    'amount': 29.99,
                    'status': 'pending',
                    'max_tags': 100,
                    'pricing_plan': {'name': 'Monthly Plan'},
                    'start_date': {'strftime': lambda fmt: '2025-01-15'}
                },
                'system': {
                    'base_url': 'http://localhost:8000',
                    'support_email': 'support@ltfpqrr.com'
                }
            }
            
            # Check if template contains new variable format
            print("\nChecking for enhanced variables in HTML content:")
            content = template.html_content
            
            # Look for enhanced variable patterns
            import re
            enhanced_vars = re.findall(r'\{\{[^}]+\}\}', content)
            legacy_vars = re.findall(r'\{[^{}]+\}', content)
            
            print(f"Enhanced variables found: {len(enhanced_vars)}")
            for var in enhanced_vars[:5]:  # Show first 5
                print(f"  - {var}")
            
            print(f"Legacy variables found: {len(legacy_vars)}")
            
            if enhanced_vars and not legacy_vars:
                print("✅ Template successfully updated to enhanced variable format!")
            elif enhanced_vars and legacy_vars:
                print("⚠️ Template contains both enhanced and legacy variables")
            else:
                print("❌ Template still uses legacy variable format")
                
        else:
            print("Template not found!")


if __name__ == '__main__':
    test_template_rendering()
