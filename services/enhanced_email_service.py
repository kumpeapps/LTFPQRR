"""
Enhanced Email Management Service with Template Category System
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from flask import current_app
from extensions import db, logger
from models.email.email_models import (
    EmailQueue, EmailLog, EmailTemplate, EmailCampaign,
    EmailStatus, EmailPriority
)
from email_utils import send_email_direct


class EmailTemplateManager:
    """Enhanced template manager with category support"""
    
    @staticmethod
    def create_template(
        name: str,
        subject: str,
        html_content: str,
        category: str,
        description: str = None,
        text_content: str = None,
        created_by_id: int = None
    ) -> EmailTemplate:
        """Create a new email template with category validation"""
        try:
            # Validate category
            template_categories = EmailTemplate.get_template_categories()
            valid_categories = [cat['value'] for cat in template_categories]
            
            if category not in valid_categories:
                raise ValueError(f"Invalid category: {category}. Valid categories: {valid_categories}")
            
            # Get category configuration to set required inputs
            category_config = None
            for cat in template_categories:
                if cat['value'] == category:
                    category_config = cat
                    break
            
            # Create template
            template = EmailTemplate(
                name=name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                description=description,
                category=category,
                required_inputs=category_config.get('required_inputs', []) if category_config else [],
                created_by_id=created_by_id,
                is_active=True
            )
            
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"Created email template '{name}' with category '{category}'")
            return template
            
        except Exception as e:
            logger.error(f"Error creating email template: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def send_from_template(
        template_name: str,
        inputs: Dict[str, Any],
        email_type: str = None,
        send_immediately: bool = True,
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> Optional[EmailQueue]:
        """Send email using template with category-based input validation"""
        try:
            # Get template
            template = EmailTemplate.query.filter_by(
                name=template_name,
                is_active=True
            ).first()
            
            if not template:
                raise ValueError(f"Template '{template_name}' not found or inactive")
            
            # Validate inputs based on template category
            validation_result = template.validate_inputs(inputs)
            if not validation_result['valid']:
                missing = ', '.join(validation_result['missing_inputs'])
                raise ValueError(f"Missing required inputs for template category: {missing}")
            
            # Load model instances based on inputs
            model_instances = EmailTemplateManager._load_model_instances(inputs)
            
            # Resolve target email
            target_email = template.resolve_target_email(model_instances)
            if not target_email:
                # Fallback: try to get email from inputs
                target_email = inputs.get('target_email') or inputs.get('admin_email')
                
                if not target_email:
                    raise ValueError(f"Could not resolve target email for template category: {template.category}")
            
            # Render template content
            rendered = template.render_content(inputs, model_instances)
            
            # Determine subscription IDs based on subscription type
            subscription_id = None
            partner_subscription_id = None
            if 'subscription_id' in inputs:
                # Check if this is a partner subscription or regular subscription
                subscription_type = inputs.get('subscription_type', 'tag')
                if subscription_type == 'partner':
                    partner_subscription_id = inputs.get('subscription_id')
                else:
                    subscription_id = inputs.get('subscription_id')
            
            # Queue email
            queue_item = EmailManager.queue_email(
                to_email=target_email,
                subject=rendered['subject'],
                html_body=rendered['html_content'],
                text_body=rendered['text_content'],
                template_id=template.id,
                user_id=inputs.get('user_id'),
                subscription_id=subscription_id,
                partner_subscription_id=partner_subscription_id,
                email_type=email_type or f"template_{template.category}",
                priority=priority,
                send_immediately=send_immediately,
                metadata={
                    'template_category': template.category,
                    'template_inputs': inputs
                }
            )
            
            logger.info(f"Email sent using template '{template_name}' to {target_email}")
            return queue_item
            
        except Exception as e:
            logger.error(f"Error sending email from template '{template_name}': {e}")
            raise
    
    @staticmethod
    def _load_model_instances(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load model instances based on input parameters"""
        instances = {}
        
        try:
            # Load User instance
            user_id = inputs.get('user_id')
            if user_id:
                from models.models import User
                user = User.query.get(user_id)
                if user:
                    instances['user'] = user
            
            # Load Partner instance
            partner_id = inputs.get('partner_id')
            if partner_id:
                from models.models import Partner
                partner = Partner.query.get(partner_id)
                if partner:
                    instances['partner'] = partner
            
            # Load Subscription instance
            subscription_id = inputs.get('subscription_id')
            if subscription_id:
                from models.models import PartnerSubscription
                subscription = PartnerSubscription.query.get(subscription_id)
                if subscription:
                    instances['subscription'] = subscription
                    # Auto-load related partner if not already loaded
                    if 'partner' not in instances and subscription.partner:
                        instances['partner'] = subscription.partner
            
            # Load Payment instance
            payment_id = inputs.get('payment_id')
            if payment_id:
                from models.models import Payment
                payment = Payment.query.get(payment_id)
                if payment:
                    instances['payment'] = payment
            
            # Add direct email addresses
            if 'admin_email' in inputs:
                instances['admin_email'] = inputs['admin_email']
            
            if 'target_email' in inputs:
                instances['target_email'] = inputs['target_email']
            
            # Add system settings (always available)
            instances['system'] = SystemSettingsProxy()
            
            return instances
            
        except Exception as e:
            logger.error(f"Error loading model instances: {e}")
            return instances


