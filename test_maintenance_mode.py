#!/usr/bin/env python3
"""
Test script to verify maintenance mode functionality.
"""

import os
import sys
import requests
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_maintenance_mode():
    """Test maintenance mode functionality"""
    
    from app import create_app
    from models.models import SystemSetting
    from extensions import db
    
    app = create_app()
    
    with app.app_context():
        print("=== Testing Maintenance Mode Functionality ===")
        print(f"Starting test at {datetime.now()}")
        
        try:
            # Get current maintenance mode setting
            maintenance_setting = SystemSetting.query.filter_by(key='maintenance_mode').first()
            original_value = maintenance_setting.value if maintenance_setting else 'false'
            
            print(f"Current maintenance_mode setting: {original_value}")
            
            # Test with maintenance mode disabled
            print("\n--- Testing with maintenance mode disabled ---")
            if maintenance_setting:
                maintenance_setting.value = 'false'
                db.session.commit()
            
            # Test with Flask test client
            with app.test_client() as client:
                response = client.get('/')
                print(f"Homepage response with maintenance OFF: {response.status_code}")
                if response.status_code == 200:
                    print("✅ Site accessible when maintenance mode is disabled")
                else:
                    print("❌ Site not accessible when maintenance mode should be disabled")
            
            # Test with maintenance mode enabled
            print("\n--- Testing with maintenance mode enabled ---")
            if maintenance_setting:
                maintenance_setting.value = 'true'
            else:
                maintenance_setting = SystemSetting(
                    key='maintenance_mode',
                    value='true',
                    description='Enable maintenance mode'
                )
                db.session.add(maintenance_setting)
            db.session.commit()
            
            # Test with Flask test client
            with app.test_client() as client:
                response = client.get('/')
                print(f"Homepage response with maintenance ON: {response.status_code}")
                if response.status_code == 503:
                    print("✅ Site properly blocked when maintenance mode is enabled")
                    # Check if maintenance page content is returned
                    content = response.get_data(as_text=True)
                    if 'Maintenance Mode' in content:
                        print("✅ Maintenance mode page displayed correctly")
                    else:
                        print("❌ Maintenance mode page content not found")
                else:
                    print("❌ Site not blocked when maintenance mode should be enabled")
            
            # Test health check still works during maintenance
            print("\n--- Testing health check during maintenance ---")
            with app.test_client() as client:
                response = client.get('/health')
                print(f"Health check response during maintenance: {response.status_code}")
                if response.status_code == 200:
                    print("✅ Health check bypasses maintenance mode")
                else:
                    print("❌ Health check blocked by maintenance mode")
            
            # Restore original setting
            print(f"\n--- Restoring original maintenance_mode setting: {original_value} ---")
            if maintenance_setting:
                maintenance_setting.value = original_value
                db.session.commit()
            
            print("\n✅ Maintenance mode functionality test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_maintenance_mode()
    exit(0 if success else 1)
