#!/usr/bin/env python3
"""
Simple email test script to send working subscription emails to jakumpe@kumpes.com
"""

from app import app
from email_utils import send_email

def send_simple_test_emails():
    """Send simple working test emails"""
    print("📧 Sending Test Emails to jakumpe@kumpes.com")
    print("=" * 50)
    
    target_email = "jakumpe@kumpes.com"
    
    with app.app_context():
        # Test 1: Basic system test
        print("1️⃣ Sending basic system test...")
        html_body1 = """
        <h2>🎉 LTFPQRR Email System Test</h2>
        <p>Hello Jake,</p>
        <p>This email confirms that the LTFPQRR email notification system is working correctly!</p>
        <p><strong>Email capabilities verified:</strong></p>
        <ul>
            <li>✅ SMTP Configuration: mail.kumpeapps.com:587</li>
            <li>✅ Email Delivery: Working</li>
            <li>✅ HTML Email Support: Active</li>
        </ul>
        <p>Best regards,<br>LTFPQRR System</p>
        """
        result1 = send_email(target_email, "✅ LTFPQRR Email System Test - Working!", html_body1)
        print(f"   Result: {'✅ Success' if result1 else '❌ Failed'}")
        
        # Test 2: Partner subscription confirmation simulation
        print("\n2️⃣ Sending partner subscription confirmation simulation...")
        html_body2 = """
        <h2>📋 Partner Subscription Confirmation</h2>
        <p>Dear Jake,</p>
        <p>Thank you for your partner subscription payment! Here are the details:</p>
        <div style="background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px;">
            <h3>Subscription Details:</h3>
            <p><strong>Plan:</strong> Professional Partner Plan</p>
            <p><strong>Amount:</strong> $29.99/month</p>
            <p><strong>Status:</strong> Pending Admin Approval</p>
            <p><strong>Max Tags:</strong> 25</p>
        </div>
        <p><strong>Next Steps:</strong></p>
        <p>Your subscription is currently pending admin approval. You will receive another email once your partner account has been approved by our team.</p>
        <p>If you have any questions, please contact our support team.</p>
        <p>Best regards,<br>LTFPQRR Team</p>
        """
        result2 = send_email(target_email, "🎯 LTFPQRR Partner Subscription Confirmation - Pending Approval", html_body2)
        print(f"   Result: {'✅ Success' if result2 else '❌ Failed'}")
        
        # Test 3: Admin approval notification simulation  
        print("\n3️⃣ Sending admin approval notification simulation...")
        html_body3 = """
        <h2>🔔 Admin: New Partner Subscription Requires Approval</h2>
        <p>Hello Admin,</p>
        <p>A new partner subscription requires your approval:</p>
        <div style="background: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #ffc107;">
            <h3>Partner Details:</h3>
            <p><strong>Company:</strong> Test Company LLC</p>
            <p><strong>Email:</strong> jakumpe@kumpes.com</p>
            <p><strong>Plan:</strong> Professional Partner Plan ($29.99/month)</p>
            <p><strong>Payment Status:</strong> Completed</p>
        </div>
        <p><strong>Action Required:</strong></p>
        <p>Please log into the admin panel to review and approve this partner subscription.</p>
        <p><a href="http://localhost:8000/admin/partner-subscriptions" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Review Subscription →</a></p>
        <p>Best regards,<br>LTFPQRR System</p>
        """
        result3 = send_email("jakumpe@kumpes.com", "🚨 LTFPQRR Admin: Partner Subscription Approval Required", html_body3)
        print(f"   Result: {'✅ Success' if result3 else '❌ Failed'}")
        
        # Test 4: Subscription approved notification
        print("\n4️⃣ Sending subscription approved notification...")
        html_body4 = """
        <h2>🎉 Partner Subscription Approved!</h2>
        <p>Dear Jake,</p>
        <p>Great news! Your partner subscription has been approved by our admin team.</p>
        <div style="background: #d4edda; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #28a745;">
            <h3>Your Active Subscription:</h3>
            <p><strong>Plan:</strong> Professional Partner Plan</p>
            <p><strong>Status:</strong> ✅ Active</p>
            <p><strong>Billing:</strong> $29.99/month</p>
            <p><strong>Tag Limit:</strong> 25 tags</p>
            <p><strong>Next Billing:</strong> One month from today</p>
        </div>
        <p><strong>What's Next:</strong></p>
        <p>You can now access your partner dashboard and start creating tags for your customers.</p>
        <p><a href="http://localhost:8000/partner" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Access Partner Dashboard →</a></p>
        <p>Thank you for choosing LTFPQRR!</p>
        <p>Best regards,<br>LTFPQRR Team</p>
        """
        result4 = send_email(target_email, "🎉 LTFPQRR Partner Subscription Approved - Welcome!", html_body4)
        print(f"   Result: {'✅ Success' if result4 else '❌ Failed'}")
        
        # Test 5: Subscription cancellation notification
        print("\n5️⃣ Sending subscription cancellation notification...")
        html_body5 = """
        <h2>📄 Subscription Cancelled</h2>
        <p>Dear Jake,</p>
        <p>This email confirms that your partner subscription has been cancelled.</p>
        <div style="background: #f8d7da; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #dc3545;">
            <h3>Cancellation Details:</h3>
            <p><strong>Plan:</strong> Professional Partner Plan</p>
            <p><strong>Reason:</strong> Admin cancelled subscription for testing purposes</p>
            <p><strong>Effective:</strong> Immediately</p>
            <p><strong>Refund:</strong> A refund has been processed to your original payment method</p>
        </div>
        <p><strong>What This Means:</strong></p>
        <ul>
            <li>Your partner access has been revoked</li>
            <li>No further charges will be made</li>
            <li>You can resubscribe at any time</li>
        </ul>
        <p>If you have any questions about this cancellation, please contact our support team.</p>
        <p>Best regards,<br>LTFPQRR Team</p>
        """
        result5 = send_email(target_email, "📋 LTFPQRR Subscription Cancelled - Refund Processed", html_body5)
        print(f"   Result: {'✅ Success' if result5 else '❌ Failed'}")
        
        print(f"\n🎉 All test emails sent! Check {target_email} for delivery.")

if __name__ == "__main__":
    send_simple_test_emails()
