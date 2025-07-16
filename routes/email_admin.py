"""
Admin routes for email management
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from extensions import db, logger
from utils import admin_required
from models.email.email_models import (
    EmailQueue, EmailLog, EmailTemplate, EmailCampaign,
    EmailStatus, EmailPriority
)
from services.email_service import (
    EmailManager, EmailTemplateManager, EmailCampaignManager
)
from models.models import User, Partner, PartnerSubscription


email_admin = Blueprint('email_admin', __name__, url_prefix='/admin/email')


@email_admin.route('/')
@admin_required
def dashboard():
    """Email management dashboard"""
    try:
        # Get queue statistics
        stats = EmailManager.get_queue_stats()
        
        # Get recent email activity
        recent_logs = EmailLog.query.order_by(
            EmailLog.created_at.desc()
        ).limit(20).all()
        
        # Get pending emails
        pending_emails = EmailQueue.query.filter(
            EmailQueue.status.in_([EmailStatus.PENDING, EmailStatus.RETRY])
        ).order_by(EmailQueue.created_at.desc()).limit(10).all()
        
        # Get recent campaigns
        recent_campaigns = EmailCampaign.query.order_by(
            EmailCampaign.created_at.desc()
        ).limit(5).all()
        
        return render_template(
            'admin/email/dashboard.html',
            stats=stats,
            recent_logs=recent_logs,
            pending_emails=pending_emails,
            recent_campaigns=recent_campaigns
        )
        
    except Exception as e:
        logger.error(f"Error loading email dashboard: {e}")
        flash(f"Error loading email dashboard: {e}", "error")
        return redirect(url_for('admin.admin_dashboard'))


@email_admin.route('/queue')
@admin_required
def queue():
    """Email queue management"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        per_page = 50
        
        # Get queue statistics
        queue_stats = EmailManager.get_queue_stats()
        
        # Build query
        query = EmailQueue.query
        
        if status_filter != 'all':
            try:
                status_enum = EmailStatus(status_filter)
                query = query.filter(EmailQueue.status == status_enum)
            except ValueError:
                flash(f"Invalid status filter: {status_filter}", "warning")
        
        # Paginate results
        emails = query.order_by(EmailQueue.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return render_template(
            'admin/email/queue.html',
            emails=emails,
            status_filter=status_filter,
            queue_stats=queue_stats,
            EmailStatus=EmailStatus
        )
        
    except Exception as e:
        logger.error(f"Error loading email queue: {e}")
        flash(f"Error loading email queue: {e}", "error")
        return redirect(url_for('email_admin.dashboard'))


@email_admin.route('/queue/process')
@admin_required
def process_queue():
    """Manually process email queue"""
    try:
        stats = EmailManager.process_queue(limit=100)
        
        if 'error' in stats:
            flash(f"Error processing queue: {stats['error']}", "error")
        else:
            flash(
                f"Queue processed: {stats['sent']} sent, {stats['failed']} failed, "
                f"{stats['expired']} expired from {stats['processed']} total",
                "success"
            )
        
        return redirect(url_for('email_admin.queue'))
        
    except Exception as e:
        logger.error(f"Error processing email queue: {e}")
        flash(f"Error processing email queue: {e}", "error")
        return redirect(url_for('email_admin.queue'))


@email_admin.route('/queue/<int:email_id>/retry')
@admin_required
def retry_email(email_id):
    """Retry a failed email"""
    try:
        email = EmailQueue.query.get_or_404(email_id)
        
        if email.status not in [EmailStatus.FAILED, EmailStatus.EXPIRED]:
            flash("Email is not in a failed or expired state", "warning")
            return redirect(url_for('email_admin.queue'))
        
        # Reset email for retry
        email.status = EmailStatus.RETRY
        email.retry_count = 0
        email.scheduled_at = datetime.utcnow()
        email.expires_at = datetime.utcnow() + timedelta(hours=72)
        email.last_error = None
        
        db.session.commit()
        
        # Try to process immediately
        success = EmailManager.process_queue_item(email)
        
        if success:
            flash("Email retried successfully!", "success")
        else:
            flash("Email queued for retry", "info")
        
        return redirect(url_for('email_admin.queue'))
        
    except Exception as e:
        logger.error(f"Error retrying email: {e}")
        flash(f"Error retrying email: {e}", "error")
        return redirect(url_for('email_admin.queue'))


@email_admin.route('/logs')
@admin_required
def logs():
    """Email logs"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        email_type_filter = request.args.get('email_type', 'all')
        per_page = 50
        
        # Build query
        query = EmailLog.query
        
        if status_filter != 'all':
            try:
                status_enum = EmailStatus(status_filter)
                query = query.filter(EmailLog.status == status_enum)
            except ValueError:
                flash(f"Invalid status filter: {status_filter}", "warning")
        
        if email_type_filter != 'all':
            query = query.filter(EmailLog.email_type == email_type_filter)
        
        # Paginate results
        logs = query.order_by(EmailLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Get available email types for filter
        email_types = db.session.query(EmailLog.email_type).distinct().all()
        email_types = [t[0] for t in email_types if t[0]]
        
        return render_template(
            'admin/email/logs.html',
            logs=logs,
            status_filter=status_filter,
            email_type_filter=email_type_filter,
            email_types=email_types,
            EmailStatus=EmailStatus
        )
        
    except Exception as e:
        logger.error(f"Error loading email logs: {e}")
        flash(f"Error loading email logs: {e}", "error")
        return redirect(url_for('email_admin.dashboard'))


@email_admin.route('/templates')
@admin_required
def templates():
    """Email templates management"""
    try:
        templates = EmailTemplate.query.filter_by(is_active=True).order_by(
            EmailTemplate.name
        ).all()
        
        return render_template(
            'admin/email/templates.html',
            templates=templates
        )
        
    except Exception as e:
        logger.error(f"Error loading email templates: {e}")
        flash(f"Error loading email templates: {e}", "error")
        return redirect(url_for('email_admin.dashboard'))


@email_admin.route('/templates/create', methods=['GET', 'POST'])
@admin_required
def create_template():
    """Create new email template"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            subject = request.form.get('subject', '').strip()
            html_content = request.form.get('html_content', '').strip()
            text_content = request.form.get('text_content', '').strip()
            description = request.form.get('description', '').strip()
            variables_str = request.form.get('variables', '').strip()
            
            # Validate required fields
            if not name or not subject or not html_content:
                flash("Name, subject, and HTML content are required", "error")
                return render_template('admin/email/create_template.html')
            
            # Parse variables
            variables = []
            if variables_str:
                variables = [v.strip() for v in variables_str.split(',') if v.strip()]
            
            # Create template
            template = EmailTemplateManager.create_template(
                name=name,
                subject=subject,
                html_content=html_content,
                text_content=text_content or None,
                description=description or None,
                variables=variables,
                created_by_id=current_user.id
            )
            
            flash(f"Email template '{name}' created successfully!", "success")
            return redirect(url_for('email_admin.templates'))
            
        except Exception as e:
            logger.error(f"Error creating email template: {e}")
            flash(f"Error creating email template: {e}", "error")
    
    return render_template('admin/email/create_template.html')


@email_admin.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_template(template_id):
    """Edit email template"""
    template = EmailTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        try:
            template.name = request.form.get('name', '').strip()
            template.subject = request.form.get('subject', '').strip()
            template.html_content = request.form.get('html_content', '').strip()
            template.text_content = request.form.get('text_content', '').strip()
            template.description = request.form.get('description', '').strip()
            variables_str = request.form.get('variables', '').strip()
            
            # Validate required fields
            if not template.name or not template.subject or not template.html_content:
                flash("Name, subject, and HTML content are required", "error")
                return render_template('admin/email/edit_template.html', template=template)
            
            # Parse variables
            variables = []
            if variables_str:
                variables = [v.strip() for v in variables_str.split(',') if v.strip()]
            
            template.variables = variables
            template.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f"Email template '{template.name}' updated successfully!", "success")
            return redirect(url_for('email_admin.templates'))
            
        except Exception as e:
            logger.error(f"Error updating email template: {e}")
            flash(f"Error updating email template: {e}", "error")
            db.session.rollback()
    
    return render_template('admin/email/edit_template.html', template=template)


