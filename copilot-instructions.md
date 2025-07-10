# GitHub Copilot Instructions Template for Flask/Python Projects

## Project Overview
LTFPQRR is a Lost Then Found Pet QR Registry consisting of a comprehensive web application that helps reunite lost pets with their owners through QR code technology. The system includes:

- **Customer Portal**: Pet owners can claim QR tags, register pets, and manage subscriptions
- **Partner Portal**: Businesses can create and distribute QR tags to customers
- **Public Access**: Anyone can scan QR codes to view pet information and contact owners
- **Admin Dashboard**: Complete system management and user administration

## Critical: Maintain These Instructions

**IMPORTANT**: These copilot instructions serve as the definitive project documentation and must be kept current with any major changes to the system.

### When to Update These Instructions
- **Architecture Changes**: Any modifications to the overall system architecture, database schema, or core technologies
- **New Features**: Addition of major features, modules, or integrations
- **Technology Stack Changes**: Updates to frameworks, libraries, or development tools
- **Security Updates**: Changes to authentication, authorization, or security practices
- **Deployment Changes**: Modifications to Docker configuration, environment setup, or deployment process
- **API Changes**: Updates to external integrations (payment gateways, third-party services)
- **Database Changes**: Schema modifications, migration patterns, or database technology changes

### How to Update These Instructions
1. **Document the change** in the relevant section of these instructions
2. **Update examples** if code patterns or usage has changed
3. **Modify guidelines** to reflect new best practices
4. **Update technology list** if new dependencies are added or removed
5. **Revise setup instructions** if development workflow changes
6. **Test instructions** ensure they accurately reflect current system state

### Sections That Require Frequent Updates
- **Key Technologies**: When dependencies change
- **Important Guidelines**: When development practices evolve
- **Environment Variables**: When configuration changes
- **External Dependencies**: When integrations are added/removed
- **Migration System**: When database patterns change
- **Security Considerations**: When security practices are updated

**Remember**: Outdated instructions can lead to confusion, bugs, and security vulnerabilities. Always update these instructions as part of any major change.

## Key Technologies
- **Python**: Primary programming language
- **Flask**: Web framework for the web interface
- **SQLAlchemy**: ORM for all database interactions
- **Docker**: Containerization for deployment
- **Database**: SQLAlchemy ORM with MySQL in development
- **Redis**: Caching and session management
- **Celery**: Background task processing
- **Bootstrap 5**: Responsive frontend framework
- **Stripe/PayPal**: Payment processing integrations
- **Alembic**: Database migration management
- **Flask-Login**: Authentication and session management
- **Flask-WTF**: Form handling and CSRF protection

## Important Guidelines

1. **Database Migration System**
   - All database operations MUST use SQLAlchemy ORM
   - Do NOT use raw SQL or .sql files for schema changes or data modifications
   - Database schema is managed by **Alembic migrations** for production consistency
   - Migrations run automatically inside Docker containers on startup
   - For fresh installs: Schema is created via SQLAlchemy + stamped with latest migration
   - For existing databases: Alembic upgrade applies pending migrations

2. **Security Considerations**
   - API keys must be encrypted at rest using the encryption utilities
   - User authentication follows secure practices with Flask-Login
   - User inputs must be validated and sanitized using WTForms
   - CSRF protection enabled through Flask-WTF
   - File uploads are validated and secured
   - Payment processing uses secure gateway APIs
   - Session management with Redis backend

3. **Role-Based Access Control**
   - Use the role-based system for all user management
   - Users must have appropriate roles: "user", "admin", "super-admin", etc.
   - All permissions are managed through the role system
   - "super-admin" should have access to all features

4. **Admin Features**
   - First user is automatically assigned admin and super-admin roles
   - SUPER_ADMIN_USERNAME environment variable defines a user that always has admin privileges
   - System settings control features like user registration and payment gateways
   - Super-admin can manually add subscriptions and manage payment settings
   - Admin dashboard provides system statistics and management tools

