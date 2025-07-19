#!/usr/bin/env python3
"""
Test script to verify pet email notification system
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.pet import Pet
from models.pet.pet import Tag
from models.user import User
from utils import send_notification_email, send_contact_email
from services.email_service import EmailManager
from extensions import logger
import json

def test_pet_notifications():
    """Test pet notification system"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Testing Pet Email Notification System")
            print("=" * 50)
            
            # Get a test pet and owner
            pet = Pet.query.first()
            if not pet:
                print("ERROR: No pets found in database")
                return False
                
            # Check if pet has a tag
            tag = Tag.query.filter_by(pet_id=pet.id).first()
            if not tag:
                print(f"WARNING: No tag found for pet {pet.id}, creating test tag...")
                from models.base import db
                # Create a test tag for this pet
                tag = Tag(
                    tag_id=f"TEST{pet.id:05d}",
                    status='active',
                    created_by=pet.owner_id,
                    owner_id=pet.owner_id,
                    pet_id=pet.id
                )
                db.session.add(tag)
                db.session.commit()
                print(f"Created tag {tag.tag_id} for pet {pet.id}")
                
            # Get the pet's owner using SQLAlchemy 2.0 syntax
            from models.base import db
            owner = db.session.get(User, pet.owner_id)
            if not owner:
                print(f"ERROR: No owner found for pet {pet.id}")
                return False
            
            print(f"Found pet: {pet.name} (ID: {pet.id})")
            print(f"Pet owner: {owner.username} ({owner.email})")
            print(f"Pet tag: {tag.tag_id}")
            
            # Test 1: Search notification email
            print("\n--- Testing Search Notification Email ---")
            search_result = send_notification_email(
                owner=owner,
                tag=tag,
                pet=pet
            )
            
            if search_result:
                print("✓ Search notification queued successfully")
            else:
                print("✗ Search notification failed")
            
            # Test 2: Contact email
            print("\n--- Testing Contact Email ---")
            contact_result = send_contact_email(
                owner=owner,
                pet=pet,
                finder_name="Test Finder",
                finder_email="finder@example.com",
                message="I have information about your pet"
            )
            
            if contact_result:
                print("✓ Contact email queued successfully")
            else:
                print("✗ Contact email failed")
            
            # Test 3: Check email queue
            print("\n--- Checking Email Queue ---")
            email_manager = EmailManager()
            from models.email.email_models import EmailQueue
            
            queued_emails = EmailQueue.query.filter_by(status='pending').all()
            print(f"Found {len(queued_emails)} pending emails in queue")
            
            for email in queued_emails:
                print(f"  - ID: {email.id}, Type: {email.email_type}, To: {email.to_email}")
                if email.email_metadata:
                    metadata = json.loads(email.email_metadata) if isinstance(email.email_metadata, str) else email.email_metadata
                    print(f"    Metadata: {metadata}")
            
            # Test 4: Process one email from queue
            print("\n--- Processing Test Email ---")
            if queued_emails:
                test_email = queued_emails[0]
                print(f"Processing email ID {test_email.id}...")
                
                # Process the email using the correct method
                metadata = json.loads(test_email.email_metadata) if isinstance(test_email.email_metadata, str) else test_email.email_metadata
                result = email_manager.process_queue_item(test_email, test_email.email_type, metadata)
                if result:
                    print("✓ Email processed successfully")
                    
                    # Check if it was marked as sent
                    db.session.refresh(test_email)
                    print(f"  Email status: {test_email.status.value}")
                    if test_email.sent_at:
                        print(f"  Sent at: {test_email.sent_at}")
                else:
                    print("✗ Email processing failed")
            
            # Test 5: Check templates exist
            print("\n--- Checking Email Templates ---")
            from models.email.email_models import EmailTemplate
            
            templates = EmailTemplate.query.filter(
                EmailTemplate.name.in_(['pet_search_notification', 'pet_found_contact'])
            ).all()
            
            print(f"Found {len(templates)} pet-related templates:")
            for template in templates:
                print(f"  - {template.name}: {template.category}")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("Starting pet email notification tests...")
    success = test_pet_notifications()
    
    print("\n" + "=" * 50)
    if success:
        print("Overall test result: SUCCESS")
    else:
        print("Overall test result: FAILED")