@email_admin.route('/templates/<int:template_id>/test', methods=['GET', 'POST'])
@admin_required
def test_template(template_id):
    """Test email template"""
    template = EmailTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        try:
            test_email = request.form.get('test_email', '').strip()
            if not test_email:
                flash("Test email address is required", "error")
                return render_template('admin/email/test_template.html', template=template)
            
            # Prepare test variables
            test_variables = {
                'user_name': 'Test User',
                'first_name': 'Test',
                'user_email': test_email,
                'company_name': 'Test Company',
                'plan_name': 'Test Plan',
                'amount': '10.00',
                'start_date': datetime.now().strftime('%B %d, %Y')
            }
            
            # Add any custom variables from form
            for key in request.form:
                if key.startswith('var_'):
                    var_name = key[4:]  # Remove 'var_' prefix
                    test_variables[var_name] = request.form[key]
            
            # Send test email
            success = EmailTemplateManager.send_from_template(
                template_name=template.name,
                to_email=test_email,
                variables=test_variables,
                email_type='template_test'
            )
            
            if success:
                flash(f"Test email sent to {test_email}!", "success")
            else:
                flash("Failed to send test email", "error")
            
        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            flash(f"Error sending test email: {e}", "error")
    
    return render_template('admin/email/test_template.html', template=template)


