#!/usr/bin/env python3
"""
Script to update email templates in the database with correct variable placeholders.
This fixes the issue where templates show correct placeholders in preview but emails use old hardcoded text.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def update_database_templates():
    """Update email templates in database with correct variable placeholders"""
    
    try:
        from app import app
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            print("🔄 Updating email template variable placeholders in database...")
            
            # Update hardcoded "Lost Then Found Pet QR Registry" to use proper variable
            result1 = db.session.execute(text("""
                UPDATE email_template 
                SET html_content = REPLACE(
                    html_content,
                    'Lost Then Found Pet QR Registry',
                    '{{ system.tagline | default("Pet Recovery System") }}'
                )
                WHERE html_content LIKE '%Lost Then Found Pet QR Registry%'
            """))
            
            # Update any remaining hardcoded "Admin Notification" in content (not titles)
            result2 = db.session.execute(text("""
                UPDATE email_template 
                SET html_content = REPLACE(
                    html_content,
                    '<p style="margin: 10px 0 0 0; font-size: 1.1rem;">Admin Notification</p>',
                    '<p style="margin: 10px 0 0 0; font-size: 1.1rem;">{{ system.tagline | default("Pet Recovery System") }}</p>'
                )
                WHERE html_content LIKE '%<p style="margin: 10px 0 0 0; font-size: 1.1rem;">Admin Notification</p>%'
            """))
            
            # Commit the changes
            total_updated = result1.rowcount + result2.rowcount
            db.session.commit()
            
            print(f"✅ Successfully updated {total_updated} email templates in database!")
            
            # Verify the updates
            check_result = db.session.execute(text("""
                SELECT COUNT(*) as count FROM email_template 
                WHERE html_content LIKE '%{{ system.tagline | default("Pet Recovery System") }}%'
            """)).fetchone()
            
            print(f"✅ Verified: {check_result.count} templates now use proper variable placeholders")
            
            # Check for any remaining hardcoded text
            hardcoded_check = db.session.execute(text("""
                SELECT COUNT(*) as count FROM email_template 
                WHERE html_content LIKE '%Lost Then Found Pet QR Registry%'
                   OR html_content LIKE '%<p style="margin: 10px 0 0 0; font-size: 1.1rem;">Admin Notification</p>%'
            """)).fetchone()
            
            if hardcoded_check.count > 0:
                print(f"⚠️  Warning: {hardcoded_check.count} templates still have hardcoded text")
            else:
                print("✅ All templates now use proper variable placeholders!")
            
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project directory")
        return False
    except Exception as e:
        print(f"❌ Error updating templates: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing email template variable placeholders...")
    success = update_database_templates()
    if success:
        print("🎉 Email template variable placeholder update completed!")
    else:
        print("❌ Email template update failed!")
        print("Try running the email template initialization script: python init_email_templates.py")
