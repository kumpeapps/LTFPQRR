#!/usr/bin/env python3
"""
LTFPQRR User Management CLI

A command-line interface for managing users, passwords, and roles in the LTFPQRR system.

Usage:
    python manage_users.py --help
    python manage_users.py list-users
    python manage_users.py create-user --email user@example.com --password secret --role user
    python manage_users.py update-password --email user@example.com --password newsecret
    python manage_users.py assign-role --email user@example.com --role admin
    python manage_users.py remove-role --email user@example.com --role admin
    python manage_users.py delete-user --email user@example.com
    python manage_users.py user-info --email user@example.com
    python manage_users.py list-roles
    python manage_users.py create-role --name moderator --description "Content moderation role"
"""

import argparse
import sys
import os
import getpass
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models.models import User, Role
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the LTFPQRR project directory.")
    sys.exit(1)


class UserManager:
    """Main class for user management operations."""
    
    def __init__(self):
        self.app = app
        
    def list_users(self, active_only=False):
        """List all users in the system."""
        with self.app.app_context():
            users = User.query.all()
            
            if not users:
                print("No users found.")
                return
            
            print(f"\n{'='*80}")
            print(f"{'EMAIL':<30} {'USERNAME':<20} {'NAME':<25} {'ROLES':<15}")
            print(f"{'='*80}")
            
            for user in users:
                roles = ', '.join([role.name for role in user.roles]) if user.roles else 'None'
                name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'N/A'
                username = user.username or 'N/A'
                
                print(f"{user.email:<30} {username:<20} {name:<25} {roles:<15}")
            
            print(f"{'='*80}")
            print(f"Total users: {len(users)}")
    
    def create_user(self, email, password=None, username=None, first_name=None, last_name=None, 
                   phone=None, address=None, role=None):
        """Create a new user."""
        with self.app.app_context():
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"Error: User with email '{email}' already exists.")
                return False
            
            # Generate username if not provided
            if not username:
                username = email.split('@')[0]
                # Check if username exists, append number if needed
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
            
            # Prompt for password if not provided
            if not password:
                password = getpass.getpass("Enter password: ")
                confirm_password = getpass.getpass("Confirm password: ")
                if password != confirm_password:
                    print("Error: Passwords do not match.")
                    return False
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first_name or 'User',
                last_name=last_name or 'Name',
                phone=phone,
                address=address,
                created_at=datetime.utcnow()
            )
            
            # Assign role if specified
            if role:
                role_obj = Role.query.filter_by(name=role).first()
                if role_obj:
                    user.roles.append(role_obj)
                else:
                    print(f"Warning: Role '{role}' not found. User created without role.")
            
            try:
                db.session.add(user)
                db.session.commit()
                print(f"✓ User '{email}' created successfully with username '{username}'.")
                
                if role:
                    print(f"✓ Role '{role}' assigned to user.")
                
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error creating user: {e}")
                return False
    
    def update_password(self, email, password=None):
        """Update a user's password."""
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"Error: User with email '{email}' not found.")
                return False
            
            # Prompt for password if not provided
            if not password:
                password = getpass.getpass("Enter new password: ")
                confirm_password = getpass.getpass("Confirm new password: ")
                if password != confirm_password:
                    print("Error: Passwords do not match.")
                    return False
            
            try:
                user.password_hash = generate_password_hash(password)
                db.session.commit()
                print(f"✓ Password updated for user '{email}'.")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error updating password: {e}")
                return False
    
    def assign_role(self, email, role_name):
        """Assign a role to a user."""
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"Error: User with email '{email}' not found.")
                return False
            
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                print(f"Error: Role '{role_name}' not found.")
                return False
            
            if role in user.roles:
                print(f"User '{email}' already has role '{role_name}'.")
                return True
            
            try:
                user.roles.append(role)
                db.session.commit()
                print(f"✓ Role '{role_name}' assigned to user '{email}'.")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error assigning role: {e}")
                return False
    
    def remove_role(self, email, role_name):
        """Remove a role from a user."""
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"Error: User with email '{email}' not found.")
                return False
            
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                print(f"Error: Role '{role_name}' not found.")
                return False
            
            if role not in user.roles:
                print(f"User '{email}' does not have role '{role_name}'.")
                return True
            
            try:
                user.roles.remove(role)
                db.session.commit()
                print(f"✓ Role '{role_name}' removed from user '{email}'.")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error removing role: {e}")
                return False
    
    def delete_user(self, email, confirm=False):
        """Delete a user (with confirmation)."""
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"Error: User with email '{email}' not found.")
                return False
            
            if not confirm:
                confirmation = input(f"Are you sure you want to delete user '{email}'? (yes/no): ")
                if confirmation.lower() not in ['yes', 'y']:
                    print("Delete operation cancelled.")
                    return False
            
            try:
                # Remove user roles first
                user.roles.clear()
                db.session.delete(user)
                db.session.commit()
                print(f"✓ User '{email}' deleted successfully.")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error deleting user: {e}")
                return False
    
    def list_roles(self):
        """List all available roles."""
        with self.app.app_context():
            roles = Role.query.all()
            
            if not roles:
                print("No roles found.")
                return
            
            print(f"\n{'='*60}")
            print(f"{'NAME':<20} {'DESCRIPTION':<40}")
            print(f"{'='*60}")
            
            for role in roles:
                description = role.description or 'No description'
                print(f"{role.name:<20} {description:<40}")
            
            print(f"{'='*60}")
            print(f"Total roles: {len(roles)}")
    
    def create_role(self, name, description=None):
        """Create a new role."""
        with self.app.app_context():
            # Check if role already exists
            existing_role = Role.query.filter_by(name=name).first()
            if existing_role:
                print(f"Error: Role '{name}' already exists.")
                return False
            
            try:
                role = Role(name=name, description=description)
                db.session.add(role)
                db.session.commit()
                print(f"✓ Role '{name}' created successfully.")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error creating role: {e}")
                return False
    
    def user_info(self, email):
        """Display detailed information about a user."""
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"Error: User with email '{email}' not found.")
                return False
            
            print(f"\n{'='*50}")
            print(f"USER INFORMATION")
            print(f"{'='*50}")
            print(f"Email:          {user.email}")
            print(f"Username:       {user.username}")
            print(f"Name:           {user.first_name or 'N/A'} {user.last_name or 'N/A'}")
            print(f"Phone:          {user.phone or 'N/A'}")
            print(f"Address:        {user.address or 'N/A'}")
            print(f"Created:        {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'}")
            print(f"Updated:        {user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else 'N/A'}")
            
            roles = [role.name for role in user.roles] if user.roles else ['None']
            print(f"Roles:          {', '.join(roles)}")
            
            # Count user's pets and tags
            pet_count = user.pets.count() if hasattr(user, 'pets') else 0
            owned_tag_count = user.owned_tags.count() if hasattr(user, 'owned_tags') else 0
            created_tag_count = user.created_tags.count() if hasattr(user, 'created_tags') else 0
            
            print(f"Pets:           {pet_count}")
            print(f"Owned Tags:     {owned_tag_count}")
            print(f"Created Tags:   {created_tag_count}")
            print(f"{'='*50}")
            
            return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LTFPQRR User Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list-users
  %(prog)s create-user --email admin@example.com --role admin
  %(prog)s update-password --email user@example.com
  %(prog)s assign-role --email user@example.com --role partner
  %(prog)s user-info --email user@example.com
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List users command
    list_parser = subparsers.add_parser('list-users', help='List all users')
    
    # Create user command
    create_parser = subparsers.add_parser('create-user', help='Create a new user')
    create_parser.add_argument('--email', required=True, help='User email address')
    create_parser.add_argument('--password', help='User password (will prompt if not provided)')
    create_parser.add_argument('--username', help='Username (will auto-generate if not provided)')
    create_parser.add_argument('--first-name', help='User first name')
    create_parser.add_argument('--last-name', help='User last name')
    create_parser.add_argument('--phone', help='User phone number')
    create_parser.add_argument('--address', help='User address')
    create_parser.add_argument('--account-type', choices=['customer', 'partner'], default='customer', help='Account type')
    create_parser.add_argument('--role', help='Initial role to assign')
    
    # Update password command
    password_parser = subparsers.add_parser('update-password', help='Update user password')
    password_parser.add_argument('--email', required=True, help='User email address')
    password_parser.add_argument('--password', help='New password (will prompt if not provided)')
    
    # Assign role command
    assign_parser = subparsers.add_parser('assign-role', help='Assign role to user')
    assign_parser.add_argument('--email', required=True, help='User email address')
    assign_parser.add_argument('--role', required=True, help='Role name to assign')
    
    # Remove role command
    remove_parser = subparsers.add_parser('remove-role', help='Remove role from user')
    remove_parser.add_argument('--email', required=True, help='User email address')
    remove_parser.add_argument('--role', required=True, help='Role name to remove')
    
    # Delete user command
    delete_parser = subparsers.add_parser('delete-user', help='Delete user account')
    delete_parser.add_argument('--email', required=True, help='User email address')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # User info command
    info_parser = subparsers.add_parser('user-info', help='Display user information')
    info_parser.add_argument('--email', required=True, help='User email address')
    
    # List roles command
    roles_parser = subparsers.add_parser('list-roles', help='List all roles')
    
    # Create role command
    create_role_parser = subparsers.add_parser('create-role', help='Create a new role')
    create_role_parser.add_argument('--name', required=True, help='Role name')
    create_role_parser.add_argument('--description', help='Role description')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = UserManager()
    
    try:
        if args.command == 'list-users':
            manager.list_users()
        
        elif args.command == 'create-user':
            manager.create_user(
                email=args.email,
                password=args.password,
                username=args.username,
                first_name=args.first_name,
                last_name=args.last_name,
                phone=args.phone,
                address=args.address,
                role=args.role
            )
        
        elif args.command == 'update-password':
            manager.update_password(args.email, args.password)
        
        elif args.command == 'assign-role':
            manager.assign_role(args.email, args.role)
        
        elif args.command == 'remove-role':
            manager.remove_role(args.email, args.role)
        
        elif args.command == 'delete-user':
            manager.delete_user(args.email, confirm=args.force)
        
        elif args.command == 'user-info':
            manager.user_info(args.email)
        
        elif args.command == 'list-roles':
            manager.list_roles()
        
        elif args.command == 'create-role':
            manager.create_role(args.name, args.description)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
