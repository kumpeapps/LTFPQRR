# LTFPQRR User Management CLI Documentation

## Overview

The LTFPQRR User Management CLI is a powerful command-line tool for managing users, passwords, and roles in the LTFPQRR system. It provides administrators with easy-to-use commands for all user management tasks.

## Installation & Setup

The CLI is included with the LTFPQRR project and requires no additional installation. Simply ensure the application is running in Docker containers.

## Usage

### Using the CLI

There are two ways to use the CLI:

1. **Direct execution** (from inside the container):
   ```bash
   python manage_users.py [command] [options]
   ```

2. **Wrapper script** (from host machine):
   ```bash
   ./cli.sh [command] [options]
   ```

The wrapper script automatically runs commands inside the Docker container and is the recommended approach.

## Available Commands

### 1. List Users

List all users in the system with their basic information.

```bash
./cli.sh list-users
```

**Output:**
- Email address
- Username
- Full name
- Assigned roles

### 2. Create User

Create a new user account with optional role assignment.

```bash
./cli.sh create-user --email user@example.com [options]
```

**Required Arguments:**
- `--email` - User's email address (must be unique)

**Optional Arguments:**
- `--password` - Password (will prompt securely if not provided)
- `--username` - Username (auto-generated from email if not provided)
- `--first-name` - User's first name
- `--last-name` - User's last name
- `--phone` - Phone number
- `--address` - Physical address
- `--account-type` - Account type: `customer` (default) or `partner`
- `--role` - Initial role to assign

**Examples:**
```bash
# Basic user creation (will prompt for password)
./cli.sh create-user --email john@example.com --first-name John --last-name Doe

# Create admin user with all details
./cli.sh create-user --email admin@company.com --password SecurePass123 \
  --first-name Admin --last-name User --role admin --account-type partner

# Create customer with minimal info
./cli.sh create-user --email customer@example.com --password pass123 --role user
```

### 3. Update Password

Change a user's password.

```bash
./cli.sh update-password --email user@example.com [--password newpass]
```

**Arguments:**
- `--email` - User's email address
- `--password` - New password (will prompt securely if not provided)

**Examples:**
```bash
# Update password with prompt
./cli.sh update-password --email user@example.com

# Update password directly
./cli.sh update-password --email user@example.com --password NewSecurePass123
```

### 4. Assign Role

Assign a role to an existing user.

```bash
./cli.sh assign-role --email user@example.com --role rolename
```

**Arguments:**
- `--email` - User's email address
- `--role` - Role name to assign

**Examples:**
```bash
./cli.sh assign-role --email user@example.com --role admin
./cli.sh assign-role --email partner@company.com --role moderator
```

### 5. Remove Role

Remove a role from a user.

```bash
./cli.sh remove-role --email user@example.com --role rolename
```

**Arguments:**
- `--email` - User's email address
- `--role` - Role name to remove

**Examples:**
```bash
./cli.sh remove-role --email user@example.com --role admin
./cli.sh remove-role --email temp@example.com --role moderator
```

### 6. User Information

Display detailed information about a specific user.

```bash
./cli.sh user-info --email user@example.com
```

**Output includes:**
- Email and username
- Full name and contact information
- Account type
- Creation and update timestamps
- Assigned roles
- Count of pets, owned tags, and created tags

### 7. Delete User

Delete a user account (with confirmation).

```bash
./cli.sh delete-user --email user@example.com [--force]
```

**Arguments:**
- `--email` - User's email address
- `--force` - Skip confirmation prompt

**Examples:**
```bash
# Delete with confirmation prompt
./cli.sh delete-user --email user@example.com

# Force delete without confirmation
./cli.sh delete-user --email user@example.com --force
```

### 8. List Roles

List all available roles in the system.

```bash
./cli.sh list-roles
```

**Output:**
- Role name
- Role description

### 9. Create Role

Create a new role.

```bash
./cli.sh create-role --name rolename [--description "Role description"]
```

