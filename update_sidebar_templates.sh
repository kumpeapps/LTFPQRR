#!/bin/bash

# Script to update all template files to use the unified dashboard sidebar

echo "🔄 Updating all dashboard templates to use unified sidebar..."

# Function to update a template file
update_template() {
    local file="$1"
    local context="$2"
    
    echo "📝 Updating $file with context: $context"
    
    # Create a temporary file with the replacement
    cat > "/tmp/sidebar_replacement.tmp" << EOF
        <!-- Sidebar -->
        {% set sidebar_context = '$context' %}
        {% include 'includes/dashboard_sidebar.html' %}
EOF
    
    # Use Python to handle the complex replacement
    python3 << PYTHON_SCRIPT
import re

# Read the file
with open('$file', 'r') as f:
    content = f.read()

# Pattern to match the sidebar section
pattern = r'(\s*<!-- Sidebar -->\s*<div class="col-md-3 col-lg-2 sidebar">.*?</div>)'
replacement = '''        <!-- Sidebar -->
        {% set sidebar_context = '$context' %}
        {% include 'includes/dashboard_sidebar.html' %}'''

# Replace the sidebar section
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back to file
with open('$file', 'w') as f:
    f.write(new_content)
    
print(f"✅ Updated {len(re.findall(pattern, content))} sidebar section(s) in $file")
PYTHON_SCRIPT
}

# Update admin templates
echo "🔧 Updating admin templates..."
update_template "templates/admin/partner_subscriptions.html" "admin"
update_template "templates/admin/pricing.html" "admin"
update_template "templates/admin/payment_gateways.html" "admin"
update_template "templates/admin/settings.html" "admin"
update_template "templates/admin/edit_user.html" "admin"
update_template "templates/admin/edit_payment_gateway.html" "admin"
update_template "templates/admin/edit_pricing_plan.html" "admin"
update_template "templates/admin/create_pricing_plan.html" "admin"
update_template "templates/admin/add_subscription.html" "admin"
update_template "templates/admin/payments.html" "admin"

# Update customer templates
echo "🔧 Updating customer templates..."
update_template "templates/customer/payments.html" "customer"
update_template "templates/customer/subscriptions.html" "customer"

echo "✅ All templates updated successfully!"
echo "🎉 Unified sidebar navigation is now in place across all dashboard pages."
