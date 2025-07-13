"""
Comprehensive Template Testing Suite

This test suite systematically tests every template page in the LTFPQRR application,
including both public and protected routes. It automatically creates test users with
appropriate roles and validates that all templates load without errors.
"""

import requests
import subprocess
import time
from urllib.parse import urljoin


class TemplateTestSuite:
    """Comprehensive template testing suite for LTFPQRR application."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_credentials = {"username": "admin", "password": "password"}
        self.test_user_credentials = {"username": "testuser", "password": "testpassword123"}
        
    def setup_test_users(self):
        """Create test users with appropriate roles using CLI."""
        print("Setting up test users...")
        
        # Create admin user with all roles
        admin_script = """
from app import create_app
from extensions import db
from models.models import User, Role
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Create admin user if it doesn't exist
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@test.com',
            password_hash=generate_password_hash('password'),
            first_name='Admin',
            last_name='User',
            is_active=True
        )
        db.session.add(admin_user)
        
        # Assign all available roles
        all_roles = Role.query.all()
        for role in all_roles:
            if role not in admin_user.roles:
                admin_user.roles.append(role)
        
        db.session.commit()
        print(f'Admin user created with roles: {[r.name for r in admin_user.roles]}')
    else:
        # Ensure admin has all roles
        all_roles = Role.query.all()
        roles_added = []
        for role in all_roles:
            if role not in admin_user.roles:
                admin_user.roles.append(role)
                roles_added.append(role.name)
        
        if roles_added:
            db.session.commit()
            print(f'Added roles to admin: {roles_added}')
        
        print(f'Admin user exists with roles: {[r.name for r in admin_user.roles]}')
    
    # Create regular test user
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(
            username='testuser',
            email='testuser@test.com',
            password_hash=generate_password_hash('testpassword123'),
            first_name='Test',
            last_name='User',
            is_active=True
        )
        # Assign basic user role
        user_role = Role.query.filter_by(name='user').first()
        if user_role:
            test_user.roles.append(user_role)
        
        db.session.add(test_user)
        db.session.commit()
        print('Test user created')
    else:
        print('Test user already exists')
