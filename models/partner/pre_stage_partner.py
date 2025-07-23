"""
Pre-stage Partner model for LTFPQRR application.
Manages pre-approved partners with automatic role assignment.
"""

from models.base import db, datetime
from sqlalchemy import func


class PreStagePartner(db.Model):
    """
    Pre-stage partner list for automatic role assignment.
    
    Statuses:
    - pre-approved: Users with this email automatically get partner role at registration
    - restricted: Prevents new partners from being created, but allows existing to continue
    - blocked: Prevents partner role and removes it if it exists
    """
    
    __tablename__ = 'pre_stage_partner'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    owner_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    status = db.Column(
        db.String(20), 
        nullable=False, 
        default='pre-approved'
    )  # 'pre-approved', 'restricted', 'blocked'
    notes = db.Column(db.Text)  # Optional notes for administrators
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    
    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by])
    updater = db.relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f'<PreStagePartner {self.company_name} ({self.email}) - {self.status}>'
    
    @classmethod
    def get_by_email(cls, email):
        """Get pre-stage partner by email (case-insensitive)"""
        return cls.query.filter(func.lower(cls.email) == func.lower(email)).first()
    
    @classmethod
    def is_pre_approved(cls, email):
        """Check if email is pre-approved for partner role"""
        partner = cls.get_by_email(email)
        return partner and partner.status == 'pre-approved'
    
    @classmethod
    def is_restricted(cls, email):
        """Check if email is restricted from creating new partners"""
        partner = cls.get_by_email(email)
        return partner and partner.status == 'restricted'
    
    @classmethod
    def is_blocked(cls, email):
        """Check if email is blocked from partner role"""
        partner = cls.get_by_email(email)
        return partner and partner.status == 'blocked'
    
    @classmethod
    def get_status(cls, email):
        """Get status for email or None if not in pre-stage list"""
        partner = cls.get_by_email(email)
        return partner.status if partner else None
    
    def can_create_partner(self):
        """Check if this pre-stage partner can create a new partner"""
        return self.status == 'pre-approved'
    
    def should_block_partner_role(self):
        """Check if this pre-stage partner should have partner role blocked/removed"""
        return self.status == 'blocked'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'owner_name': self.owner_name,
            'email': self.email,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'creator': self.creator.username if self.creator else None,
            'updater': self.updater.username if self.updater else None
        }
