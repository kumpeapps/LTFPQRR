"""
Customer subscription management routes for LTFPQRR application.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from datetime import datetime

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')


@customer_bp.route('/subscription/<int:subscription_id>')
@login_required
def manage_subscription(subscription_id):
    """Show subscription management page"""
    from models.payment.payment import Subscription
    
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Ensure user owns this subscription
    if subscription.user_id != current_user.id:
        flash("You don't have permission to access this subscription.", "error")
        return redirect(url_for('dashboard.customer_dashboard'))
    
    return render_template('customer/manage_subscription.html', 
                         subscription=subscription, 
                         now=datetime.utcnow())


@customer_bp.route('/subscription/<int:subscription_id>/toggle-auto-renew', methods=['POST'])
@login_required
def toggle_auto_renew(subscription_id):
    """Toggle auto-renewal for a subscription"""
    from models.payment.payment import Subscription
    
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Ensure user owns this subscription
    if subscription.user_id != current_user.id:
        flash("You don't have permission to modify this subscription.", "error")
        return redirect(url_for('dashboard.customer_dashboard'))
    
    # Don't allow toggling for lifetime subscriptions
    if subscription.subscription_type == 'lifetime':
        flash("Auto-renewal is not applicable for lifetime subscriptions.", "info")
        return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))
    
    # Don't allow enabling auto-renewal for expired subscriptions
    if subscription.status != 'active':
        flash("Cannot modify auto-renewal for inactive subscriptions.", "error")
        return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))
    
    try:
        # Toggle auto-renewal
        subscription.auto_renew = not subscription.auto_renew
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = "enabled" if subscription.auto_renew else "disabled"
        flash(f"Auto-renewal has been {status} for your {subscription.subscription_type} subscription.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating your subscription. Please try again.", "error")
    
    return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))


@customer_bp.route('/subscription/<int:subscription_id>/cancel', methods=['POST'])
@login_required
def cancel_subscription(subscription_id):
    """Request cancellation for a subscription"""
    from models.payment.payment import Subscription
    
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Ensure user owns this subscription
    if subscription.user_id != current_user.id:
        flash("You don't have permission to modify this subscription.", "error")
        return redirect(url_for('dashboard.customer_dashboard'))
    
    # Check if subscription can be cancelled
    if not subscription.can_be_cancelled():
        flash("This subscription cannot be cancelled at this time.", "error")
        return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))
    
    try:
        # Request cancellation (takes effect at end of current period)
        subscription.request_cancellation()
        db.session.commit()
        
        if subscription.end_date:
            flash(f"Your subscription has been scheduled for cancellation. It will remain active until {subscription.end_date.strftime('%B %d, %Y')}.", "info")
        else:
            flash("Your subscription cancellation has been requested.", "info")
        
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while cancelling your subscription. Please try again.", "error")
    
    return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))


@customer_bp.route('/subscription/<int:subscription_id>/renew', methods=['POST'])
@login_required
def renew_subscription(subscription_id):
    """Renew an expired subscription"""
    from models.payment.payment import Subscription
    
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Ensure user owns this subscription
    if subscription.user_id != current_user.id:
        flash("You don't have permission to modify this subscription.", "error")
        return redirect(url_for('dashboard.customer_dashboard'))
    
    # Only allow renewal of expired subscriptions
    if subscription.status != 'expired':
        flash("Only expired subscriptions can be manually renewed.", "error")
        return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))
    
    # Redirect to payment page for renewal
    flash("Please complete payment to renew your subscription.", "info")
    return redirect(url_for('payment.process_payment', 
                          subscription_type=subscription.subscription_type,
                          tag_id=subscription.tag_id if hasattr(subscription, 'tag_id') else None))


@customer_bp.route('/subscription/<int:subscription_id>/reactivate-auto-renew', methods=['POST'])
@login_required
def reactivate_auto_renew(subscription_id):
    """Reactivate auto-renewal for a subscription with cancellation requested"""
    from models.payment.payment import Subscription
    
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Ensure user owns this subscription
    if subscription.user_id != current_user.id:
        flash("You don't have permission to modify this subscription.", "error")
        return redirect(url_for('dashboard.customer_dashboard'))
    
    # Only allow for active subscriptions with cancellation requested
    if subscription.status != 'active' or not subscription.cancellation_requested:
        flash("This subscription cannot be reactivated.", "error")
        return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))
    
    try:
        # Reactivate auto-renewal
        subscription.cancellation_requested = False
        subscription.auto_renew = True
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash("Auto-renewal has been reactivated for your subscription.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while reactivating your subscription. Please try again.", "error")
    
    return redirect(url_for('customer.manage_subscription', subscription_id=subscription_id))


# Tag Management Routes

@customer_bp.route('/tags')
@login_required
def my_tags():
    """Show user's claimed tags and their status"""
    from models.pet.pet import Tag
    
    # Get all tags owned by the current user
    tags = Tag.query.filter_by(owner_id=current_user.id).all()
    
    return render_template('customer/my_tags.html', tags=tags)


