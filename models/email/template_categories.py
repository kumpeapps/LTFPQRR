"""
Email Template Category System Design

This file defines the template categories and their configurations.
Each category specifies:
- Available models and their fields
- Required input parameters
- Target audience
- Email routing logic
"""

from enum import Enum
from typing import Dict, List, Any


class TemplateCategory(Enum):
    """Email template categories"""
    USER_ACCOUNT = "user_account"
    USER_NOTIFICATION = "user_notification"
    PARTNER_ACCOUNT = "partner_account"
    PARTNER_SUBSCRIPTION = "partner_subscription"
    PARTNER_NOTIFICATION = "partner_notification"
    SYSTEM_ADMIN = "system_admin"
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"


class TemplateCategoryConfig:
    """Configuration for template categories"""
    
    CATEGORIES = {
        TemplateCategory.USER_ACCOUNT: {
            'name': 'User Account',
            'description': 'User account-related emails (registration, password reset, etc.)',
            'required_inputs': ['user_id'],
            'optional_inputs': [],
            'available_models': ['user', 'system'],
            'target_field': 'user.email',
            'examples': [
                'Welcome email',
                'Email verification',
                'Password reset',
                'Account activation',
                'Account deletion confirmation'
            ]
        },
        
        TemplateCategory.USER_NOTIFICATION: {
            'name': 'User Notification',
            'description': 'General notifications to users',
            'required_inputs': ['user_id'],
            'optional_inputs': ['partner_id', 'subscription_id'],
            'available_models': ['user', 'partner', 'subscription', 'system'],
            'target_field': 'user.email',
            'examples': [
                'Service updates',
                'Feature announcements',
                'Maintenance notifications',
                'Policy updates'
            ]
        },
        
        TemplateCategory.PARTNER_ACCOUNT: {
            'name': 'Partner Account',
            'description': 'Partner account management emails',
            'required_inputs': ['partner_id'],
            'optional_inputs': ['user_id'],
            'available_models': ['partner', 'user', 'system'],
            'target_field': 'partner.owner.email',
            'examples': [
                'Partner application approved',
                'Partner account setup',
                'Partner profile updates',
                'Partner verification'
            ]
        },
        
        TemplateCategory.PARTNER_SUBSCRIPTION: {
            'name': 'Partner Subscription',
            'description': 'Partner subscription and billing emails',
            'required_inputs': ['subscription_id'],
            'optional_inputs': ['partner_id', 'user_id', 'payment_id'],
            'available_models': ['subscription', 'partner', 'user', 'payment', 'system'],
            'target_field': 'subscription.partner.owner.email',
            'examples': [
                'Subscription created',
                'Payment successful',
                'Payment failed',
                'Subscription renewal',
                'Subscription cancelled',
                'Plan upgrade/downgrade'
            ]
        },
        
        TemplateCategory.PARTNER_NOTIFICATION: {
            'name': 'Partner Notification',
            'description': 'General notifications to partners',
            'required_inputs': ['partner_id'],
            'optional_inputs': ['user_id', 'subscription_id'],
            'available_models': ['partner', 'user', 'subscription', 'system'],
            'target_field': 'partner.owner.email',
            'examples': [
                'New features for partners',
                'Partner program updates',
                'Commission reports',
                'Performance alerts'
            ]
        },
        
        TemplateCategory.SYSTEM_ADMIN: {
            'name': 'System Admin',
            'description': 'Administrative and internal system emails',
            'required_inputs': [],
            'optional_inputs': ['user_id', 'partner_id', 'subscription_id', 'admin_email'],
            'available_models': ['user', 'partner', 'subscription', 'system'],
            'target_field': 'admin_email',  # Must be provided or use system default
            'examples': [
                'Error alerts',
                'System reports',
                'Security alerts',
                'Backup notifications',
                'Admin notifications'
            ]
        },
        
        TemplateCategory.MARKETING: {
            'name': 'Marketing',
            'description': 'Marketing and promotional emails',
            'required_inputs': [],
            'optional_inputs': ['user_id', 'partner_id', 'target_email'],
            'available_models': ['user', 'partner', 'system'],
            'target_field': 'target_email',  # Can target users, partners, or custom lists
            'examples': [
                'Newsletter',
                'Product announcements',
                'Special offers',
                'Event invitations',
                'Survey requests'
            ]
        },
        
        TemplateCategory.TRANSACTIONAL: {
            'name': 'Transactional',
            'description': 'Transaction-related emails',
            'required_inputs': ['user_id'],
            'optional_inputs': ['partner_id', 'subscription_id', 'transaction_id'],
            'available_models': ['user', 'partner', 'subscription', 'system'],
            'target_field': 'user.email',
            'examples': [
                'Purchase confirmation',
                'Receipt',
                'Refund notification',
                'Invoice',
                'Payment reminder'
            ]
        }
    }
    
    @classmethod
    def get_category_config(cls, category: TemplateCategory) -> Dict[str, Any]:
        """Get configuration for a specific category"""
        return cls.CATEGORIES.get(category, {})
    
    @classmethod
    def get_available_models_for_category(cls, category: TemplateCategory) -> List[str]:
        """Get available models for a category"""
        config = cls.get_category_config(category)
        return config.get('available_models', [])
    
    @classmethod
    def get_required_inputs_for_category(cls, category: TemplateCategory) -> List[str]:
        """Get required inputs for a category"""
        config = cls.get_category_config(category)
        return config.get('required_inputs', [])
    
    @classmethod
    def get_target_field_for_category(cls, category: TemplateCategory) -> str:
        """Get target email field for a category"""
        config = cls.get_category_config(category)
        return config.get('target_field', 'user.email')
    
    @classmethod
    def validate_inputs_for_category(cls, category: TemplateCategory, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs for a category"""
        config = cls.get_category_config(category)
        required_inputs = config.get('required_inputs', [])
        
        missing_inputs = []
        for required_input in required_inputs:
            if required_input not in inputs or inputs[required_input] is None:
                missing_inputs.append(required_input)
        
        return {
            'valid': len(missing_inputs) == 0,
            'missing_inputs': missing_inputs,
            'required_inputs': required_inputs
        }


class ModelFieldConfig:
    """Configuration for model fields available in templates"""
    
    MODELS = {
        'user': {
            'name': 'User',
            'description': 'User account information',
            'model_class': 'models.models.User',
            'fields': {
                'id': {'type': 'int', 'description': 'User ID'},
                'username': {'type': 'str', 'description': 'Username'},
                'email': {'type': 'str', 'description': 'Email address'},
                'first_name': {'type': 'str', 'description': 'First name'},
                'last_name': {'type': 'str', 'description': 'Last name'},
                'get_full_name()': {'type': 'method', 'description': 'Full name (first + last)'},
                'created_at': {'type': 'datetime', 'description': 'Account creation date'},
                'last_login': {'type': 'datetime', 'description': 'Last login date'},
                'is_active': {'type': 'bool', 'description': 'Account active status'},
                'phone': {'type': 'str', 'description': 'Phone number'},
                'timezone': {'type': 'str', 'description': 'User timezone'}
            }
        },
        
        'partner': {
            'name': 'Partner',
            'description': 'Partner company information',
            'model_class': 'models.models.Partner',
            'fields': {
                'id': {'type': 'int', 'description': 'Partner ID'},
                'company_name': {'type': 'str', 'description': 'Company name'},
                'status': {'type': 'str', 'description': 'Partner status'},
                'created_at': {'type': 'datetime', 'description': 'Partner creation date'},
                'website': {'type': 'str', 'description': 'Company website'},
                'phone': {'type': 'str', 'description': 'Company phone'},
                'address': {'type': 'str', 'description': 'Company address'},
                'owner.email': {'type': 'str', 'description': 'Owner email address'},
                'owner.get_full_name()': {'type': 'method', 'description': 'Owner full name'}
            }
        },
        
        'subscription': {
            'name': 'Partner Subscription',
            'description': 'Partner subscription details',
            'model_class': 'models.models.PartnerSubscription',
            'fields': {
                'id': {'type': 'int', 'description': 'Subscription ID'},
                'status': {'type': 'str', 'description': 'Subscription status'},
                'plan_name': {'type': 'str', 'description': 'Subscription plan name'},
                'amount': {'type': 'decimal', 'description': 'Subscription amount'},
                'start_date': {'type': 'datetime', 'description': 'Subscription start date'},
                'end_date': {'type': 'datetime', 'description': 'Subscription end date'},
                'created_at': {'type': 'datetime', 'description': 'Subscription creation date'},
                'partner.company_name': {'type': 'str', 'description': 'Partner company name'},
                'partner.owner.email': {'type': 'str', 'description': 'Partner owner email'}
            }
        },
        
        'system': {
            'name': 'System Settings',
            'description': 'System-wide settings and variables',
            'model_class': 'models.models.SystemSetting',
            'fields': {
                'site_url': {'type': 'str', 'description': 'Site URL'},
                'app_name': {'type': 'str', 'description': 'Application name'},
                'support_email': {'type': 'str', 'description': 'Support email address'},
                'company_name': {'type': 'str', 'description': 'Company name'},
                'company_address': {'type': 'str', 'description': 'Company address'},
                'phone': {'type': 'str', 'description': 'Company phone'},
                'logo_url': {'type': 'str', 'description': 'Company logo URL'}
            }
        }
    }
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        return cls.MODELS.get(model_name, {})
    
    @classmethod
    def get_fields_for_model(cls, model_name: str) -> Dict[str, Dict[str, str]]:
        """Get fields for a specific model"""
        config = cls.get_model_config(model_name)
        return config.get('fields', {})
    
    @classmethod
    def get_available_fields_for_category(cls, category: TemplateCategory) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get all available fields for models in a category"""
        available_models = TemplateCategoryConfig.get_available_models_for_category(category)
        
        fields = {}
        for model_name in available_models:
            model_config = cls.get_model_config(model_name)
            if model_config:
                fields[model_name] = {
                    'name': model_config['name'],
                    'description': model_config['description'],
                    'fields': model_config['fields']
                }
        
        return fields
