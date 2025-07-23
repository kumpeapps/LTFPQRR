#!/usr/bin/env python3
"""
Script to update all email templates to include embedded logo in the header.
This updates the init_email_templates.py file to include the logo using cid:logo reference.
"""

import re


def update_email_templates():
    """Update email templates to include embedded logo in header"""

    template_file = "init_email_templates.py"

    # Read the current file
    with open(template_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern to match the header section with app name - handle both {{ system.app_name }} and hardcoded LTFPQRR
    # Look for the div with gradient background that contains the app name
    header_pattern1 = r'(<div style="background: linear-gradient\(135deg, #667eea 0%, #764ba2 100%\); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">)\s*(<h1 style="color: #13c1be; margin: 0; font-size: 2\.5rem; text-shadow: 2px 2px 4px rgba\(0,0,0,0\.3\);">{{ system\.app_name }}</h1>)\s*(<p style="margin: 10px 0 0 0; font-size: 1\.1rem;">{{ system\.tagline \| default\("Lost Then Found Pet QR Registry"\) }}</p>)\s*(</div>)'

    # Pattern for hardcoded LTFPQRR
    header_pattern2 = r'(<div style="background: linear-gradient\(135deg, #667eea 0%, #764ba2 100%\); padding: 30px; text-align: center; color: white; border-radius: 12px 12px 0 0;">)\s*(<h1 style="color: #13c1be; margin: 0; font-size: 2\.5rem; text-shadow: 2px 2px 4px rgba\(0,0,0,0\.3\);">LTFPQRR</h1>)\s*(<p style="margin: 10px 0 0 0; font-size: 1\.1rem;">{{ system\.tagline \| default\("Lost Then Found Pet QR Registry"\) }}</p>)\s*(</div>)'

    # Replacement with logo (same for both patterns)
    replacement = r"""\1
        <div style="margin-bottom: 20px;">
            <img src="cid:logo" alt="{{ system.app_name }} Logo" style="max-width: 20px; height: auto; border-radius: 4px;">
        </div>
        \2
        \3
    \4"""

    # Apply the replacement for both patterns
    updated_content = re.sub(
        header_pattern1, replacement, content, flags=re.MULTILINE | re.DOTALL
    )
    updated_content = re.sub(
        header_pattern2, replacement, updated_content, flags=re.MULTILINE | re.DOTALL
    )

    # Check if any replacements were made
    if updated_content == content:
        print("No email template headers found to update.")
        return False

    # Count the number of replacements made
    num_replacements1 = len(
        re.findall(header_pattern1, content, flags=re.MULTILINE | re.DOTALL)
    )
    num_replacements2 = len(
        re.findall(header_pattern2, content, flags=re.MULTILINE | re.DOTALL)
    )
    total_replacements = num_replacements1 + num_replacements2

    # Write the updated content back to the file
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(
        f"Successfully updated {total_replacements} email templates with embedded logo!"
    )
    return True


if __name__ == "__main__":
    print("Updating email templates to include embedded logo...")
    update_email_templates()
    print("Email template update complete.")
