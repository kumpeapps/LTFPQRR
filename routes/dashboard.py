"""
Dashboard routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def dashboard():
    """Main dashboard route - redirects to appropriate dashboard."""
    # Show unified dashboard selection for users with partner role
    if current_user.has_partner_role():
        owned_partners = current_user.get_owned_partners()
        accessible_partners = current_user.get_accessible_partners()

        # If no partners exist, show the partner management dashboard
        if not owned_partners and not accessible_partners:
            return redirect(url_for("partner.management_dashboard"))

        # Otherwise show partner dashboard
        return redirect(url_for("partner.dashboard"))
    else:
        return redirect(url_for("dashboard.customer_dashboard"))


@dashboard_bp.route("/customer")
@login_required
def customer_dashboard():
    """Customer dashboard."""
    from models.models import Tag, Pet
    from models.payment.payment import Subscription
    from datetime import datetime

    # All users have customer access
    # Get customer's claimed tags and pets
    tags = Tag.query.filter_by(owner_id=current_user.id).all()
    pets = Pet.query.filter_by(owner_id=current_user.id).all()

    # Get user's subscriptions
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "customer/dashboard.html",
        tags=tags,
        pets=pets,
        subscriptions=subscriptions,
        now=datetime.utcnow(),
    )
