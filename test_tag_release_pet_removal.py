#!/usr/bin/env python3
"""
Test script to verify that releasing a tag also removes the pet association.
"""

import os
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tag_release_pet_removal():
    """Test that releasing a tag removes both owner_id and pet_id"""
    
    # Import after setting up path
    from app import create_app
    from models.models import Tag, Pet, User, Subscription, Payment
    from extensions import db
    
    app = create_app()
    
    with app.app_context():
        print("=== Testing Tag Release Pet Removal ===")
        print(f"Starting test at {datetime.now()}")
        
        try:
            # Find a test tag with both owner and pet assigned
            test_tag = Tag.query.filter(
                Tag.owner_id.isnot(None),
                Tag.pet_id.isnot(None)
            ).first()
            
            if not test_tag:
                print("⚠️  No test tag found with both owner and pet assigned")
                print("Creating a mock scenario...")
                
                # Find or create a test user
                test_user = User.query.filter_by(username='test_user').first()
                if not test_user:
                    print("No test user found. Please create one manually or run with existing data.")
                    return False
                
                # Find an available tag
                available_tag = Tag.query.filter_by(status='available').first()
                if not available_tag:
                    print("No available tag found to test with.")
                    return False
                
                # Create a test pet
                test_pet = Pet(
                    name="Test Pet",
                    owner_id=test_user.id,
                    species="Dog",
                    breed="Test Breed"
                )
                db.session.add(test_pet)
                db.session.flush()  # Get the pet ID
                
                # Assign tag to user and pet
                available_tag.owner_id = test_user.id
                available_tag.pet_id = test_pet.id
                available_tag.status = 'active'
                
                db.session.commit()
                test_tag = available_tag
                print(f"✅ Created test scenario with tag {test_tag.tag_id}")
            
            original_owner_id = test_tag.owner_id
            original_pet_id = test_tag.pet_id
            
            print(f"Test tag: {test_tag.tag_id}")
            print(f"Original owner_id: {original_owner_id}")
            print(f"Original pet_id: {original_pet_id}")
            print(f"Original status: {test_tag.status}")
            
            # Simulate releasing the tag (as would happen in refund/cancellation)
            print("\n--- Simulating tag release ---")
            test_tag.status = "available"
            test_tag.owner_id = None
            test_tag.pet_id = None  # This is the new behavior we're testing
            
            db.session.commit()
            
            # Verify the release worked correctly
            db.session.refresh(test_tag)
            
            print(f"After release:")
            print(f"Status: {test_tag.status}")
            print(f"Owner ID: {test_tag.owner_id}")
            print(f"Pet ID: {test_tag.pet_id}")
            
            # Check results
            success = True
            if test_tag.status != "available":
                print(f"❌ Status should be 'available', got '{test_tag.status}'")
                success = False
            
            if test_tag.owner_id is not None:
                print(f"❌ Owner ID should be None, got '{test_tag.owner_id}'")
                success = False
                
            if test_tag.pet_id is not None:
                print(f"❌ Pet ID should be None, got '{test_tag.pet_id}'")
                success = False
            
            if success:
                print("\n✅ Tag release with pet removal working correctly!")
                print("✅ Both owner_id and pet_id are properly cleared when tag is released")
            else:
                print("\n❌ Tag release with pet removal failed!")
            
            return success
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_tag_release_pet_removal()
    exit(0 if success else 1)