5. **Docker Deployment**
   - Local development uses docker-compose with MySQL
   - Production deployment uses pre-built images
   - Database backend is configurable via DATABASE_URL
   - Health checks are implemented for all services
   - ALWAYS use `./dev.sh rebuild-dev` instead of `docker restart` to apply changes
   - ALWAYS use `./dev.sh rebuild-dev` instead of `docker compose build` to apply changes
   - ALWAYS use `./dev.sh start-dev` instead of `docker compose up` to apply changes
   - ALWAYS use `./dev.sh stop` instead of `docker compose down ` to apply changes
   - Never use individual container restarts like `docker restart container-name`

6. **Code Structure**
   - Models are defined in models/models.py
   - Forms are defined in forms.py
   - Templates are organized by feature (auth/, admin/, customer/, partner/, etc.)
   - Static files in static/ directory with uploads/ subdirectory
   - Alembic migrations in alembic/ directory
   - Main application logic in app.py

7. **Core Features**
   - **QR Tag Management**: Partners create tags, customers claim them
   - **Pet Registration**: Detailed pet profiles with photos and contact info
   - **Subscription System**: Monthly, yearly, and lifetime plans
   - **Public Pet Search**: Anyone can scan QR codes to find pet info
   - **Secure Messaging**: Contact owners without exposing personal info
   - **Payment Processing**: Stripe and PayPal integration
   - **Tag Transfer**: Users can transfer tags to other accounts
   - **Notification System**: Email alerts when pets are found

8. **Documentation Maintenance**
   - **CRITICAL**: Update these copilot instructions with any structural changes
   - Document new features, integrations, or architectural decisions
   - Keep environment variables, dependencies, and setup instructions current
   - Test all documented procedures after making changes
   - Maintain accuracy of technology stack and deployment information

## Error Handling and Debugging

1. **Container Troubleshooting**
   - Use `docker ps` to check container status and health
   - Check container logs with `docker logs [container_name]` for startup issues
   - Use `./dev.sh rebuild-dev` to apply code changes and restart services
   - Monitor container restart loops and investigate root causes

2. **Database Connection Issues**
   - Verify database connectivity before starting application services
   - Implement proper connection pooling and timeout handling
   - Use health checks to validate database schema state
   - Check migration status during container startup

3. **Code Quality and Syntax**
   - Use proper indentation and syntax validation
   - Implement comprehensive error handling in route handlers
   - Use try-catch blocks for database operations
   - Log errors with appropriate detail levels

4. **Performance Debugging**
   - Profile database queries for slow operations
   - Monitor session management and memory usage
   - Use Flask debug mode for development troubleshooting
   - Implement proper logging for performance monitoring

## Performance Optimization

1. **Database Query Optimization**
   - Use eager loading with `joinedload()` for related data
   - Implement session-based caching for frequently accessed data
   - Optimize context processors to reduce database hits
   - Use connection pooling in database configuration

2. **Flask Application Performance**
   - Enable Flask session caching with appropriate timeout
   - Configure static file caching
   - Use `@cache.memoize` for expensive operations
   - Implement proper session management

3. **Authentication and Authorization**
   - Cache user permissions in session
   - Use efficient user loading with eager loading
   - Implement proper session invalidation
   - Optimize permission checking logic

## Common Tasks

- **Add New Model**: Define in `models/`
- **Database Changes**: 
  1. Update SQLAlchemy model definitions
  2. Generate Alembic migration: `python migrate.py autogenerate --message "description"`
  3. Review and test migration files
  4. Rebuild containers using `./dev.sh rebuild-dev`
- **Admin Settings**: Add to SystemSetting initialization in app.py
- **API Key Management**: Use the encryption utilities for secure storage
- **Applying Changes**: Always use `./dev.sh rebuild-dev` to rebuild and restart services
- **⚠️ Update Instructions**: **ALWAYS** update these copilot instructions when making structural changes, adding features, or changing technologies

## Development Workflow
Use the `dev.sh` script for common development tasks such as:
- Starting/stopping services: `./dev.sh start-dev`, `./dev.sh stop`
- Building images: Use `./dev.sh rebuild-dev` to rebuild and restart development environment
- Running migrations: Migrations execute automatically at container startup
- Resetting the database: `./dev.sh reset-db`
- User and role management: Use the web interface at `/admin/users` for all user and role management tasks

