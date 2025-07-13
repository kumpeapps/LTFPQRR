"""
Settings and notifications routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

settings = Blueprint('settings', __name__, url_prefix='/settings')


@settings.route("/notifications")
@login_required
def notifications():
    """User notification settings."""
    from models.models import NotificationPreference
    
    preferences = NotificationPreference.query.filter_by(user_id=current_user.id).all()
    return render_template("settings/notifications.html", preferences=preferences)


@settings.route("/notifications/toggle/<notification_type>")
@login_required
def toggle_notification(notification_type):
    """Toggle notification preference."""
    from models.models import NotificationPreference
    from extensions import db
    
    preference = NotificationPreference.query.filter_by(
        user_id=current_user.id, notification_type=notification_type
    ).first()

    if not preference:
        preference = NotificationPreference(
            user_id=current_user.id, notification_type=notification_type, enabled=True
        )
        db.session.add(preference)
    else:
        preference.enabled = not preference.enabled

    db.session.commit()

    flash(f"Notification preference updated.", "success")
    return redirect(url_for("settings.notifications"))
