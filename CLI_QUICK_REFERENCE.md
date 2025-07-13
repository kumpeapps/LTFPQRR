# LTFPQRR CLI Quick Reference

## Quick Commands

```bash
# List all users
./cli.sh list-users

# Create new user
./cli.sh create-user --email user@example.com --first-name John --last-name Doe --role user

# Get user details
./cli.sh user-info --email user@example.com

# Update password
./cli.sh update-password --email user@example.com

# Assign role
./cli.sh assign-role --email user@example.com --role admin

# Remove role
./cli.sh remove-role --email user@example.com --role admin

# List all roles
./cli.sh list-roles

# Create new role
./cli.sh create-role --name moderator --description "Content moderation"

# Delete user (with confirmation)
./cli.sh delete-user --email user@example.com
```

## Available Roles

- `user` - Basic user role
- `admin` - Administrator role  
- `super-admin` - Super administrator role
- `moderator` - Content moderation role (if created)

## Account Types

- `customer` - Regular customer account (default)
- `partner` - Partner/business account

## Files

- `manage_users.py` - Main CLI script
- `cli.sh` - Docker wrapper script
- `CLI_DOCUMENTATION.md` - Complete documentation

## Prerequisites

- LTFPQRR application running in Docker containers
- Execute from project root directory

## Getting Help

```bash
./cli.sh --help
./cli.sh [command] --help
```
