"""
Email management models for LTFPQRR system
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from extensions import db
import enum


class EmailStatus(enum.Enum):
    """Email status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"
    EXPIRED = "expired"


class EmailPriority(enum.Enum):
    """Email priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EmailTemplate(db.Model):
    """Email template model for reusable email templates with category system"""
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    subject = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    description = Column(String(500))
    category = Column(String(50), nullable=False, default='user_notification')  # Template category
    variables = Column(JSON)  # Store template variables as JSON (legacy)
    required_inputs = Column(JSON)  # Store required input parameters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('user.id'))
    
    # Relationships
    created_by = relationship("User", backref="email_templates_created", lazy='select')
    email_logs = relationship("EmailLog", back_populates="template")
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}:{self.category}>'
    
    def get_category_enum(self):
        """Get the category as enum"""
        try:
            from models.email.template_categories import TemplateCategory
            return TemplateCategory(self.category)
        except (ValueError, ImportError):
            from models.email.template_categories import TemplateCategory
            return TemplateCategory.USER_NOTIFICATION  # Default fallback
    
    def get_category_config(self):
        """Get the configuration for this template's category"""
        try:
            from models.email.template_categories import TemplateCategoryConfig
            return TemplateCategoryConfig.get_category_config(self.get_category_enum())
        except ImportError:
            return {}
    
    def get_required_inputs(self):
        """Get required inputs for this template category"""
        config = self.get_category_config()
        return config.get('required_inputs', [])
    
    def get_available_models(self):
        """Get available models for this template category"""
        config = self.get_category_config()
        return config.get('available_models', ['user', 'system'])
    
    def get_target_email_field(self):
        """Get the target email field for this template category"""
        config = self.get_category_config()
        return config.get('target_field', 'user.email')
    
    def validate_inputs(self, inputs):
        """Validate inputs for this template category"""
        try:
            from models.email.template_categories import TemplateCategoryConfig
            return TemplateCategoryConfig.validate_inputs_for_category(
                self.get_category_enum(), 
                inputs
            )
        except ImportError:
            return {'valid': True, 'missing_inputs': [], 'required_inputs': []}
    
    def get_variables(self):
        """Get template variables as list (legacy support)"""
        return self.variables or []
    
    def render_content(self, variables=None, model_instances=None):
        """Render template content with variables and model instances using Jinja2"""
        if not variables:
            variables = {}
        if not model_instances:
            model_instances = {}
        
        try:
            from jinja2 import Template
            
            html_content = self.html_content
            text_content = self.text_content or ""
            subject = self.subject
            
            # Get system variables
            system_variables = self.get_system_variables()
            
            # Merge system variables with provided variables
            all_variables = {**system_variables, **variables}
            
            # Replace simple variables in content (backward compatibility)
            for key, value in all_variables.items():
                if isinstance(value, str):
                    placeholder = f"{{{key}}}"
                    html_content = html_content.replace(placeholder, str(value))
                    text_content = text_content.replace(placeholder, str(value))
                    subject = subject.replace(placeholder, str(value))
            
            # Replace model-based variables {{model.field}} using category-aware models
            available_models = self.get_available_models()
            filtered_instances = {k: v for k, v in model_instances.items() if k in available_models}
            
            # Always ensure system is available as a model instance
            if 'system' in available_models and 'system' not in filtered_instances:
                # Create a system object from system variables
                class SystemObject:
                    def __init__(self, vars_dict):
                        # Add both direct access and prefixed access
                        for key, value in vars_dict.items():
                            if key.startswith('system.'):
                                # Remove 'system.' prefix for direct access
                                setattr(self, key.replace('system.', ''), value)
                            elif not '.' in key:
                                # Add direct properties for non-prefixed vars
                                setattr(self, key, value)
                
                filtered_instances['system'] = SystemObject(system_variables)
            
            # First replace model variables in a backwards-compatible way
            html_content = self.replace_model_variables(html_content, filtered_instances)
            text_content = self.replace_model_variables(text_content, filtered_instances)
            subject = self.replace_model_variables(subject, filtered_instances)
            
            # Now process with Jinja2 for {% if %} and other template syntax
            # Prepare context for Jinja2 (variables + model instances)
            jinja_context = {**all_variables, **filtered_instances}
            
            # Add safe defaults for missing objects to prevent template errors
            safe_defaults = {
                'payment': type('DefaultPayment', (), {
                    'refund_processed': 'No',
                    'refund_message': 'Your refund is being processed and will appear in your account within 3-5 business days.'
                })(),
                'user': type('DefaultUser', (), {'first_name': 'Valued Customer'})(),
                'partner': type('DefaultPartner', (), {'company_name': 'Partner'})(),
                'subscription': type('DefaultSubscription', (), {
                    'plan_name': 'Subscription Plan', 
                    'amount': '0.00', 
                    'start_date': 'N/A'
                })(),
                'system': SystemObject(system_variables) if 'system' not in jinja_context else jinja_context['system']
            }
            
            # Only add defaults for missing objects that are in available models
            for key, default_obj in safe_defaults.items():
                if key in available_models and key not in jinja_context:
                    jinja_context[key] = default_obj
            
            # Render with Jinja2 - now with safe defaults
            try:
                html_template = Template(html_content)
                html_content = html_template.render(**jinja_context)
            except Exception as jinja_error:
                # Log the error and raise for debugging
                import logging
                logging.error(f"Jinja2 HTML rendering failed for template {self.name}: {jinja_error}")
                # Re-raise the error instead of using fallback that breaks templates
                raise jinja_error
            
            try:
                if text_content:
                    text_template = Template(text_content)
                    text_content = text_template.render(**jinja_context)
            except Exception as jinja_error:
                import logging
                logging.error(f"Jinja2 text rendering failed for template {self.name}: {jinja_error}")
                # Re-raise the error instead of using fallback that breaks templates
                raise jinja_error
            
            try:
                subject_template = Template(subject)
                subject = subject_template.render(**jinja_context)
            except Exception as jinja_error:
                import logging
                logging.error(f"Jinja2 subject rendering failed for template {self.name}: {jinja_error}")
                # Re-raise the error instead of using fallback that breaks templates
                raise jinja_error
            
            return {
                'subject': subject,
                'html_content': html_content,
                'text_content': text_content
            }
        except Exception as e:
            raise ValueError(f"Error rendering template: {e}")
    
    def resolve_target_email(self, model_instances):
        """Resolve the target email address based on category configuration"""
        target_field = self.get_target_email_field()
        
        try:
            # Handle direct email field (for admin emails)
            if target_field == 'admin_email' and 'admin_email' in model_instances:
                return model_instances['admin_email']
            
            if target_field == 'target_email' and 'target_email' in model_instances:
                return model_instances['target_email']
            
            # Handle model.field syntax
            if '.' in target_field:
                model_name, field_path = target_field.split('.', 1)
                model_instance = model_instances.get(model_name)
                
                if model_instance:
                    # Navigate through field path (e.g., partner.owner.email)
                    current_obj = model_instance
                    for field in field_path.split('.'):
                        if hasattr(current_obj, field):
                            current_obj = getattr(current_obj, field)
                            
                            # Handle callable methods
                            if callable(current_obj):
                                try:
                                    current_obj = current_obj()
                                except:
                                    return None
                        else:
                            return None
                    
                    return str(current_obj) if current_obj else None
            
            return None
            
        except Exception as e:
            from extensions import logger
            logger.error(f"Error resolving target email for template {self.id}: {e}")
            return None
    
    def get_system_variables(self):
        """Get system-wide variables from settings"""
        from models.models import SystemSetting
        
        variables = {}
        
        # Get site URL
        site_url = SystemSetting.get_value('site_url', 'http://localhost:5000')
        variables['site_url'] = site_url
        variables['system.site_url'] = site_url
        
        # Get company/app name
        app_name = SystemSetting.get_value('app_name', 'LTFPQRR')
        variables['app_name'] = app_name
        variables['system.app_name'] = app_name
        
        # Get support email
        support_email = SystemSetting.get_value('support_email', 'support@example.com')
        variables['support_email'] = support_email
        variables['system.support_email'] = support_email
        
        return variables
    
    def replace_model_variables(self, content, variables):
        """Replace model-based variables like {{user.first_name}}"""
        import re
        
        # Pattern to match {{model.field}} syntax with optional spaces and method calls
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_().]*)\s*\}\}'
        
        def replace_match(match):
            var_path = match.group(1)  # e.g., "user.first_name" or "partner.owner.get_full_name()"
            
            try:
                # Split into model and field path
                parts = var_path.split('.')
                model_name = parts[0]
                field_path = parts[1:]
                
                # Get the model instance from variables
                model_instance = variables.get(model_name)
                if model_instance is None:
                    return match.group(0)  # Return original if model not found
                
                # Navigate through the field path
                current_obj = model_instance
                for i, field in enumerate(field_path):
                    if field.endswith('()'):
                        # Handle method calls
                        method_name = field[:-2]  # Remove ()
                        if hasattr(current_obj, method_name):
                            method = getattr(current_obj, method_name)
                            if callable(method):
                                try:
                                    current_obj = method()
                                except:
                                    return match.group(0)  # Return original on error
                            else:
                                current_obj = method
                        else:
                            return match.group(0)  # Return original if method not found
                    else:
                        # Handle regular fields
                        if hasattr(current_obj, field):
                            current_obj = getattr(current_obj, field)
                            
                            # Handle callable fields (but don't call methods without () explicitly)
                            if callable(current_obj) and not field.startswith('_'):
                                # Only auto-call simple property-like methods if this is the last field
                                if i == len(field_path) - 1:
                                    try:
                                        if hasattr(current_obj, '__name__') and not current_obj.__name__.startswith('_'):
                                            current_obj = current_obj()
                                    except:
                                        pass  # Keep original value if call fails
                        else:
                            return match.group(0)  # Return original if field not found
                
                return str(current_obj) if current_obj is not None else ''
                    
            except Exception:
                return match.group(0)  # Return original on any error
        
        return re.sub(pattern, replace_match, content)
    
    @staticmethod
    def get_available_models_for_category(category_name):
        """Get available models and their fields for a specific template category"""
        try:
            from models.email.template_categories import TemplateCategory, ModelFieldConfig
            
            # Convert string to enum
            if isinstance(category_name, str):
                category = TemplateCategory(category_name)
            else:
                category = category_name
            
            return ModelFieldConfig.get_available_fields_for_category(category)
            
        except (ImportError, ValueError) as e:
            # Fallback to basic model info
            return {
                'user': {
                    'name': 'User',
                    'description': 'User account information',
                    'fields': {
                        'email': {'type': 'str', 'description': 'Email address'},
                        'first_name': {'type': 'str', 'description': 'First name'},
                        'last_name': {'type': 'str', 'description': 'Last name'},
                        'get_full_name()': {'type': 'method', 'description': 'Full name'}
                    }
                },
                'system': {
                    'name': 'System Settings',
                    'description': 'System-wide settings',
                    'fields': {
                        'site_url': {'type': 'str', 'description': 'Site URL'},
                        'app_name': {'type': 'str', 'description': 'Application name'},
                        'support_email': {'type': 'str', 'description': 'Support email'}
                    }
                }
            }
    
    @staticmethod
    def get_template_categories():
        """Get all available template categories"""
        try:
            from models.email.template_categories import TemplateCategory, TemplateCategoryConfig
            
            categories = []
            for category in TemplateCategory:
                config = TemplateCategoryConfig.get_category_config(category)
                categories.append({
                    'value': category.value,
                    'name': config.get('name', category.value),
                    'description': config.get('description', ''),
                    'required_inputs': config.get('required_inputs', []),
                    'available_models': config.get('available_models', []),
                    'examples': config.get('examples', [])
                })
            
            return categories
            
        except ImportError:
            # Fallback categories
            return [
                {
                    'value': 'user_account',
                    'name': 'User Account',
                    'description': 'User account-related emails',
                    'required_inputs': ['user_id'],
                    'available_models': ['user', 'system'],
                    'examples': ['Welcome email', 'Password reset']
                },
                {
                    'value': 'user_notification',
                    'name': 'User Notification',
                    'description': 'General notifications to users',
                    'required_inputs': ['user_id'],
                    'available_models': ['user', 'system'],
                    'examples': ['Service updates', 'Feature announcements']
                }
            ]


