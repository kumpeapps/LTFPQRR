"""
Timezone utilities for LTFPQRR system

Provides comprehensive timezone support for displaying dates and times
in user's preferred timezone while storing everything in UTC.
"""

import pytz
from datetime import datetime
from flask import session, g
from typing import List, Tuple, Optional


class TimezoneService:
    """Service for handling timezone conversions and utilities"""
    
    @classmethod
    def init_app(cls, app):
        """Initialize the timezone service with the Flask app"""
        # Register context processors for timezone functionality
        @app.context_processor
        def inject_timezone_functions():
            return {
                'user_timezone': cls.get_user_timezone,
                'format_datetime': cls.format_datetime,
                'format_relative': cls.format_relative,
                'utc_to_user': cls.utc_to_user
            }
    
    # Common timezones for dropdowns
    COMMON_TIMEZONES = [
        ('UTC', 'UTC (Coordinated Universal Time)'),
        ('US/Eastern', 'US Eastern Time'),
        ('US/Central', 'US Central Time'),
        ('US/Mountain', 'US Mountain Time'),
        ('US/Pacific', 'US Pacific Time'),
        ('US/Alaska', 'US Alaska Time'),
        ('US/Hawaii', 'US Hawaii Time'),
        ('Canada/Atlantic', 'Canada Atlantic Time'),
        ('Canada/Eastern', 'Canada Eastern Time'),
        ('Canada/Central', 'Canada Central Time'),
        ('Canada/Mountain', 'Canada Mountain Time'),
        ('Canada/Pacific', 'Canada Pacific Time'),
        ('Europe/London', 'Europe London (GMT/BST)'),
        ('Europe/Paris', 'Europe Paris (CET/CEST)'),
        ('Europe/Berlin', 'Europe Berlin (CET/CEST)'),
        ('Europe/Rome', 'Europe Rome (CET/CEST)'),
        ('Europe/Madrid', 'Europe Madrid (CET/CEST)'),
        ('Europe/Amsterdam', 'Europe Amsterdam (CET/CEST)'),
        ('Europe/Zurich', 'Europe Zurich (CET/CEST)'),
        ('Europe/Vienna', 'Europe Vienna (CET/CEST)'),
        ('Europe/Warsaw', 'Europe Warsaw (CET/CEST)'),
        ('Europe/Prague', 'Europe Prague (CET/CEST)'),
        ('Europe/Stockholm', 'Europe Stockholm (CET/CEST)'),
        ('Europe/Helsinki', 'Europe Helsinki (EET/EEST)'),
        ('Europe/Moscow', 'Europe Moscow (MSK)'),
        ('Asia/Tokyo', 'Asia Tokyo (JST)'),
        ('Asia/Shanghai', 'Asia Shanghai (CST)'),
        ('Asia/Hong_Kong', 'Asia Hong Kong (HKT)'),
        ('Asia/Singapore', 'Asia Singapore (SGT)'),
        ('Asia/Kolkata', 'Asia Kolkata (IST)'),
        ('Asia/Dubai', 'Asia Dubai (GST)'),
        ('Australia/Sydney', 'Australia Sydney (AEST/AEDT)'),
        ('Australia/Melbourne', 'Australia Melbourne (AEST/AEDT)'),
        ('Australia/Perth', 'Australia Perth (AWST)'),
        ('Pacific/Auckland', 'Pacific Auckland (NZST/NZDT)'),
    ]
    
    @staticmethod
    def get_user_timezone() -> str:
        """Get the current user's timezone preference"""
        # Import here to avoid circular imports
        try:
            from flask_login import current_user
            # Check if user is logged in and has timezone preference
            if current_user.is_authenticated and hasattr(current_user, 'timezone'):
                return current_user.timezone or 'UTC'
        except (ImportError, AttributeError):
            pass
        
        # Check session for temporary timezone
        if 'timezone' in session:
            return session['timezone']
        
        # Default to UTC
        return 'UTC'
    
    @staticmethod
    def set_user_timezone(timezone: str) -> bool:
        """Set timezone for current session"""
        try:
            # Validate timezone
            pytz.timezone(timezone)
            session['timezone'] = timezone
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    @staticmethod
    def utc_to_user(utc_datetime: datetime, user_timezone: Optional[str] = None) -> datetime:
        """Convert UTC datetime to user's timezone"""
        if utc_datetime is None:
            return None
            
        if user_timezone is None:
            user_timezone = TimezoneService.get_user_timezone()
        
        try:
            # Ensure UTC datetime is timezone-aware
            if utc_datetime.tzinfo is None:
                utc_datetime = pytz.utc.localize(utc_datetime)
            
            # Convert to user timezone
            user_tz = pytz.timezone(user_timezone)
            return utc_datetime.astimezone(user_tz)
            
        except (pytz.exceptions.UnknownTimeZoneError, AttributeError):
            # Fallback to UTC if conversion fails
            return utc_datetime
    
    @staticmethod
    def user_to_utc(user_datetime: datetime, user_timezone: Optional[str] = None) -> datetime:
        """Convert user timezone datetime to UTC"""
        if user_datetime is None:
            return None
            
        if user_timezone is None:
            user_timezone = TimezoneService.get_user_timezone()
        
        try:
            user_tz = pytz.timezone(user_timezone)
            
            # If datetime is naive, localize it to user timezone
            if user_datetime.tzinfo is None:
                user_datetime = user_tz.localize(user_datetime)
            
            # Convert to UTC
            return user_datetime.astimezone(pytz.utc).replace(tzinfo=None)
            
        except (pytz.exceptions.UnknownTimeZoneError, AttributeError):
            # Fallback - assume it's already UTC
            return user_datetime
    
    @staticmethod
    def format_datetime(utc_datetime: datetime, format_str: str = '%Y-%m-%d %H:%M:%S', 
                       user_timezone: Optional[str] = None, include_timezone: bool = True) -> str:
        """Format UTC datetime in user's timezone"""
        if utc_datetime is None:
            return ''
        
        user_dt = TimezoneService.utc_to_user(utc_datetime, user_timezone)
        
        if include_timezone and user_dt.tzinfo:
            # Get timezone abbreviation
            tz_abbr = user_dt.strftime('%Z')
            formatted = user_dt.strftime(format_str)
            return f"{formatted} {tz_abbr}"
        else:
            return user_dt.strftime(format_str)
    
    @staticmethod
    def format_relative(utc_datetime: datetime, user_timezone: Optional[str] = None) -> str:
        """Format datetime as relative time (e.g., '2 hours ago', 'in 3 days')"""
        if utc_datetime is None:
            return ''
        
        now_utc = datetime.utcnow()
        user_dt = TimezoneService.utc_to_user(utc_datetime, user_timezone)
        now_user = TimezoneService.utc_to_user(now_utc, user_timezone)
        
        # Calculate difference
        diff = user_dt - now_user
        abs_diff = abs(diff.total_seconds())
        
        # Format relative time
        if abs_diff < 60:  # Less than a minute
            return 'just now' if diff.total_seconds() >= 0 else 'moments ago'
        elif abs_diff < 3600:  # Less than an hour
            minutes = int(abs_diff // 60)
            suffix = 'ago' if diff.total_seconds() < 0 else 'from now'
            return f"{minutes} minute{'s' if minutes != 1 else ''} {suffix}"
        elif abs_diff < 86400:  # Less than a day
            hours = int(abs_diff // 3600)
            suffix = 'ago' if diff.total_seconds() < 0 else 'from now'
            return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"
        elif abs_diff < 604800:  # Less than a week
            days = int(abs_diff // 86400)
            suffix = 'ago' if diff.total_seconds() < 0 else 'from now'
            return f"{days} day{'s' if days != 1 else ''} {suffix}"
        else:
            # For longer periods, show actual date
            return TimezoneService.format_datetime(utc_datetime, '%Y-%m-%d', user_timezone, False)
    
    @staticmethod
    def get_timezone_choices() -> List[Tuple[str, str]]:
        """Get list of timezone choices for forms - includes all available timezones"""
        # Get all timezone names from pytz
        all_timezones = list(pytz.all_timezones)
        all_timezones.sort()
        
        # Create choices list with timezone ID and display name
        choices = []
        
        # Add UTC first as it's the most common
        choices.append(('UTC', 'UTC (Coordinated Universal Time)'))
        
        # Group common US timezones at the top for better UX
        us_timezones = [
            ('US/Eastern', 'US Eastern (EST/EDT)'),
            ('US/Central', 'US Central (CST/CDT)'),
            ('US/Mountain', 'US Mountain (MST/MDT)'),
            ('US/Pacific', 'US Pacific (PST/PDT)'),
            ('US/Alaska', 'US Alaska (AKST/AKDT)'),
            ('US/Hawaii', 'US Hawaii (HST)'),
        ]
        
        # Add America/* equivalents for US timezones
        america_us_timezones = [
            ('America/New_York', 'America/New_York (EST/EDT)'),
            ('America/Chicago', 'America/Chicago (CST/CDT)'),
            ('America/Denver', 'America/Denver (MST/MDT)'),
            ('America/Los_Angeles', 'America/Los_Angeles (PST/PDT)'),
            ('America/Anchorage', 'America/Anchorage (AKST/AKDT)'),
            ('Pacific/Honolulu', 'Pacific/Honolulu (HST)'),
        ]
        
        # Add common timezones at the top
        choices.extend(us_timezones)
        choices.extend(america_us_timezones)
        
        # Add separator
        choices.append(('', '--- All Available Timezones ---'))
        
        # Add all other timezones
        used_timezones = ['UTC'] + [tz[0] for tz in us_timezones + america_us_timezones]
        
        for tz in all_timezones:
            if tz not in used_timezones:
                try:
                    # Validate timezone
                    pytz.timezone(tz)
                    # Create readable display name
                    display_name = tz.replace('_', ' ')
                    choices.append((tz, display_name))
                except Exception:
                    # Skip invalid timezones
                    continue
        
        return choices
    
    @staticmethod
    def get_all_timezones() -> List[Tuple[str, str]]:
        """Get comprehensive list of all timezones"""
        timezones = []
        for tz in pytz.all_timezones:
            try:
                # Format timezone name for display
                display_name = tz.replace('_', ' ')
                timezones.append((tz, display_name))
            except Exception:
                continue
        return sorted(timezones, key=lambda x: x[1])
    
    @staticmethod
    def detect_timezone_from_browser() -> str:
        """Detect timezone from browser (requires JavaScript)"""
        # This would typically be set via JavaScript
        # For now, return UTC as default
        return 'UTC'
    
    @staticmethod
    def get_business_hours_utc(user_timezone: str, start_hour: int = 9, end_hour: int = 17) -> Tuple[datetime, datetime]:
        """Get business hours in UTC for a given timezone"""
        try:
            user_tz = pytz.timezone(user_timezone)
            today = datetime.now(user_tz).date()
            
            # Create business hours in user timezone
            start_time = user_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=start_hour)))
            end_time = user_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=end_hour)))
            
            # Convert to UTC
            start_utc = start_time.astimezone(pytz.utc).replace(tzinfo=None)
            end_utc = end_time.astimezone(pytz.utc).replace(tzinfo=None)
            
            return start_utc, end_utc
            
        except pytz.exceptions.UnknownTimeZoneError:
            # Fallback to UTC business hours
            today = datetime.utcnow().date()
            start_utc = datetime.combine(today, datetime.min.time().replace(hour=start_hour))
            end_utc = datetime.combine(today, datetime.min.time().replace(hour=end_hour))
            return start_utc, end_utc


def init_timezone_context_processor(app):
    """Initialize timezone context processor for templates"""
    
    @app.context_processor
    def timezone_context():
        """Add timezone utilities to template context"""
        return {
            'format_datetime': TimezoneService.format_datetime,
            'format_relative': TimezoneService.format_relative,
            'user_timezone': TimezoneService.get_user_timezone(),
            'utc_to_user': TimezoneService.utc_to_user
        }
    
    @app.before_request
    def load_user_timezone():
        """Load user's timezone preference before each request"""
        from flask_login import current_user
        
        if current_user.is_authenticated and hasattr(current_user, 'timezone'):
            g.user = current_user
            if current_user.timezone and 'timezone' not in session:
                session['timezone'] = current_user.timezone