"""
        
        try:
            # Execute user creation script in container
            result = subprocess.run([
                "docker", "exec", "ltfpqrr-web-1", "python", "-c", admin_script
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Test users setup completed")
                print(result.stdout)
            else:
                print("❌ Error setting up test users:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Timeout setting up test users")
            return False
        except Exception as e:
            print(f"❌ Exception setting up test users: {e}")
            return False
            
        return True
    
    def login_user(self, credentials):
        """Login with given credentials and return success status."""
        try:
            # Get login page to extract CSRF token
            login_page = self.session.get(urljoin(self.base_url, "/auth/login"))
            if login_page.status_code != 200:
                print(f"❌ Could not access login page: {login_page.status_code}")
                return False
            
            # Extract CSRF token from the form
            csrf_token = None
            for line in login_page.text.split('\n'):
                if 'csrf_token' in line and 'value=' in line:
                    start = line.find('value="') + 7
                    end = line.find('"', start)
                    csrf_token = line[start:end]
                    break
            
            if not csrf_token:
                print("❌ Could not extract CSRF token")
                return False
            
            # Perform login
            login_data = {
                'username': credentials['username'],
                'password': credentials['password'],
                'csrf_token': csrf_token
            }
            
            response = self.session.post(
                urljoin(self.base_url, "/auth/login"),
                data=login_data,
                allow_redirects=False
            )
            
            # Check if login was successful (redirect to dashboard)
            if response.status_code == 302:
                print(f"✅ Login successful for {credentials['username']}")
                return True
            else:
                print(f"❌ Login failed for {credentials['username']}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error for {credentials['username']}: {e}")
            return False
    
    def logout_user(self):
        """Logout current user."""
        try:
            response = self.session.get(urljoin(self.base_url, "/auth/logout"))
            print("🔓 User logged out")
            return True
        except Exception as e:
            print(f"❌ Logout error: {e}")
            return False
    
    def test_route(self, route, description, requires_auth=False, requires_admin=False):
        """Test a single route and return result."""
        try:
            url = urljoin(self.base_url, route)
            response = self.session.get(url, allow_redirects=True)
            
            result = {
                'route': route,
                'description': description,
                'status_code': response.status_code,
                'success': False,
                'error': None,
                'final_url': response.url,
                'requires_auth': requires_auth,
                'requires_admin': requires_admin
            }
            
            # Determine success based on status code and requirements
            if response.status_code == 200:
                result['success'] = True
            elif response.status_code == 302:
                # Redirects are acceptable for certain scenarios
                if requires_auth and 'login' in response.url:
                    result['success'] = True
                    result['error'] = 'Correctly redirected to login (authentication required)'
                elif not requires_auth:
                    result['success'] = True
                    result['error'] = 'Redirect occurred (may be normal behavior)'
                else:
                    result['error'] = f'Unexpected redirect to {response.url}'
            elif response.status_code == 403:
                result['error'] = 'Forbidden - insufficient permissions'
            elif response.status_code == 404:
                result['error'] = 'Route not found'
            elif response.status_code == 500:
                result['error'] = 'Server error - check container logs'
            else:
                result['error'] = f'Unexpected status code: {response.status_code}'
            
            return result
            
        except Exception as e:
            return {
                'route': route,
                'description': description,
                'status_code': None,
                'success': False,
                'error': f'Exception: {str(e)}',
                'final_url': None,
                'requires_auth': requires_auth,
                'requires_admin': requires_admin
            }
    
    def get_test_routes(self):
        """Define all routes to test with their requirements."""
        return [
            # Public routes (no authentication required)
            ('/', 'Homepage', False, False),
            ('/contact', 'Contact page', False, False),
            ('/privacy', 'Privacy policy', False, False),
            ('/auth/login', 'Login page', False, False),
            ('/auth/register', 'Registration page', False, False),
            
            # Authentication routes (user must be logged out)
            ('/auth/logout', 'Logout', False, False),
            
            # Protected user routes (authentication required)
            ('/dashboard/', 'Main dashboard', True, False),
            ('/dashboard/customer', 'Customer dashboard', True, False),
            ('/profile/', 'User profile', True, False),
            ('/profile/edit', 'Edit profile', True, False),
            ('/profile/change-password', 'Change password', True, False),
            
            # Pet management routes
            ('/pet/create', 'Create pet', True, False),
            
            # Tag management routes
            ('/tag/claim', 'Claim tag', True, False),
            
            # Partner routes (may require partner role)
            ('/partner/management', 'Partner management', True, False),
            ('/partner/dashboard', 'Partner dashboard', True, False),
            
            # Payment routes
            ('/payment/tag', 'Tag payment', True, False),
            ('/payment/success', 'Payment success', True, False),
            
            # Settings routes
            ('/settings/notifications', 'Notification settings', True, False),
            
            # Admin routes (require admin role)
            ('/admin/dashboard', 'Admin dashboard', True, True),
            ('/admin/users', 'User management', True, True),
            ('/admin/tags', 'Tag management', True, True),
            ('/admin/subscriptions', 'Subscription management', True, True),
            ('/admin/partner-subscriptions', 'Partner subscriptions', True, True),
            ('/admin/pricing', 'Pricing management', True, True),
            ('/admin/payment-gateways', 'Payment gateway settings', True, True),
            ('/admin/settings', 'System settings', True, True),
            
            # Tag creation routes
            ('/admin/tags/create', 'Create tag (admin)', True, True),
            ('/admin/pricing/create', 'Create pricing plan', True, True),
        ]
    
    def run_comprehensive_test(self):
        """Run comprehensive template testing."""
        print("🚀 Starting Comprehensive Template Test Suite")
        print("=" * 60)
        
        # Setup test users
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return False
        
        # Wait a moment for user creation to complete
        time.sleep(2)
        
        routes = self.get_test_routes()
        results = {
            'public': [],
            'user_protected': [],
            'admin_protected': [],
            'errors': []
        }
        
        print("\n📝 Testing Public Routes (No Authentication)")
        print("-" * 40)
        
        # Test public routes first
        for route, description, requires_auth, requires_admin in routes:
            if not requires_auth:
                result = self.test_route(route, description, requires_auth, requires_admin)
                results['public'].append(result)
                
                status_icon = "✅" if result['success'] else "❌"
                print(f"{status_icon} {route:30} {result['status_code']} - {description}")
                if result['error']:
                    print(f"   └─ {result['error']}")
        
        print("\n🔐 Testing User Protected Routes")
        print("-" * 40)
        
        # Login as regular user
        if not self.login_user(self.test_user_credentials):
            print("❌ Could not login as test user. Skipping user protected routes.")
        else:
            for route, description, requires_auth, requires_admin in routes:
                if requires_auth and not requires_admin:
                    result = self.test_route(route, description, requires_auth, requires_admin)
                    results['user_protected'].append(result)
                    
                    status_icon = "✅" if result['success'] else "❌"
                    print(f"{status_icon} {route:30} {result['status_code']} - {description}")
                    if result['error']:
                        print(f"   └─ {result['error']}")
            
            self.logout_user()
        
        print("\n👑 Testing Admin Protected Routes")
        print("-" * 40)
        
        # Login as admin user
        if not self.login_user(self.admin_credentials):
            print("❌ Could not login as admin user. Skipping admin protected routes.")
        else:
            for route, description, requires_auth, requires_admin in routes:
                if requires_admin:
                    result = self.test_route(route, description, requires_auth, requires_admin)
                    results['admin_protected'].append(result)
                    
                    status_icon = "✅" if result['success'] else "❌"
                    print(f"{status_icon} {route:30} {result['status_code']} - {description}")
                    if result['error']:
                        print(f"   └─ {result['error']}")
            
            self.logout_user()
        
        # Generate summary report
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results):
        """Generate a comprehensive summary report."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEMPLATE TEST SUMMARY")
        print("=" * 60)
        
        all_results = results['public'] + results['user_protected'] + results['admin_protected']
        total_tests = len(all_results)
        successful_tests = len([r for r in all_results if r['success']])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Routes Tested: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Detailed breakdown
        categories = [
            ('Public Routes', results['public']),
            ('User Protected Routes', results['user_protected']),
            ('Admin Protected Routes', results['admin_protected'])
        ]
        
        for category_name, category_results in categories:
            if category_results:
                category_success = len([r for r in category_results if r['success']])
                category_total = len(category_results)
                print(f"\n{category_name}:")
                print(f"  ✅ {category_success}/{category_total} successful")
                
                # List failures
                failures = [r for r in category_results if not r['success']]
                if failures:
                    print(f"  ❌ Failed routes:")
                    for failure in failures:
                        print(f"    • {failure['route']} - {failure['error']}")
        
        # Container log recommendations
        if failed_tests > 0:
            print(f"\n🔧 TROUBLESHOOTING RECOMMENDATIONS:")
            print(f"• Check container logs: docker logs ltfpqrr-web-1 --tail 50")
            print(f"• Look for template errors, missing routes, or blueprint issues")
            print(f"• Verify all blueprint registrations in app.py")
            print(f"• Check for missing url_for() references in templates")
        
        print("=" * 60)


