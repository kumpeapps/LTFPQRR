#!/usr/bin/env python3
"""
Test script to verify QR scanner functionality
"""

import requests
import time

def test_qr_scanner_page():
    """Test that the found page loads with QR scanner functionality"""
    print("=== Testing QR Scanner Implementation ===\n")
    
    try:
        # Test found page loads
        print("1. Testing found page access...")
        response = requests.get("http://localhost:8000/found", timeout=10)
        print(f"Found page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for QR scanner elements
            checks = [
                ("Html5-QRCode library", "html5-qrcode" in content),
                ("QR scanner container", "qr-scanner-container" in content),
                ("Start scanner button", "startQRScanner()" in content),
                ("Camera switching", "switchCamera()" in content),
                ("Tag ID extraction", "extractTagId" in content),
                ("Scanner controls", "scanner-controls" in content),
                ("HTTPS warning", "Camera access requires HTTPS" in content),
            ]
            
            print("\n2. Checking QR scanner components:")
            all_good = True
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}: {'Present' if result else 'Missing'}")
                if not result:
                    all_good = False
            
            if all_good:
                print("\n✅ All QR scanner components are properly implemented!")
            else:
                print("\n⚠️  Some QR scanner components may be missing")
                
        else:
            print(f"❌ Found page not accessible (status: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure the development server is running")
    
    print("\n=== Test Complete ===")
    print("\nTo test QR scanning manually:")
    print("1. Open http://localhost:8000/found in a web browser")
    print("2. Click 'Start Scanner' button")
    print("3. Allow camera access when prompted")
    print("4. Point camera at a QR code containing a tag ID")
    print("5. The scanner should automatically detect and redirect")

if __name__ == "__main__":
    # Wait a moment for rebuild to complete
    print("Waiting for development server to be ready...")
    time.sleep(10)
    test_qr_scanner_page()