### Migration System Guidelines
- Database schema is managed through **Alembic migrations** inside Docker containers
- Migration files are located in `alembic/`
- Container startup workflow:
  1. Check if `alembic_version` table exists
  2. If exists → Run `alembic upgrade head` to apply pending migrations
  3. If not exists → Create schema via SQLAlchemy + stamp with latest migration
- Model changes require container rebuild using `./dev.sh rebuild-dev`
- Always test schema changes in development using `./dev.sh rebuild-dev`

## Migration Architecture

### Container-Based Migration System
The platform uses a production-ready migration system that runs inside Docker containers:

#### LTFPQRR (Primary Application)
- **File**: `start_ltfpqrr.sh`
- **Responsibility**: Database schema creation, migration management, and web application
- **Startup Process**:
  1. Wait for database connection (any SQLAlchemy-supported database)
  2. Check for `alembic_version` table existence
  3. If table exists: Run `python migrate.py upgrade` (apply pending migrations)
  4. If table missing: Create schema via SQLAlchemy + stamp with latest migration
  5. Initialize system roles and settings
  6. Start Flask web application with Gunicorn

#### Migration File Structure
```
/
├── alembic/
│   ├── versions/          # Migration scripts
│   ├── env.py            # Alembic environment configuration
│   └── script.py.mako    # Migration template
├── alembic.ini           # Alembic configuration
├── migrate.py            # Migration helper script
└── models/               # SQLAlchemy model definitions
```

#### Key Benefits
- **Production Ready**: Migrations run automatically in Docker containers
- **Consistent Schema**: Single source of truth through main application
- **Zero Downtime**: Migrations apply automatically on container startup
- **Rollback Capable**: Alembic supports schema version management
- **Environment Agnostic**: Works in development, staging, and production
- **Multi-Service Ready**: Supports web app, background workers, and API services

## Testing Framework

### Test Structure
The platform includes a comprehensive test suite located in the `tests/` directory:
- **Unit Tests** (`test_models.py`) - Database model validation and relationships
- **Integration Tests** (`test_user_registration.py`) - User registration and role assignment logic
- **Web Tests** (`test_web_integration.py`) - HTTP endpoints, authentication, and form processing
- **[ADD_PROJECT_SPECIFIC_TEST_CATEGORIES]**

### Running Tests
Use the test runner script for all testing needs:
```bash
./run_tests.sh                    # Run all tests with coverage
./run_tests.sh --no-coverage      # Run tests without coverage
./run_tests.sh --verbose          # Verbose output
./run_tests.sh --pattern="test_*" # Run specific test patterns
```

### Test Categories and Coverage

#### Model Tests
- [MODEL_1] model creation and validation
- [MODEL_2] model relationships and constraints
- User settings without legacy fields (no is_admin flag)
- System settings initialization and value handling
- [ADD_PROJECT_SPECIFIC_MODEL_TESTS]

#### User Registration Tests
- **First user automatically gets admin roles**: admin, super-admin, and user
- **Subsequent users get only user role**: enforces proper role hierarchy
- Password hashing and authentication validation
- Username uniqueness enforcement
- User settings creation and association

#### Web Integration Tests
- **Registration workflow**: Page loading, form submission, validation
- **Authentication flow**: Login success/failure, session management
- **Permission enforcement**: Role-based access control
- **Protected routes**: Dashboard requires authentication
- **System settings**: Registration can be disabled dynamically
- **Error handling**: Duplicate users, invalid credentials
- **[ADD_PROJECT_SPECIFIC_WEB_TESTS]**

### Test Database Configuration
- Uses SQLite in-memory database for isolation
- Separate test Flask app with minimal templates
- Fixtures for roles, system settings, and clean database state
- No dependency on production [DATABASE_TYPE] database

