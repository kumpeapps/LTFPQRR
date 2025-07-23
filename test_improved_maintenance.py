#!/usr/bin/env python3
"""
Test the improved maintenance mode functionality.
"""

import requests
import time

def test_improved_maintenance_mode():
    """Test the improved maintenance mode functionality"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Improved Maintenance Mode ===")
    
    # Test 1: Regular homepage (should show maintenance page)
    print("\n1. Testing regular homepage access...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Homepage status: {response.status_code}")
        if response.status_code == 503:
            print("✅ Site correctly shows maintenance page (503)")
            # Check if it contains theme elements
            content = response.text
            if 'maintenance-gradient' in content and 'LTFPQRR' in content:
                print("✅ Maintenance page uses themed design")
            else:
                print("❌ Maintenance page missing theme elements")
        else:
            print(f"❌ Expected 503, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Admin login (should be accessible)
    print("\n2. Testing admin login access...")
    try:
        response = requests.get(f"{base_url}/auth/login", timeout=10)
        print(f"Login page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Admin login accessible during maintenance")
        else:
            print(f"❌ Login page not accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Health check (should still work)
    print("\n3. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check working during maintenance")
            print(f"Health response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Static files (should work)
    print("\n4. Testing static file access...")
    try:
        response = requests.get(f"{base_url}/static/css/style.css", timeout=10)
        print(f"CSS file status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Static files accessible during maintenance")
        else:
            print(f"Static file status: {response.status_code}")
    except Exception as e:
        print(f"Static file test: {e}")
    
    print("\n=== Manual Testing Instructions ===")
    print("To test admin functionality during maintenance:")
    print("1. Go to http://localhost:8000/auth/login")
    print("2. Login with admin credentials")
    print("3. You should see a maintenance banner at the top")
    print("4. The site should work normally for you")
    print("5. Go to http://localhost:8000/admin/settings")
    print("6. Toggle maintenance mode OFF to restore normal access")
    print("7. Test in incognito window to verify public access restored")
    
    return True

if __name__ == "__main__":
    test_improved_maintenance_mode()
