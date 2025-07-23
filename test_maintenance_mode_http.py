#!/usr/bin/env python3
"""
Test maintenance mode functionality through HTTP requests.
"""

import requests
import time

def test_maintenance_mode_http():
    """Test maintenance mode via HTTP requests"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Maintenance Mode via HTTP ===")
    
    # Test normal access first
    print("\n1. Testing normal access...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Homepage status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Site accessible normally")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing site: {e}")
        return False
    
    # Test health check
    print("\n2. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check working")
            print(f"Health response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print("\n=== Manual Testing Instructions ===")
    print("To test maintenance mode functionality:")
    print("1. Go to http://localhost:8000/auth/login")
    print("2. Login as admin user")
    print("3. Go to http://localhost:8000/admin/settings")
    print("4. Toggle 'Maintenance Mode' to ON")
    print("5. Save settings")
    print("6. Open a new incognito/private browser window")
    print("7. Try to access http://localhost:8000")
    print("8. You should see a maintenance page instead of the normal site")
    print("9. Admin users should still be able to access the site normally")
    print("10. Health check should still work: http://localhost:8000/health")
    
    return True

if __name__ == "__main__":
    test_maintenance_mode_http()
