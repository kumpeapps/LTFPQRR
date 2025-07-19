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
