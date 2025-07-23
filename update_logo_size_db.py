#!/usr/bin/env python3
"""
Script to force update email templates in database with new logo sizes.
This updates existing database records to use the smaller 20px logo.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def update_logo_size_in_db():
    """Update logo size from 80px to 20px in existing email templates"""
    
    try:
        from app import app
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            print("Updating email template logo sizes in database...")
            
            # Update all templates that have the old 80px logo to use 20px
            result = db.session.execute(text("""
                UPDATE email_template 
                SET html_content = REPLACE(
                    REPLACE(
                        html_content,
                        'max-width: 80px; height: auto; border-radius: 8px;',
                        'max-width: 20px; height: auto; border-radius: 4px;'
                    ),
                    'max-width: 80px',
                    'max-width: 20px'
                )
                WHERE html_content LIKE '%max-width: 80px%' OR html_content LIKE '%border-radius: 8px%'
            """))
            
            updated_count = result.rowcount
            db.session.commit()
            
            print(f"✅ Successfully updated {updated_count} email templates with smaller logo size!")
            
            # Verify the updates
            check_result = db.session.execute(text("""
                SELECT COUNT(*) as count FROM email_template 
                WHERE html_content LIKE '%max-width: 20px%'
            """)).fetchone()
            
            print(f"✅ Verified: {check_result.count} templates now have 20px logo size")
            
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project directory")
        return False
    except Exception as e:
        print(f"❌ Error updating templates: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Updating email template logo sizes...")
    success = update_logo_size_in_db()
    if success:
        print("🎉 Email template logo size update completed!")
    else:
        print("❌ Email template update failed!")
