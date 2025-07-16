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
    """Email template model for reusable email templates"""
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    subject = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    description = Column(String(500))
    variables = Column(JSON)  # Store template variables as JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('user.id'))
    
    # Relationships
    created_by = relationship("User", backref="email_templates_created")
    email_logs = relationship("EmailLog", back_populates="template")
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'
    
    def get_variables(self):
        """Get template variables as list"""
        return self.variables or []
    
    def render_content(self, variables=None):
        """Render template content with variables"""
        if not variables:
            variables = {}
        
        try:
            html_content = self.html_content
            text_content = self.text_content or ""
            subject = self.subject
            
            # Replace variables in content
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                html_content = html_content.replace(placeholder, str(value))
                text_content = text_content.replace(placeholder, str(value))
                subject = subject.replace(placeholder, str(value))
            
            return {
                'subject': subject,
                'html_content': html_content,
                'text_content': text_content
            }
        except Exception as e:
            raise ValueError(f"Error rendering template: {e}")


class EmailQueue(db.Model):
    """Email queue model for managing outgoing emails"""
    __tablename__ = 'email_queue'
    
    id = Column(Integer, primary_key=True)
    to_email = Column(String(255), nullable=False)
    from_email = Column(String(255))
    from_name = Column(String(100))
    subject = Column(String(255), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text)
    
    # Email management
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING)
    priority = Column(Enum(EmailPriority), default=EmailPriority.NORMAL)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
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
    
    def mark_sent(self):
        """Mark email as sent"""
        self.status = EmailStatus.SENT
        self.sent_at = datetime.utcnow()
    
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
