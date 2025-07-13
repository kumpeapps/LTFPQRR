# LTFPQRR - Lost Then Found Pet QR Registry

A comprehensive web application for managing pet identification through QR codes, helping reunite lost pets with their families.

## Features

- 🐾 **Pet Registration** - Register pets with detailed profiles and photos
- 🏷️ **QR Tag Management** - Generate and manage QR codes for pet identification
- 👥 **User Management** - Customer and partner account systems
- 🔍 **Lost Pet Recovery** - Easy-to-use system for found pet reporting
- 💳 **Payment Integration** - Stripe and PayPal support for premium features
- 🏢 **Partner Program** - Multi-level partnership system with commissions
- 📱 **Mobile Friendly** - Responsive design for all devices

## Quick Start

1. **Start the application:**
   ```bash
   ./dev.sh start-dev
   ```

2. **Access the website:**
   - Main site: http://localhost:8000
   - Database admin: http://localhost:8080

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

## User Management CLI

LTFPQRR includes a powerful command-line interface for managing users, passwords, and roles:

```bash
# List all users
./cli.sh list-users

# Create new user
./cli.sh create-user --email admin@example.com --role admin

# Update user password
./cli.sh update-password --email user@example.com

# Assign roles
./cli.sh assign-role --email user@example.com --role admin

# Get help
./cli.sh --help
```

See [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md) for complete CLI documentation.

## Architecture

- **Backend:** Flask with SQLAlchemy ORM
- **Database:** MySQL 8.0
- **Queue System:** Redis + Celery for background tasks
- **Frontend:** Bootstrap 5 + Custom CSS/JS
- **Deployment:** Docker Compose

## Production Deployment

The application is production-ready. See [PRODUCTION_READY.md](PRODUCTION_READY.md) for deployment checklist and configuration details.

## Documentation

- [CLI Documentation](CLI_DOCUMENTATION.md) - Complete CLI usage guide
- [CLI Quick Reference](CLI_QUICK_REFERENCE.md) - Quick command reference
- [Production Guide](PRODUCTION_READY.md) - Production deployment guide
- [Error Resolution](ERROR_RESOLUTION_REPORT.md) - Troubleshooting guide

## License

MIT License - see LICENSE file for details.