@email_admin.route('/campaigns')
@admin_required
def campaigns():
    """Email campaigns management"""
    try:
        campaigns = EmailCampaign.query.order_by(
            EmailCampaign.created_at.desc()
        ).all()
        
        return render_template(
            'admin/email/campaigns.html',
            campaigns=campaigns
        )
        
    except Exception as e:
        logger.error(f"Error loading email campaigns: {e}")
        flash(f"Error loading email campaigns: {e}", "error")
        return redirect(url_for('email_admin.dashboard'))


@email_admin.route('/campaigns/create', methods=['GET', 'POST'])
@admin_required
def create_campaign():
    """Create new email campaign"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            template_id = request.form.get('template_id', type=int)
            target_type = request.form.get('target_type', 'all_users')
            send_now = request.form.get('send_now') == 'on'
            
            # Validate required fields
            if not name or not template_id:
                flash("Name and template are required", "error")
                return redirect(url_for('email_admin.create_campaign'))
            
            # Create campaign
            campaign = EmailCampaignManager.create_campaign(
                name=name,
                template_id=template_id,
                target_type=target_type,
                description=description,
                created_by_id=current_user.id
            )
            
            if send_now:
                # Send campaign immediately
                result = EmailCampaignManager.send_campaign(campaign.id)
                if 'error' in result:
                    flash(f"Campaign created but failed to send: {result['error']}", "error")
                else:
                    flash(
                        f"Campaign '{name}' created and sent! "
                        f"{result['sent']} emails sent, {result['failed']} failed",
                        "success"
                    )
            else:
                flash(f"Campaign '{name}' created successfully!", "success")
            
            return redirect(url_for('email_admin.campaigns'))
            
        except Exception as e:
            logger.error(f"Error creating email campaign: {e}")
            flash(f"Error creating email campaign: {e}", "error")
    
    # Get templates for dropdown
    templates = EmailTemplate.query.filter_by(is_active=True).order_by(
        EmailTemplate.name
    ).all()
    
    return render_template(
        'admin/email/create_campaign.html',
        templates=templates
    )


@email_admin.route('/campaigns/<int:campaign_id>/send')
@admin_required
def send_campaign_redirect(campaign_id):
    """Send email campaign (redirect version)"""
    try:
        result = EmailCampaignManager.send_campaign(campaign_id)
        
        if 'error' in result:
            flash(f"Error sending campaign: {result['error']}", "error")
        else:
            flash(
                f"Campaign sent! {result['sent']} emails sent, {result['failed']} failed",
                "success"
            )
        
        return redirect(url_for('email_admin.campaigns'))
        
    except Exception as e:
        logger.error(f"Error sending campaign: {e}")
        flash(f"Error sending campaign: {e}", "error")
        return redirect(url_for('email_admin.campaigns'))


@email_admin.route('/send-individual', methods=['GET', 'POST'])
@admin_required
def send_individual():
    """Send individual email to users"""
    if request.method == 'POST':
        try:
            recipient_type = request.form.get('recipient_type')
            recipient_id = request.form.get('recipient_id', type=int)
            template_id = request.form.get('template_id', type=int)
            custom_subject = request.form.get('custom_subject', '').strip()
            custom_variables = {}
            
            # Get custom variables from form
            for key in request.form:
                if key.startswith('var_'):
                    var_name = key[4:]  # Remove 'var_' prefix
                    custom_variables[var_name] = request.form[key]
            
            # Get recipient
            if recipient_type == 'user':
                recipient = User.query.get(recipient_id)
            elif recipient_type == 'partner':
                partner = Partner.query.get(recipient_id)
                recipient = partner.owner if partner else None
            else:
                flash("Invalid recipient type", "error")
                return redirect(url_for('email_admin.send_individual'))
            
            if not recipient:
                flash("Recipient not found", "error")
                return redirect(url_for('email_admin.send_individual'))
            
            # Get template
            template = EmailTemplate.query.get(template_id)
            if not template:
                flash("Template not found", "error")
                return redirect(url_for('email_admin.send_individual'))
            
            # Prepare variables
            variables = {
                'user_name': recipient.get_full_name(),
                'first_name': recipient.first_name or 'there',
                'user_email': recipient.email,
                **custom_variables
            }
            
            # Render content
            rendered = template.render_content(variables)
            
            # Use custom subject if provided
            if custom_subject:
                rendered['subject'] = custom_subject
            
            # Send email
            queue_item = EmailManager.queue_email(
                to_email=recipient.email,
                subject=rendered['subject'],
                html_body=rendered['html_content'],
                text_body=rendered['text_content'],
                template_id=template.id,
                user_id=recipient.id,
                email_type='admin_individual',
                metadata={
                    'sent_by_admin': current_user.id,
                    'template_name': template.name
                }
            )
            
            if queue_item.status == EmailStatus.SENT:
                flash(f"Email sent successfully to {recipient.email}!", "success")
            else:
                flash(f"Email queued for sending to {recipient.email}", "info")
            
            return redirect(url_for('email_admin.send_individual'))
            
        except Exception as e:
            logger.error(f"Error sending individual email: {e}")
            flash(f"Error sending individual email: {e}", "error")
    
    # Get data for form
    templates = EmailTemplate.query.filter_by(is_active=True).order_by(
        EmailTemplate.name
    ).all()
    
    users = User.query.order_by(
        User.first_name, User.last_name
    ).all()
    
    partners = Partner.query.filter_by(status='active').order_by(
        Partner.company_name
    ).all()
    
    return render_template(
        'admin/email/send_individual.html',
        templates=templates,
        users=users,
        partners=partners
    )


@email_admin.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for email statistics"""
    try:
        stats = EmailManager.get_queue_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@email_admin.route('/cleanup')
