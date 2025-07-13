"""
Partner-related models for LTFPQRR application.
"""
from models.base import db, datetime

# Association table for many-to-many relationship between partners and users
partner_users = db.Table('partner_users',
    db.Column('partner_id', db.Integer, db.ForeignKey('partner.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role', db.String(20), default='member'),  # 'owner', 'admin', 'member'
    db.Column('granted_at', db.DateTime, default=datetime.utcnow),
    db.Column('granted_by', db.Integer, db.ForeignKey('user.id'))
)

class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'suspended', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_partners')
    users = db.relationship('User', secondary=partner_users, 
                           primaryjoin='Partner.id == partner_users.c.partner_id',
                           secondaryjoin='User.id == partner_users.c.user_id',
                           backref=db.backref('partners', lazy='dynamic'))
    subscriptions = db.relationship('PartnerSubscription', backref='partner', lazy='dynamic')
    tags = db.relationship('Tag', backref='partner', lazy='dynamic')
    
    def get_active_subscription(self):
        """Get the current active subscription for this partner"""
        from models.payment.payment import Subscription
        return Subscription.query.filter_by(
            partner_id=self.id,
            subscription_type='partner',
            status='active',
            admin_approved=True
        ).first()
    
    def get_pending_subscription(self):
        """Get any pending subscription for this partner"""
        from models.payment.payment import Subscription
        return Subscription.query.filter_by(
            partner_id=self.id,
            subscription_type='partner',
            admin_approved=False
        ).filter(Subscription.status.in_(['pending', 'active'])).first()
    
    def get_any_subscription(self):
        """Get any subscription (active or pending) for this partner"""
        active = self.get_active_subscription()
        if active:
            return active
        return self.get_pending_subscription()
    
    def has_active_subscription(self):
        """Check if partner has an active subscription"""
        subscription = self.get_active_subscription()
        return subscription and subscription.is_active()
    
    def has_any_subscription(self):
        """Check if partner has any subscription (active or pending)"""
        return self.get_any_subscription() is not None
    
    def can_create_tags(self):
        """Check if partner can create new tags"""
        subscription = self.get_active_subscription()
        if not subscription or not subscription.is_active():
            return False
            
        # Check if partner hasn't exceeded tag limit
        if subscription.max_tags > 0:
            current_tags = self.tags.count()
            return current_tags < subscription.max_tags
        
        return True
    
    def get_remaining_tag_count(self):
        """Get remaining tags partner can create"""
        subscription = self.get_active_subscription()
        if not subscription or not subscription.is_active():
            return 0
            
        if subscription.max_tags == 0:  # Unlimited
            return float('inf')
            
        current_tags = self.tags.count()
        return max(0, subscription.max_tags - current_tags)
    
    def user_has_access(self, user):
        """Check if a user has access to this partner"""
        if user.id == self.owner_id:
            return True
        return user in self.users
    
    def get_user_role(self, user):
        """Get the role of a user in this partner"""
        if user.id == self.owner_id:
            return 'owner'
        
        # Query the association table to get the role
        result = db.session.execute(
            partner_users.select().where(
                partner_users.c.partner_id == self.id,
                partner_users.c.user_id == user.id
            )
        ).first()
        
        return result.role if result else None
    
    def add_user(self, user, role='member', granted_by=None):
        """Add a user to this partner with specified role"""
        if not self.user_has_access(user):
            # Insert into association table
            db.session.execute(
                partner_users.insert().values(
                    partner_id=self.id,
                    user_id=user.id,
                    role=role,
                    granted_by=granted_by.id if granted_by else None,
                    granted_at=datetime.utcnow()
                )
            )
            db.session.commit()
    
    def remove_user(self, user):
        """Remove a user from this partner"""
        if user.id != self.owner_id:  # Can't remove owner
            db.session.execute(
                partner_users.delete().where(
                    partner_users.c.partner_id == self.id,
                    partner_users.c.user_id == user.id
                )
            )
            db.session.commit()
    
    def __repr__(self):
        return f'<Partner {self.company_name}>'


class PartnerAccessRequest(db.Model):
    """Model for users requesting partner access"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    business_name = db.Column(db.String(120))
    business_description = db.Column(db.Text)
    justification = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='partner_access_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_partner_requests')
    
    def approve(self, admin_user, notes=None):
        """Approve the partner access request"""
        self.status = 'approved'
        self.reviewed_by = admin_user.id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes
        
        # Add partner role to user
        from models.user.user import Role
        partner_role = Role.query.filter_by(name='partner').first()
        if partner_role and partner_role not in self.user.roles:
            self.user.roles.append(partner_role)
        
        db.session.commit()
    
    def reject(self, admin_user, notes=None):
        """Reject the partner access request"""
        self.status = 'rejected'
        self.reviewed_by = admin_user.id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes
        db.session.commit()
    
    def __repr__(self):
        return f'<PartnerAccessRequest {self.user.username}>'


class PartnerSubscription(db.Model):
    """Partner-specific subscription model"""
    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    pricing_plan_id = db.Column(db.Integer, db.ForeignKey('pricing_plans.id'))
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'active', 'cancelled', 'expired'
    admin_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    max_tags = db.Column(db.Integer, default=0)  # 0 = unlimited
    payment_method = db.Column(db.String(20))  # 'stripe', 'paypal', 'manual'
    payment_id = db.Column(db.String(100))
    amount = db.Column(db.DECIMAL(10, 2))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    auto_renew = db.Column(db.Boolean, default=False)
    cancellation_requested = db.Column(db.Boolean, default=False)
    
    # Relationships
    pricing_plan = db.relationship('PricingPlan', backref='partner_subscriptions')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_partner_subscriptions')
    
    def is_active(self):
        """Check if subscription is active"""
        if self.status != 'active':
            return False
        if not self.admin_approved:
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
        """Check if subscription can be cancelled"""
        return self.status == 'active' and not self.cancellation_requested
    
    def approve(self, admin_user):
        """Approve the partner subscription"""
        self.admin_approved = True
        self.approved_by = admin_user.id
        self.approved_at = datetime.utcnow()
        self.status = 'active'
        db.session.commit()
    
    def reject(self, admin_user):
        """Reject the partner subscription"""
        self.status = 'cancelled'
        self.approved_by = admin_user.id
        self.approved_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<PartnerSubscription {self.partner.company_name}>'
