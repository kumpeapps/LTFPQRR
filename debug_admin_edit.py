#!/usr/bin/env python3
"""
Detailed debugging of admin edit user functionality
"""
from app import create_app
from extensions import db
from models.models import User, Role
from flask import url_for

def debug_admin_edit():
    """Debug admin edit user functionality step by step"""
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            # Get testuser
            test_user = User.query.filter_by(username='testuser').first()
            print(f"=== User Info ===")
            print(f"User: {test_user.username}")
            print(f"Is authenticated: {test_user.is_active}")
            print(f"Current roles: {[r.name for r in test_user.roles]}")
            print(f"Has admin role: {test_user.has_role('admin')}")
            print(f"Has super-admin role: {test_user.has_role('super-admin')}")
            
            # Test login
            with client.session_transaction() as sess:
                print(f"Session before login: {dict(sess)}")
            
            login_response = client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'password123'
            }, follow_redirects=True)
            
            print(f"Login response status: {login_response.status_code}")
            print(f"Login final URL: {login_response.request.url}")
            
            with client.session_transaction() as sess:
                print(f"Session after login: {dict(sess)}")
            
            # Test dashboard access first
            dashboard_response = client.get('/dashboard/')
            print(f"Dashboard access status: {dashboard_response.status_code}")
            
            # Test admin dashboard access
            admin_dashboard_response = client.get('/admin/dashboard')
            print(f"Admin dashboard access status: {admin_dashboard_response.status_code}")
            
            # Test users list access
            users_response = client.get('/admin/users')
            print(f"Admin users list access status: {users_response.status_code}")
            
            # Now test edit page access
            edit_response = client.get('/admin/users/edit/1')
            print(f"Edit user page access status: {edit_response.status_code}")
            
            if edit_response.status_code == 200:
                print("✅ Successfully accessed edit page")
                content = edit_response.get_data(as_text=True)
                
                # Check for role checkboxes
                print(f"Partner checkbox present: {'name=\"roles\" value=\"4\"' in content}")
                print(f"Partner role text present: {'partner' in content.lower()}")
                
                # Submit form
                form_data = {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'email': 'testuser@example.com',
                    'phone': '',
                    'address': '',
                    'roles': ['1', '2', '3', '4']  # All roles
                }
                
                submit_response = client.post('/admin/users/edit/1', data=form_data, follow_redirects=True)
                print(f"Form submission status: {submit_response.status_code}")
                
                # Check updated roles
                db.session.refresh(test_user)
                print(f"Updated roles: {[r.name for r in test_user.roles]}")
                
                return any(role.name == 'partner' for role in test_user.roles)
            else:
                print(f"❌ Cannot access edit page: {edit_response.status_code}")
                if edit_response.status_code == 302:
                    print(f"Redirect location: {edit_response.headers.get('Location', 'None')}")
                return False

if __name__ == "__main__":
    success = debug_admin_edit()
    print(f"Final result: {'SUCCESS' if success else 'FAILED'}")
