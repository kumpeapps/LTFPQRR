"""
Profile management routes
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ProfileForm, ChangePasswordForm

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route("/")
@login_required
def profile():
    """User profile page."""
    return render_template("profile.html", user=current_user)


@profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Edit user profile."""
    from models.models import User
    from extensions import db
    
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != current_user.id:
            flash("Email already registered to another user.", "error")
            return render_template("profile/edit.html", form=form)

        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.email = form.email.data
        current_user.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.profile"))

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change user password."""
    from extensions import db
    
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not check_password_hash(
            current_user.password_hash, form.current_password.data
        ):
            flash("Current password is incorrect.", "error")
            return render_template("profile/change_password.html", form=form)

        current_user.password_hash = generate_password_hash(form.new_password.data)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Password changed successfully!", "success")
        return redirect(url_for("profile.profile"))

    return render_template("profile/change_password.html", form=form)
