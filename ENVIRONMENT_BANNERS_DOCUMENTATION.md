# Environment Banners Documentation

## Overview

The LTFPQRR platform now supports environment-specific banners to clearly indicate when users are accessing demo or pre-production environments. These banners are controlled by environment variables and provide visual cues to prevent confusion about which environment is being used.

## Environment Variables

### DEMO_MODE
- **Variable**: `DEMO_MODE`
- **Default**: `false`
- **Valid Values**: `true` (case insensitive), `false`, or unset
- **Purpose**: Displays a blue demo banner indicating the environment is for demonstration purposes

### PREPROD_MODE
- **Variable**: `PREPROD_MODE`  
- **Default**: `false`
- **Valid Values**: `true` (case insensitive), `false`, or unset
- **Purpose**: Displays an orange pre-production banner indicating the environment is for testing

## Banner Styles

### Demo Banner
- **Color**: Blue gradient (#17a2b8 to #138496)
- **Icon**: Flask with bouncing animation
- **Message**: "DEMO ENVIRONMENT - You are viewing a demonstration environment. Data and payments are simulated."
- **Badge**: "Demo Mode"

### Pre-Production Banner
- **Color**: Orange gradient (#fd7e14 to #e55a00)
- **Icon**: Bug with pulsing animation
- **Message**: "PRE-PRODUCTION ENVIRONMENT - You are viewing a pre-production testing environment. Features may be unstable."
- **Badge**: "Pre-Prod"

## Usage Examples

### Docker Compose Setup

```yaml
# docker-compose.yml
services:
  web:
    environment:
      - DEMO_MODE=true
      # OR
      - PREPROD_MODE=true
```

### Environment Variable Setup

```bash
# Demo environment
export DEMO_MODE=true
./dev.sh start-dev

# Pre-production environment
export PREPROD_MODE=true
./dev.sh start-dev

# Production (no banners)
unset DEMO_MODE
unset PREPROD_MODE
./dev.sh start-dev
```

### Both Banners Simultaneously

```bash
# Both banners will be displayed (useful for comprehensive testing)
export DEMO_MODE=true
export PREPROD_MODE=true
./dev.sh start-dev
```

## Implementation Details

### Configuration (config.py)
```python
class Config:
    # Environment banners
    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
    PREPROD_MODE = os.environ.get("PREPROD_MODE", "false").lower() == "true"
```

### Flask Integration (app.py)
The banners are set in the Flask application's `before_request` handler:

```python
@app.before_request
def check_maintenance_mode():
    # Set environment-based banner flags
    g.demo_mode = app.config.get('DEMO_MODE', False)
    g.preprod_mode = app.config.get('PREPROD_MODE', False)
```

### Template Integration
The banners are included in `base.html` and rendered via `environment_banners.html`:

```html
<!-- Environment Banners (Demo/Pre-Production) -->
{% include 'components/environment_banners.html' %}
```

## Banner Hierarchy

The banners appear in the following order from top to bottom:
1. **Environment Banners** (Demo/Pre-Production) - Always visible when enabled
2. **Maintenance Banner** - Only visible to admins when maintenance mode is active

## Features

### User Experience
- **Dismissible**: Users can dismiss banners with the close button
- **Responsive**: Banners adapt to different screen sizes
- **Animated Icons**: Visual animations draw attention to the banner
- **Clear Messaging**: Specific messages explain the environment purpose

### Developer Experience
- **Environment Variable Control**: Easy to enable/disable via environment variables
- **Case Insensitive**: Accepts 'true', 'TRUE', 'True', etc.
- **Default Safe**: Defaults to false (no banners) if not set
- **Multiple Banner Support**: Can display both demo and preprod banners simultaneously

## Testing

### Unit Tests
Run the test script to verify configuration:

```bash
python test_environment_banners.py
```

### Manual Testing

1. **Test Demo Banner**:
   ```bash
   export DEMO_MODE=true
   ./dev.sh rebuild-dev
   # Visit http://localhost:8000
   ```

2. **Test Pre-Production Banner**:
   ```bash
   export PREPROD_MODE=true  
   ./dev.sh rebuild-dev
   # Visit http://localhost:8000
   ```

3. **Test Both Banners**:
   ```bash
   export DEMO_MODE=true
   export PREPROD_MODE=true
   ./dev.sh rebuild-dev
   # Visit http://localhost:8000
   ```

## Production Deployment

### Security Considerations
- **Never set demo/preprod flags in production**
- **Environment variables should be managed through deployment pipeline**
- **Consider using deployment-specific configuration files**

### Deployment Pipeline Integration

```yaml
# Example CI/CD pipeline
stages:
  - name: demo
    environment:
      DEMO_MODE: "true"
      
  - name: preprod
    environment:
      PREPROD_MODE: "true"
      
  - name: production
    environment:
      # No demo/preprod flags set
```

## Troubleshooting

### Banner Not Appearing
1. Verify environment variable is set: `echo $DEMO_MODE`
2. Restart the application after setting environment variables
3. Check browser console for JavaScript errors
4. Ensure the value is exactly 'true' (case insensitive)

### Multiple Banners Overlapping
- This is expected behavior when multiple environment flags are set
- Banners are designed to stack vertically
- Consider using only one environment flag per deployment

### CSS Conflicts
- Banners use Bootstrap classes and custom CSS
- If styles appear broken, check for CSS conflicts in custom stylesheets
- Banners are positioned at the top of the page with high z-index

## Related Documentation

- [System Settings Documentation](ADMIN_SETTINGS_FIX_REPORT.md)
- [Maintenance Mode Documentation](templates/components/maintenance_banner.html)
- [Docker Deployment Guide](README.md)
