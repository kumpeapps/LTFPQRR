"""
Partner-related routes for LTFPQRR application.
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.models import db, Partner, PartnerAccessRequest, PartnerSubscription, User, Role
from app import app


@app.route('/partner/request-access', methods=['GET', 'POST'])
@login_required
def request_partner_access():
    """Allow users to request partner access"""
    if current_user.has_partner_role():
        flash('You already have partner access.', 'info')
        return redirect(url_for('partner_dashboard'))
    
    if not current_user.can_request_partner_access():
        flash('You already have a pending partner access request.', 'warning')
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        business_name = request.form.get('business_name', '').strip()
        business_description = request.form.get('business_description', '').strip()
        justification = request.form.get('justification', '').strip()
        
        if not justification:
            flash('Please provide a justification for your partner access request.', 'error')
            return render_template('partner/request_access.html')
        
        # Create the access request
        access_request = PartnerAccessRequest(
            user_id=current_user.id,
            business_name=business_name if business_name else None,
            business_description=business_description if business_description else None,
            justification=justification
        )
        
        db.session.add(access_request)
        db.session.commit()
        
        # TODO: Send email notification to admins
        
        flash('Your partner access request has been submitted. You will be notified once it is reviewed.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('partner/request_access.html')


@app.route('/partner/dashboard')
@login_required
def partner_dashboard():
    """Partner dashboard - shows owned and accessible partners"""
    if not current_user.can_access_partner_dashboard():
        flash('You need partner access to view this page.', 'error')
        return redirect(url_for('request_partner_access'))
    
    # Check if user has pending partner subscription
    if current_user.has_pending_partner_subscription():
        # Show pending subscription status
        pending_subscription = current_user.subscriptions.filter_by(
            subscription_type='partner',
            status='pending'
        ).first()
        
        return render_template('partner/dashboard.html', 
                             pending_subscription=pending_subscription,
                             show_pending_status=True)
    
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    return render_template('partner/dashboard.html', 
                         owned_partners=owned_partners,
                         accessible_partners=accessible_partners)


@app.route('/partner/create', methods=['GET', 'POST'])
@login_required
def create_partner():
    """Create a new partner company"""
    if not current_user.has_partner_role():
        flash('You need partner access to create a partner company.', 'error')
        return redirect(url_for('request_partner_access'))
    
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        if not company_name or not email:
            flash('Company name and email are required.', 'error')
            return render_template('partner/create.html')
        
        # Create the partner
        partner = Partner(
            company_name=company_name,
            email=email,
            phone=phone if phone else None,
            address=address if address else None,
            owner_id=current_user.id
        )
        
        db.session.add(partner)
        db.session.commit()
        
        flash(f'Partner company "{company_name}" created successfully!', 'success')
        
        # Redirect to partner detail page with option to subscribe
        return redirect(url_for('partner_detail', partner_id=partner.id, prompt_subscription=1))
    
    return render_template('partner/create.html')


@app.route('/partner/<int:partner_id>')
@login_required
def partner_detail(partner_id):
    """View partner details and manage"""
    partner = Partner.query.get_or_404(partner_id)
    
    if not partner.user_has_access(current_user):
        flash('You do not have access to this partner.', 'error')
        return redirect(url_for('partner_management_dashboard'))
    
    user_role = partner.get_user_role(current_user)
    subscription = partner.get_active_subscription()
    
    # Check if we should prompt for subscription (new partner)
    prompt_subscription = request.args.get('prompt_subscription', False)
    
    return render_template('partner/detail.html', 
                         partner=partner,
                         user_role=user_role,
                         subscription=subscription,
                         prompt_subscription=prompt_subscription)


@app.route('/partner/<int:partner_id>/subscription', methods=['GET', 'POST'])
@login_required
def partner_subscription(partner_id):
    """Manage partner subscription"""
    partner = Partner.query.get_or_404(partner_id)
    
    if not partner.user_has_access(current_user):
        flash('You do not have access to this partner.', 'error')
        return redirect(url_for('partner_dashboard'))
    
    # Only owner can manage subscription
    if partner.owner_id != current_user.id:
        flash('Only the partner owner can manage subscriptions.', 'error')
        return redirect(url_for('partner_detail', partner_id=partner_id))
    
    from models.models import PricingPlan
    pricing_plans = PricingPlan.query.filter_by(plan_type='partner').all()
    current_subscription = partner.get_active_subscription()
    
    if request.method == 'POST':
        plan_id = request.form.get('pricing_plan_id')
        payment_method = request.form.get('payment_method', 'stripe')
        
        if not plan_id:
            flash('Please select a pricing plan.', 'error')
            return render_template('partner/subscription.html', 
                                 partner=partner,
                                 pricing_plans=pricing_plans,
                                 current_subscription=current_subscription)
        
        pricing_plan = PricingPlan.query.get(plan_id)
        if not pricing_plan:
            flash('Invalid pricing plan selected.', 'error')
            return render_template('partner/subscription.html', 
                                 partner=partner,
                                 pricing_plans=pricing_plans,
                                 current_subscription=current_subscription)
        
        # Create new subscription
        from datetime import datetime, timedelta
        start_date = datetime.utcnow()
        end_date = None
        if pricing_plan.duration_months > 0:
            end_date = start_date + timedelta(days=pricing_plan.duration_months * 30)
        
        subscription = PartnerSubscription(
            partner_id=partner.id,
            pricing_plan_id=pricing_plan.id,
            max_tags=pricing_plan.max_tags,
            payment_method=payment_method,
            amount=pricing_plan.price,
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        flash('Subscription created successfully! Waiting for admin approval.', 'success')
        return redirect(url_for('partner_detail', partner_id=partner_id))
    
    return render_template('partner/subscription.html', 
                         partner=partner,
                         pricing_plans=pricing_plans,
                         current_subscription=current_subscription)


@app.route('/admin/partner-requests')
@login_required
def admin_partner_requests():
    """Admin view for partner access requests"""
    if not current_user.has_role('admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    pending_requests = PartnerAccessRequest.query.filter_by(status='pending').all()
    all_requests = PartnerAccessRequest.query.order_by(PartnerAccessRequest.created_at.desc()).all()
    
    return render_template('admin/partner_requests.html',
                         pending_requests=pending_requests,
                         all_requests=all_requests)


@app.route('/admin/partner-request/<int:request_id>/review', methods=['POST'])
@login_required
def review_partner_request(request_id):
    """Admin approve/reject partner access request"""
    if not current_user.has_role('admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    access_request = PartnerAccessRequest.query.get_or_404(request_id)
    action = request.form.get('action')
    notes = request.form.get('notes', '').strip()
    
    if action == 'approve':
        access_request.approve(current_user, notes)
        flash(f'Partner access approved for {access_request.user.get_full_name()}.', 'success')
    elif action == 'reject':
        access_request.reject(current_user, notes)
        flash(f'Partner access rejected for {access_request.user.get_full_name()}.', 'info')
    else:
        flash('Invalid action.', 'error')
    
    return redirect(url_for('admin_partner_requests'))


@app.route('/admin/partner-subscriptions')
@login_required
def admin_partner_subscriptions():
    """Admin view for partner subscriptions needing approval"""
    if not current_user.has_role('admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    pending_subscriptions = PartnerSubscription.query.filter_by(
        status='pending',
        admin_approved=False
    ).all()
    
    all_subscriptions = PartnerSubscription.query.order_by(
        PartnerSubscription.created_at.desc()
    ).all()
    
    return render_template('admin/partner_subscriptions.html',
                         pending_subscriptions=pending_subscriptions,
                         all_subscriptions=all_subscriptions)


@app.route('/admin/partner-subscription/<int:subscription_id>/review', methods=['POST'])
@login_required
def review_partner_subscription(subscription_id):
    """Admin approve/reject partner subscription"""
    if not current_user.has_role('admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    subscription = PartnerSubscription.query.get_or_404(subscription_id)
    action = request.form.get('action')
    
    if action == 'approve':
        subscription.approve(current_user)
        flash(f'Subscription approved for {subscription.partner.company_name}.', 'success')
    elif action == 'reject':
        subscription.reject(current_user)
        flash(f'Subscription rejected for {subscription.partner.company_name}.', 'info')
    else:
        flash('Invalid action.', 'error')
    
    return redirect(url_for('admin_partner_subscriptions'))