**Arguments:**
- `--name` - Role name (must be unique)
- `--description` - Optional role description

**Examples:**
```bash
./cli.sh create-role --name moderator --description "Content moderation and user management"
./cli.sh create-role --name supervisor --description "Supervises customer service operations"
```

## Common Use Cases

### Initial Setup

Create the first admin user:
```bash
./cli.sh create-user --email admin@ltfpqrr.com --first-name System --last-name Admin \
  --role super-admin --account-type partner
```

### Daily Administration

1. **List all users:**
   ```bash
   ./cli.sh list-users
   ```

2. **Check user details:**
   ```bash
   ./cli.sh user-info --email user@example.com
   ```

3. **Reset user password:**
   ```bash
   ./cli.sh update-password --email user@example.com
   ```

4. **Promote user to admin:**
   ```bash
   ./cli.sh assign-role --email user@example.com --role admin
   ```

### Role Management

1. **Create custom roles:**
   ```bash
   ./cli.sh create-role --name support --description "Customer support team"
   ./cli.sh create-role --name manager --description "Department manager"
   ```

2. **Assign roles to users:**
   ```bash
   ./cli.sh assign-role --email support@company.com --role support
   ./cli.sh assign-role --email manager@company.com --role manager
   ```

### Bulk Operations

For bulk operations, you can create shell scripts:

```bash
#!/bin/bash
# bulk_create_users.sh

users=(
  "user1@example.com:User1:Name1:user"
  "user2@example.com:User2:Name2:user"
  "admin@example.com:Admin:User:admin"
)

for user_data in "${users[@]}"; do
  IFS=':' read -r email first last role <<< "$user_data"
  ./cli.sh create-user --email "$email" --first-name "$first" \
    --last-name "$last" --role "$role" --password "TempPass123"
done
```

## Security Considerations

1. **Password Security:**
   - Use the prompt option instead of command-line passwords for better security
   - Passwords passed via command line may be visible in process lists

2. **Role Assignments:**
   - Be careful when assigning admin or super-admin roles
   - Regularly audit user roles with `list-users` command

3. **User Deletion:**
   - User deletion is permanent and removes all associated data
   - Always use confirmation unless absolutely certain

## Troubleshooting

### Common Issues

1. **Container not running:**
   ```
   Error: LTFPQRR web container is not running.
   ```
   **Solution:** Start the application with `./dev.sh start-dev`

2. **User already exists:**
   ```
   Error: User with email 'user@example.com' already exists.
   ```
   **Solution:** Choose a different email or update the existing user

3. **Role not found:**
   ```
   Error: Role 'invalid-role' not found.
   ```
   **Solution:** Check available roles with `./cli.sh list-roles`

### Getting Help

- Use `--help` with any command for detailed usage information
- Check the container logs if experiencing database issues
- Ensure the Docker containers are running and healthy

## Examples

### Complete User Setup Workflow

```bash
# 1. Check current users
./cli.sh list-users

# 2. Create new user
./cli.sh create-user --email newuser@example.com --first-name John --last-name Doe

# 3. Check user info
./cli.sh user-info --email newuser@example.com

# 4. Assign additional role
./cli.sh assign-role --email newuser@example.com --role admin

# 5. Update password
./cli.sh update-password --email newuser@example.com

# 6. Verify changes
./cli.sh user-info --email newuser@example.com
```

### Role Management Workflow

```bash
# 1. List existing roles
./cli.sh list-roles

# 2. Create new roles
./cli.sh create-role --name editor --description "Content editor role"
./cli.sh create-role --name viewer --description "Read-only access"

# 3. Assign roles to users
./cli.sh assign-role --email editor@company.com --role editor
./cli.sh assign-role --email viewer@company.com --role viewer

# 4. Verify role assignments
./cli.sh list-users
```

This CLI provides comprehensive user management capabilities for the LTFPQRR system, making it easy to manage users, passwords, and roles efficiently from the command line.