class EmailQueue(db.Model):
    """Email queue model for managing outgoing emails"""
    __tablename__ = 'email_queue'
    
    id = Column(Integer, primary_key=True)
    to_email = Column(String(255), nullable=False)
    from_email = Column(String(255))
    from_name = Column(String(100))
    reply_to = Column(String(255))  # Reply-To header for contact forms
    subject = Column(String(255), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text)
    
    # Email management
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING)
    priority = Column(Enum(EmailPriority), default=EmailPriority.NORMAL)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Custom processing
    email_type = Column(String(50))  # For custom processors like 'pet_search_notification'
    email_metadata = Column(JSON)  # Store additional data for custom processors
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=72))
    
    # Relationships
    template_id = Column(Integer, ForeignKey('email_templates.id'))
    template = relationship("EmailTemplate")
    
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", backref="queued_emails")
    
    # Optional relationships for tracking
    subscription_id = Column(Integer, ForeignKey('subscription.id'))
    subscription = relationship("Subscription")
    
    partner_subscription_id = Column(Integer, ForeignKey('partner_subscription.id'))
    partner_subscription = relationship("PartnerSubscription")
    
    # Error tracking
    last_error = Column(Text)
    error_history = Column(JSON)  # Store error history as JSON
    
    def __repr__(self):
        return f'<EmailQueue {self.to_email} - {self.status.value}>'
    
    def add_error(self, error_message):
        """Add error to history"""
        if not self.error_history:
            self.error_history = []
        
        self.error_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(error_message),
            'retry_count': self.retry_count
        })
        
        self.last_error = str(error_message)
    
    def can_retry(self):
        """Check if email can be retried"""
        return (
            self.status in [EmailStatus.FAILED, EmailStatus.RETRY] and
            self.retry_count < self.max_retries and
            datetime.utcnow() < self.expires_at
        )
    
    def should_expire(self):
        """Check if email should be expired"""
        return datetime.utcnow() >= self.expires_at
    
    def mark_sent(self, message_id=None):
        """Mark email as sent"""
        self.status = EmailStatus.SENT
        self.sent_at = datetime.utcnow()
        # message_id can be stored in metadata if needed
    
    def mark_failed(self, error_message):
        """Mark email as failed with error"""
        self.add_error(error_message)
        self.retry_count += 1
        
        if self.can_retry():
            self.status = EmailStatus.RETRY
            # Schedule next retry with exponential backoff
            delay_minutes = min(60, 5 * (2 ** (self.retry_count - 1)))
            self.scheduled_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        else:
            self.status = EmailStatus.FAILED
    
    def mark_expired(self):
        """Mark email as expired"""
        self.status = EmailStatus.EXPIRED


