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
            SystemSetting.key.in_(
                [
                    "smtp_enabled",
                    "smtp_server",
                    "smtp_port",
                    "smtp_username",
                    "smtp_password",
                    "smtp_use_tls",
                    "smtp_use_ssl",
                    "smtp_from_email",
                    "smtp_from_name",
                ]
            )
        ).all()

        for setting in settings:
            if setting.key in ["smtp_use_tls", "smtp_use_ssl", "smtp_enabled"]:
                # Handle both boolean and string values
                if isinstance(setting.value, bool):
                    smtp_settings[setting.key] = setting.value
                else:
                    smtp_settings[setting.key] = str(setting.value).lower() == "true"
            elif setting.key == "smtp_port":
                smtp_settings[setting.key] = (
                    int(setting.value) if setting.value else 587
                )
            else:
                smtp_settings[setting.key] = setting.value

        return smtp_settings
    except Exception as e:
        logger.error(f"Error getting SMTP configuration: {e}")
        return {}


def send_email(
    to_email, subject, html_body, text_body=None, from_email=None, from_name=None
):
    """Send an email using configured SMTP settings"""
    try:
        smtp_config = get_smtp_config()

        # Check if SMTP is enabled
        if not smtp_config.get("smtp_enabled", False):
            logger.warning("SMTP is disabled, cannot send email")
            return False

        if not smtp_config.get("smtp_server"):
            logger.warning("SMTP not configured, cannot send email")
            return False

        # Create message
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = (
            from_email
            or f"{from_name or smtp_config.get('smtp_from_name', 'LTFPQRR')} <{smtp_config.get('smtp_from_email', 'noreply@ltfpqrr.com')}>"
        )
        msg["To"] = to_email

        # Create a multipart/alternative container
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        # Add text and HTML parts
        if text_body:
            text_part = MIMEText(text_body, "plain", "utf-8")
            msg_alternative.attach(text_part)

        html_part = MIMEText(html_body, "html", "utf-8")
        msg_alternative.attach(html_part)

        # Attach logo image
        try:
            import os

            logo_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "static",
                "assets",
                "logo",
                "logo.png",
            )
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_data = f.read()

                logo_attachment = MIMEBase("image", "png")
                logo_attachment.set_payload(logo_data)
                encoders.encode_base64(logo_attachment)
                logo_attachment.add_header("Content-ID", "<logo>")
                logo_attachment.add_header(
                    "Content-Disposition", "inline", filename="logo.png"
                )
                msg.attach(logo_attachment)
        except Exception as e:
            logger.warning(f"Could not attach logo: {e}")

        # Send email
        with smtplib.SMTP(
            smtp_config["smtp_server"], smtp_config.get("smtp_port", 587)
        ) as server:
            if smtp_config.get("smtp_use_tls", True):
                server.starttls()

            if smtp_config.get("smtp_username") and smtp_config.get("smtp_password"):
                server.login(smtp_config["smtp_username"], smtp_config["smtp_password"])

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
                <div class="tagline">Lost Then Found Pet QR Registry</div>
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
        if subscription.subscription_type == "partner":
            subject = "Partner Subscription Confirmed - Pending Approval"
            plan_name = (
                subscription.pricing_plan.name
                if subscription.pricing_plan
                else "Partner Plan"
            )
            status_color = "#ffc107"
            status_bg = "#fff3cd"
            status_message = "Your subscription is pending admin approval. You will receive another email once approved."
            cta_url = "http://localhost:8000/partner"
            cta_text = "Access Partner Dashboard"
        else:
            subject = "Tag Subscription Confirmed - Active"
            plan_name = (
                subscription.pricing_plan.name
                if subscription.pricing_plan
                else "Tag Plan"
            )
            status_color = "#28a745"
            status_bg = "#d4edda"
            status_message = "Your subscription is now active!"
            cta_url = "http://localhost:8000/dashboard"
            cta_text = "Access Your Dashboard"

        # Build the subscription details table
        details_rows = [
            f"<tr><td>Plan:</td><td><strong>{plan_name}</strong></td></tr>",
            f"<tr><td>Amount:</td><td><strong>${subscription.amount}</strong></td></tr>",
            f"<tr><td>Billing:</td><td>{subscription.pricing_plan.billing_period.title() if subscription.pricing_plan else 'One-time'}</td></tr>",
            f"<tr><td>Start Date:</td><td>{subscription.start_date.strftime('%B %d, %Y')}</td></tr>",
        ]

        if subscription.end_date:
            details_rows.append(
                f"<tr><td>End Date:</td><td>{subscription.end_date.strftime('%B %d, %Y')}</td></tr>"
            )

        if hasattr(subscription, "max_tags") and subscription.max_tags:
            details_rows.append(
                f"<tr><td>Max Tags:</td><td>{subscription.max_tags}</td></tr>"
            )

        details_table = "\n".join(details_rows)

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LTFPQRR Subscription Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
                <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <p style="font-size: 1.15rem; margin-bottom: 25px; color: #495057;">Hello {user.get_full_name()},</p>
                
                <h2 style="color: #212529; margin-bottom: 20px;">Thank you for your subscription!</h2>
                
                <p style="color: #6c757d; margin-bottom: 25px;">We have successfully processed your payment and created your subscription. Here are the details:</p>
                
                <div style="background: #f8f9fa; border-left: 5px solid #13c1be; padding: 25px; margin: 25px 0; border-radius: 8px;">
                    <h3 style="color: #495057; margin-top: 0;">Subscription Details</h3>
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        {details_table}
                    </table>
                </div>
                
                <div style="background: {status_bg}; border-left: 5px solid {status_color}; padding: 25px; margin: 25px 0; border-radius: 8px;">
                    <h3 style="color: #495057; margin-top: 0;">Status Update</h3>
                    <p>{status_message}</p>
                </div>
                
                <div style="height: 2px; background: linear-gradient(135deg, #13c1be 0%, #667eea 100%); margin: 25px 0; border-radius: 1px;"></div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{cta_url}" style="display: inline-block; background: linear-gradient(135deg, #13c1be 0%, #667eea 100%); color: white; padding: 16px 32px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 1.05rem;">{cta_text}</a>
                </div>
                
                <p>Thank you for choosing LTFPQRR! If you have any questions, our support team is here to help.</p>
            </div>
            
            <div style="background: #2c3e50; color: #ecf0f1; padding: 20px; text-align: center; font-size: 0.9rem; margin-top: 20px; border-radius: 8px;">
                <p style="margin: 0;"><strong>LTFPQRR</strong> - Helping reunite lost pets with their families</p>
                <p style="margin: 10px 0 0 0;">Need help? Contact us at <a href="mailto:support@ltfpqrr.com" style="color: #13c1be;">support@ltfpqrr.com</a></p>
                <small style="color: #bdc3c7;">© 2025 LTFPQRR. All rights reserved.</small>
            </div>
        </body>
        </html>
        """

        # Add CSS for table styling
        html_body = html_body.replace(
            '<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">',
            '<table style="width: 100%; border-collapse: collapse; margin: 20px 0;"><style>table td { padding: 15px 12px; border-bottom: 1px solid #f1f3f4; } table tr:last-child td { border-bottom: none; } table td:first-child { font-weight: 600; color: #495057; width: 35%; background: #f8f9fa; } table td:last-child { color: #212529; }</style>',
        )

        text_body = f"""
        Hello {user.get_full_name()},
        
        Thank you for your subscription!
        
        Subscription Details:
        - Plan: {plan_name}
        - Amount: ${subscription.amount}
        - Billing: {subscription.pricing_plan.billing_period.title() if subscription.pricing_plan else 'One-time'}
        - Start Date: {subscription.start_date.strftime('%B %d, %Y')}
        {('- End Date: ' + subscription.end_date.strftime("%B %d, %Y")) if subscription.end_date else ''}
        {('- Max Tags: ' + str(subscription.max_tags)) if hasattr(subscription, 'max_tags') and subscription.max_tags else ''}
        
        Status: {status_message}
        
        Best regards,
        The LTFPQRR Team
        """

        success = send_email(user.email, subject, html_body, text_body)
        if success:
            logger.info("Subscription confirmation email sent to %s", user.email)
        return success

    except Exception as e:
        logger.error("Error sending subscription confirmation email: %s", e)
        return False


def send_partner_subscription_confirmation_email(user, partner_subscription):
    """Send subscription confirmation email to partner customer"""
    try:
        # Determine approval status
        if partner_subscription.admin_approved:
            subject = "Partner Subscription Activated - Welcome!"
            status_color = "#28a745"
            status_bg = "#d4edda"
            status_message = "Your partner subscription is now active!"
        else:
            subject = "Partner Subscription Confirmed - Pending Approval"
            status_color = "#ffc107"
            status_bg = "#fff3cd"
            status_message = "Your subscription is pending admin approval. You will receive another email once approved."

        plan_name = (
            partner_subscription.pricing_plan.name
            if hasattr(partner_subscription, "pricing_plan")
            and partner_subscription.pricing_plan
            else "Partner Plan"
        )
        partner_name = (
            partner_subscription.partner.company_name
            if hasattr(partner_subscription, "partner") and partner_subscription.partner
            else "Your Partner"
        )
        cta_url = "http://localhost:8000/partner"
        cta_text = "Access Partner Dashboard"

        # Build the subscription details table
        details_rows = [
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;'>Partner:</td><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'><strong>{partner_name}</strong></td></tr>",
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;'>Plan:</td><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'><strong>{plan_name}</strong></td></tr>",
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;'>Amount:</td><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'><strong>${partner_subscription.amount}</strong></td></tr>",
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;'>Start Date:</td><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{partner_subscription.start_date.strftime('%B %d, %Y')}</td></tr>",
        ]

        if partner_subscription.pricing_plan:
            details_rows.append(
                f"<tr><td style='padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;'>Billing:</td><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{partner_subscription.pricing_plan.billing_period.title()}</td></tr>"
            )

        if partner_subscription.end_date:
            details_rows.append(
                f"<tr><td style='padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;'>End Date:</td><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{partner_subscription.end_date.strftime('%B %d, %Y')}</td></tr>"
            )

        if partner_subscription.max_tags:
            max_tags_text = (
                str(partner_subscription.max_tags)
                if partner_subscription.max_tags > 0
                else "Unlimited"
            )
            details_rows.append(
                f"<tr><td style='padding: 8px; color: #666;'>Max Tags:</td><td style='padding: 8px;'>{max_tags_text}</td></tr>"
            )
        else:
            details_rows.append(
                "<tr><td style='padding: 8px; color: #666;'>Max Tags:</td><td style='padding: 8px;'>Unlimited</td></tr>"
            )

        details_table = "\n".join(details_rows)

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LTFPQRR Partner Subscription Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
                <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="margin-bottom: 30px;">
                    <h2 style="color: #333; margin: 0 0 10px 0; font-size: 1.8rem;">Hi {user.get_full_name()},</h2>
                    <p style="color: #666; margin: 0; font-size: 1.1rem;">Thank you for your partner subscription!</p>
                </div>
                
                <div style="background: {status_bg}; border: 1px solid {status_color}; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
                    <h3 style="color: {status_color}; margin: 0 0 10px 0; font-size: 1.3rem;">Subscription Status</h3>
                    <p style="margin: 0; font-size: 1rem; color: #333;">{status_message}</p>
                </div>
                
                <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
                    <h3 style="color: #333; margin: 0 0 20px 0; font-size: 1.3rem; text-align: center;">Subscription Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        {details_table}
                    </table>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{cta_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 1.1rem;">{cta_text}</a>
                </div>
                
                <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px; color: #666; font-size: 0.9rem;">
                    <p>Questions about your subscription? Contact us at <a href="mailto:support@ltfpqrr.com" style="color: #667eea;">support@ltfpqrr.com</a></p>
                    <p style="margin: 10px 0 0 0;">Thank you for choosing LTFPQRR!</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        plain_body = f"""
        LTFPQRR - Partner Subscription Confirmation
        
        Hi {user.get_full_name()},
        
        Thank you for your partner subscription!
        
        Status: {status_message}
        
        Subscription Details:
        - Partner: {partner_name}
        - Plan: {plan_name}
        - Amount: ${partner_subscription.amount}
        - Start Date: {partner_subscription.start_date.strftime('%B %d, %Y')}
        
        Access your partner dashboard: {cta_url}
        
        Questions? Contact us at support@ltfpqrr.com
        
        Thank you for choosing LTFPQRR!
        """

        return send_email(user.email, subject, html_body, plain_body)

    except Exception as e:
        logger.error(f"Error sending partner subscription confirmation email: {e}")
        return False


def send_admin_approval_notification(subscription):
    """Send notification to admins when a partner subscription needs approval"""
    try:
        from models.models import User, Role

        # Get all admin users
        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
            logger.warning("No admin role found")
            return False

        admin_users = admin_role.users
        if not admin_users:
            logger.warning("No admin users found")
            return False

        subject = "New Partner Subscription Requires Approval"
        partner_name = (
            subscription.partner.company_name
            if subscription.partner
            else "Unknown Partner"
        )
        user_name = subscription.user.get_full_name()
        plan_name = (
            subscription.pricing_plan.name
            if subscription.pricing_plan
            else "Partner Plan"
        )

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

        logger.info(
            f"Admin approval notification sent to {success_count}/{len(admin_users)} admin users"
        )
        return success_count > 0

    except Exception as e:
        logger.error(f"Error sending admin approval notification: {e}")
        return False


def send_subscription_approved_email(user, subscription):
    """Send email to customer when subscription is approved"""
    try:
        subject = "Partner Subscription Approved - Welcome to LTFPQRR!"

        plan_name = (
            subscription.pricing_plan.name
            if subscription.pricing_plan
            else "Partner Plan"
        )
        partner_name = (
            subscription.partner.company_name
            if subscription.partner
            else "Your Partner Account"
        )

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

        # Handle both regular subscriptions and partner subscriptions
        if hasattr(subscription, "pricing_plan") and subscription.pricing_plan:
            plan_name = subscription.pricing_plan.name
        else:
            plan_name = "Subscription Plan"

        amount = str(subscription.amount) if subscription.amount else "N/A"
        start_date = (
            subscription.start_date.strftime("%B %d, %Y")
            if subscription.start_date
            else "N/A"
        )
        end_date = (
            subscription.end_date.strftime("%B %d, %Y")
            if subscription.end_date
            else "Today"
        )

        refund_message = (
            "A refund has been processed and should appear in your account within 5-10 business days."
            if refunded
            else "No refund was processed for this cancellation."
        )

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
                    <td>${amount}</td>
                </tr>
                <tr>
                    <td>Original Start:</td>
                    <td>{start_date}</td>
                </tr>
                <tr>
                    <td>Cancelled:</td>
                    <td>{end_date}</td>
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
        - Amount: ${amount}
        - Original Start: {start_date}
        - Cancelled: {end_date}
        - Refund: {'Processed' if refunded else 'None'}
        
        {refund_message}
        
        Best regards,
        The LTFPQRR Team
        """

        return send_email(
            to_email=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

        return send_email(
            to_email=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    except Exception as e:
        logger.error(f"Error sending subscription cancelled email: {e}")
        return False


def send_subscription_renewal_email(user, subscription):
    """Send email to customer when subscription is renewed"""
    try:
        subject = "Subscription Renewed - LTFPQRR"

        plan_name = (
            subscription.pricing_plan.name
            if subscription.pricing_plan
            else "Subscription Plan"
        )

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
        subject = "LTFPQRR - Test Email"

        # Simple HTML template without complex formatting
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LTFPQRR Test Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
                <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h2 style="color: #212529; margin-bottom: 20px;">SMTP Configuration Test</h2>
                
                <p>Hello!</p>
                
                <p>This is a test email to verify that your SMTP configuration is working correctly.</p>
                
                <div style="background: #d4edda; border-left: 5px solid #28a745; padding: 20px; margin: 20px 0; border-radius: 8px;">
                    <h3 style="color: #155724; margin-top: 0;">Test Results</h3>
                    <p style="margin-bottom: 10px;">If you are receiving this email, your SMTP settings are configured correctly!</p>
                    <ul>
                        <li>SMTP server connection: ✓ Working</li>
                        <li>Email formatting: ✓ Working</li>
                        <li>Template rendering: ✓ Working</li>
                    </ul>
                </div>
                
                <div style="background: #f8f9fa; border-left: 5px solid #13c1be; padding: 20px; margin: 20px 0; border-radius: 8px;">
                    <h3 style="color: #495057; margin-top: 0;">Next Steps</h3>
                    <p>Your email system is ready to send notifications for:</p>
                    <ul>
                        <li>Subscription confirmations</li>
                        <li>Admin notifications</li>
                        <li>Subscription approvals</li>
                        <li>Cancellation notices</li>
                        <li>Renewal reminders</li>
                    </ul>
                </div>
                
                <p style="margin-top: 30px;">Best regards,<br>The LTFPQRR Team</p>
            </div>
            
            <div style="background: #2c3e50; color: #ecf0f1; padding: 20px; text-align: center; font-size: 0.9rem; margin-top: 20px; border-radius: 8px;">
                <p style="margin: 0;"><strong>LTFPQRR</strong> - Helping reunite lost pets with their families</p>
                <p style="margin: 10px 0 0 0;">Need help? Contact us at <a href="mailto:support@ltfpqrr.com" style="color: #13c1be;">support@ltfpqrr.com</a></p>
                <small style="color: #bdc3c7;">© 2025 LTFPQRR. All rights reserved.</small>
            </div>
        </body>
        </html>
        """

        text_body = """
        LTFPQRR - Email Test
        
        This is a test email to verify SMTP configuration.
        
        If you receive this, your email system is working correctly!
        
        Test Results:
        - SMTP server connection: Working
        - Email formatting: Working  
        - Template rendering: Working
        
        Best regards,
        The LTFPQRR Team
        """

        success = send_email(to_email, subject, html_body, text_body)
        if success:
            logger.info("Test email sent successfully to %s", to_email)
        return success

    except Exception as e:
        logger.error("Error sending test email: %s", e)
        return False


def send_subscription_rejected_email(user, subscription):
    """Send email to customer when subscription is rejected"""
    try:
        subject = "Subscription Request Rejected - LTFPQRR"

        html_template = get_email_template_base()

        html_body = html_template.format(
            content=f"""
        <div class="title">Subscription Request Rejected</div>
        
        <div class="subtitle">We're sorry, but your subscription request has been rejected.</div>
        
        <div class="content-box">
            <div class="box-title">Rejected Subscription</div>
            <div class="box-content">
                <p><strong>Subscription Type:</strong> {subscription.subscription_type.title()}</p>
                <p><strong>Status:</strong> Rejected</p>
                <p><strong>Request Date:</strong> {subscription.created_at.strftime('%B %d, %Y')}</p>
                <p><strong>Rejected Date:</strong> {subscription.updated_at.strftime('%B %d, %Y') if subscription.updated_at else 'Today'}</p>
            </div>
        </div>
        
        <div class="content-box">
            <div class="box-title">What's Next?</div>
            <div class="box-content">
                <p>If you believe this rejection was made in error, please contact our support team for assistance.</p>
                <p>You may also review our subscription requirements and submit a new request if appropriate.</p>
            </div>
        </div>
        
        <div class="content-box">
            <div class="box-title">Need Help?</div>
            <div class="box-content">
                <p>If you have any questions about this rejection or need assistance, please don't hesitate to contact our support team.</p>
                <p>Thank you for your interest in LTFPQRR.</p>
            </div>
        </div>
        """
        )

        text_body = f"""
        Your subscription request has been rejected.
        
        Rejected Subscription:
        - Type: {subscription.subscription_type.title()}
        - Status: Rejected
        - Request Date: {subscription.created_at.strftime('%B %d, %Y')}
        - Rejected Date: {subscription.updated_at.strftime('%B %d, %Y') if subscription.updated_at else 'Today'}
        
        If you believe this rejection was made in error, please contact our support team for assistance.
        
        Thank you for your interest in LTFPQRR.
        """

        success = send_email(user.email, subject, html_body, text_body)

        if success:
            logger.info(f"Subscription rejected email sent to {user.email}")
        return success

    except Exception as e:
        logger.error(f"Error sending subscription rejected email: {e}")
        return False


def send_partner_admin_approval_notification(partner_subscription):
    """Send notification to admins when a partner subscription needs approval"""
    try:
        from models.models import User, Role

        # Get all admin users
        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
            logger.warning("No admin role found")
            return False

        admin_users = admin_role.users
        if not admin_users:
            logger.warning("No admin users found")
            return False

        subject = "New Partner Subscription Requires Approval"

        # Safely get partner and user information
        try:
            partner_name = (
                partner_subscription.partner.company_name
                if hasattr(partner_subscription, "partner")
                and partner_subscription.partner
                else "Unknown Partner"
            )
            user_name = (
                partner_subscription.partner.owner.get_full_name()
                if (
                    hasattr(partner_subscription, "partner")
                    and partner_subscription.partner
                    and hasattr(partner_subscription.partner, "owner")
                    and partner_subscription.partner.owner
                )
                else "Unknown User"
            )
            plan_name = (
                partner_subscription.pricing_plan.name
                if hasattr(partner_subscription, "pricing_plan")
                and partner_subscription.pricing_plan
                else "Partner Plan"
            )
        except Exception as attr_error:
            logger.error(
                f"Error accessing partner subscription attributes: {attr_error}"
            )
            partner_name = "Unknown Partner"
            user_name = "Unknown User"
            plan_name = "Partner Plan"

        content = f"""
        <div style="margin-bottom: 30px;">
            <h2 style="color: #333; margin: 0 0 10px 0; font-size: 1.8rem;">Hello Admin,</h2>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <h3 style="color: #333; margin: 0 0 10px 0; font-size: 1.5rem;">New Partner Subscription Awaiting Approval</h3>
            <p style="color: #666; margin: 0; font-size: 1.1rem;">A new partner subscription has been purchased and requires your approval.</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h4 style="color: #333; margin: 0 0 20px 0; font-size: 1.3rem; text-align: center;">Subscription Details</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{partner_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Owner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{user_name}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{plan_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${partner_subscription.amount}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{partner_subscription.start_date.strftime('%B %d, %Y')}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{'Unlimited' if partner_subscription.max_tags == 0 else partner_subscription.max_tags}</td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:8000/admin/partner-subscriptions" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 1.1rem;">Review Subscription</a>
        </div>
        
        <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px; color: #666; font-size: 0.9rem; text-align: center;">
            <p>Please review and approve this subscription in the admin panel.</p>
        </div>
        """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LTFPQRR - Partner Subscription Approval Needed</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
                <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                {content}
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; border-top: 1px solid #e9ecef; color: #666; font-size: 0.9rem;">
                <p style="margin: 0;">LTFPQRR - Lost Then Found Pet QR Registry</p>
            </div>
        </body>
        </html>
        """

        plain_body = f"""
        LTFPQRR - Partner Subscription Approval Needed
        
        Hello Admin,
        
        A new partner subscription requires approval:
        
        Partner: {partner_name}
        Owner: {user_name}
        Plan: {plan_name}
        Amount: ${partner_subscription.amount}
        Start Date: {partner_subscription.start_date.strftime('%B %d, %Y')}
        Max Tags: {'Unlimited' if partner_subscription.max_tags == 0 else partner_subscription.max_tags}
        
        Please review and approve this subscription in the admin panel:
        http://localhost:8000/admin/partner-subscriptions
        
        Thank you,
        LTFPQRR Team
        """

        # Send to all admin users
        success = True
        for admin in admin_users:
            if not send_email(admin.email, subject, html_body, plain_body):
                success = False

        return success

    except Exception as e:
        logger.error(f"Error sending admin approval notification: {e}")
        return False


def send_partner_subscription_approved_email_enhanced(user, partner_subscription):
    """Enhanced version of partner subscription approved email"""
    return send_partner_subscription_approved_email(user, partner_subscription)


def send_partner_subscription_approved_email(user, partner_subscription):
    """Send approval notification email to partner customer using enhanced template system"""
    try:
        from services.enhanced_email_service import EmailTemplateManager
        
        # Use the enhanced email system with model instances
        inputs = {
            'user_id': user.id,
            'subscription_id': partner_subscription.id,
            'partner_id': partner_subscription.partner.id if partner_subscription.partner else None,
            'target_email': user.email  # Explicit email targeting
        }
        
        # Send using enhanced template system
        result = EmailTemplateManager.send_from_template(
            template_name='partner_subscription_approved',
            inputs=inputs,
            email_type='partner_subscription_approved'
        )
        
        if result:
            logger.info(f"Partner subscription approved email sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send partner subscription approved email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending partner subscription approved email: {e}")
        return False

        content = f"""
        <div style="margin-bottom: 30px;">
            <h2 style="color: #333; margin: 0 0 10px 0; font-size: 1.8rem;">Hi {user.get_full_name()},</h2>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <h3 style="color: #28a745; margin: 0 0 10px 0; font-size: 1.5rem;">Congratulations! Your Partner Subscription is Approved</h3>
            <p style="color: #666; margin: 0; font-size: 1.1rem;">Great news! Your partner subscription has been approved by our admin team. Welcome to the LTFPQRR partner network!</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h4 style="color: #333; margin: 0 0 20px 0; font-size: 1.3rem; text-align: center;">Subscription Details</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{partner_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{plan_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${partner_subscription.amount}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Start Date:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{partner_subscription.start_date.strftime('%B %d, %Y')}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Max Tags:</td><td style="padding: 8px;">{'Unlimited' if partner_subscription.max_tags == 0 else partner_subscription.max_tags}</td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:8000/partner" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 1.1rem;">Access Partner Dashboard</a>
        </div>
        
        <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px; color: #666; font-size: 0.9rem; text-align: center;">
            <p>You can now start creating and managing QR tags for your partner business!</p>
        </div>
        """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LTFPQRR - Partner Subscription Approved</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
                <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                {content}
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; border-top: 1px solid #e9ecef; color: #666; font-size: 0.9rem;">
                <p style="margin: 0;">LTFPQRR - Lost Then Found Pet QR Registry</p>
            </div>
        </body>
        </html>
        """

        plain_body = f"""
        LTFPQRR - Partner Subscription Approved
        
        Hi {user.get_full_name()},
        
        Congratulations! Your partner subscription has been approved.
        
        Subscription Details:
        Partner: {partner_name}
        Plan: {plan_name}
        Amount: ${partner_subscription.amount}
        Start Date: {partner_subscription.start_date.strftime('%B %d, %Y')}
        Max Tags: {'Unlimited' if partner_subscription.max_tags == 0 else partner_subscription.max_tags}
        
        Access your partner dashboard: http://localhost:8000/partner
        
        You can now start creating and managing QR tags for your partner business!
        
        Thank you for choosing LTFPQRR!
        """

        return send_email(user.email, subject, html_body, plain_body)

    except Exception as e:
        logger.error(f"Error sending partner subscription approved email: {e}")
        return False


def send_partner_subscription_rejected_email(
    user, partner_subscription, refund_processed=False
):
    """Send rejection notification email to partner customer using enhanced template system"""
    try:
        from services.enhanced_email_service import EmailTemplateManager
        
        # Use the enhanced email system with model instances
        inputs = {
            'user_id': user.id,
            'subscription_id': partner_subscription.id,
            'partner_id': partner_subscription.partner.id if partner_subscription.partner else None,
            'target_email': user.email,  # Explicit email targeting
            'refund_processed': 'Yes' if refund_processed else 'No',
            'refund_message': 'A full refund has been processed and will appear in your account within 3-5 business days.' if refund_processed else 'No refund was processed.'
        }
        
        # Send using enhanced template system
        result = EmailTemplateManager.send_from_template(
            template_name='partner_subscription_rejected',
            inputs=inputs,
            email_type='partner_subscription_rejected'
        )
        
        if result:
            logger.info(f"Partner subscription rejected email sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send partner subscription rejected email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending partner subscription rejected email: {e}")
        return False

        refund_message = ""
        if refund_processed:
            refund_message = """
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 25px 0;">
                <h4 style="color: #155724; margin: 0 0 10px 0; font-size: 1.2rem;">
                    <i class="fas fa-check-circle"></i> Refund Processed
                </h4>
                <p style="color: #155724; margin: 0;">
                    Your payment has been fully refunded and should appear in your account within 5-10 business days.
                </p>
            </div>
            """

        content = f"""
        <div style="margin-bottom: 30px;">
            <h2 style="color: #333; margin: 0 0 10px 0; font-size: 1.8rem;">Hi {user.get_full_name()},</h2>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <h3 style="color: #dc3545; margin: 0 0 10px 0; font-size: 1.5rem;">Partner Subscription Update</h3>
            <p style="color: #666; margin: 0; font-size: 1.1rem;">We regret to inform you that your partner subscription request could not be approved at this time.</p>
        </div>
        
        {refund_message}
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h4 style="color: #333; margin: 0 0 20px 0; font-size: 1.3rem; text-align: center;">Subscription Details</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Partner:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{partner_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Plan:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>{plan_name}</strong></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #666;">Amount:</td><td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>${partner_subscription.amount}</strong></td></tr>
                <tr><td style="padding: 8px; color: #666;">Requested Date:</td><td style="padding: 8px;">{partner_subscription.start_date.strftime('%B %d, %Y')}</td></tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="mailto:support@ltfpqrr.com" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 1.1rem;">Contact Support</a>
        </div>
        
        <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px; color: #666; font-size: 0.9rem; text-align: center;">
            <p>If you have questions about this decision or would like to reapply, please contact our support team at support@ltfpqrr.com.</p>
        </div>
        """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LTFPQRR - Partner Subscription Update</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">
                <h1 style="color: #13c1be; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">LTFPQRR</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Lost Then Found Pet QR Registry</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                {content}
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; border-top: 1px solid #e9ecef; color: #666; font-size: 0.9rem;">
                <p style="margin: 0;">LTFPQRR - Lost Then Found Pet QR Registry</p>
            </div>
        </body>
        </html>
        """

        plain_body = f"""
        LTFPQRR - Partner Subscription Update
        
        Hi {user.get_full_name()},
        
        We regret to inform you that your partner subscription request could not be approved at this time.
        
        Subscription Details:
        Partner: {partner_name}
        Plan: {plan_name}
        Amount: ${partner_subscription.amount}
        Requested Date: {partner_subscription.start_date.strftime('%B %d, %Y')}
        
        If you have questions about this decision or would like to reapply, please contact our support team:
        support@ltfpqrr.com
        
        Thank you for your interest in LTFPQRR.
        """

        return send_email(user.email, subject, html_body, plain_body)

    except Exception as e:
        logger.error(f"Error sending partner subscription rejected email: {e}")
        return False


# Enhanced Email Functions with Queue Management
def send_email_with_queue(
    to_email, 
    subject, 
    html_body, 
    text_body=None, 
    priority='normal',
    email_type=None,
    user_id=None,
    template_name=None,
    variables=None,
    **kwargs
):
    """
    Send email with queue management and retry logic
    Falls back to direct sending if queue is not available
    """
    try:
        # Try to use the queue system
        from services.email_service import EmailManager, EmailPriority
        from models.email.email_models import EmailStatus
        
        # Convert priority string to enum
        priority_map = {
            'low': EmailPriority.LOW,
            'normal': EmailPriority.NORMAL,
            'high': EmailPriority.HIGH,
            'critical': EmailPriority.CRITICAL
        }
        priority_enum = priority_map.get(priority.lower(), EmailPriority.NORMAL)
        
        # Queue the email
        queue_item = EmailManager.queue_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            priority=priority_enum,
            user_id=user_id,
            email_type=email_type,
            metadata={
                'template_name': template_name,
                'variables': variables
            } if template_name or variables else None,
            **kwargs
        )
        
        # Return True if sent successfully
        return queue_item.status == EmailStatus.SENT
        
    except ImportError:
        # Queue system not available, fall back to direct sending
        logger.warning("Email queue system not available, sending directly")
        return send_email(to_email, subject, html_body, text_body, **kwargs)
    except Exception as e:
        logger.error(f"Error using email queue system: {e}")
        # Fall back to direct sending
        return send_email(to_email, subject, html_body, text_body, **kwargs)


def send_template_email(template_name, to_email, variables=None, **kwargs):
    """
    Send email using a template
    """
    try:
        from services.email_service import EmailTemplateManager
        
        return EmailTemplateManager.send_from_template(
            template_name=template_name,
            to_email=to_email,
            variables=variables or {},
            **kwargs
        )
        
    except ImportError:
        logger.error("Email template system not available")
        return False
    except Exception as e:
        logger.error(f"Error sending template email: {e}")
        return False


# Update existing email functions to use queue system
def send_partner_subscription_confirmation_email_enhanced(user, partner_subscription):
    """Enhanced partner subscription confirmation email with queue system"""
    try:
        from services.enhanced_email_service import EmailTemplateManager
        
        # Use the enhanced email system with model instances
        inputs = {
            'user_id': user.id,
            'subscription_id': partner_subscription.id,
            'partner_id': partner_subscription.partner.id if partner_subscription.partner else None,
            'target_email': user.email  # Explicit email targeting
        }
        
        # Send using enhanced template system
        result = EmailTemplateManager.send_from_template(
            template_name='partner_subscription_confirmation',
            inputs=inputs,
            email_type='partner_subscription_confirmation'
        )
        
        if result:
            logger.info(f"Enhanced partner subscription confirmation email sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send enhanced partner subscription confirmation email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending enhanced partner subscription confirmation email: {e}")
        # Fallback to old system
        return send_partner_subscription_confirmation_email_fallback(user, partner_subscription)


def send_partner_subscription_confirmation_email_fallback(user, partner_subscription):
    """Fallback partner subscription confirmation email"""
    try:
        # Prepare template variables (legacy format)
        variables = {
            'user_name': user.get_full_name(),
            'first_name': user.first_name or 'there',
            'partner_name': partner_subscription.partner.company_name if hasattr(partner_subscription, 'partner') and partner_subscription.partner else "Your Partner",
            'plan_name': partner_subscription.pricing_plan.name if hasattr(partner_subscription, 'pricing_plan') and partner_subscription.pricing_plan else "Partner Plan",
            'amount': str(partner_subscription.amount),
            'start_date': partner_subscription.start_date.strftime('%B %d, %Y'),
            'max_tags': 'Unlimited' if partner_subscription.max_tags == 0 else str(partner_subscription.max_tags),
            'status': 'Approved' if partner_subscription.admin_approved else 'Pending Approval'
        }
        
        # Try to use template system first
        template_name = 'partner_subscription_confirmation'
        success = send_template_email(
            template_name=template_name,
            to_email=user.email,
            variables=variables,
            user_id=user.id,
            email_type='partner_subscription_confirmation',
            priority='high'
        )
        
        if success:
            return True
        
        # Fall back to existing function
        logger.info("Template not found, using existing email function")
        return send_partner_subscription_confirmation_email(user, partner_subscription)
        
    except Exception as e:
        logger.error(f"Error sending enhanced partner subscription confirmation: {e}")
        # Fall back to existing function
        return send_partner_subscription_confirmation_email(user, partner_subscription)


def send_partner_subscription_approved_email_enhanced(user, partner_subscription):
    """Enhanced partner subscription approval email with queue system"""
    try:
        # Prepare template variables
        variables = {
            'user_name': user.get_full_name(),
            'first_name': user.first_name or 'there',
            'partner_name': partner_subscription.partner.company_name if hasattr(partner_subscription, 'partner') and partner_subscription.partner else "Your Partner",
            'plan_name': partner_subscription.pricing_plan.name if hasattr(partner_subscription, 'pricing_plan') and partner_subscription.pricing_plan else "Partner Plan",
            'amount': str(partner_subscription.amount),
            'start_date': partner_subscription.start_date.strftime('%B %d, %Y'),
            'max_tags': 'Unlimited' if partner_subscription.max_tags == 0 else str(partner_subscription.max_tags)
        }
        
        # Try to use template system first
        template_name = 'partner_subscription_approved'
        success = send_template_email(
            template_name=template_name,
            to_email=user.email,
            variables=variables,
            user_id=user.id,
            email_type='partner_subscription_approved',
            priority='high'
        )
        
        if success:
            return True
        
        # Fall back to existing function
        logger.info("Template not found, using existing email function")
        return send_partner_subscription_approved_email(user, partner_subscription)
        
    except Exception as e:
        logger.error(f"Error sending enhanced partner subscription approval: {e}")
        # Fall back to existing function
        return send_partner_subscription_approved_email(user, partner_subscription)


def send_partner_subscription_rejected_email_enhanced(user, partner_subscription, refund_processed=False):
    """Enhanced partner subscription rejection email with queue system"""
    try:
        # Prepare template variables
        variables = {
            'user_name': user.get_full_name(),
            'first_name': user.first_name or 'there',
            'partner_name': partner_subscription.partner.company_name if hasattr(partner_subscription, 'partner') and partner_subscription.partner else "Your Partner",
            'plan_name': partner_subscription.pricing_plan.name if hasattr(partner_subscription, 'pricing_plan') and partner_subscription.pricing_plan else "Partner Plan",
            'amount': str(partner_subscription.amount),
            'start_date': partner_subscription.start_date.strftime('%B %d, %Y'),
            'refund_processed': 'Yes' if refund_processed else 'No',
            'refund_message': 'Your payment has been fully refunded and should appear in your account within 5-10 business days.' if refund_processed else 'No refund was processed for this request.'
        }
        
        # Try to use template system first
        template_name = 'partner_subscription_rejected'
        success = send_template_email(
            template_name=template_name,
            to_email=user.email,
            variables=variables,
            user_id=user.id,
            email_type='partner_subscription_rejected',
            priority='high'
        )
        
        if success:
            return True
        
        # Fall back to existing function
        logger.info("Template not found, using existing email function")
        return send_partner_subscription_rejected_email(user, partner_subscription, refund_processed)
        
    except Exception as e:
        logger.error(f"Error sending enhanced partner subscription rejection: {e}")
        # Fall back to existing function
        return send_partner_subscription_rejected_email(user, partner_subscription, refund_processed)


# Backward compatibility - update existing functions to use enhanced versions
def send_partner_subscription_confirmation_email_original(user, partner_subscription):
    """Original function - keeping for compatibility"""
    return send_partner_subscription_confirmation_email_enhanced(user, partner_subscription)


def send_partner_subscription_approved_email_original(user, partner_subscription):
    """Original function - keeping for compatibility"""
    return send_partner_subscription_approved_email_enhanced(user, partner_subscription)


def send_partner_subscription_rejected_email_original(user, partner_subscription, refund_processed=False):
    """Original function - keeping for compatibility"""
    return send_partner_subscription_rejected_email_enhanced(user, partner_subscription, refund_processed)