class SystemSettingsProxy:
    """Proxy class to access system settings as model attributes"""
    
    def __getattr__(self, name):
        try:
            from models.models import SystemSetting
            return SystemSetting.get_value(name, '')
        except:
            return ''
    
    @property
    def site_url(self):
        from models.models import SystemSetting
        return SystemSetting.get_value('site_url', 'http://localhost:5000')
    
    @property
    def app_name(self):
        from models.models import SystemSetting
        return SystemSetting.get_value('app_name', 'LTFPQRR')
    
    @property
    def support_email(self):
        from models.models import SystemSetting
        return SystemSetting.get_value('support_email', 'support@example.com')
    
    @property
    def company_name(self):
        from models.models import SystemSetting
        return SystemSetting.get_value('company_name', 'Your Company')


class EmailManager:
    """Enhanced email manager with category support"""
    
    @staticmethod
    def queue_email(
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = None,
        from_email: str = None,
        from_name: str = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        template_id: int = None,
        user_id: int = None,
        subscription_id: int = None,
        partner_subscription_id: int = None,
        email_type: str = None,
        metadata: Dict = None,
        max_retries: int = 3,
        send_immediately: bool = True
    ) -> EmailQueue:
        """Queue an email for sending"""
        try:
            # Create queue item
            queue_item = EmailQueue(
                to_email=to_email,
                from_email=from_email,
                from_name=from_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                priority=priority,
                template_id=template_id,
                user_id=user_id,
                subscription_id=subscription_id,
                partner_subscription_id=partner_subscription_id,
                max_retries=max_retries,
                status=EmailStatus.PENDING
            )
            
            db.session.add(queue_item)
            db.session.commit()
            
            # Send immediately if requested
            if send_immediately:
                success = EmailManager.process_queue_item(queue_item, email_type=email_type, metadata=metadata)
                if success:
                    logger.info(f"Email sent immediately to {to_email}")
                else:
                    logger.warning(f"Email queued for retry: {to_email}")
            else:
                # Only create initial log entry if not sending immediately
                EmailManager.log_email(
                    queue_item=queue_item,
                    status=EmailStatus.PENDING,
                    email_type=email_type,
                    metadata=metadata
                )
            
            return queue_item
            
        except Exception as e:
            logger.error(f"Error queuing email: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def process_queue_item(queue_item: EmailQueue, email_type: str = None, metadata: Dict = None) -> bool:
        """Process a single queue item"""
        try:
            # Check if email has expired
            if queue_item.should_expire():
                queue_item.mark_expired()
                db.session.commit()
                
                EmailManager.log_email(
                    queue_item=queue_item,
                    status=EmailStatus.EXPIRED,
                    email_type=email_type,
                    metadata=metadata,
                    error_message="Email expired after 72 hours"
                )
                
                logger.warning(f"Email expired: {queue_item.to_email}")
                return False
            
            # Try to send email
            success, message_id, error = send_email_direct(
                to_email=queue_item.to_email,
                subject=queue_item.subject,
                html_body=queue_item.html_body,
                text_body=queue_item.text_body,
                from_email=queue_item.from_email,
                from_name=queue_item.from_name
            )
            
            if success:
                # Mark as sent
                queue_item.mark_sent(message_id)
                db.session.commit()
                
                # Log success
                log_metadata = metadata or {}
                if message_id:
                    log_metadata['message_id'] = message_id
                
                EmailManager.log_email(
                    queue_item=queue_item,
                    status=EmailStatus.SENT,
                    email_type=email_type,
                    metadata=log_metadata
                )
                
                logger.info(f"Email sent successfully to {queue_item.to_email}")
                return True
            else:
                # Mark as failed and retry if possible
                queue_item.mark_failed(error)
                db.session.commit()
                
                # Log failure
                EmailManager.log_email(
                    queue_item=queue_item,
                    status=EmailStatus.FAILED,
                    email_type=email_type,
                    metadata=metadata,
                    error_message=error
                )
                
                logger.error(f"Email failed to {queue_item.to_email}: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing queue item {queue_item.id}: {e}")
            
            # Mark as failed
            try:
                queue_item.mark_failed(str(e))
                db.session.commit()
                
                EmailManager.log_email(
                    queue_item=queue_item,
                    status=EmailStatus.FAILED,
                    email_type=email_type,
                    metadata=metadata,
                    error_message=str(e)
                )
            except:
                pass
            
            return False
    
    @staticmethod
    def log_email(
        queue_item: EmailQueue,
        status: EmailStatus,
        email_type: str = None,
        metadata: Dict = None,
        error_message: str = None
    ):
        """Log email activity"""
        try:
            log = EmailLog(
                queue_id=queue_item.id,
                template_id=queue_item.template_id,
                user_id=queue_item.user_id,
                to_email=queue_item.to_email,
                subject=queue_item.subject,
                status=status,
                email_type=email_type,
                email_metadata=metadata,
                error_message=error_message,
                sent_at=datetime.utcnow() if status == EmailStatus.SENT else None
            )
            
            db.session.add(log)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging email: {e}")
            db.session.rollback()
    
    @staticmethod
    def get_queue_stats():
        """Get email queue statistics"""
        try:
            stats = {
                'pending': EmailQueue.query.filter_by(status=EmailStatus.PENDING).count(),
                'retry': EmailQueue.query.filter_by(status=EmailStatus.RETRY).count(),
                'failed': EmailQueue.query.filter_by(status=EmailStatus.FAILED).count(),
                'sent': EmailQueue.query.filter_by(status=EmailStatus.SENT).count(),
                'expired': EmailQueue.query.filter_by(status=EmailStatus.EXPIRED).count(),
            }
            
            stats['total_pending'] = stats['pending'] + stats['retry']
            stats['total'] = sum(stats.values()) - stats['total_pending']  # Avoid double counting
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def process_queue(limit: int = 100):
        """Process pending emails in queue"""
        try:
            # Get pending emails
            pending_emails = EmailQueue.query.filter(
                EmailQueue.status.in_([EmailStatus.PENDING, EmailStatus.RETRY])
            ).order_by(
                EmailQueue.priority.desc(),
                EmailQueue.created_at.asc()
            ).limit(limit).all()
            
            stats = {'processed': 0, 'sent': 0, 'failed': 0, 'expired': 0}
            
            for email in pending_emails:
                stats['processed'] += 1
                
                success = EmailManager.process_queue_item(email)
                
                if email.status == EmailStatus.SENT:
                    stats['sent'] += 1
                elif email.status == EmailStatus.FAILED:
                    stats['failed'] += 1
                elif email.status == EmailStatus.EXPIRED:
                    stats['expired'] += 1
            
            logger.info(f"Processed {stats['processed']} emails: {stats['sent']} sent, {stats['failed']} failed, {stats['expired']} expired")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing email queue: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def cleanup_old_emails(days: int = 30):
        """Clean up old email logs and queue items"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old logs
            old_logs = EmailLog.query.filter(EmailLog.created_at < cutoff_date).all()
            logs_deleted = len(old_logs)
            
            for log in old_logs:
                db.session.delete(log)
            
            # Delete old sent/failed queue items
            old_queue = EmailQueue.query.filter(
                EmailQueue.created_at < cutoff_date,
                EmailQueue.status.in_([EmailStatus.SENT, EmailStatus.FAILED, EmailStatus.EXPIRED])
            ).all()
            queue_deleted = len(old_queue)
            
            for item in old_queue:
                db.session.delete(item)
            
            db.session.commit()
            
            logger.info(f"Cleaned up {logs_deleted} old logs and {queue_deleted} old queue items")
            return {'logs_deleted': logs_deleted, 'queue_deleted': queue_deleted}
            
        except Exception as e:
            logger.error(f"Error cleaning up old emails: {e}")
            db.session.rollback()
            return {'error': str(e)}


# Backward compatibility alias
EmailCampaignManager = EmailManager
