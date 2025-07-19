"""
Email Management Service for LTFPQRR system
Handles email queuing, retry logic, and bulk sending
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from flask import current_app
from extensions import db, logger
from models.email.email_models import (
    EmailQueue, EmailLog, EmailTemplate, EmailCampaign,
    EmailStatus, EmailPriority
)
from email_utils import send_email as send_email_direct


class EmailManager:
    """Central email management service"""
    
    # Custom email processors for specific email types
    custom_processors = {}
    
    @staticmethod
    def queue_email(
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = None,
        from_email: str = None,
        from_name: str = None,
        reply_to: str = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        template_id: int = None,
        user_id: int = None,
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
                reply_to=reply_to,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                priority=priority,
                template_id=template_id,
                user_id=user_id,
                partner_subscription_id=partner_subscription_id,
                max_retries=max_retries,
                status=EmailStatus.PENDING,
                email_type=email_type,
                email_metadata=metadata
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
            
            # Check for custom processor first
            if email_type and email_type in EmailManager.custom_processors:
                return EmailManager.custom_processors[email_type](queue_item, email_type, metadata or {})
            
            # Default email processing
            success = send_email_direct(
                to_email=queue_item.to_email,
                subject=queue_item.subject,
                html_body=queue_item.html_body,
                text_body=queue_item.text_body,
                from_email=queue_item.from_email,
                from_name=queue_item.from_name,
                reply_to=queue_item.reply_to
            )
            
            if success:
                # Mark as sent
                queue_item.mark_sent()
                db.session.commit()
                
                EmailManager.log_email(
                    queue_item=queue_item,
                    status=EmailStatus.SENT,
                    email_type=email_type,
                    metadata=metadata
                )
                
                logger.info(f"Email sent successfully: {queue_item.to_email}")
                return True
            else:
                # Mark as failed and schedule retry
                error_msg = "Email sending failed"
                queue_item.mark_failed(error_msg)
                db.session.commit()
                
                EmailManager.log_email(
                    queue_item=queue_item,
                    status=EmailStatus.FAILED if not queue_item.can_retry() else EmailStatus.RETRY,
                    email_type=email_type,
                    metadata=metadata,
                    error_message=error_msg
                )
                
                logger.warning(f"Email failed, retry count: {queue_item.retry_count}/{queue_item.max_retries}")
                return False
                
        except Exception as e:
            # Mark as failed with error details
            error_msg = str(e)
            queue_item.mark_failed(error_msg)
            db.session.commit()
            
            EmailManager.log_email(
                queue_item=queue_item,
                status=EmailStatus.FAILED if not queue_item.can_retry() else EmailStatus.RETRY,
                email_type=email_type,
                metadata=metadata,
                error_message=error_msg
            )
            
            logger.error(f"Error processing email queue item: {e}")
            return False
    
    @staticmethod
    def process_queue(limit: int = 50) -> Dict[str, int]:
        """Process pending emails in the queue"""
        try:
            # Get emails ready to send
            ready_emails = EmailQueue.query.filter(
                EmailQueue.status.in_([EmailStatus.PENDING, EmailStatus.RETRY]),
                EmailQueue.scheduled_at <= datetime.utcnow(),
                EmailQueue.expires_at > datetime.utcnow()
            ).order_by(
                EmailQueue.priority.desc(),
                EmailQueue.created_at.asc()
            ).limit(limit).all()
            
            stats = {
                'processed': 0,
                'sent': 0,
                'failed': 0,
                'expired': 0
            }
            
            for queue_item in ready_emails:
                stats['processed'] += 1
                
                # Get email_type and metadata from the queue item
                email_type = queue_item.email_type
                metadata = queue_item.email_metadata or {}
                
                success = EmailManager.process_queue_item(queue_item, email_type, metadata)
                if success:
                    stats['sent'] += 1
                elif queue_item.status == EmailStatus.EXPIRED:
                    stats['expired'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info(f"Email queue processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing email queue: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def log_email(
        queue_item: EmailQueue = None,
        status: EmailStatus = None,
        email_type: str = None,
        metadata: Dict = None,
        error_message: str = None,
        sent_by_id: int = None,
        to_email: str = None,
        subject: str = None,
        template_id: int = None,
        user_id: int = None
    ):
        """Create an email log entry"""
        try:
            log_entry = EmailLog(
                to_email=to_email or (queue_item.to_email if queue_item else None),
                from_email=queue_item.from_email if queue_item else None,
                from_name=queue_item.from_name if queue_item else None,
                subject=subject or (queue_item.subject if queue_item else None),
                status=status,
                sent_at=datetime.utcnow() if status == EmailStatus.SENT else None,
                template_id=template_id or (queue_item.template_id if queue_item else None),
                queue_id=queue_item.id if queue_item else None,
                user_id=user_id or (queue_item.user_id if queue_item else None),
                sent_by_id=sent_by_id,
                email_type=email_type,
                email_metadata=metadata,
                error_message=error_message
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating email log: {e}")
            db.session.rollback()
    
    @staticmethod
    def cleanup_old_emails(days: int = 30):
        """Clean up old email logs and expired queue items"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old logs
            old_logs = EmailLog.query.filter(EmailLog.created_at < cutoff_date).delete()
            
            # Delete expired queue items
            expired_queue = EmailQueue.query.filter(
                EmailQueue.status.in_([EmailStatus.SENT, EmailStatus.EXPIRED, EmailStatus.FAILED]),
                EmailQueue.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {old_logs} old email logs and {expired_queue} old queue items")
            return {'logs_deleted': old_logs, 'queue_deleted': expired_queue}
            
        except Exception as e:
            logger.error(f"Error cleaning up old emails: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    @staticmethod
    def get_queue_stats() -> Dict[str, Any]:
        """Get email queue statistics"""
        try:
            from sqlalchemy import func
            
            stats = {}
            
            # Queue stats by status
            queue_stats = db.session.query(
                EmailQueue.status,
                func.count(EmailQueue.id)
            ).group_by(EmailQueue.status).all()
            
            stats['queue'] = {status.value: count for status, count in queue_stats}
            
            # Recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_logs = db.session.query(
                EmailLog.status,
                func.count(EmailLog.id)
            ).filter(
                EmailLog.created_at >= recent_cutoff
            ).group_by(EmailLog.status).all()
            
            stats['recent_24h'] = {status.value: count for status, count in recent_logs}
            
            # Failure rate
            total_recent = sum(stats['recent_24h'].values())
            failed_recent = stats['recent_24h'].get('failed', 0)
            stats['failure_rate'] = (failed_recent / total_recent * 100) if total_recent > 0 else 0
            
            # Pending emails
            stats['pending_count'] = EmailQueue.query.filter(
                EmailQueue.status.in_([EmailStatus.PENDING, EmailStatus.RETRY])
            ).count()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {'error': str(e)}


class EmailTemplateManager:
    """Manager for email templates"""
    
    @staticmethod
    def create_template(
        name: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        description: str = None,
        variables: List[str] = None,
        created_by_id: int = None
    ) -> EmailTemplate:
        """Create a new email template"""
        try:
            template = EmailTemplate(
                name=name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                description=description,
                variables=variables or [],
                created_by_id=created_by_id
            )
            
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"Created email template: {name}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating email template: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_template(template_id: int = None, name: str = None) -> Optional[EmailTemplate]:
        """Get template by ID or name"""
        if template_id:
            return EmailTemplate.query.get(template_id)
        elif name:
            return EmailTemplate.query.filter_by(name=name, is_active=True).first()
        return None
    
    @staticmethod
    def send_from_template(
        template_name: str,
        to_email: str,
        variables: Dict[str, Any] = None,
        user_id: int = None,
        partner_id: int = None,
        subscription_id: int = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        email_type: str = None
    ) -> bool:
        """Send email using a template"""
        try:
            template = EmailTemplateManager.get_template(name=template_name)
            if not template:
                raise ValueError(f"Template not found: {template_name}")
            
            # Prepare template variables with model instances
            template_variables = variables or {}
            
            # Add model instances to variables
            template_variables.update(
                EmailTemplateManager.get_model_instances(
                    user_id=user_id,
                    partner_id=partner_id,
                    subscription_id=subscription_id
                )
            )
            
            # Render content with variables
            rendered = template.render_content(template_variables)
            
            # Queue the email
            queue_item = EmailManager.queue_email(
                to_email=to_email,
                subject=rendered['subject'],
                html_body=rendered['html_content'],
                text_body=rendered['text_content'],
                priority=priority,
                template_id=template.id,
                user_id=user_id,
                email_type=email_type or f'template_{template_name}',
                metadata={'template_name': template_name, 'variables': variables}
            )
            
            return queue_item.status == EmailStatus.SENT
            
        except Exception as e:
            logger.error(f"Error sending email from template: {e}")
            return False
    
    @staticmethod
    def get_model_instances(user_id=None, partner_id=None, subscription_id=None):
        """Get model instances for template variables"""
        from models.models import User, Partner, PartnerSubscription
        
        instances = {}
        
        # Get user instance
        if user_id:
            user = User.query.get(user_id)
            if user:
                instances['user'] = user
        
        # Get partner instance
        if partner_id:
            partner = Partner.query.get(partner_id)
            if partner:
                instances['partner'] = partner
                # Also add the partner owner as user if not already set
                if 'user' not in instances and partner.owner:
                    instances['user'] = partner.owner
        
        # Get subscription instance
        if subscription_id:
            subscription = PartnerSubscription.query.get(subscription_id)
            if subscription:
                instances['subscription'] = subscription
                # Also add related partner and user if not already set
                if 'partner' not in instances and subscription.partner:
                    instances['partner'] = subscription.partner
                if 'user' not in instances and subscription.partner and subscription.partner.owner:
                    instances['user'] = subscription.partner.owner
        
        return instances


class EmailCampaignManager:
    """Manager for email campaigns"""
    
    @staticmethod
    def create_campaign(
        name: str,
        template_id: int,
        target_type: str,
        target_criteria: Dict = None,
        description: str = None,
        created_by_id: int = None,
        scheduled_at: datetime = None
    ) -> EmailCampaign:
        """Create a new email campaign"""
        try:
            campaign = EmailCampaign(
                name=name,
                description=description,
                template_id=template_id,
                target_type=target_type,
                target_criteria=target_criteria or {},
                created_by_id=created_by_id,
                scheduled_at=scheduled_at
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            # Update recipient count
            campaign.update_stats()
            db.session.commit()
            
            logger.info(f"Created email campaign: {name}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating email campaign: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def send_campaign(campaign_id: int) -> Dict[str, Any]:
        """Send emails for a campaign"""
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")
            
            if campaign.status != 'draft':
                raise ValueError(f"Campaign already processed: {campaign.status}")
            
            # Get template
            template = campaign.template
            if not template:
                raise ValueError("Campaign template not found")
            
            # Get recipients
            recipients = campaign.get_recipients()
            
            # Update campaign status
            campaign.status = 'sending'
            campaign.started_at = datetime.utcnow()
            campaign.total_recipients = len(recipients)
            db.session.commit()
            
            # Send emails
            sent_count = 0
            failed_count = 0
            
            for recipient in recipients:
                try:
                    # Prepare variables for template
                    variables = {
                        'user_name': recipient.get_full_name(),
                        'user_email': recipient.email,
                        'first_name': recipient.first_name or 'there',
                        'campaign_name': campaign.name
                    }
                    
                    # Render template
                    rendered = template.render_content(variables)
                    
                    # Queue email
                    EmailManager.queue_email(
                        to_email=recipient.email,
                        subject=rendered['subject'],
                        html_body=rendered['html_content'],
                        text_body=rendered['text_content'],
                        template_id=template.id,
                        user_id=recipient.id,
                        email_type=f'campaign_{campaign.id}',
                        metadata={'campaign_id': campaign.id, 'campaign_name': campaign.name},
                        priority=EmailPriority.NORMAL,
                        send_immediately=True
                    )
                    
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Error sending campaign email to {recipient.email}: {e}")
                    failed_count += 1
            
            # Update campaign status
            campaign.status = 'completed'
            campaign.completed_at = datetime.utcnow()
            campaign.emails_sent = sent_count
            campaign.emails_failed = failed_count
            db.session.commit()
            
            logger.info(f"Campaign {campaign.name} completed: {sent_count} sent, {failed_count} failed")
            
            return {
                'sent': sent_count,
                'failed': failed_count,
                'total': len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Error sending campaign: {e}")
            if 'campaign' in locals():
                campaign.status = 'failed'
                db.session.commit()
            return {'error': str(e)}


# Convenience functions for backward compatibility
def queue_email_with_retry(to_email, subject, html_body, text_body=None, **kwargs):
    """Queue email with retry logic (backward compatibility)"""
    return EmailManager.queue_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        **kwargs
    )


def process_email_queue():
    """Process the email queue (for scheduled tasks)"""
    return EmailManager.process_queue()


def cleanup_old_emails():
    """Clean up old emails (for scheduled tasks)"""
    return EmailManager.cleanup_old_emails()
