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
from routes.customer import customer_bp
from routes.partner import partner
from routes.tag import tag
from routes.pet import pet
from routes.payment import payment
from routes.profile import profile_bp
from routes.admin import admin
from routes.settings import settings
from routes.timezone import timezone_bp


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
    
    # Initialize timezone service
    from services.timezone_service import TimezoneService
    TimezoneService.init_app(app)
    
    # Initialize utilities
    init_utils(app)
    
    # Register blueprints
    app.register_blueprint(public)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(partner)
    app.register_blueprint(tag)
    app.register_blueprint(pet)
    app.register_blueprint(payment)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin)
    app.register_blueprint(settings)
    app.register_blueprint(timezone_bp)
    
    # Health check endpoint for Docker
    @app.route('/health')
    def health_check():
        """Health check endpoint for container monitoring"""
        try:
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 503
    
    # Register email admin blueprint
    from routes.email_admin import email_admin
    app.register_blueprint(email_admin)
    
    # Import models to ensure they are registered with SQLAlchemy
    from models.models import (
        User, Role, Tag, Pet, Subscription, SearchLog, 
        NotificationPreference, SystemSetting, PaymentGateway, 
        PricingPlan, Payment, EmailQueue, EmailLog, EmailTemplate, EmailCampaign
    )
    from models.partner.partner import Partner, PartnerAccessRequest, PartnerSubscription
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Register pet email processors
        try:
            from services.pet_email_service import register_pet_email_processor
            register_pet_email_processor()
        except Exception as e:
            app.logger.warning(f"Could not register pet email processors: {e}")
        
        # Configure payment gateways after app and database initialization
        try:
            configure_payment_gateways()
        except Exception as e:
            app.logger.warning(f"Could not configure payment gateways: {e}")
        
        # Initialize timezone settings
        try:
            from init_timezone_settings import init_timezone_settings
            init_timezone_settings()
        except Exception as e:
            app.logger.warning(f"Could not initialize timezone settings: {e}")
    
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
