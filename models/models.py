from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import DECIMAL

db = SQLAlchemy()

# Association table for many-to-many relationship between users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    account_type = db.Column(db.String(20), nullable=False)  # 'customer' or 'partner'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    owned_tags = db.relationship('Tag', foreign_keys='Tag.owner_id', backref='owner', lazy='dynamic')
    created_tags = db.relationship('Tag', foreign_keys='Tag.created_by', backref='creator', lazy='dynamic')
    pets = db.relationship('Pet', backref='owner', lazy='dynamic')
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')
    notifications = db.relationship('NotificationPreference', backref='user', lazy='dynamic')
    
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'available', 'claimed', 'active'
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pet = db.relationship('Pet', backref='tag', uselist=False)
    subscriptions = db.relationship('Subscription', backref='tag', lazy='dynamic')
    search_logs = db.relationship('SearchLog', backref='tag', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tag {self.tag_id}>'

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100))
    color = db.Column(db.String(50))
    photo = db.Column(db.String(255))
    vet_name = db.Column(db.String(100))
    vet_phone = db.Column(db.String(20))
    vet_address = db.Column(db.Text)
    groomer_name = db.Column(db.String(100))
    groomer_phone = db.Column(db.String(20))
    groomer_address = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Pet {self.name}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))
    subscription_type = db.Column(db.String(20), nullable=False)  # 'monthly', 'yearly', 'lifetime', 'partner'
    status = db.Column(db.String(20), nullable=False)  # 'active', 'cancelled', 'expired'
    restrictions_active = db.Column(db.Boolean, default=True)  # For lifetime subscriptions
    payment_method = db.Column(db.String(20))  # 'stripe', 'paypal', 'manual'
    payment_id = db.Column(db.String(100))
    amount = db.Column(DECIMAL(10, 2))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_active(self):
        if self.status != 'active':
            return False
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        return True
    
    def __repr__(self):
        return f'<Subscription {self.subscription_type} - {self.status}>'

class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SearchLog {self.tag_id} - {self.timestamp}>'

class NotificationPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'tag_search', 'payment_reminder', etc.
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationPreference {self.notification_type} - {self.enabled}>'

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_value(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            # Convert string representations to appropriate types
            if setting.value.lower() == 'true':
                return True
            elif setting.value.lower() == 'false':
                return False
            elif setting.value.isdigit():
                return int(setting.value)
            else:
                return setting.value
        return default
    
    @classmethod
    def set_value(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            setting.updated_at = datetime.utcnow()
        else:
            setting = cls(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()
    
    def __repr__(self):
        return f'<SystemSetting {self.key}>'

class PaymentGateway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 'stripe', 'paypal'
    enabled = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.Text)  # Encrypted
    secret_key = db.Column(db.Text)  # Encrypted
    webhook_secret = db.Column(db.Text)  # Encrypted
    environment = db.Column(db.String(20), default='sandbox')  # 'sandbox', 'production'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PaymentGateway {self.name}>'
