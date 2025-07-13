"""
Base database configuration and utilities for LTFPQRR models.
"""
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import DECIMAL

# Common imports used by multiple models
__all__ = ['db', 'datetime', 'timedelta', 'DECIMAL']
