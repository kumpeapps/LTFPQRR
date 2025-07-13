"""
Authentication routes (login, register, logout)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route("/register", methods=["GET", "POST"])
def register():
    """User registration."""
    from models.models import SystemSetting, User, Role
    from extensions import db
    
    # Check if registration is enabled before processing
    registration_enabled = SystemSetting.get_value("registration_enabled", True)
    if not registration_enabled:
        flash(
            "Registration is currently disabled. Please contact an administrator.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Double check registration is still enabled
        registration_enabled = SystemSetting.get_value("registration_enabled", True)
        if not registration_enabled:
            flash("Registration is currently disabled.", "error")
            return redirect(url_for("auth.login"))

        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "error")
            return redirect(url_for("auth.register"))

        # Create new user (all users are customers by default)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            address=form.address.data,
        )

        # First user gets admin roles
        if User.query.count() == 0:
            user.roles = [
                Role.query.filter_by(name="user").first(),
                Role.query.filter_by(name="admin").first(),
                Role.query.filter_by(name="super-admin").first(),
            ]
        else:
            user.roles = [Role.query.filter_by(name="user").first()]

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    from models.models import User
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("dashboard.dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    """User logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.index"))