### Key Test Validations
- **Role Assignment Logic**: First user gets all admin roles, others get user role only
- **Authentication Security**: Password hashing, login validation, session management
- **Permission System**: Role-based access control without legacy is_admin flags
- **Error Handling**: Proper validation and error messages for edge cases
- **Database Integrity**: Model relationships and constraints work correctly
- **[ADD_PROJECT_SPECIFIC_VALIDATIONS]**

### CI/CD Integration
- GitHub Actions workflow runs all tests automatically
- Matrix testing across Python versions
- Docker integration tests
- Security scanning with safety and bandit
- Coverage reporting with minimum thresholds

### Test Development Guidelines
- All new features should include corresponding tests
- Test both happy path and error conditions
- Use descriptive test names that explain the scenario
- Follow the existing fixture pattern for database setup
- Ensure tests are isolated and don't depend on each other

## Code Cleanup and Maintenance

### Documentation Maintenance
- **Update copilot instructions** immediately after any major changes
- **Document architectural decisions** in these instructions
- **Keep environment variable lists current** when configuration changes
- **Update dependency lists** when packages are added or removed
- **Revise setup instructions** when development workflow changes
- **Test all documented procedures** to ensure they work correctly

### Temporary Files and Test Scripts
- **Always remove temporary test scripts** when development tasks are complete
- Delete any `.py` files created for testing, debugging, or one-time operations
- Clean up temporary scripts like `test_*.py`, `debug_*.py`, `verify_*.py`, etc.
- Use `git status` to identify untracked temporary files before committing
- Keep the project root directory clean of temporary development artifacts

### Important: Migration Scripts Are NOT Temporary
The following migration-related files are **permanent project files** and should **NEVER** be deleted:
- `alembic_setup_summary.py` - Alembic configuration and setup utilities
- `generate_initial_migration.py` - Initial migration generation script
- `manage_migrations.py` - Migration management utilities
- [ADD_PROJECT_SPECIFIC_PERMANENT_FILES]

These files are part of the core database migration system and are required for proper database schema management.

### File Management Best Practices
- Temporary scripts should be created in a `/tmp/` directory or similar when possible
- If temporary files must be in the project directory, use descriptive names with dates
- Document any temporary files that need to persist in comments or README updates
- Remove any test data files, temporary exports, or debug outputs after use

### Examples of Files to Clean Up
```bash
# Common temporary files to remove after development:
rm test_*.py debug_*.py verify_*.py simulate_*.py
rm assign_*.py ensure_*.py
rm *.temp *.tmp test_*.sh.temp

# DO NOT DELETE these migration files:
# alembic_setup_summary.py
# generate_initial_migration.py  
# manage_migrations.py
# [ADD_PROJECT_SPECIFIC_PERMANENT_FILES]
```

### Version Control Hygiene
- Review `git status` before committing to ensure no temporary files are included
- Use `.gitignore` patterns for common temporary file types
- Clean up any experimental branches or temporary commits
- Maintain a clean commit history without debugging artifacts

## Project-Specific Customizations

### [PROJECT_SPECIFIC_SECTION_1]
[Add project-specific guidelines, patterns, or requirements here]

### [PROJECT_SPECIFIC_SECTION_2]
[Add additional project-specific sections as needed]

### Environment Variables
Required environment variables for this project:
- `DATABASE_URL`: Database connection string (supports MySQL, PostgreSQL, SQLite, etc.)
- `REDIS_URL`: Redis connection string for caching
- `SECRET_KEY`: Flask secret key for sessions
- `ENCRYPTION_KEY`: Key for encrypting sensitive data
- `SUPER_ADMIN_USERNAME`: Username that always has admin privileges
- `SMTP_SERVER`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Email configuration
- `STRIPE_SECRET_KEY`, `PAYPAL_CLIENT_ID`: Payment gateways

### External Dependencies
Key external services or APIs this project integrates with:
- **Stripe**: Credit card payment processing
- **PayPal**: PayPal payment processing
- **SMTP Server**: Email notifications and messaging
- **Database**: SQLAlchemy ORM supporting multiple database backends
- **MySQL**: Default database for development environment
- **Redis**: Session management and caching
