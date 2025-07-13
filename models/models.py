"""
LTFPQRR Models - Centralized import for all models to maintain backward compatibility.

This file imports all models from their respective modules and re-exports them
to maintain compatibility with existing code that imports from models.models.
"""

# Import base SQLAlchemy instance
from extensions import db

# Import all models from their respective modules
from models.user.user import User, Role, user_roles
from models.pet.pet import Pet, Tag, SearchLog
from models.payment.payment import Subscription, PaymentGateway, PricingPlan, Payment
from models.system.system import NotificationPreference, SystemSetting
from models.partner.partner import Partner, PartnerAccessRequest, PartnerSubscription

# Export all models for backward compatibility
__all__ = [
    'db',
    'User', 'Role', 'user_roles',
    'Pet', 'Tag', 'SearchLog',
    'Subscription', 'PaymentGateway', 'PricingPlan', 'Payment',
    'NotificationPreference', 'SystemSetting',
    'Partner', 'PartnerAccessRequest', 'PartnerSubscription'
]
