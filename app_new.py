"""
LTFPQRR Flask Application Factory
"""
import os
from flask import Flask
from config import config
from extensions import db, init_login_manager, make_celery, get_cipher_suite
from utils import init_utils, configure_payment_gateways

# Import blueprint modules
from routes.public import public
from routes.auth import auth
from routes.dashboard import dashboard_bp
from routes.partner import partner
from routes.tag import tag
from routes.pet import pet
from routes.payment import payment
from routes.profile import profile_bp
from routes.admin import admin
from routes.settings import settings


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    init_login_manager(app)
    
    # Initialize utilities
    init_utils(app)
    
    # Register blueprints
    app.register_blueprint(public)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(partner)
    app.register_blueprint(tag)
    app.register_blueprint(pet)
    app.register_blueprint(payment)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin)
    app.register_blueprint(settings)
    
    # Import models to ensure they are registered with SQLAlchemy
    from models.models import (
        User, Role, Tag, Pet, Subscription, SearchLog, 
        NotificationPreference, SystemSetting, PaymentGateway, 
        PricingPlan, Payment
    )
    from models.partner.partner import Partner, PartnerAccessRequest, PartnerSubscription
    
    # Configure payment gateways after app initialization
    with app.app_context():
        configure_payment_gateways()
    
    return app


def create_celery_app(app=None):
    """Create Celery app."""
    app = app or create_app()
    return make_celery(app)


# Create app instance for direct running
app = create_app()
celery = create_celery_app(app)


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
