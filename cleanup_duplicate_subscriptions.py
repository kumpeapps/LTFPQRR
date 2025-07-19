#!/usr/bin/env python3
"""
Clean up duplicate subscriptions on remote server
Run this script on the remote server to remove duplicate tag subscriptions
"""
import sys
import os
from datetime import datetime

# Set up the Flask app context
sys.path.insert(0, '/app')

from app import create_app
from extensions import db
from models.models import Subscription, User, Tag
from sqlalchemy import func

def cleanup_duplicate_subscriptions():
    """Remove duplicate active subscriptions for the same user/tag combination"""
    app = create_app()
    
    with app.app_context():
        print("=== Duplicate Subscription Cleanup ===")
        print(f"Starting cleanup at {datetime.now()}")
        
        # Find all active subscriptions grouped by user_id and tag_id
        print("\nFinding duplicate subscriptions...")
        
        # Query to find duplicates
        duplicates_query = db.session.query(
            Subscription.user_id,
            Subscription.tag_id,
            func.count(Subscription.id).label('count')
        ).filter(
            Subscription.status == 'active',
            Subscription.tag_id.isnot(None)  # Only tag subscriptions
        ).group_by(
            Subscription.user_id,
            Subscription.tag_id
        ).having(
            func.count(Subscription.id) > 1
        ).all()
        
        print(f"Found {len(duplicates_query)} user/tag combinations with duplicates")
        
        total_removed = 0
        
        for user_id, tag_id, count in duplicates_query:
            print(f"\nProcessing user_id={user_id}, tag_id={tag_id} ({count} subscriptions)")
            
            # Get all subscriptions for this user/tag combo
            subscriptions = Subscription.query.filter_by(
                user_id=user_id,
                tag_id=tag_id,
                status='active'
            ).order_by(Subscription.created_at.asc()).all()
            
            if len(subscriptions) > 1:
                # Keep the first (oldest) subscription, remove the rest
                keep_subscription = subscriptions[0]
                remove_subscriptions = subscriptions[1:]
                
                print(f"  Keeping subscription ID {keep_subscription.id} (created: {keep_subscription.created_at})")
                
                for sub in remove_subscriptions:
                    print(f"  Removing duplicate subscription ID {sub.id} (created: {sub.created_at})")
                    
                    # Get user and tag info for logging
                    user = User.query.get(user_id)
                    tag = Tag.query.get(tag_id)
                    
                    print(f"    User: {user.username if user else 'Unknown'}")
                    print(f"    Tag: {tag.tag_id if tag else 'Unknown'}")
                    print(f"    Amount: ${sub.amount}")
                    print(f"    Subscription Type: {sub.subscription_type}")
                    
                    # Remove the duplicate
                    db.session.delete(sub)
                    total_removed += 1
        
        if total_removed > 0:
            print(f"\nCommitting changes...")
            db.session.commit()
            print(f"✅ Successfully removed {total_removed} duplicate subscriptions")
        else:
            print("\n✅ No duplicate subscriptions found to remove")
        
        # Verify cleanup
        print("\nVerifying cleanup...")
        remaining_duplicates = db.session.query(
            Subscription.user_id,
            Subscription.tag_id,
            func.count(Subscription.id).label('count')
        ).filter(
            Subscription.status == 'active',
            Subscription.tag_id.isnot(None)
        ).group_by(
            Subscription.user_id,
            Subscription.tag_id
        ).having(
            func.count(Subscription.id) > 1
        ).count()
        
        if remaining_duplicates == 0:
            print("✅ All duplicates successfully removed")
        else:
            print(f"⚠️  {remaining_duplicates} duplicate combinations still exist")
        
        print(f"\nCleanup completed at {datetime.now()}")

if __name__ == "__main__":
    cleanup_duplicate_subscriptions()
