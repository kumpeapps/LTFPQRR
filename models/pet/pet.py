"""
Pet-related models for LTFPQRR application.
"""
from models.base import db, datetime


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50))
    breed = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    color = db.Column(db.String(50))
    photo = db.Column(db.String(255))
    vet_name = db.Column(db.String(100))
    vet_phone = db.Column(db.String(20))
    vet_address = db.Column(db.Text)
    vet_info_public = db.Column(db.Boolean, default=False)
    groomer_name = db.Column(db.String(100))
    groomer_phone = db.Column(db.String(20))
    groomer_address = db.Column(db.Text)
    groomer_info_public = db.Column(db.Boolean, default=False)
    phone_public = db.Column(db.Boolean, default=True)  # Privacy setting for owner phone
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        
        from datetime import date
        today = date.today()
        age_years = today.year - self.date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year yet
        if today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age_years -= 1
            
        return age_years
    
    def __repr__(self):
        return f'<Pet {self.name}>'


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'available', 'claimed', 'active'
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who created the tag
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'))  # Partner company that owns this tag
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Customer who claimed the tag
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pet = db.relationship('Pet', backref='tag', uselist=False)
    subscriptions = db.relationship('Subscription', backref='tag', lazy='dynamic')
    search_logs = db.relationship('SearchLog', backref='tag', lazy='dynamic')
    
    def can_be_activated_by_partner(self):
        """Check if the tag can be activated by its partner"""
        if not self.partner:
            return False
        
        # Check if partner has an active approved subscription
        return self.partner.has_active_subscription()
    
    def can_be_managed_by_user(self, user):
        """Check if a user can manage this tag"""
        if not self.partner:
            return False
        
        # User must have access to the partner and partner must have active subscription
        return self.partner.user_has_access(user) and self.partner.has_active_subscription()
    
    def has_active_subscription(self):
        """Check if the tag has an active subscription"""
        for subscription in self.subscriptions:
            if subscription.subscription_type == 'tag' and subscription.is_active():
                return True
        return False
    
    def activate_by_partner(self):
        """Activate the tag (mark as available for claiming)"""
        if not self.can_be_activated_by_partner():
            return False
        
        self.status = 'available'
        self.updated_at = datetime.utcnow()
        return True
    
    def __repr__(self):
        return f'<Tag {self.tag_id}>'


class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SearchLog {self.tag_id} - {self.timestamp}>'