def test_all_templates():
    """Main test function that can be called directly."""
    tester = TemplateTestSuite()
    results = tester.run_comprehensive_test()
    
    # Check that critical routes work
    all_results = results['public'] + results['user_protected'] + results['admin_protected']
    failed_routes = [r for r in all_results if not r['success']]
    
    if failed_routes:
        failure_summary = "\n".join([f"• {r['route']}: {r['error']}" for r in failed_routes])
        print(f"Template test failures detected:\n{failure_summary}")
        return False
    
    return True


if __name__ == "__main__":
    """Run the comprehensive template test suite."""
    print("🧪 Running Comprehensive Template Test Suite")
    print("Make sure the LTFPQRR application is running on http://localhost:8000")
    print("")
    
    # Check if application is running
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        print("✅ Application is running")
    except requests.exceptions.RequestException:
        print("❌ Application is not running on http://localhost:8000")
        print("Please start the application first with: ./dev.sh start-dev")
        exit(1)
    
    # Run the test suite
    tester = TemplateTestSuite()
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    all_results = results['public'] + results['user_protected'] + results['admin_protected']
    failed_tests = len([r for r in all_results if not r['success']])
    
    if failed_tests == 0:
        print("\n🎉 All template tests passed!")
        exit(0)
    else:
        print(f"\n💥 {failed_tests} template tests failed!")
        exit(1)
