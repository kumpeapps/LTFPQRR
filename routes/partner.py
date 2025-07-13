"""
Partner management routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

partner = Blueprint('partner', __name__, url_prefix='/partner')


@partner.route("/management")
@login_required  
def management_dashboard():
    """Partner management dashboard - allows creating and selecting partners."""
    if not current_user.has_partner_role():
        flash("Partner access required.", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    return render_template(
        "partner/management.html",
        owned_partners=owned_partners,
        accessible_partners=accessible_partners
    )


@partner.route("/dashboard")
@login_required
def dashboard():
    """Partner dashboard."""
    if not current_user.can_access_partner_dashboard():
        flash("Partner access required.", "error")
        return redirect(url_for("dashboard.dashboard"))

    # Check if user has pending partner subscription
    if current_user.has_pending_partner_subscription():
        # Show pending subscription status
        pending_subscription = current_user.subscriptions.filter_by(
            subscription_type='partner',
            status='pending'
        ).first()
        
        # If user doesn't have partner role yet, show only pending status
        if not current_user.has_partner_role():
            # Create forms for CSRF protection and batch actions
            from flask_wtf import FlaskForm
            from forms import BatchTagActionForm
            form = FlaskForm()
            batch_form = BatchTagActionForm()
            
            return render_template('partner/dashboard.html', 
                                 pending_subscription=pending_subscription,
                                 show_pending_status=True,
                                 owned_partners=[],
                                 accessible_partners=[],
                                 tags=[],
                                 subscription=None,
                                 partner=None,
                                 form=form,
                                 batch_form=batch_form)
        
        # If user has partner role, show normal dashboard but with pending status banner
        owned_partners = current_user.get_owned_partners()
        accessible_partners = current_user.get_accessible_partners()
        
        # If user doesn't have any partners, redirect to management page
        if not owned_partners and not accessible_partners:
            flash("You need to create or have access to a partner account first.", "info")
            return redirect(url_for("partner.management_dashboard"))
        
        # If there are multiple partners, let user select one from query parameter
        partner_id = request.args.get('partner_id', type=int)
        if partner_id:
            all_partners = owned_partners + accessible_partners
            partner_obj = next((p for p in all_partners if p.id == partner_id), None)
            if not partner_obj:
                flash("Invalid partner selected.", "error")
                return redirect(url_for("partner.management_dashboard"))
        else:
            # Default to first available partner
            partner_obj = owned_partners[0] if owned_partners else accessible_partners[0]
        
        # Check if partner has active subscription
        subscription = partner_obj.get_active_subscription()
        
        # Get partner's tags
        tags = partner_obj.tags.all()
        
        # Create forms for CSRF protection and batch actions
        from flask_wtf import FlaskForm
        from forms import BatchTagActionForm
        form = FlaskForm()
        batch_form = BatchTagActionForm()

        return render_template(
            "partner/dashboard.html", 
            tags=tags, 
            subscription=subscription,
            partner=partner_obj,
            owned_partners=owned_partners,
            accessible_partners=accessible_partners,
            pending_subscription=pending_subscription,
            show_pending_status=True,
            form=form,
            batch_form=batch_form
        )

    # Get user's owned partners
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    # If user doesn't have any partners, redirect to management page
    if not owned_partners and not accessible_partners:
        flash("You need to create or have access to a partner account first.", "info")
        return redirect(url_for("partner.management_dashboard"))
    
    # If there are multiple partners, let user select one from query parameter
    partner_id = request.args.get('partner_id', type=int)
    if partner_id:
        all_partners = owned_partners + accessible_partners
        partner_obj = next((p for p in all_partners if p.id == partner_id), None)
        if not partner_obj:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner.management_dashboard"))
    else:
        # Default to first available partner
        partner_obj = owned_partners[0] if owned_partners else accessible_partners[0]
    
    # Check if partner has active subscription
    subscription = partner_obj.get_active_subscription()
    
    # Get partner's tags
    tags = partner_obj.tags.all()
    
    # Create forms for CSRF protection and batch actions
    from flask_wtf import FlaskForm
    from forms import BatchTagActionForm
    form = FlaskForm()
    batch_form = BatchTagActionForm()

    return render_template(
        "partner/dashboard.html", 
        tags=tags, 
        subscription=subscription,
        partner=partner_obj,
        owned_partners=owned_partners,
        accessible_partners=accessible_partners,
        form=form,
        batch_form=batch_form
    )


@partner.route('/<int:partner_id>')
@login_required
def detail(partner_id):
    """View partner details and manage."""
    from models.models import Partner
    
    partner_obj = Partner.query.get_or_404(partner_id)
    
    if not partner_obj.user_has_access(current_user):
        flash('You do not have access to this partner.', 'error')
        return redirect(url_for('partner.management_dashboard'))
    
    user_role = partner_obj.get_user_role(current_user)
    subscription = partner_obj.get_active_subscription()
    
    # Check if we should prompt for subscription (new partner)
    prompt_subscription = request.args.get('prompt_subscription', False)
    
    return render_template('partner/detail.html', 
                         partner=partner_obj,
                         user_role=user_role,
                         subscription=subscription,
                         prompt_subscription=prompt_subscription)


@partner.route("/subscription")
@partner.route("/<int:partner_id>/subscription")
@login_required
def subscription(partner_id=None):
    """Show subscription info and allow managing partner subscriptions."""
    if not current_user.has_partner_role():
        flash("Partner access required to view subscriptions.", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    # Get user's partners
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    # If partner_id specified, show that specific partner's subscription
    if partner_id:
        from models.models import Partner
        
        all_partners = owned_partners + accessible_partners
        partner_obj = next((p for p in all_partners if p.id == partner_id), None)
        if not partner_obj:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner.management_dashboard"))
        
        subscription_obj = partner_obj.get_active_subscription()
        return render_template("partner/subscription_management.html", 
                             partner=partner_obj,
                             subscription=subscription_obj,
                             owned_partners=owned_partners,
                             accessible_partners=accessible_partners)
    
    # Otherwise show all partners and their subscriptions
    return render_template("partner/subscription_management.html", 
                         owned_partners=owned_partners,
                         accessible_partners=accessible_partners)


@partner.route("/purchase-subscription")
@partner.route("/<int:partner_id>/purchase-subscription")
@login_required
def purchase_subscription(partner_id=None):
    """Show subscription purchase options for partners."""
    from models.models import PricingPlan
    
    if not current_user.has_partner_role():
        flash("Partner access required to purchase subscriptions.", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    # Get available partner pricing plans
    partner_plans = PricingPlan.query.filter_by(
        plan_type="partner",
        is_active=True
    ).order_by(PricingPlan.price).all()
    
    # Get user's partners
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    # If partner_id specified, show purchase options for that specific partner
    if partner_id:
        from models.models import Partner
        
        all_partners = owned_partners + accessible_partners
        partner_obj = next((p for p in all_partners if p.id == partner_id), None)
        if not partner_obj:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner.management_dashboard"))
        
        # Check if partner already has an active subscription
        subscription_obj = partner_obj.get_active_subscription()
        if subscription_obj:
            flash("This partner already has an active subscription.", "info")
            return redirect(url_for("partner.subscription", partner_id=partner_id))
        
        return render_template("partner/purchase_subscription.html", 
                             partner=partner_obj,
                             partner_plans=partner_plans,
                             owned_partners=owned_partners,
                             accessible_partners=accessible_partners)
    
    # Otherwise show general purchase options
    return render_template("partner/purchase_subscription.html", 
                         partner_plans=partner_plans,
                         owned_partners=owned_partners,
                         accessible_partners=accessible_partners)


@partner.route("/create", methods=["GET", "POST"])
@login_required
def create_partner():
    """Create a new partner company."""
    if not current_user.has_partner_role():
        flash("You need partner access to create a partner company.", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    if request.method == "POST":
        from models.models import Partner
        from extensions import db
        
        company_name = request.form.get("company_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        
        if not company_name or not email:
            flash("Company name and email are required.", "error")
            return render_template("partner/create.html")
        
        # Create the partner
        partner_obj = Partner(
            company_name=company_name,
            email=email,
            phone=phone if phone else None,
            address=address if address else None,
            owner_id=current_user.id
        )
        
        db.session.add(partner_obj)
        db.session.commit()
        
        flash(f'Partner company "{company_name}" created successfully!', "success")
        
        # Redirect to partner detail page with option to subscribe
        return redirect(url_for("partner.detail", partner_id=partner_obj.id, prompt_subscription=1))
    
    return render_template("partner/create.html")
