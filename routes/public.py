"""
Public routes (homepage, contact, privacy, etc.)
"""
from flask import Blueprint, render_template, request, redirect, url_for

public = Blueprint('public', __name__)


@public.route("/")
def index():
    """Homepage."""
    # Handle tag search from homepage
    tag_id = request.args.get("tag_id")
    if tag_id:
        return redirect(url_for("tag.found_pet", tag_id=tag_id))

    # Get pricing plans for homepage
    from models.models import PricingPlan, Pet
    
    pricing_plans = (
        PricingPlan.query.filter_by(show_on_homepage=True, is_active=True)
        .order_by(PricingPlan.sort_order.asc())
        .all()
    )

    # Get stats for homepage
    total_pets = Pet.query.count()

    return render_template(
        "index.html", pricing_plans=pricing_plans, total_pets=total_pets
    )


@public.route("/contact")
def contact():
    """Contact page."""
    return render_template("contact.html")


@public.route("/privacy")
def privacy():
    """Privacy policy page."""
    return render_template("privacy.html")


@public.route("/found")
def found_index():
    """Found pet search page."""
    return render_template("found/index.html")


@public.route("/found/<tag_id>")
def found_redirect(tag_id):
    """Redirect /found/<tag_id> to the tag blueprint route."""
    return redirect(url_for("tag.found_pet", tag_id=tag_id))