@admin_required
def cleanup():
    """Clean up old emails"""
    try:
        days = request.args.get('days', 30, type=int)
        result = EmailManager.cleanup_old_emails(days=days)
        
        if 'error' in result:
            flash(f"Error cleaning up emails: {result['error']}", "error")
        else:
            flash(
                f"Cleaned up {result['logs_deleted']} old logs and "
                f"{result['queue_deleted']} old queue items",
                "success"
            )
        
        return redirect(url_for('email_admin.dashboard'))
        
    except Exception as e:
        logger.error(f"Error cleaning up emails: {e}")
        flash(f"Error cleaning up emails: {e}", "error")
        return redirect(url_for('email_admin.dashboard'))


@email_admin.route('/templates/<int:template_id>/delete', methods=['DELETE'])
@admin_required
def delete_template(template_id):
    """Delete email template"""
    try:
        template = EmailTemplate.query.get_or_404(template_id)
        
        # Check if template is being used by any campaigns
        campaigns_using = EmailCampaign.query.filter_by(template_id=template_id).count()
        if campaigns_using > 0:
            return jsonify({
                'success': False,
                'message': f'Cannot delete template. It is being used by {campaigns_using} campaign(s).'
            }), 400
        
        template_name = template.name
        db.session.delete(template)
        db.session.commit()
        
        logger.info(f"Email template '{template_name}' deleted by admin {current_user.id}")
        return jsonify({
            'success': True,
            'message': f'Template "{template_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@email_admin.route('/templates/<int:template_id>/preview')
@admin_required
def preview_template(template_id):
    """Preview email template"""
    try:
        template = EmailTemplate.query.get_or_404(template_id)
        
        # Use sample variables for preview
        sample_variables = {
            'user_name': 'John Doe',
            'first_name': 'John',
            'user_email': 'john.doe@example.com',
            'company_name': 'Sample Company',
            'subscription_plan': 'Professional Plan',
            'expiry_date': '2025-12-31'
        }
        
        rendered = template.render_content(sample_variables)
        
        return render_template(
            'admin/email/preview_template.html',
            template=template,
            rendered=rendered,
            sample_variables=sample_variables
        )
        
    except Exception as e:
        logger.error(f"Error previewing template: {e}")
        flash(f"Error previewing template: {e}", "error")
        return redirect(url_for('email_admin.templates'))


@email_admin.route('/campaigns/<int:campaign_id>/delete', methods=['DELETE'])
@admin_required
def delete_campaign(campaign_id):
    """Delete email campaign"""
    try:
        campaign = EmailCampaign.query.get_or_404(campaign_id)
        
        # Only allow deletion of draft campaigns
        if campaign.status != 'draft':
            return jsonify({
                'success': False,
                'message': 'Only draft campaigns can be deleted'
            }), 400
        
        campaign_name = campaign.name
        db.session.delete(campaign)
        db.session.commit()
        
        logger.info(f"Email campaign '{campaign_name}' deleted by admin {current_user.id}")
        return jsonify({
            'success': True,
            'message': f'Campaign "{campaign_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@email_admin.route('/campaigns/<int:campaign_id>/send', methods=['POST'])
@admin_required
def send_campaign(campaign_id):
    """Send campaign via API"""
    try:
        result = EmailCampaignManager.send_campaign(campaign_id)
        
        if 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 400
        
        return jsonify({
            'success': True,
            'message': f"Campaign sent! {result['sent']} emails sent, {result['failed']} failed",
            'sent': result['sent'],
            'failed': result['failed']
        })
        
    except Exception as e:
        logger.error(f"Error sending campaign: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@email_admin.route('/campaigns/<int:campaign_id>')
@admin_required
def view_campaign(campaign_id):
    """View campaign details"""
    try:
        campaign = EmailCampaign.query.get_or_404(campaign_id)
        
        # Get campaign stats
        sent_emails = EmailLog.query.filter(
            EmailLog.email_metadata['campaign_id'].astext == str(campaign_id),
            EmailLog.status == EmailStatus.SENT
        ).count()
        
        failed_emails = EmailLog.query.filter(
            EmailLog.email_metadata['campaign_id'].astext == str(campaign_id),
            EmailLog.status == EmailStatus.FAILED
        ).count()
        
        return render_template(
            'admin/email/view_campaign.html',
            campaign=campaign,
            sent_emails=sent_emails,
            failed_emails=failed_emails
        )
        
    except Exception as e:
        logger.error(f"Error viewing campaign: {e}")
        flash(f"Error viewing campaign: {e}", "error")
        return redirect(url_for('email_admin.campaigns'))


@email_admin.route('/queue/<int:email_id>/delete', methods=['DELETE'])
@admin_required
def delete_queue_item(email_id):
    """Delete email from queue"""
    try:
        queue_item = EmailQueue.query.get_or_404(email_id)
        
        db.session.delete(queue_item)
        db.session.commit()
        
        logger.info(f"Email queue item {email_id} deleted by admin {current_user.id}")
        return jsonify({'success': True, 'message': 'Email deleted from queue'})
        
    except Exception as e:
        logger.error(f"Error deleting queue item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@email_admin.route('/queue/<int:email_id>')
@admin_required
def view_email(email_id):
    """View email details"""
    try:
        queue_item = EmailQueue.query.get_or_404(email_id)
        
        return render_template(
            'admin/email/view_email.html',
            queue_item=queue_item
        )
        
    except Exception as e:
        logger.error(f"Error viewing email: {e}")
        flash(f"Error viewing email: {e}", "error")
        return redirect(url_for('email_admin.queue'))


@email_admin.route('/queue/clear-failed', methods=['DELETE'])
@admin_required
def clear_failed():
    """Clear all failed emails from queue"""
    try:
        deleted_count = EmailQueue.query.filter_by(status=EmailStatus.FAILED).delete()
        db.session.commit()
        
        logger.info(f"Cleared {deleted_count} failed emails from queue by admin {current_user.id}")
        return jsonify({
            'success': True,
            'message': f'{deleted_count} failed emails cleared',
            'cleared': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error clearing failed emails: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@email_admin.route('/logs/<int:log_id>')
@admin_required
def view_log_details(log_id):
    """API endpoint for log details"""
    try:
        log = EmailLog.query.get_or_404(log_id)
        
        # Get message_id from metadata if available
        message_id = None
        if log.email_metadata and isinstance(log.email_metadata, dict):
            message_id = log.email_metadata.get('message_id')
        
        # Get HTML content from queue item if available
        html_content = None
        if log.queue_item:
            html_content = log.queue_item.html_body
        
        return jsonify({
            'success': True,
            'log': {
                'id': log.id,
                'status': log.status.value,
                'to_email': log.to_email,
                'subject': log.subject,
                'email_type': log.email_type,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sent_at': log.sent_at.strftime('%Y-%m-%d %H:%M:%S') if log.sent_at else None,
                'message_id': message_id,
                'template_name': log.template.name if log.template else None,
                'error_message': log.error_message,
                'html_content': html_content
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting log details: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
