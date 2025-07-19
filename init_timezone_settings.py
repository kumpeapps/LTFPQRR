"""
Initialize timezone settings for LTFPQRR application
"""

from services.timezone_service import TimezoneService
from flask import current_app

def init_timezone_settings():
    """Initialize timezone settings and services"""
    try:
        # Initialize the timezone service with the current app
        TimezoneService.init_app(current_app)
        current_app.logger.info("Timezone settings initialized successfully")
        return True
    except (ImportError, AttributeError) as e:
        current_app.logger.error(f"Failed to initialize timezone settings: {e}")
        return False
