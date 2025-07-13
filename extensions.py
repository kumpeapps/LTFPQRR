"""
Flask extensions initialization.
"""
import os
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from cryptography.fernet import Fernet

# Optional imports with fallbacks
try:
    from celery import Celery
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    Celery = None

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_login_manager(app):
    """Initialize login manager."""
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.models import User
        return User.query.get(int(user_id))


def make_celery(app):
    """Create Celery instance."""
    celery = Celery(
        app.import_name,
        backend=app.config.get("CELERY_RESULT_BACKEND"),
        broker=app.config.get("CELERY_BROKER_URL"),
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def get_cipher_suite(app):
    """Get encryption cipher suite."""
    encryption_key_str = os.environ.get("ENCRYPTION_KEY")
    if not encryption_key_str:
        # Generate a new key if not provided
        encryption_key = Fernet.generate_key()
        logger.warning(
            "No ENCRYPTION_KEY provided, generated a new one. This should be set in production."
        )
    else:
        # Convert string to bytes for Fernet
        encryption_key = encryption_key_str.encode("utf-8")

    return Fernet(encryption_key)
