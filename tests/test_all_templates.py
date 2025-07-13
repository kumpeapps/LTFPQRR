#!/usr/bin/env python3
"""
Comprehensive Template Testing Suite for LTFPQRR

This test suite systematically tests every single template page in the application,
including proper authentication, user creation, and error handling.

Usage:
    python tests/test_all_templates.py
    
Requirements:
    - Application must be running on localhost:8000
    - Will automatically create admin user if needed
    - Tests both authenticated and unauthenticated access
"""

import requests
import sys
import os
import json
from urllib.parse import urljoin

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TemplateTestSuite:
    """Comprehensive test suite for all LTFPQRR templates."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LTFPQRR-Template-Test-Suite/1.0'
        })
        
        # Test results storage
        self.results = {
            'public_routes': {},
            'authenticated_routes': {},
            'admin_routes': {},
            'partner_routes': {},
            'errors': [],
            'summary': {}
        }
        
        # Define all routes to test
        self.public_routes = [
            ('/', 'Homepage'),
            ('/contact', 'Contact Page'),
            ('/privacy', 'Privacy Policy'),
            ('/found', 'Found Pet Page'),
            ('/found/test001', 'Found Pet with Tag ID (lowercase)'),
            ('/found/TEST001', 'Found Pet with Tag ID (uppercase)'),
            ('/auth/login', 'Login Page'),
            ('/auth/register', 'Registration Page'),
        ]
        
        self.authenticated_routes = [
            ('/dashboard/', 'User Dashboard'),
            ('/dashboard/customer', 'Customer Dashboard'),
            ('/profile/', 'User Profile'),
            ('/profile/edit', 'Edit Profile'),
            ('/profile/change-password', 'Change Password'),
            ('/pet/create', 'Create Pet'),
            ('/tag/claim', 'Claim Tag'),
            ('/settings/notifications', 'Notification Settings'),
            ('/payment/tag', 'Tag Payment'),
            ('/payment/success', 'Payment Success'),
        ]
        
        self.admin_routes = [
            ('/admin/dashboard', 'Admin Dashboard'),
            ('/admin/users', 'User Management'),
            ('/admin/partners', 'Partner Management'),
            ('/admin/tags', 'Tag Management'),
            ('/admin/subscriptions', 'Subscription Management'),
            ('/admin/partner-subscriptions', 'Partner Subscriptions'),
            ('/admin/pricing', 'Pricing Management'),
            ('/admin/pricing/create', 'Create Pricing Plan'),
            ('/admin/payment-gateways', 'Payment Gateway Settings'),
            ('/admin/settings', 'System Settings'),
        ]
        
        self.partner_routes = [
            ('/partner/management', 'Partner Management'),
            ('/partner/dashboard', 'Partner Dashboard'),
            ('/partner/create', 'Create Partner'),
        ]
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp."""
        print(f"[{level}] {message}")
    
    def create_admin_user_if_needed(self):
        """Create admin user using CLI if it doesn't exist."""
        self.log("Checking if admin user exists...")
        
        try:
            # First try to login with existing admin user
            login_response = self.session.get(urljoin(self.base_url, '/auth/login'))
            if login_response.status_code != 200:
                self.log("Cannot access login page", "ERROR")
                return False
            
            # Extract CSRF token
            csrf_token = self.extract_csrf_token(login_response.text)
            if not csrf_token:
                self.log("Could not extract CSRF token", "ERROR")
                return False
            
            # Attempt login
            login_data = {
                'username': 'admin',
                'password': 'password',
                'csrf_token': csrf_token
            }
            
            login_result = self.session.post(
                urljoin(self.base_url, '/auth/login'),
                data=login_data,
                allow_redirects=False
            )
            
            if login_result.status_code == 302:
                self.log("Admin user login successful")
                return True
            else:
                self.log("Admin user does not exist or login failed, creating...")
                return self.create_admin_user_via_cli()
                
        except Exception as e:
            self.log(f"Error checking admin user: {e}", "ERROR")
            return self.create_admin_user_via_cli()
    
    def create_admin_user_via_cli(self):
        """Create admin user using the CLI script."""
        self.log("Creating admin user via CLI...")
        
        import subprocess
        
        try:
            # Use CLI to create admin user
            cmd = [
                './cli.sh', 'create-user', 
                '--username', 'admin',
                '--email', 'admin@test.com',
                '--password', 'password',
                '--first-name', 'Admin',
                '--last-name', 'User',
                '--roles', 'user,admin,super-admin'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                self.log("Admin user created successfully via CLI")
                return True
            else:
                self.log(f"CLI user creation failed: {result.stderr}", "ERROR")
                return self.create_admin_user_via_docker()
                
        except Exception as e:
            self.log(f"CLI creation failed: {e}", "ERROR")
            return self.create_admin_user_via_docker()
    
    def create_admin_user_via_docker(self):
        """Create admin user directly via Docker container."""
        self.log("Creating admin user via Docker...")
        
        import subprocess
        
        docker_script = '''
from app import create_app
from extensions import db
from models.models import User, Role
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Check if admin user exists
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print('Admin user already exists')
    else:
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@test.com',
            password_hash=generate_password_hash('password'),
            first_name='Admin',
            last_name='User',
            is_active=True
        )
        
        # Assign all roles
        roles_to_assign = ['user', 'admin', 'super-admin']
        for role_name in roles_to_assign:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                admin_user.roles.append(role)
        
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created successfully')
'''
        
        try:
            cmd = ['docker', 'exec', 'ltfpqrr-web-1', 'python', '-c', docker_script]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("Admin user created successfully via Docker")
                return True
            else:
                self.log(f"Docker user creation failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Docker creation failed: {e}", "ERROR")
            return False
    
    def extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML content."""
        import re
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', html_content)
        return csrf_match.group(1) if csrf_match else None
    
    def login_as_admin(self):
        """Login as admin user."""
        self.log("Logging in as admin user...")
        
        try:
            # Get login page
            login_page = self.session.get(urljoin(self.base_url, '/auth/login'))
            if login_page.status_code != 200:
                self.log("Cannot access login page", "ERROR")
                return False
            
            # Extract CSRF token
            csrf_token = self.extract_csrf_token(login_page.text)
            if not csrf_token:
                self.log("Could not extract CSRF token from login page", "ERROR")
                return False
            
            # Login
            login_data = {
                'username': 'admin',
                'password': 'password',
                'csrf_token': csrf_token
            }
            
            login_result = self.session.post(
                urljoin(self.base_url, '/auth/login'),
                data=login_data,
                allow_redirects=True
            )
            
            if login_result.status_code == 200 and 'dashboard' in login_result.url.lower():
                self.log("Successfully logged in as admin")
                return True
            else:
                self.log(f"Login failed - Status: {login_result.status_code}, URL: {login_result.url}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Login error: {e}", "ERROR")
            return False
    
    def create_partner_user_if_needed(self):
        """Create partner user using Docker if it doesn't exist."""
        self.log("Creating partner user if needed...")
        
        docker_script = '''
from app import create_app
from extensions import db
from models.models import User, Role
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Check if partner user exists
    partner_user = User.query.filter_by(username='partner').first()
    if partner_user:
        print('Partner user already exists')
    else:
        # Create partner user
        partner_user = User(
            username='partner',
            email='partner@test.com',
            password_hash=generate_password_hash('password'),
            first_name='Partner',
            last_name='User'
        )
        
        # Assign user and partner roles
        user_role = Role.query.filter_by(name='user').first()
        partner_role = Role.query.filter_by(name='partner').first()
        
        if user_role:
            partner_user.roles.append(user_role)
        if partner_role:
            partner_user.roles.append(partner_role)
        
        db.session.add(partner_user)
        db.session.commit()
        print('Partner user created successfully')
'''
        
        try:
            import subprocess
            cmd = ['docker', 'exec', 'ltfpqrr-web-1', 'python', '-c', docker_script]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("Partner user created/verified successfully")
                return True
            else:
                self.log(f"Partner user creation failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Partner user creation failed: {e}", "ERROR")
            return False

    def login_as_partner(self):
        """Login as partner user."""
        self.log("Logging in as partner user...")
        
        try:
            # Clear session first
            self.session.cookies.clear()
            
            # Get login page
            login_page = self.session.get(urljoin(self.base_url, '/auth/login'))
            if login_page.status_code != 200:
                self.log("Cannot access login page", "ERROR")
                return False
            
            # Extract CSRF token
            csrf_token = self.extract_csrf_token(login_page.text)
            if not csrf_token:
                self.log("Could not extract CSRF token from login page", "ERROR")
                return False
            
            # Login
            login_data = {
                'username': 'partner',
                'password': 'password',
                'csrf_token': csrf_token
            }
            
            login_result = self.session.post(
                urljoin(self.base_url, '/auth/login'),
                data=login_data,
                allow_redirects=True
            )
            
            if login_result.status_code == 200 and 'dashboard' in login_result.url.lower():
                self.log("Successfully logged in as partner")
                return True
            else:
                self.log(f"Partner login failed - Status: {login_result.status_code}, URL: {login_result.url}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Partner login error: {e}", "ERROR")
            return False
    
    def test_route(self, route, description, expected_codes=[200]):
        """Test a single route and return results."""
        try:
            response = self.session.get(urljoin(self.base_url, route), timeout=10)
            
            result = {
                'status_code': response.status_code,
                'success': response.status_code in expected_codes,
                'final_url': response.url,
                'description': description,
                'error': None
            }
            
            # Check for template errors in the response
            if response.status_code == 200:
                content = response.text.lower()
                if 'error' in content and 'template' in content:
                    result['error'] = 'Potential template error detected'
                elif 'builderror' in content:
                    result['error'] = 'URL building error detected'
                elif 'internal server error' in content:
                    result['error'] = 'Internal server error'
            
            return result
            
        except Exception as e:
            return {
                'status_code': 0,
                'success': False,
                'final_url': route,
                'description': description,
                'error': str(e)
            }
    
    def test_public_routes(self):
        """Test all public routes (no authentication required)."""
        self.log("Testing public routes...")
        
        for route, description in self.public_routes:
            result = self.test_route(route, description)
            self.results['public_routes'][route] = result
            
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.log(f"  {route} ({description}): {status} [{result['status_code']}]")
            
            if result['error']:
                self.log(f"    Error: {result['error']}", "WARNING")
    
    def test_authenticated_routes(self):
        """Test routes that require authentication."""
        self.log("Testing authenticated routes...")
        
        for route, description in self.authenticated_routes:
            # Test both with and without redirects
            result = self.test_route(route, description, expected_codes=[200, 302])
            self.results['authenticated_routes'][route] = result
            
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            redirect_info = ""
            if result['status_code'] == 302:
                redirect_info = " (redirect)"
            
            self.log(f"  {route} ({description}): {status} [{result['status_code']}]{redirect_info}")
            
            if result['error']:
                self.log(f"    Error: {result['error']}", "WARNING")
    
    def test_admin_routes(self):
        """Test admin routes (require admin authentication)."""
        self.log("Testing admin routes...")
        
        for route, description in self.admin_routes:
            result = self.test_route(route, description, expected_codes=[200, 302])
            self.results['admin_routes'][route] = result
            
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            redirect_info = ""
            if result['status_code'] == 302:
                redirect_info = " (redirect)"
            
            self.log(f"  {route} ({description}): {status} [{result['status_code']}]{redirect_info}")
            
            if result['error']:
                self.log(f"    Error: {result['error']}", "WARNING")
    
    def test_partner_routes(self):
        """Test partner routes (require partner role)."""
        self.log("Testing partner routes...")
        
        for route, description in self.partner_routes:
            result = self.test_route(route, description, expected_codes=[200, 302])
            self.results['partner_routes'][route] = result  # Store in partner_routes section
            
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            redirect_info = ""
            if result['status_code'] == 302:
                redirect_info = " (redirect)"
            
            self.log(f"  {route} ({description}): {status} [{result['status_code']}]{redirect_info}")
            
            if result['error']:
                self.log(f"    Error: {result['error']}", "WARNING")
    
    def generate_summary(self):
        """Generate test summary statistics."""
        all_results = {}
        all_results.update(self.results['public_routes'])
        all_results.update(self.results['authenticated_routes'])
        all_results.update(self.results['admin_routes'])
        all_results.update(self.results['partner_routes'])
        
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results.values() if r['success'])
        failed_tests = total_tests - passed_tests
        
        errors = [r for r in all_results.values() if r['error']]
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'errors': len(errors)
        }
        
        return self.results['summary']
    
    def print_summary_report(self):
        """Print a comprehensive summary report."""
        summary = self.generate_summary()
        
        print("\n" + "="*80)
        print("LTFPQRR TEMPLATE TEST SUITE - COMPREHENSIVE REPORT")
        print("="*80)
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Errors: {summary['errors']}")
        
        # Detailed breakdown
        for category, routes in [
            ("Public Routes", self.results['public_routes']),
            ("Authenticated Routes", self.results['authenticated_routes']),
            ("Admin Routes", self.results['admin_routes']),
            ("Partner Routes", self.results['partner_routes'])
        ]:
            if routes:
                passed = sum(1 for r in routes.values() if r['success'])
                total = len(routes)
                print(f"\n📋 {category.upper()}: {passed}/{total} passed")
                
                for route, result in routes.items():
                    status = "✅" if result['success'] else "❌"
                    error_info = f" - {result['error']}" if result['error'] else ""
                    print(f"   {status} {route} [{result['status_code']}]{error_info}")
        
        # Errors section
        if summary['errors'] > 0:
            print(f"\n🚨 ERRORS DETECTED:")
            all_results = {}
            all_results.update(self.results['public_routes'])
            all_results.update(self.results['authenticated_routes'])
            all_results.update(self.results['admin_routes'])
            all_results.update(self.results['partner_routes'])
            
            for route, result in all_results.items():
                if result['error']:
                    print(f"   ❌ {route}: {result['error']}")
        
        print("\n" + "="*80)
        
        return summary['success_rate'] > 80  # Return True if success rate > 80%
    
    def save_results_to_file(self, filename='template_test_results.json'):
        """Save detailed test results to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            self.log(f"Detailed results saved to {filename}")
        except Exception as e:
            self.log(f"Failed to save results: {e}", "ERROR")
    
    def run_comprehensive_test(self):
        """Run the complete test suite."""
        print("🚀 Starting LTFPQRR Comprehensive Template Test Suite")
        print("="*60)
        
        # Step 1: Ensure admin user exists
        if not self.create_admin_user_if_needed():
            self.log("Failed to create/verify admin user", "ERROR")
            return False
        
        # Step 1.5: Ensure partner user exists
        if not self.create_partner_user_if_needed():
            self.log("Failed to create/verify partner user", "ERROR")
            return False
        
        # Step 2: Test public routes first (no auth needed)
        self.test_public_routes()
        
        # Step 3: Login as admin for authenticated and admin tests
        if not self.login_as_admin():
            self.log("Failed to login as admin, skipping admin tests", "ERROR")
        else:
            # Step 4: Test authenticated routes
            self.test_authenticated_routes()
            
            # Step 5: Test admin routes
            self.test_admin_routes()
        
        # Step 6: Login as partner for partner tests
        if not self.login_as_partner():
            self.log("Failed to login as partner, skipping partner tests", "ERROR")
        else:
            # Step 7: Test partner routes
            self.test_partner_routes()
        
        # Step 8: Generate and display results
        success = self.print_summary_report()
        
        # Step 9: Save detailed results
        self.save_results_to_file()
        
        return success

def main():
    """Main function to run the test suite."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LTFPQRR Comprehensive Template Test Suite')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL for testing')
    parser.add_argument('--save-results', default='template_test_results.json', help='File to save results')
    
    args = parser.parse_args()
    
    # Create and run test suite
    test_suite = TemplateTestSuite(base_url=args.url)
    success = test_suite.run_comprehensive_test()
    
    # Save results if specified
    if args.save_results:
        test_suite.save_results_to_file(args.save_results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
