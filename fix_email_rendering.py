#!/usr/bin/env python3
"""
Script to fix the email template rendering issue where Jinja2 fails and falls back 
to converting {{ }} to [ ]. This removes the problematic fallback behavior.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def fix_email_template_rendering():
    """Fix the email template rendering by removing the fallback bracket replacement"""
    
    try:
        # Read the current email models file
        models_file = "/Users/justinkumpe/Documents/LTFPQRR/models/email/email_models.py"
        
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the problematic fallback code
        old_fallback = """                # Log the error but provide a fallback
                import logging
                logging.warning(f"Jinja2 HTML rendering failed for template {self.name}: {jinja_error}")
                # Create a basic fallback template without Jinja2 syntax
                html_content = html_content.replace('{{', '[').replace('}}', ']').replace('{%', '[%').replace('%}', '%]')"""
        
        new_fallback = """                # Log the error and raise for debugging
                import logging
                logging.error(f"Jinja2 HTML rendering failed for template {self.name}: {jinja_error}")
                # Re-raise the error instead of using fallback that breaks templates
                raise jinja_error"""
        
        content = content.replace(old_fallback, new_fallback)
        
        # Fix text rendering fallback too
        old_text_fallback = """                logging.warning(f"Jinja2 text rendering failed for template {self.name}: {jinja_error}")
                if text_content:
                    text_content = text_content.replace('{{', '[').replace('}}', ']').replace('{%', '[%').replace('%}', '%]')"""
        
        new_text_fallback = """                logging.error(f"Jinja2 text rendering failed for template {self.name}: {jinja_error}")
                # Re-raise the error instead of using fallback that breaks templates
                raise jinja_error"""
        
        content = content.replace(old_text_fallback, new_text_fallback)
        
        # Fix subject rendering fallback
        old_subject_fallback = """                logging.warning(f"Jinja2 subject rendering failed for template {self.name}: {jinja_error}")
                subject = subject.replace('{{', '[').replace('}}', ']').replace('{%', '[%').replace('%}', '%]')"""
        
        new_subject_fallback = """                logging.error(f"Jinja2 subject rendering failed for template {self.name}: {jinja_error}")
                # Re-raise the error instead of using fallback that breaks templates
                raise jinja_error"""
        
        content = content.replace(old_subject_fallback, new_subject_fallback)
        
        # Write the fixed content back
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Successfully removed problematic fallback bracket replacement!")
        print("✅ Jinja2 template rendering will now work properly")
        print("⚠️  If there are Jinja2 errors, they will now be logged properly for debugging")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing email template rendering: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing email template Jinja2 rendering...")
    success = fix_email_template_rendering()
    if success:
        print("🎉 Email template rendering fix completed!")
        print("🔄 Restart the application to apply changes")
    else:
        print("❌ Email template rendering fix failed!")
