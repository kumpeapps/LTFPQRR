"""
Email utility functions for LTFPQRR system
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import current_app, render_template_string
from extensions import logger


def get_smtp_config():
    """Get SMTP configuration from database settings"""
    try:
        from models.models import SystemSetting
        
        smtp_settings = {}
        settings = SystemSetting.query.filter(
            SystemSetting.key.in_([
                'smtp_server', 'smtp_port', 'smtp_username', 'smtp_password',
                'smtp_use_tls', 'smtp_use_ssl', 'smtp_from_email', 'smtp_from_name'
            ])
        ).all()
        
        for setting in settings:
            if setting.key in ['smtp_use_tls', 'smtp_use_ssl']:
                # Handle both boolean and string values
                if isinstance(setting.value, bool):
                    smtp_settings[setting.key] = setting.value
                else:
                    smtp_settings[setting.key] = str(setting.value).lower() == 'true'
            elif setting.key == 'smtp_port':
                smtp_settings[setting.key] = int(setting.value) if setting.value else 587
            else:
                smtp_settings[setting.key] = setting.value
        
        return smtp_settings
    except Exception as e:
        logger.error(f"Error getting SMTP configuration: {e}")
        return {}


def send_email(to_email, subject, html_body, text_body=None, from_email=None, from_name=None):
    """Send an email using configured SMTP settings"""
    try:
        smtp_config = get_smtp_config()
        
        if not smtp_config.get('smtp_server'):
            logger.warning("SMTP not configured, cannot send email")
            return False
        
        # Create message
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = from_email or f"{from_name or smtp_config.get('smtp_from_name', 'LTFPQRR')} <{smtp_config.get('smtp_from_email', 'noreply@ltfpqrr.com')}>"
        msg['To'] = to_email
        
        # Create a multipart/alternative container
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        # Add text and HTML parts
        if text_body:
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            msg_alternative.attach(text_part)
        
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg_alternative.attach(html_part)
        
        # Attach logo image
        try:
            import os
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'assets', 'logo', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                
                logo_attachment = MIMEBase('image', 'png')
                logo_attachment.set_payload(logo_data)
                encoders.encode_base64(logo_attachment)
                logo_attachment.add_header('Content-ID', '<logo>')
                logo_attachment.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(logo_attachment)
        except Exception as e:
            logger.warning(f"Could not attach logo: {e}")
        
        # Send email
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config.get('smtp_port', 587)) as server:
            if smtp_config.get('smtp_use_tls', True):
                server.starttls()
            
            if smtp_config.get('smtp_username') and smtp_config.get('smtp_password'):
                server.login(smtp_config['smtp_username'], smtp_config['smtp_password'])
            
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return False


def get_email_template_base():
    """Get the base email template with LTFPQRR branding"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LTFPQRR</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333333;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px 0;
            }
            
            .email-container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                border-radius: 16px;
                overflow: hidden;
                border: 1px solid #e9ecef;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 30px;
                text-align: center;
                color: white;
                position: relative;
                overflow: hidden;
            }
            
            .header::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><circle cx="200" cy="200" r="100" fill="rgba(255,255,255,0.05)"/><circle cx="800" cy="300" r="150" fill="rgba(255,255,255,0.03)"/><circle cx="300" cy="700" r="80" fill="rgba(255,255,255,0.04)"/></svg>');
                pointer-events: none;
            }
            
            .logo-container {
                position: relative;
                z-index: 2;
                margin-bottom: 15px;
            }
            
            .logo-img {
                max-width: 120px;
                height: auto;
                margin-bottom: 10px;
                filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
            }
            
            .logo-img {
                max-width: 120px;
                height: auto;
                margin-bottom: 10px;
                filter: brightness(0) invert(1);
            }
            
            .logo-text {
                font-size: 2.8rem;
                font-weight: 700;
                color: #13c1be;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                font-family: 'Comic Sans MS', cursive, sans-serif;
                margin-bottom: 5px;
                line-height: 1.1;
            }
            
            .tagline {
                font-size: 1.1rem;
                color: rgba(255, 255, 255, 0.95);
                font-weight: 400;
                position: relative;
                z-index: 2;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            }
            
            .content {
                padding: 45px 35px;
                background: #ffffff;
            }
            
            .greeting {
                font-size: 1.15rem;
                margin-bottom: 25px;
                color: #495057;
                font-weight: 500;
            }
            
            .title {
                font-size: 1.6rem;
                font-weight: 700;
                color: #212529;
                margin-bottom: 25px;
                line-height: 1.3;
            }
            
            .subtitle {
                font-size: 1.1rem;
                color: #6c757d;
                margin-bottom: 25px;
                line-height: 1.5;
            }
            
            .info-box {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-left: 5px solid #13c1be;
                padding: 25px;
                margin: 25px 0;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            
            .success-box {
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border-left: 5px solid #28a745;
                padding: 25px;
                margin: 25px 0;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(40, 167, 69, 0.1);
            }
            
            .warning-box {
                background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
                border-left: 5px solid #ffc107;
                padding: 25px;
                margin: 25px 0;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(255, 193, 7, 0.1);
            }
            
            .error-box {
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                border-left: 5px solid #dc3545;
                padding: 25px;
                margin: 25px 0;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(220, 53, 69, 0.1);
            }
            
            .box-title {
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 15px;
                color: #495057;
                display: flex;
                align-items: center;
            }
            
            .box-title .icon {
                margin-right: 10px;
                font-size: 1.3rem;
            }
            
            .details-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            
            .details-table td {
                padding: 15px 12px;
                border-bottom: 1px solid #f1f3f4;
            }
            
            .details-table tr:last-child td {
                border-bottom: none;
            }
            
            .details-table td:first-child {
                font-weight: 600;
                color: #495057;
                width: 35%;
                background: #f8f9fa;
            }
            
            .details-table td:last-child {
                color: #212529;
            }
            
            .cta-button {
                display: inline-block;
                background: linear-gradient(135deg, #13c1be 0%, #667eea 100%);
                color: white;
                padding: 16px 32px;
                text-decoration: none;
                border-radius: 12px;
                font-weight: 600;
                font-size: 1.05rem;
                margin: 25px 0;
                box-shadow: 0 6px 20px rgba(19, 193, 190, 0.3);
                transition: all 0.3s ease;
                text-align: center;
            }
            
            .cta-button:hover {
                background: linear-gradient(135deg, #667eea 0%, #13c1be 100%);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(19, 193, 190, 0.4);
                color: white;
                text-decoration: none;
            }
            
            .footer {
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: #ecf0f1;
                padding: 35px 30px;
                text-align: center;
                font-size: 0.95rem;
            }
            
            .footer-logo {
                font-size: 1.5rem;
                font-weight: 700;
                color: #13c1be;
                margin-bottom: 15px;
                font-family: 'Comic Sans MS', cursive, sans-serif;
            }
            
            .footer-text {
                margin-bottom: 20px;
                line-height: 1.6;
            }
            
            .footer a {
                color: #13c1be;
                text-decoration: none;
                font-weight: 500;
            }
            
            .footer a:hover {
                text-decoration: underline;
                color: #0fa8a5;
            }
            
            .divider {
                height: 2px;
                background: linear-gradient(135deg, #13c1be 0%, #667eea 100%);
                margin: 25px 0;
                border-radius: 1px;
            }
            
            @media (max-width: 600px) {
                body {
                    padding: 10px 0;
                }
                
                .email-container {
                    margin: 0 10px;
                    border-radius: 12px;
                }
                
                .content {
                    padding: 35px 25px;
                }
                
                .header {
                    padding: 30px 20px;
                }
                
                .logo-text {
                    font-size: 2.2rem;
                }
                
                .tagline {
                    font-size: 1rem;
                }
                
                .title {
                    font-size: 1.4rem;
                }
                
                .cta-button {
                    padding: 14px 28px;
                    font-size: 1rem;
                }
                
                .details-table td {
                    padding: 12px 8px;
                    font-size: 0.9rem;
                }
                
                .details-table td:first-child {
                    width: 40%;
                }
            }
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo-container">
                    <img src="cid:logo" alt="LTFPQRR Logo" class="logo-img" style="max-width: 120px; height: auto; margin-bottom: 10px; filter: brightness(0) invert(1);">
                    <div class="logo-text">LTFPQRR</div>
                </div>
                <div class="tagline">Lost & Found Pet Recovery System</div>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <div class="footer-logo">LTFPQRR</div>
                <div class="footer-text">
                    <strong>Helping reunite lost pets with their families</strong>
                </div>
                <p>
                    Need help? Contact us at <a href="mailto:support@ltfpqrr.com">support@ltfpqrr.com</a><br>
                    <small style="color: #bdc3c7;">© 2025 LTFPQRR. All rights reserved.</small>
                </p>
            </div>
        </div>
    </body>
    </html>
    """


def send_subscription_confirmation_email(user, subscription):
    """Send subscription confirmation email to customer"""
    try:
        # Determine subscription type details
        if subscription.subscription_type == 'partner':
            subject = "Partner Subscription Confirmed - Pending Approval"
            plan_name = subscription.pricing_plan.name if subscription.pricing_plan else "Partner Plan"
            status_box_class = "warning-box"
            status_message = "Your subscription is pending admin approval. You will receive another email once approved."
        else:
            subject = "Tag Subscription Confirmed - Active"
            plan_name = subscription.pricing_plan.name if subscription.pricing_plan else "Tag Plan"
            status_box_class = "success-box"
            status_message = "Your subscription is now active!"
        
        content = f"""
        <div class="greeting">Hello {user.get_full_name()},</div>
        
        <div class="title">Thank you for your subscription!</div>
        
        <div class="subtitle">We have successfully processed your payment and created your subscription. Here are the details:</div>
        
        <div class="info-box">
            <div class="box-title">Subscription Details</div>
            <table class="details-table">
                <tr>
                    <td>Plan:</td>
                    <td><strong>{plan_name}</strong></td>
                </tr>
                <tr>
                    <td>Amount:</td>
                    <td><strong>${subscription.amount}</strong></td>
                </tr>
                <tr>
                    <td>Billing:</td>
                    <td>{subscription.pricing_plan.billing_period.title() if subscription.pricing_plan else 'One-time'}</td>
                </tr>
                <tr>
                    <td>Start Date:</td>
                    <td>{subscription.start_date.strftime('%B %d, %Y')}</td>
                </tr>
                {f'<tr><td>End Date:</td><td>{subscription.end_date.strftime("%B %d, %Y")}</td></tr>' if subscription.end_date else ''}
                {f'<tr><td>Max Tags:</td><td>{subscription.max_tags}</td></tr>' if hasattr(subscription, 'max_tags') and subscription.max_tags else ''}
            </table>
        </div>
        
        <div class="{status_box_class}">
            <div class="box-title">Status Update</div>
            <p>{status_message}</p>
        </div>
        
        <div class="divider"></div>
        
        {f'<a href="http://localhost:8000/partner" class="cta-button">Access Partner Dashboard</a>' if subscription.subscription_type == 'partner' else '<a href="http://localhost:8000/dashboard" class="cta-button">Access Your Dashboard</a>'}
        
        <p>Thank you for choosing LTFPQRR! If you have any questions, our support team is here to help.</p>
        """
        
        template = get_email_template_base()
        html_body = template.format(content=content)
        
        text_body = f"""
        Hello {user.get_full_name()},
        
        Thank you for your subscription!
        
        Subscription Details:
        - Plan: {plan_name}
        - Amount: ${subscription.amount}
        - Billing: {subscription.pricing_plan.billing_period.title() if subscription.pricing_plan else 'One-time'}
        - Start Date: {subscription.start_date.strftime('%B %d, %Y')}
        {f'- End Date: {subscription.end_date.strftime("%B %d, %Y")}' if subscription.end_date else ''}
        {f'- Max Tags: {subscription.max_tags}' if hasattr(subscription, 'max_tags') and subscription.max_tags else ''}
        
        Status: {status_message}
        
        Best regards,
        The LTFPQRR Team
        """
        
        success = send_email(user.email, subject, html_body, text_body)
        if success:
            logger.info(f"Subscription confirmation email sent to {user.email}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending subscription confirmation email: {e}")
        return False


def send_admin_approval_notification(subscription):
    """Send notification to admins when a partner subscription needs approval"""
    try:
        from models.models import User, Role
        
        # Get all admin users
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            logger.warning("No admin role found")
            return False
            
        admin_users = admin_role.users
        if not admin_users:
            logger.warning("No admin users found")
            return False
        
        subject = "New Partner Subscription Requires Approval"
        partner_name = subscription.partner.company_name if subscription.partner else "Unknown Partner"
        user_name = subscription.user.get_full_name()
        plan_name = subscription.pricing_plan.name if subscription.pricing_plan else "Partner Plan"
        
        content = f"""
        <div class="greeting">Hello Admin,</div>
        
        <div class="title">New Partner Subscription Awaiting Approval</div>
        
        <div class="subtitle">A new partner subscription has been purchased and requires your approval.</div>
        
        <div class="info-box">
            <div class="box-title">Subscription Details</div>
            <table class="details-table">
                <tr>
                    <td>Partner:</td>
                    <td><strong>{partner_name}</strong></td>
                </tr>
                <tr>
                    <td>User:</td>
                    <td><strong>{user_name}</strong> ({subscription.user.email})</td>
                </tr>
                <tr>
                    <td>Plan:</td>
                    <td><strong>{plan_name}</strong></td>
                </tr>
                <tr>
                    <td>Amount:</td>
                    <td><strong>${subscription.amount}</strong></td>
                </tr>
                <tr>
                    <td>Payment Date:</td>
                    <td>{subscription.start_date.strftime('%B %d, %Y at %I:%M %p')}</td>
                </tr>
            </table>
        </div>
        
        <div class="warning-box">
            <div class="box-title">Action Required</div>
            <p>Please log into the admin panel to review and approve this subscription.</p>
        </div>
        
        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/admin/subscriptions" class="cta-button">Review Subscription</a>
        
        <p>This is an automated notification from the LTFPQRR system.</p>
        """
        
        template = get_email_template_base()
        html_body = template.format(content=content)
        
        text_body = f"""
        Hello Admin,
        
        A new partner subscription requires approval:
        
        - Partner: {partner_name}
        - User: {user_name} ({subscription.user.email})
        - Plan: {plan_name}
        - Amount: ${subscription.amount}
        - Payment Date: {subscription.start_date.strftime('%B %d, %Y at %I:%M %p')}
        
        Please log into the admin panel to review and approve this subscription.
        
        Admin Panel: {current_app.config.get('BASE_URL', 'http://localhost:5000')}/admin/subscriptions
        
        This is an automated notification from the LTFPQRR system.
        """
        
        # Send to all admin users
        success_count = 0
        for admin_user in admin_users:
            if send_email(admin_user.email, subject, html_body, text_body):
                success_count += 1
        
        logger.info(f"Admin approval notification sent to {success_count}/{len(admin_users)} admin users")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending admin approval notification: {e}")
        return False


def send_subscription_approved_email(user, subscription):
    """Send email to customer when subscription is approved"""
    try:
        subject = "Partner Subscription Approved - Welcome to LTFPQRR!"
        
        plan_name = subscription.pricing_plan.name if subscription.pricing_plan else "Partner Plan"
        partner_name = subscription.partner.company_name if subscription.partner else "Your Partner Account"
        
        content = f"""
        <div class="greeting">Hello {user.get_full_name()},</div>
        
        <div class="title">Congratulations! Your Partner Subscription is Approved</div>
        
        <div class="subtitle">Great news! Your partner subscription has been approved by our admin team. Welcome to the LTFPQRR partner network!</div>
        
        <div class="success-box">
            <div class="box-title">Your Active Subscription</div>
            <table class="details-table">
                <tr>
                    <td>Company:</td>
                    <td><strong>{partner_name}</strong></td>
                </tr>
                <tr>
                    <td>Plan:</td>
                    <td><strong>{plan_name}</strong></td>
                </tr>
                <tr>
                    <td>Status:</td>
                    <td><span style="color: #28a745; font-weight: 600;">Active</span></td>
                </tr>
                <tr>
                    <td>Start Date:</td>
                    <td>{subscription.start_date.strftime('%B %d, %Y')}</td>
                </tr>
                {f'<tr><td>End Date:</td><td>{subscription.end_date.strftime("%B %d, %Y")}</td></tr>' if subscription.end_date else ''}
                <tr>
                    <td>Billing:</td>
                    <td>{subscription.pricing_plan.billing_period.title() if subscription.pricing_plan else 'One-time'}</td>
                </tr>
                <tr>
                    <td>Max Tags:</td>
                    <td>{subscription.max_tags if hasattr(subscription, 'max_tags') else 'Unlimited'}</td>
                </tr>
            </table>
        </div>
        
        <div class="info-box">
            <div class="box-title">What's Next?</div>
            <ul style="margin: 15px 0; padding-left: 20px;">
                <li>Access your partner dashboard to manage your tags and services</li>
                <li>Start creating and managing lost pet tags for your customers</li>
                <li>Set up your partner profile and contact information</li>
                <li>Review our partner guidelines and best practices</li>
            </ul>
        </div>
        
        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/partner" class="cta-button">Access Partner Dashboard</a>
        
        <div class="divider"></div>
        
        <p>Thank you for joining LTFPQRR as a partner! We look forward to working with you to help reunite lost pets with their families.</p>
        
        <p>Best regards,<br>The LTFPQRR Team</p>
        """
        
        template = get_email_template_base()
        html_body = template.format(content=content)
        
        text_body = f"""
        Hello {user.get_full_name()},
        
        Congratulations! Your partner subscription has been approved.
        
        Active Subscription Details:
        - Company: {partner_name}
        - Plan: {plan_name}
        - Status: Active
        - Start Date: {subscription.start_date.strftime('%B %d, %Y')}
        {f'- End Date: {subscription.end_date.strftime("%B %d, %Y")}' if subscription.end_date else ''}
        - Max Tags: {subscription.max_tags if hasattr(subscription, 'max_tags') else 'Unlimited'}
        
        Access Partner Dashboard: {current_app.config.get('BASE_URL', 'http://localhost:5000')}/partner
        
        Best regards,
        The LTFPQRR Team
        """
        
        success = send_email(user.email, subject, html_body, text_body)
        if success:
            logger.info(f"Subscription approved email sent to {user.email}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending subscription approved email: {e}")
        return False


def send_subscription_cancelled_email(user, subscription, refunded=False):
    """Send email to customer when subscription is cancelled"""
    try:
        subject = "Subscription Cancelled - LTFPQRR"
        
        plan_name = subscription.pricing_plan.name if subscription.pricing_plan else "Subscription Plan"
        refund_message = "A refund has been processed and should appear in your account within 5-10 business days." if refunded else "No refund was processed for this cancellation."
        
        content = f"""
        <div class="greeting">Hello {user.get_full_name()},</div>
        
        <div class="title">Subscription Cancelled</div>
        
        <div class="subtitle">Your subscription has been cancelled as requested.</div>
        
        <div class="error-box">
            <div class="box-title">Cancelled Subscription</div>
            <table class="details-table">
                <tr>
                    <td>Plan:</td>
                    <td><strong>{plan_name}</strong></td>
                </tr>
                <tr>
                    <td>Amount:</td>
                    <td>${subscription.amount}</td>
                </tr>
                <tr>
                    <td>Original Start:</td>
                    <td>{subscription.start_date.strftime('%B %d, %Y')}</td>
                </tr>
                <tr>
                    <td>Cancelled:</td>
                    <td>{subscription.end_date.strftime('%B %d, %Y') if subscription.end_date else 'Today'}</td>
                </tr>
                <tr>
                    <td>Refund Status:</td>
                    <td>{'Processed' if refunded else 'None'}</td>
                </tr>
            </table>
        </div>
        
        <div class="info-box">
            <div class="box-title">Important Information</div>
            <p>{refund_message}</p>
            <p>If you have any questions about this cancellation, please contact our support team.</p>
        </div>
        
        <p>We're sorry to see you go. If you decide to return in the future, we'll be here to help you protect your pets.</p>
        
        <p>Best regards,<br>The LTFPQRR Team</p>
        """
        
        template = get_email_template_base()
        html_body = template.format(content=content)
        
        text_body = f"""
        Hello {user.get_full_name()},
        
        Your subscription has been cancelled.
        
        Cancelled Subscription:
        - Plan: {plan_name}
        - Amount: ${subscription.amount}
        - Original Start: {subscription.start_date.strftime('%B %d, %Y')}
        - Cancelled: {subscription.end_date.strftime('%B %d, %Y') if subscription.end_date else 'Today'}
        - Refund: {'Processed' if refunded else 'None'}
        
        {refund_message}
        
        Best regards,
        The LTFPQRR Team
        """
        
        success = send_email(user.email, subject, html_body, text_body)
        if success:
            logger.info(f"Subscription cancelled email sent to {user.email}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending subscription cancelled email: {e}")
        return False


def send_subscription_renewal_email(user, subscription):
    """Send email to customer when subscription is renewed"""
    try:
        subject = "Subscription Renewed - LTFPQRR"
        
        plan_name = subscription.pricing_plan.name if subscription.pricing_plan else "Subscription Plan"
        
        content = f"""
        <div class="greeting">Hello {user.get_full_name()},</div>
        
        <div class="title">Subscription Successfully Renewed</div>
        
        <div class="subtitle">Your subscription has been automatically renewed. Thank you for continuing with LTFPQRR!</div>
        
        <div class="success-box">
            <div class="box-title">Renewed Subscription</div>
            <table class="details-table">
                <tr>
                    <td>Plan:</td>
                    <td><strong>{plan_name}</strong></td>
                </tr>
                <tr>
                    <td>Amount:</td>
                    <td><strong>${subscription.amount}</strong></td>
                </tr>
                <tr>
                    <td>Renewed:</td>
                    <td>{subscription.start_date.strftime('%B %d, %Y')}</td>
                </tr>
                <tr>
                    <td>Next Renewal:</td>
                    <td>{subscription.end_date.strftime('%B %d, %Y') if subscription.end_date else 'N/A'}</td>
                </tr>
                <tr>
                    <td>Status:</td>
                    <td><span style="color: #28a745; font-weight: 600;">Active</span></td>
                </tr>
            </table>
        </div>
        
        <div class="info-box">
            <div class="box-title">Your Service Continues</div>
            <p>Your pet protection services continue without interruption. All your tags and settings remain active.</p>
            <p>To manage your subscription or update payment methods, visit your dashboard.</p>
        </div>
        
        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/dashboard" class="cta-button">Manage Subscription</a>
        
        <p>Thank you for your continued trust in LTFPQRR!</p>
        
        <p>Best regards,<br>The LTFPQRR Team</p>
        """
        
        template = get_email_template_base()
        html_body = template.format(content=content)
        
        text_body = f"""
        Hello {user.get_full_name()},
        
        Your subscription has been successfully renewed.
        
        Renewed Subscription:
        - Plan: {plan_name}
        - Amount: ${subscription.amount}
        - Renewed: {subscription.start_date.strftime('%B %d, %Y')}
        - Next Renewal: {subscription.end_date.strftime('%B %d, %Y') if subscription.end_date else 'N/A'}
        
        Your pet protection services continue without interruption.
        
        Best regards,
        The LTFPQRR Team
        """
        
        success = send_email(user.email, subject, html_body, text_body)
        if success:
            logger.info(f"Subscription renewal email sent to {user.email}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending subscription renewal email: {e}")
        return False


def send_test_email(to_email, test_type="basic"):
    """Send a test email to verify SMTP configuration"""
    try:
        if test_type == "basic":
            subject = "LTFPQRR - Test Email"
            content = """
            <div class="greeting">Hello!</div>
            
            <div class="title">SMTP Configuration Test</div>
            
            <div class="subtitle">This is a test email to verify that your SMTP configuration is working correctly.</div>
            
            <div class="success-box">
                <div class="box-title">Test Results</div>
                <p>If you are receiving this email, your SMTP settings are configured correctly!</p>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>SMTP server connection: ✓ Working</li>
                    <li>Email formatting: ✓ Working</li>
                    <li>Template rendering: ✓ Working</li>
                </ul>
            </div>
            
            <div class="info-box">
                <div class="box-title">Next Steps</div>
                <p>Your email system is ready to send notifications for:</p>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>Subscription confirmations</li>
                    <li>Admin notifications</li>
                    <li>Subscription approvals</li>
                    <li>Cancellation notices</li>
                    <li>Renewal reminders</li>
                </ul>
            </div>
            
            <p>Best regards,<br>The LTFPQRR Team</p>
            """
        else:
            subject = "LTFPQRR - Advanced Email Test"
            content = """
            <div class="greeting">Hello Administrator!</div>
            
            <div class="title">Advanced Email Template Test</div>
            
            <div class="subtitle">This test demonstrates all email styling components and features.</div>
            
            <div class="success-box">
                <div class="box-title">Success Box Example</div>
                <p>This is how success messages appear in emails.</p>
            </div>
            
            <div class="warning-box">
                <div class="box-title">Warning Box Example</div>
                <p>This is how warning messages appear in emails.</p>
            </div>
            
            <div class="error-box">
                <div class="box-title">Error Box Example</div>
                <p>This is how error messages appear in emails.</p>
            </div>
            
            <div class="info-box">
                <div class="box-title">Sample Data Table</div>
                <table class="details-table">
                    <tr>
                        <td>Email System:</td>
                        <td><strong>LTFPQRR v2.0</strong></td>
                    </tr>
                    <tr>
                        <td>Template Engine:</td>
                        <td>Custom HTML/CSS</td>
                    </tr>
                    <tr>
                        <td>Test Date:</td>
                        <td>January 12, 2025</td>
                    </tr>
                    <tr>
                        <td>Status:</td>
                        <td><span style="color: #28a745; font-weight: 600;">Working</span></td>
                    </tr>
                </table>
            </div>
            
            <a href="http://localhost:5000" class="cta-button">Visit LTFPQRR</a>
            
            <div class="divider"></div>
            
            <p>All email templates are working correctly and ready for production use.</p>
            
            <p>Best regards,<br>The LTFPQRR Development Team</p>
            """
        
        template = get_email_template_base()
        html_body = template.format(content=content)
        
        text_body = f"""
        LTFPQRR - Email Test
        
        This is a test email to verify SMTP configuration.
        
        If you receive this, your email system is working correctly!
        
        Best regards,
        The LTFPQRR Team
        """
        
        success = send_email(to_email, subject, html_body, text_body)
        if success:
            logger.info(f"Test email sent successfully to {to_email}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return False
