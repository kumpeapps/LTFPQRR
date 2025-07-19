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
                
            # Get the pet's owner
            from sqlalchemy.orm import sessionmaker
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
                pet_id=pet.id,
                finder_email="finder@example.com",
                finder_name="Test Finder",
                message="Found your pet at the park!"
            )
                print(f"ERROR: Owner not found for pet {pet.id}")
                return False
            
            tag = Tag.query.filter_by(pet_id=pet.id).first()
            if not tag:
                print(f"ERROR: No tag found for pet {pet.id}")
                return False
            
            print(f"Found test data:")
            print(f"  Pet: {pet.name} (ID: {pet.id})")
            print(f"  Owner: {owner.first_name} {owner.last_name} ({owner.email})")
            print(f"  Tag: {tag.tag_id}")
            print()
            
            # Test 1: Pet search notification
            print("Test 1: Triggering pet search notification...")
            success1 = send_notification_email(owner, tag, pet)
            print(f"  Result: {'SUCCESS' if success1 else 'FAILED'}")
            
            # Test 2: Pet found contact
            print("Test 2: Triggering pet found contact...")
            success2 = send_contact_email(
                owner, pet, 
                "John Finder", "john.finder@example.com", 
                "Hi! I found your pet in the park. Please contact me to arrange pickup."
            )
            print(f"  Result: {'SUCCESS' if success2 else 'FAILED'}")
            
            print()
            
            # Check queue status
            print("Checking email queue...")
            from models.email.email_models import EmailQueue, EmailStatus
            
            pending_emails = EmailQueue.query.filter_by(status=EmailStatus.PENDING).all()
            print(f"  Pending emails in queue: {len(pending_emails)}")
            
            for email in pending_emails:
                print(f"    - To: {email.to_email}")
                print(f"      Subject: {email.subject}")
                print(f"      Type: {email.email_type}")
                print(f"      Metadata: {json.dumps(email.email_metadata, indent=2) if email.email_metadata else 'None'}")
                print()
            
            # Process queue manually
            print("Processing email queue manually...")
            stats = EmailManager.process_queue(limit=10)
            print(f"  Queue processing stats: {stats}")
            
            # Check for processed emails
            processed_emails = EmailQueue.query.filter(
                EmailQueue.status.in_([EmailStatus.SENT, EmailStatus.FAILED])
            ).order_by(EmailQueue.updated_at.desc()).limit(5).all()
            
            print(f"  Recently processed emails: {len(processed_emails)}")
            for email in processed_emails:
                print(f"    - To: {email.to_email}")
                print(f"      Status: {email.status}")
                print(f"      Subject: {email.subject}")
                print(f"      Type: {email.email_type}")
                print()
            
            return success1 and success2
            
        except Exception as e:
            print(f"ERROR: {e}")
            logger.error(f"Test error: {e}")
            return False

if __name__ == '__main__':
    success = test_pet_notifications()
    print("=" * 50)
    print(f"Overall test result: {'PASSED' if success else 'FAILED'}")