class EmailLog(db.Model):
    """Email log model for tracking all email activity"""
    __tablename__ = 'email_logs'
    
    id = Column(Integer, primary_key=True)
    
    # Email details
    to_email = Column(String(255), nullable=False)
    from_email = Column(String(255))
    from_name = Column(String(100))
    subject = Column(String(255), nullable=False)
    
    # Status and timing
    status = Column(Enum(EmailStatus), nullable=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Content references
    template_id = Column(Integer, ForeignKey('email_templates.id'))
    template = relationship("EmailTemplate", back_populates="email_logs")
    
    queue_id = Column(Integer, ForeignKey('email_queue.id'))
    queue_item = relationship("EmailQueue", backref="logs")
    
    # User tracking
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", foreign_keys=[user_id], backref="email_logs")
    
    sent_by_id = Column(Integer, ForeignKey('user.id'))
    sent_by = relationship("User", foreign_keys=[sent_by_id], backref="emails_sent")
    
    # Additional metadata
    email_type = Column(String(50))  # e.g., 'subscription_confirmation', 'admin_broadcast'
    email_metadata = Column(JSON)  # Store additional data as JSON
    error_message = Column(Text)
    
    def __repr__(self):
        return f'<EmailLog {self.to_email} - {self.status.value}>'


class EmailCampaign(db.Model):
    """Email campaign model for bulk email sending"""
    __tablename__ = 'email_campaigns'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Campaign settings
    template_id = Column(Integer, ForeignKey('email_templates.id'), nullable=False)
    template = relationship("EmailTemplate")
    
    # Targeting
    target_type = Column(String(50), nullable=False)  # 'all_users', 'partners', 'customers', 'custom'
    target_criteria = Column(JSON)  # Store targeting criteria as JSON
    
    # Campaign status
    status = Column(String(50), default='draft')  # draft, scheduled, sending, completed, failed
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Stats
    total_recipients = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_failed = Column(Integer, default=0)
    
    # Creator
    created_by_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_by = relationship("User", backref="email_campaigns")
    
    def __repr__(self):
        return f'<EmailCampaign {self.name}>'
    
    def get_recipients(self):
        """Get list of recipients based on target criteria"""
        from models.models import User, Partner, PartnerSubscription
        from extensions import db
        
        recipients = []
        
        if self.target_type == 'all_users':
            recipients = User.query.filter_by(is_active=True).all()
        
        elif self.target_type == 'partners':
            # Get all partner owners
            partner_owners = db.session.query(User).join(Partner).filter(Partner.is_active == True).all()
            recipients = partner_owners
        
        elif self.target_type == 'customers':
            # Get all non-partner users
            partner_user_ids = db.session.query(User.id).join(Partner).subquery()
            recipients = User.query.filter(~User.id.in_(partner_user_ids), User.is_active == True).all()
        
        elif self.target_type == 'custom' and self.target_criteria:
            # Handle custom targeting criteria
            query = User.query.filter_by(is_active=True)
            
            criteria = self.target_criteria
            if criteria.get('has_subscription'):
                # Users with active subscriptions
                query = query.join(PartnerSubscription).filter(
                    PartnerSubscription.admin_approved == True,
                    PartnerSubscription.status == 'active'
                )
            
            if criteria.get('partner_status'):
                # Filter by partner status
                if criteria['partner_status'] == 'active':
                    query = query.join(Partner).filter(Partner.is_active == True)
                elif criteria['partner_status'] == 'inactive':
                    query = query.join(Partner).filter(Partner.is_active == False)
            
            recipients = query.all()
        
        return recipients
    
    def update_stats(self):
        """Update campaign statistics"""
        recipients = self.get_recipients()
        self.total_recipients = len(recipients)
        
        # Count sent/failed emails for this campaign
        logs = EmailLog.query.filter_by(
            email_type=f'campaign_{self.id}'
        ).all()
        
        self.emails_sent = len([log for log in logs if log.status == EmailStatus.SENT])
        self.emails_failed = len([log for log in logs if log.status == EmailStatus.FAILED])
