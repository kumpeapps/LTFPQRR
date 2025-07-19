#!/usr/bin/env python3
"""
Apply subscription fixes and run cleanup for existing duplicate subscriptions
This script should be run after deploying the code fixes to clean up any existing duplicates
"""

import sys
import os
from datetime import datetime

# Set up the Flask app context
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

def main():
    """Apply fixes and cleanup existing duplicates"""
    print("🔧 LTFPQRR Subscription Fixes - Deployment Script")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    try:
        # Import the existing cleanup script
        from cleanup_duplicate_subscriptions import cleanup_duplicate_subscriptions
        
        print("\n📋 Running duplicate subscription cleanup...")
        cleanup_duplicate_subscriptions()
        
        print("\n✅ Cleanup completed successfully!")
        print("\n🎯 Next Steps:")
        print("1. Verify webhook events are configured in Stripe:")
        print("   - customer.subscription.deleted")
        print("   - payment_intent.canceled")
        print("   - invoice.payment_action_required")
        print("   - payment_method.attached")
        print("   - customer.subscription.updated")
        print("\n2. Monitor application logs for webhook event processing")
        print("3. Test subscription creation to verify duplicate prevention")
        print("4. Test subscription cancellation in Stripe dashboard")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
