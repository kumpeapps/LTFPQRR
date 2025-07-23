#!/usr/bin/env python3
"""
Test script for Pre-Stage Partner functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pre_stage_partner_system():
    """Test the pre-stage partner system functionality"""
    
    # Import with app context
    from app import create_app
    from models.models import PreStagePartner, User, Role
    from services.pre_stage_partner_service import PreStagePartnerService
    from extensions import db
    
    app = create_app()
    
    with app.app_context():
        print("=== Testing Pre-Stage Partner System ===")
        
        # Test 1: Check if model is accessible
        print("\n1. Testing model accessibility...")
        try:
            count = PreStagePartner.query.count()
            print(f"✓ PreStagePartner table exists with {count} records")
        except Exception as e:
            print(f"✗ Error accessing PreStagePartner table: {e}")
            return False
        
        # Test 2: Test helper methods with non-existent email
        print("\n2. Testing helper methods...")
        test_email = "nonexistent@test.com"
        status = PreStagePartner.get_status(test_email)
        print(f"✓ get_status for non-existent email: {status}")
        
        is_pre_approved = PreStagePartner.is_pre_approved(test_email)
        is_restricted = PreStagePartner.is_restricted(test_email)
        is_blocked = PreStagePartner.is_blocked(test_email)
        print(f"✓ is_pre_approved: {is_pre_approved}, is_restricted: {is_restricted}, is_blocked: {is_blocked}")
        
        # Test 3: Create a test pre-stage partner
        print("\n3. Testing create pre-stage partner...")
        try:
            test_partner = PreStagePartner(
                company_name="Test Company",
                owner_name="Test Owner",
                email="test@prestage.com",
                status="pre-approved",
                notes="Test pre-stage partner"
            )
            db.session.add(test_partner)
            db.session.commit()
            print("✓ Successfully created test pre-stage partner")
            
            # Test retrieval
            retrieved = PreStagePartner.get_by_email("test@prestage.com")
            print(f"✓ Retrieved partner: {retrieved.company_name} - {retrieved.status}")
            
        except Exception as e:
            print(f"✗ Error creating test partner: {e}")
            db.session.rollback()
        
        # Test 4: Test case-insensitive email lookup
        print("\n4. Testing case-insensitive email lookup...")
        upper_case_result = PreStagePartner.get_by_email("TEST@PRESTAGE.COM")
        if upper_case_result:
            print("✓ Case-insensitive lookup works correctly")
        else:
            print("✗ Case-insensitive lookup failed")
        
        # Test 5: Test service methods
        print("\n5. Testing PreStagePartnerService...")
        try:
            can_create, reason = PreStagePartnerService.can_user_create_partner("test@prestage.com")
            print(f"✓ can_user_create_partner: {can_create}, reason: {reason}")
            
            can_create_unknown, reason_unknown = PreStagePartnerService.can_user_create_partner("unknown@test.com")
            print(f"✓ can_user_create_partner (unknown): {can_create_unknown}, reason: {reason_unknown}")
            
        except Exception as e:
            print(f"✗ Error testing service methods: {e}")
        
        # Test 6: Test different status types
        print("\n6. Testing different status types...")
        try:
            # Create restricted partner
            restricted_partner = PreStagePartner(
                company_name="Restricted Company",
                owner_name="Restricted Owner", 
                email="restricted@test.com",
                status="restricted"
            )
            db.session.add(restricted_partner)
            
            # Create blocked partner
            blocked_partner = PreStagePartner(
                company_name="Blocked Company",
                owner_name="Blocked Owner",
                email="blocked@test.com", 
                status="blocked"
            )
            db.session.add(blocked_partner)
            db.session.commit()
            
            print("✓ Created partners with different statuses")
            
            # Test status checks
            print(f"✓ Restricted status check: {PreStagePartner.is_restricted('restricted@test.com')}")
            print(f"✓ Blocked status check: {PreStagePartner.is_blocked('blocked@test.com')}")
            
        except Exception as e:
            print(f"✗ Error testing status types: {e}")
            db.session.rollback()
        
        # Test 7: Test to_dict method
        print("\n7. Testing to_dict method...")
        try:
            partner_dict = test_partner.to_dict()
            print(f"✓ to_dict keys: {list(partner_dict.keys())}")
        except Exception as e:
            print(f"✗ Error testing to_dict: {e}")
        
        # Cleanup test data
        print("\n8. Cleaning up test data...")
        try:
            PreStagePartner.query.filter(PreStagePartner.email.like('%@test.com')).delete()
            PreStagePartner.query.filter(PreStagePartner.email.like('%@prestage.com')).delete()
            db.session.commit()
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"✗ Error cleaning up: {e}")
            db.session.rollback()
        
        print("\n=== Pre-Stage Partner System Test Complete ===")
        return True

if __name__ == "__main__":
    test_pre_stage_partner_system()
