"""
Payment-related models for LTFPQRR application.
"""
from models.base import db, datetime, timedelta, DECIMAL


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))  # For tag-specific subscriptions
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'))  # For partner subscriptions
    pricing_plan_id = db.Column(db.Integer, db.ForeignKey('pricing_plans.id'))
    subscription_type = db.Column(db.String(20), nullable=False)  # 'tag', 'partner'
    status = db.Column(db.String(20), nullable=False)  # 'active', 'cancelled', 'expired', 'pending'
    admin_approved = db.Column(db.Boolean, default=False)  # Required for partner subscriptions
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who approved
    approved_at = db.Column(db.DateTime)
    max_tags = db.Column(db.Integer, default=0)  # For partner subscriptions, 0 = unlimited
    restrictions_active = db.Column(db.Boolean, default=True)  # For lifetime subscriptions
    payment_method = db.Column(db.String(20))  # 'stripe', 'paypal', 'manual'
    payment_id = db.Column(db.String(100))
    amount = db.Column(DECIMAL(10, 2))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    auto_renew = db.Column(db.Boolean, default=False)  # Auto-renewal flag
    cancellation_requested = db.Column(db.Boolean, default=False)  # Cancellation requested by user
    
    # Renewal retry tracking
    renewal_attempts = db.Column(db.Integer, default=0)  # Number of renewal attempts made
    last_renewal_attempt = db.Column(db.DateTime)  # Last attempt timestamp
    renewal_failure_reason = db.Column(db.String(500))  # Reason for last renewal failure
    
    # Relationships
    # user and tag relationships already defined in their respective models with backref
    pricing_plan = db.relationship('PricingPlan', backref='subscriptions')
    approver = db.relationship('User', foreign_keys=[approved_by])
    partner = db.relationship('Partner')
    
    def is_active(self):
        if self.status != 'active':
            return False
        if self.subscription_type == 'partner' and not self.admin_approved:
            return False
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        return True
    
    def is_expired(self):
        """Check if subscription is expired"""
        if self.end_date and datetime.utcnow() > self.end_date:
            return True
        return False
    
    def can_be_cancelled(self):
        """Check if subscription can be cancelled by user"""
        return self.status == 'active' and not self.cancellation_requested
    
    def approve(self, admin_user):
        """Approve the subscription (for partner subscriptions)"""
        self.admin_approved = True
        self.approved_by = admin_user.id
        self.approved_at = datetime.utcnow()
        if self.status == 'pending':
            self.status = 'active'
        self.updated_at = datetime.utcnow()
    
    def request_cancellation(self):
        """Request cancellation (takes effect at end of current period)"""
        if self.can_be_cancelled():
            self.cancellation_requested = True
            self.auto_renew = False
            self.updated_at = datetime.utcnow()
    
    def cancel_immediately(self):
        """Cancel subscription immediately (admin action)"""
        self.status = 'cancelled'
        self.auto_renew = False
        self.cancellation_requested = True
        self.updated_at = datetime.utcnow()
    
    def renew_subscription(self, new_end_date=None):
        """Renew subscription for another period"""
        if new_end_date:
            self.end_date = new_end_date
        elif self.pricing_plan:
            if self.pricing_plan.billing_period == 'monthly':
                self.end_date = datetime.utcnow() + timedelta(days=30)
            elif self.pricing_plan.billing_period == 'yearly':
                self.end_date = datetime.utcnow() + timedelta(days=365)
        
        self.cancellation_requested = False
        self.status = 'active'
        self.updated_at = datetime.utcnow()
    
    def needs_approval(self):
        """Check if subscription needs admin approval"""
        return self.subscription_type == 'partner' and not self.admin_approved
    
    def __repr__(self):
        return f'<Subscription {self.subscription_type} - {self.status}>'


class PaymentGateway(db.Model):
    __tablename__ = 'payment_gateways'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    api_key = db.Column(db.Text)
    secret_key = db.Column(db.Text)
    publishable_key = db.Column(db.Text)
    client_id = db.Column(db.Text)
    webhook_secret = db.Column(db.Text)
    environment = db.Column(db.String(20), default='sandbox')
    enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PricingPlan(db.Model):
    __tablename__ = 'pricing_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    billing_period = db.Column(db.String(20), nullable=False)  # monthly, yearly, lifetime
    plan_type = db.Column(db.String(20), nullable=False)  # tag, partner
    max_tags = db.Column(db.Integer, default=0)  # For partner plans, 0 = unlimited
    max_pets = db.Column(db.Integer, default=0)  # Maximum pets allowed
    features = db.Column(db.JSON)  # Store plan features as JSON
    requires_approval = db.Column(db.Boolean, default=False)  # Whether plan requires admin approval
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # Whether to feature this plan
    show_on_homepage = db.Column(db.Boolean, default=False)  # Whether to show on homepage
    sort_order = db.Column(db.Integer, default=0)  # Order for display
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_max_pets_display(self):
        """Get display string for max pets limit"""
        if self.max_pets == 0:
            return "Unlimited"
        return str(self.max_pets)
    
    def get_max_tags_display(self):
        """Get display string for max tags limit"""
        if self.max_tags == 0:
            return "Unlimited"
        return str(self.max_tags)
    
    def get_price_display(self):
        """Get formatted price display"""
        return f"${self.price:.2f}"
    
    def get_features_list(self):
        """Get features as a list for display"""
        if self.features and isinstance(self.features, dict):
            return self.features.get('features', [])
        return []

    def set_features_list(self, features_list):
        """Set features from a list"""
        if features_list is None:
            features_list = []
        if not isinstance(features_list, list):
            features_list = list(features_list) if features_list else []
        
        # Ensure we have a dictionary structure for features
        if not self.features:
            self.features = {}
        elif not isinstance(self.features, dict):
            self.features = {}
        
        self.features['features'] = features_list

    def __repr__(self):
        return f'<PricingPlan {self.name}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))
    partner_subscription_id = db.Column(db.Integer, db.ForeignKey('partner_subscription.id'))  # Link to PartnerSubscription
    payment_gateway = db.Column(db.String(50), nullable=False)  # stripe, paypal
    payment_intent_id = db.Column(db.String(200), unique=True)  # External payment ID - UNIQUE to prevent duplicates
    transaction_id = db.Column(db.String(200))  # Our internal transaction ID
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), nullable=False)  # pending, completed, failed, refunded
    payment_type = db.Column(db.String(50), nullable=False)  # tag, partner, renewal
    payment_metadata = db.Column(db.JSON)  # Store additional payment info
    gateway_response = db.Column(db.JSON)  # Store full gateway response
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='payments')
    subscription = db.relationship('Subscription', backref='payments')
    partner_subscription = db.relationship('PartnerSubscription', backref='payments')
    
    def generate_transaction_id(self):
        """Generate internal transaction ID"""
        import uuid
        self.transaction_id = f"TXN_{datetime.utcnow().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
    
    def mark_completed(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.processed_at = datetime.utcnow()
    
    def mark_failed(self, reason=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if reason and self.payment_metadata:
            self.payment_metadata['failure_reason'] = reason
        elif reason:
            self.payment_metadata = {'failure_reason': reason}
