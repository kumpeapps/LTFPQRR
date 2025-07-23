#!/usr/bin/env python3
"""
Test script for Demo and Pre-Production banners.
"""

import os
import sys

def test_environment_banners():
    """Test that environment banners work correctly with environment variables."""
    
    print("=== Demo and Pre-Production Banner Test ===\n")
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from config import Config, DevelopmentConfig
        
        print("1. Testing default configuration (no env vars set)...")
        config = Config()
        print(f"   DEMO_MODE: {config.DEMO_MODE}")
        print(f"   PREPROD_MODE: {config.PREPROD_MODE}")
        print("   ✓ Both should be False by default")
        
        print("\n2. Testing with DEMO_MODE=true...")
        os.environ['DEMO_MODE'] = 'true'
        # Reload config to pick up new env var
        from importlib import reload
        import config as config_module
        reload(config_module)
        from config import Config
        
        config = Config()
        print(f"   DEMO_MODE: {config.DEMO_MODE}")
        print(f"   PREPROD_MODE: {config.PREPROD_MODE}")
        print("   ✓ DEMO_MODE should be True, PREPROD_MODE should be False")
        
        print("\n3. Testing with PREPROD_MODE=true...")
        os.environ['DEMO_MODE'] = 'false'
        os.environ['PREPROD_MODE'] = 'true'
        reload(config_module)
        from config import Config
        
        config = Config()
        print(f"   DEMO_MODE: {config.DEMO_MODE}")
        print(f"   PREPROD_MODE: {config.PREPROD_MODE}")
        print("   ✓ DEMO_MODE should be False, PREPROD_MODE should be True")
        
        print("\n4. Testing with both enabled...")
        os.environ['DEMO_MODE'] = 'true'
        os.environ['PREPROD_MODE'] = 'true'
        reload(config_module)
        from config import Config
        
        config = Config()
        print(f"   DEMO_MODE: {config.DEMO_MODE}")
        print(f"   PREPROD_MODE: {config.PREPROD_MODE}")
        print("   ✓ Both should be True")
        
        print("\n5. Testing case insensitive values...")
        os.environ['DEMO_MODE'] = 'TRUE'
        os.environ['PREPROD_MODE'] = 'True'
        reload(config_module)
        from config import Config
        
        config = Config()
        print(f"   DEMO_MODE: {config.DEMO_MODE}")
        print(f"   PREPROD_MODE: {config.PREPROD_MODE}")
        print("   ✓ Both should be True (case insensitive)")
        
        print("\n6. Testing invalid values...")
        os.environ['DEMO_MODE'] = 'yes'
        os.environ['PREPROD_MODE'] = '1'
        reload(config_module)
        from config import Config
        
        config = Config()
        print(f"   DEMO_MODE: {config.DEMO_MODE}")
        print(f"   PREPROD_MODE: {config.PREPROD_MODE}")
        print("   ✓ Both should be False (only 'true' is valid)")
        
        # Clean up environment variables
        if 'DEMO_MODE' in os.environ:
            del os.environ['DEMO_MODE']
        if 'PREPROD_MODE' in os.environ:
            del os.environ['PREPROD_MODE']
        
        print("\n=== Test Completed Successfully! ===")
        print("\nTo test the banners in action:")
        print("1. Set environment variables: export DEMO_MODE=true")
        print("2. Start the development server: ./dev.sh start-dev")
        print("3. Visit http://localhost:8000 to see the demo banner")
        print("4. Set PREPROD_MODE=true instead to see the pre-prod banner")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_environment_banners()
    sys.exit(0 if success else 1)
