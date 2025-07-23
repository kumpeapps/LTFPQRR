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
    
    # Maintenance mode middleware
    @app.before_request
    def check_maintenance_mode():
        """Check if maintenance mode is enabled and block access for non-admins"""
        from flask import request, render_template_string, g
        from flask_login import current_user
        from models.models import SystemSetting
        
        # Set environment-based banner flags
        g.demo_mode = app.config.get('DEMO_MODE', False)
        g.preprod_mode = app.config.get('PREPROD_MODE', False)
        
        # Skip maintenance check for health check endpoint
        if request.endpoint == 'health_check':
            return
        
        # Skip maintenance check for static files
        if request.endpoint == 'static':
            return
        
        # Allow admin login and logout during maintenance
        if request.endpoint in ['auth.login', 'auth.logout']:
            return
            
        # Allow found pet routes during maintenance (critical functionality)
        if request.endpoint and (request.endpoint.startswith('tag.found') or request.endpoint.startswith('public.found')):
            # Set maintenance mode flag for banner display
            maintenance_setting = SystemSetting.query.filter_by(key='maintenance_mode').first()
            if maintenance_setting and maintenance_setting.value.lower() == 'true':
                g.maintenance_mode = True
            return
            
        try:
            # Check if maintenance mode is enabled
            maintenance_setting = SystemSetting.query.filter_by(key='maintenance_mode').first()
            if maintenance_setting and maintenance_setting.value.lower() == 'true':
                # Store maintenance mode status in g for template access
                g.maintenance_mode = True
                
                # Allow admins and super-admins to bypass maintenance mode
                if current_user.is_authenticated and (current_user.has_role('admin') or current_user.has_role('super-admin')):
                    return
                
                # Get maintenance message
                message_setting = SystemSetting.query.filter_by(key='maintenance_message').first()
                maintenance_message = message_setting.value if message_setting else "The site is temporarily down for maintenance. Please check back soon."
                
                # Return themed maintenance page
                maintenance_template = '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Maintenance - LTFPQRR</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
                    <link href="/static/css/custom.css" rel="stylesheet">
                    <style>
                        .maintenance-gradient {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }
                        .maintenance-card {
                            background: rgba(255, 255, 255, 0.95);
                            border: none;
                            border-radius: 20px;
                            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                        }
                        .maintenance-icon {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;
                        }
                    </style>
                </head>
                <body class="maintenance-gradient">
                    <!-- Navigation -->
                    <nav class="navbar navbar-expand-lg navbar-dark">
                        <div class="container">
                            <a class="navbar-brand d-flex align-items-center" href="#">
                                <img src="/static/assets/logo/logo.png" alt="LTFPQRR" height="40" class="me-2">
                                <span class="fw-bold">LTFPQRR</span>
                            </a>
                            <div class="ms-auto">
                                <a href="/auth/login" class="btn btn-outline-light">
                                    <i class="fas fa-sign-in-alt me-2"></i>Admin Login
                                </a>
                            </div>
                        </div>
                    </nav>

                    <!-- Maintenance Content -->
                    <div class="container-fluid d-flex align-items-center justify-content-center" style="min-height: 80vh;">
                        <div class="row justify-content-center w-100">
                            <div class="col-md-8 col-lg-6">
                                <div class="card maintenance-card text-center">
                                    <div class="card-body py-5 px-4">
                                        <i class="fas fa-tools fa-5x maintenance-icon mb-4"></i>
                                        <h1 class="display-5 fw-bold text-dark mb-3">Under Maintenance</h1>
                                        <p class="lead text-muted mb-4">{{ message }}</p>
                                        
                                        <div class="row g-3 mb-4">
                                            <div class="col-md-4">
                                                <div class="d-flex align-items-center justify-content-center h-100">
                                                    <div>
                                                        <i class="fas fa-sync fa-2x text-primary mb-2"></i>
                                                        <h6>Updating</h6>
                                                        <small class="text-muted">System improvements</small>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="d-flex align-items-center justify-content-center h-100">
                                                    <div>
                                                        <i class="fas fa-shield-alt fa-2x text-success mb-2"></i>
                                                        <h6>Securing</h6>
                                                        <small class="text-muted">Enhanced protection</small>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="d-flex align-items-center justify-content-center h-100">
                                                    <div>
                                                        <i class="fas fa-rocket fa-2x text-warning mb-2"></i>
                                                        <h6>Optimizing</h6>
                                                        <small class="text-muted">Better performance</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="alert alert-info border-0 bg-light">
                                            <i class="fas fa-info-circle me-2"></i>
                                            <strong>We'll be back online shortly!</strong><br>
                                            Thank you for your patience while we make improvements.
                                        </div>
                                        
                                        <div class="mt-4">
                                            <small class="text-muted">
                                                <i class="fas fa-clock me-1"></i>
                                                Estimated downtime: Just a few minutes
                                            </small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <footer class="text-center text-white py-3 mt-auto">
                        <div class="container">
                            <small>&copy; 2025 LTFPQRR. All rights reserved.</small>
                        </div>
                    </footer>
                </body>
                </html>
                '''
                return render_template_string(maintenance_template, message=maintenance_message), 503
            else:
                # Not in maintenance mode
                g.maintenance_mode = False
        except Exception:
            # If there's an error checking maintenance mode, allow normal access
            g.maintenance_mode = False
    
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
