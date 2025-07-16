# Email Management System

The LTFPQRR Email Management System provides comprehensive email handling with queuing, retry logic, templates, and bulk sending capabilities.

## Features

### 📧 Email Queue System
- **Reliable Delivery**: All emails are queued for reliable delivery with retry logic
- **Priority Handling**: Support for different priority levels (low, normal, high, critical)
- **Automatic Retries**: Failed emails are automatically retried with exponential backoff
- **72-Hour Timeout**: Emails expire after 72 hours to prevent indefinite retries
- **Background Processing**: Emails can be processed in background without blocking the UI

### 📝 Email Templates
- **Reusable Templates**: Create and manage reusable email templates with variables
- **Variable Substitution**: Dynamic content using template variables like `{user_name}`, `{amount}`, etc.
- **HTML & Text**: Support for both HTML and plain text versions
- **Template Testing**: Built-in testing functionality to preview templates

### 📊 Email Campaigns
- **Bulk Sending**: Send emails to groups of users (all users, partners, customers, custom criteria)
- **Target Filtering**: Advanced targeting based on user attributes and subscription status
- **Campaign Tracking**: Monitor sent/failed counts and campaign status
- **Scheduled Sending**: Support for scheduling campaigns for future delivery

### 📈 Monitoring & Analytics
- **Comprehensive Logging**: Every email action is logged with timestamps and status
- **Queue Statistics**: Real-time stats on pending, sent, failed, and expired emails
- **Failure Rate Monitoring**: Track email delivery success rates
- **Admin Dashboard**: Web interface for monitoring and managing the email system

## System Components

### Models
- **EmailQueue**: Manages outgoing emails with retry logic
- **EmailLog**: Comprehensive logging of all email activities
- **EmailTemplate**: Reusable email templates with variables
- **EmailCampaign**: Bulk email campaigns with targeting

### Services
- **EmailManager**: Core service for queuing and processing emails
- **EmailTemplateManager**: Template creation and rendering
- **EmailCampaignManager**: Campaign creation and execution

### Admin Interface
- **Dashboard**: Overview of email system status and statistics
- **Queue Management**: View and manage pending emails
- **Template Editor**: Create and edit email templates
- **Campaign Manager**: Create and send bulk email campaigns
- **Individual Emails**: Send custom emails to specific users

## Usage Examples

### Basic Email Sending
```python
from email_utils import send_email_with_queue

# Send email with queue management
success = send_email_with_queue(
    to_email="user@example.com",
    subject="Welcome to LTFPQRR",
    html_body="<h1>Welcome!</h1>",
    priority="high",
    email_type="welcome"
)
```

### Template-Based Emails
```python
from services.email_service import EmailTemplateManager

# Send using template
success = EmailTemplateManager.send_from_template(
    template_name="partner_subscription_approved",
    to_email="partner@example.com",
    variables={
        'user_name': 'John Doe',
        'partner_name': 'Pet Clinic',
        'amount': '10.00'
    }
)
```

### Bulk Email Campaigns
```python
from services.email_service import EmailCampaignManager

# Create and send campaign
campaign = EmailCampaignManager.create_campaign(
    name="Monthly Newsletter",
    template_id=1,
    target_type="partners",
    description="Monthly partner update"
)

# Send immediately
result = EmailCampaignManager.send_campaign(campaign.id)
```

## Queue Processing

### Automatic Processing
The email queue is processed automatically in the background. You can also process it manually:

```bash
# Process pending emails
python email_queue_manager.py process

# Get queue status
python email_queue_manager.py status

# Clean up old emails (30+ days)
python email_queue_manager.py cleanup
```

### Scheduled Processing
For production environments, set up a cron job to process the queue regularly:

```bash
# Add to crontab for every 5 minutes
*/5 * * * * cd /path/to/ltfpqrr && python email_queue_manager.py process
```

## Default Templates

The system includes pre-configured templates for:

1. **partner_subscription_confirmation** - Sent when partner creates subscription
2. **partner_subscription_approved** - Sent when admin approves subscription
3. **partner_subscription_rejected** - Sent when admin rejects subscription
4. **admin_partner_approval_notification** - Sent to admins for approval

### Initialize Default Templates
```bash
python init_email_templates.py
```

## Admin Interface URLs

- **Dashboard**: `/admin/email/`
- **Email Queue**: `/admin/email/queue`
- **Email Logs**: `/admin/email/logs`
- **Templates**: `/admin/email/templates`
- **Campaigns**: `/admin/email/campaigns`
- **Send Individual**: `/admin/email/send-individual`

## Configuration

### Database Tables
The system uses these new database tables:
- `email_queue` - Pending and processed emails
- `email_logs` - All email activity logs
- `email_templates` - Reusable email templates
- `email_campaigns` - Bulk email campaigns

### Environment Variables
The system uses existing SMTP configuration from the database settings.

## Migration

To add the email management system to an existing installation:

1. **Create Migration**:
   ```bash
   python migrate.py revision --autogenerate --message "Add email management system"
   python migrate.py upgrade
   ```

2. **Initialize Templates**:
   ```bash
   python init_email_templates.py
   ```

3. **Update Existing Code**:
   Replace direct email calls with queue-based functions:
   ```python
   # Old way
   send_partner_subscription_approved_email(user, subscription)
   
   # New way (automatic fallback)
   send_partner_subscription_approved_email_enhanced(user, subscription)
   ```

## Benefits

### Reliability
- **No Lost Emails**: All emails are queued and logged
- **Automatic Retries**: Failed emails are retried automatically
- **Error Tracking**: Detailed error logging for troubleshooting

### Scalability
- **Background Processing**: Emails don't block the main application
- **Bulk Operations**: Efficient handling of large email campaigns
- **Performance Monitoring**: Track system performance and bottlenecks

### Management
- **Admin Interface**: Easy-to-use web interface for email management
- **Template System**: Consistent branding and messaging
- **Campaign Tools**: Professional bulk email capabilities

### Compliance
- **Audit Trail**: Complete logging of all email activities
- **Retry Limits**: Prevents infinite retry loops
- **Expiration**: Automatic cleanup of old emails

## Troubleshooting

### Common Issues

1. **Emails Not Sending**: Check SMTP configuration in database settings
2. **Queue Not Processing**: Run manual processing to check for errors
3. **Template Errors**: Use template testing feature to debug issues
4. **High Failure Rate**: Check SMTP server logs and connectivity

### Monitoring Commands
```bash
# Check queue status
python email_queue_manager.py status

# Process queue manually
python email_queue_manager.py process --verbose

# Clean up old data
python email_queue_manager.py cleanup --days 30
```

### Log Files
Monitor the application logs for email-related errors:
- Queue processing errors
- SMTP connection issues
- Template rendering problems
- Campaign execution status

## Future Enhancements

Planned improvements include:
- Email bounce handling
- Unsubscribe management  
- A/B testing for campaigns
- Advanced analytics and reporting
- Integration with external email services
- Webhook support for email events
