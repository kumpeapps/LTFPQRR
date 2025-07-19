# Email Template Category System Implementation

## Overview

The email template system has been redesigned to use a category-based approach that defines:
- Available models and their fields for each template type
- Required input parameters based on the category
- Target email resolution logic
- Template variable validation

## Template Categories

### 1. User Account (`user_account`)
- **Purpose**: User account-related emails (registration, password reset, etc.)
- **Required Inputs**: `user_id`
- **Available Models**: `user`, `system`
- **Target Email**: `user.email`
- **Examples**: Welcome email, Email verification, Password reset

### 2. User Notification (`user_notification`)
- **Purpose**: General notifications to users
- **Required Inputs**: `user_id`
- **Optional Inputs**: `partner_id`, `subscription_id`
- **Available Models**: `user`, `partner`, `subscription`, `system`
- **Target Email**: `user.email`
- **Examples**: Service updates, Feature announcements, Maintenance notifications

### 3. Partner Account (`partner_account`)
- **Purpose**: Partner account management emails
- **Required Inputs**: `partner_id`
- **Optional Inputs**: `user_id`
- **Available Models**: `partner`, `user`, `system`
- **Target Email**: `partner.owner.email`
- **Examples**: Partner application approved, Partner account setup

### 4. Partner Subscription (`partner_subscription`)
- **Purpose**: Partner subscription and billing emails
- **Required Inputs**: `subscription_id`
- **Optional Inputs**: `partner_id`, `user_id`
- **Available Models**: `subscription`, `partner`, `user`, `system`
- **Target Email**: `subscription.partner.owner.email`
- **Examples**: Subscription created, Payment successful, Payment failed

### 5. Partner Notification (`partner_notification`)
- **Purpose**: General notifications to partners
- **Required Inputs**: `partner_id`
- **Optional Inputs**: `user_id`, `subscription_id`
- **Available Models**: `partner`, `user`, `subscription`, `system`
- **Target Email**: `partner.owner.email`
- **Examples**: New features for partners, Commission reports

### 6. System Admin (`system_admin`)
- **Purpose**: Administrative and internal system emails
- **Required Inputs**: None
- **Optional Inputs**: `user_id`, `partner_id`, `subscription_id`, `admin_email`
- **Available Models**: `user`, `partner`, `subscription`, `system`
- **Target Email**: `admin_email` (must be provided)
- **Examples**: Error alerts, System reports, Security alerts

### 7. Marketing (`marketing`)
- **Purpose**: Marketing and promotional emails
- **Required Inputs**: None
- **Optional Inputs**: `user_id`, `partner_id`, `target_email`
- **Available Models**: `user`, `partner`, `system`
- **Target Email**: `target_email` (flexible targeting)
- **Examples**: Newsletter, Product announcements, Special offers

### 8. Transactional (`transactional`)
- **Purpose**: Transaction-related emails
- **Required Inputs**: `user_id`
- **Optional Inputs**: `partner_id`, `subscription_id`, `transaction_id`
- **Available Models**: `user`, `partner`, `subscription`, `system`
- **Target Email**: `user.email`
- **Examples**: Purchase confirmation, Receipt, Refund notification

## Model Fields Available

### User Model (`user`)
- `id`: User ID
- `username`: Username
- `email`: Email address
- `first_name`: First name
- `last_name`: Last name
- `get_full_name()`: Full name (method)
- `created_at`: Account creation date
- `last_login`: Last login date
- `is_active`: Account active status
- `phone`: Phone number
- `timezone`: User timezone

### Partner Model (`partner`)
- `id`: Partner ID
- `company_name`: Company name
- `status`: Partner status
- `created_at`: Partner creation date
- `website`: Company website
- `phone`: Company phone
- `address`: Company address
- `owner.email`: Owner email address
- `owner.get_full_name()`: Owner full name

### Subscription Model (`subscription`)
- `id`: Subscription ID
- `status`: Subscription status
- `plan_name`: Subscription plan name
- `amount`: Subscription amount
- `start_date`: Subscription start date
- `end_date`: Subscription end date
- `created_at`: Subscription creation date
- `partner.company_name`: Partner company name
- `partner.owner.email`: Partner owner email

### System Model (`system`)
- `site_url`: Site URL
- `app_name`: Application name
- `support_email`: Support email address
- `company_name`: Company name
- `company_address`: Company address
- `phone`: Company phone
- `logo_url`: Company logo URL

## Usage Examples

### Creating a Partner Subscription Template

```python
from services.enhanced_email_service import EmailTemplateManager

# Create template
template = EmailTemplateManager.create_template(
    name="partner_payment_success",
    subject="Payment Received - {{subscription.plan_name}}",
    html_content="""
    <h1>Payment Confirmation</h1>
    <p>Dear {{partner.owner.get_full_name()}},</p>
    <p>We have successfully received your payment for {{subscription.plan_name}}.</p>
    <ul>
        <li>Amount: ${{subscription.amount}}</li>
        <li>Start Date: {{subscription.start_date}}</li>
        <li>Company: {{partner.company_name}}</li>
    </ul>
    <p>Thank you for your business!</p>
    <p>Best regards,<br>{{system.app_name}} Team</p>
    """,
    category="partner_subscription"
)
```

### Sending Email Using Template

```python
from services.enhanced_email_service import EmailTemplateManager

# Send email with required inputs
queue_item = EmailTemplateManager.send_from_template(
    template_name="partner_payment_success",
    inputs={
        'subscription_id': 123,  # Required for partner_subscription category
        # partner_id and user_id will be auto-loaded from subscription
    },
    email_type="payment_confirmation"
)
```

### Template Validation

The system automatically validates that all required inputs are provided based on the template category:

```python
# This will fail validation
EmailTemplateManager.send_from_template(
    template_name="partner_payment_success",
    inputs={},  # Missing required subscription_id
    email_type="test"
)
# Raises: ValueError("Missing required inputs for template category: subscription_id")
```

## Benefits

1. **Type Safety**: Templates are validated based on their category requirements
2. **Auto Email Resolution**: Target email addresses are automatically resolved based on category
3. **Model Context**: Only relevant models are available for each template category
4. **Input Validation**: Required inputs are enforced at send time
5. **Better UX**: Template editor shows relevant variables and requirements
6. **Maintainability**: Clear separation of concerns for different email types

## File Structure

```
models/email/
├── email_models.py          # Enhanced EmailTemplate model
├── template_categories.py   # Category definitions and configurations

services/
├── enhanced_email_service.py # Enhanced email service with category support

routes/
├── email_admin.py           # Updated admin routes with category support

templates/admin/email/
├── create_template_enhanced.html  # Category-aware template creation
├── edit_template_enhanced.html    # Category-aware template editing
├── test_template_enhanced.html    # Category-aware template testing
```

## Migration Required

A database migration is needed to add the new fields to the `email_templates` table:

```sql
ALTER TABLE email_templates 
ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'user_notification',
ADD COLUMN required_inputs JSON;
```

This migration will be generated automatically when the container rebuilds with the new model definitions.

## Backward Compatibility

The system maintains backward compatibility:
- Existing templates default to `user_notification` category
- Legacy variable replacement (`{variable}`) still works alongside new model syntax (`{{model.field}}`)
- Old template creation methods still function but use default category