@customer_bp.route('/tag/<int:tag_id>/release', methods=['POST'])
@login_required
def release_tag(tag_id):
    """Manually release a tag back to available status"""
    from models.pet.pet import Tag
    
    tag = Tag.query.get_or_404(tag_id)
    
    # Check if user can release this tag
    if not tag.can_be_released_by_user(current_user):
        flash("You don't have permission to release this tag or it cannot be released at this time.", "error")
        return redirect(url_for('customer.my_tags'))
    
    try:
        # Release the tag
        if tag.release_tag():
            db.session.commit()
            flash(f"Tag {tag.tag_id} has been released and is now available for others to claim.", "success")
        else:
            flash("Unable to release this tag. Please try again.", "error")
            
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while releasing the tag. Please try again.", "error")
    
    return redirect(url_for('customer.my_tags'))


@customer_bp.route('/tag/<int:tag_id>/purchase-subscription')
@login_required
def purchase_subscription_for_tag(tag_id):
    """Show subscription purchase options for a specific tag"""
    from models.pet.pet import Tag
    from models.payment.payment import PricingPlan
    
    tag = Tag.query.get_or_404(tag_id)
    
    # Check if user can purchase subscription for this tag
    if not tag.can_purchase_subscription_for_tag(current_user):
        flash("You don't have permission to purchase a subscription for this tag.", "error")
        return redirect(url_for('customer.my_tags'))
    
    # Get available tag pricing plans
    pricing_plans = PricingPlan.query.filter_by(
        plan_type='tag',
        is_active=True
    ).order_by(PricingPlan.sort_order, PricingPlan.price).all()
    
    return render_template('customer/purchase_tag_subscription.html', 
                         tag=tag, 
                         pricing_plans=pricing_plans)


@customer_bp.route('/tag/<int:tag_id>/purchase-subscription', methods=['POST'])
@login_required
def process_tag_subscription_purchase(tag_id):
    """Process subscription purchase for a specific tag"""
    from models.pet.pet import Tag
    from models.payment.payment import PricingPlan
    from flask import session
    
    tag = Tag.query.get_or_404(tag_id)
    
    # Check if user can purchase subscription for this tag
    if not tag.can_purchase_subscription_for_tag(current_user):
        flash("You don't have permission to purchase a subscription for this tag.", "error")
        return redirect(url_for('customer.my_tags'))
    
    pricing_plan_id = request.form.get('pricing_plan_id')
    payment_method = request.form.get('payment_method', 'stripe')
    
    if not pricing_plan_id:
        flash("Please select a pricing plan.", "error")
        return redirect(url_for('customer.purchase_subscription_for_tag', tag_id=tag_id))
    
    pricing_plan = PricingPlan.query.get_or_404(pricing_plan_id)
    
    # Verify it's a tag plan
    if pricing_plan.plan_type != 'tag':
        flash("Invalid pricing plan selected.", "error")
        return redirect(url_for('customer.purchase_subscription_for_tag', tag_id=tag_id))
    
    try:
        # Store payment session data to be used by the payment processor
        session['payment_data'] = {
            'user_id': current_user.id,
            'amount': float(pricing_plan.price),
            'payment_type': 'tag',
            'payment_method': payment_method,
            'claiming_tag_id': tag.tag_id,
            'subscription_type': pricing_plan.billing_period,
            'pricing_plan_id': pricing_plan.id,
            'renewal_for_tag_id': tag.id  # Special flag for renewals
        }
        
        # Redirect to payment processing
        if payment_method == 'stripe':
            return redirect(url_for('payment.stripe_checkout'))
        else:
            return redirect(url_for('payment.checkout'))
            
    except Exception as e:
        flash("An error occurred while processing your subscription. Please try again.", "error")
        return redirect(url_for('customer.purchase_subscription_for_tag', tag_id=tag_id))
