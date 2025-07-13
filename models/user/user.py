"""
User-related models for LTFPQRR application.
"""

from flask_login import UserMixin
from models.base import db, datetime

# Association table for many-to-many relationship between users and roles
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True),
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    roles = db.relationship(
        "Role", secondary=user_roles, backref=db.backref("users", lazy="dynamic")
    )
    owned_tags = db.relationship(
        "Tag", foreign_keys="Tag.owner_id", backref="owner", lazy="dynamic"
    )
    created_tags = db.relationship(
        "Tag", foreign_keys="Tag.created_by", backref="creator", lazy="dynamic"
    )
    pets = db.relationship("Pet", backref="owner", lazy="dynamic")
    subscriptions = db.relationship(
        "Subscription",
        foreign_keys="Subscription.user_id",
        backref="user",
        lazy="dynamic",
    )
    notifications = db.relationship(
        "NotificationPreference", backref="user", lazy="dynamic"
    )

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def has_partner_role(self):
        """Check if user has partner role"""
        return self.has_role("partner")

    def has_pending_partner_subscription(self):
        """Check if user has a pending partner subscription"""
        pending_subscription = self.subscriptions.filter_by(
            subscription_type="partner", status="pending"
        ).first()
        return pending_subscription is not None

    def can_access_partner_dashboard(self):
        """Check if user can access partner dashboard (has role or pending subscription)"""
        return self.has_partner_role() or self.has_pending_partner_subscription()

    def can_request_partner_access(self):
        """Check if user can request partner access"""
        if self.has_partner_role():
            return False

        # Check if user has a pending request - avoid circular import
        from sqlalchemy import text

        result = db.session.execute(
            text(
                "SELECT id FROM partner_access_request WHERE user_id = :user_id AND status = 'pending' LIMIT 1"
            ),
            {"user_id": self.id},
        ).fetchone()

        return result is None

    def get_accessible_partners(self):
        """Get all partners this user has access to"""
        if not self.has_partner_role():
            return []

        # Return owned partners and partners where user has access
        return list(self.owned_partners) + list(self.partners)

    def get_owned_partners(self):
        """Get partners owned by this user"""
        return self.owned_partners if self.has_partner_role() else []

    def can_activate_tags(self):
        """Check if user can activate tags (partner role required)"""
        return self.has_partner_role()

    def __repr__(self):
        return f"<User {self.username}>"


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Role {self.name}>"
