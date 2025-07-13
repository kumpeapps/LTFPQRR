#!/usr/bin/env python3
"""
Database migration script to add partner_id column to subscription table
and migrate existing PartnerSubscription data.
"""

def migrate_subscription_table():
    """Add partner_id column and migrate PartnerSubscription data."""
    from extensions import db
    from models.models import Subscription, PartnerSubscription, Partner
    from sqlalchemy import text
    import logging
    
    print("🔄 Starting subscription table migration...")
    
    try:
        # Add partner_id column to subscription table if it doesn't exist
        print("📝 Adding partner_id column to subscription table...")
        db.session.execute(text("""
            ALTER TABLE subscription 
            ADD COLUMN partner_id INTEGER;
        """))
        db.session.commit()
        print("✅ Added partner_id column")
        
    except Exception as e:
        if "already exists" in str(e) or "duplicate column" in str(e).lower():
            print("ℹ️  partner_id column already exists")
            db.session.rollback()
        else:
            print(f"❌ Error adding partner_id column: {e}")
            db.session.rollback()
            return False
    
    try:
        # Add foreign key constraint
        print("🔗 Adding foreign key constraint for partner_id...")
        db.session.execute(text("""
            ALTER TABLE subscription 
            ADD CONSTRAINT fk_subscription_partner_id 
            FOREIGN KEY (partner_id) REFERENCES partner(id);
        """))
        db.session.commit()
        print("✅ Added foreign key constraint")
        
    except Exception as e:
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            print("ℹ️  Foreign key constraint already exists")
            db.session.rollback()
        else:
            print(f"⚠️  Could not add foreign key constraint: {e}")
            db.session.rollback()
            # Continue anyway as this is not critical
    
    try:
        # Migrate existing PartnerSubscription records to unified subscription table
        print("🔄 Migrating PartnerSubscription records...")
        
        partner_subscriptions = PartnerSubscription.query.all()
        migrated_count = 0
        
        for ps in partner_subscriptions:
            # Check if this subscription is already migrated
            existing = Subscription.query.filter_by(
                partner_id=ps.partner_id,
                subscription_type="partner",
                payment_id=ps.payment_id
            ).first()
            
            if existing:
                print(f"⏭️  Skipping already migrated subscription for partner {ps.partner_id}")
                continue
            
            # Create new unified subscription record
            new_subscription = Subscription(
                user_id=ps.partner.owner_id,
                partner_id=ps.partner_id,
                pricing_plan_id=ps.pricing_plan_id,
                subscription_type="partner",
                status=ps.status,
                admin_approved=ps.admin_approved,
                approved_by=ps.approved_by,
                approved_at=ps.approved_at,
                max_tags=ps.max_tags,
                payment_method=ps.payment_method,
                payment_id=ps.payment_id,
                amount=ps.amount,
                start_date=ps.start_date,
                end_date=ps.end_date,
                created_at=ps.created_at,
                updated_at=ps.updated_at,
                auto_renew=ps.auto_renew,
                cancellation_requested=ps.cancellation_requested
            )
            
            db.session.add(new_subscription)
            migrated_count += 1
            
        if migrated_count > 0:
            db.session.commit()
            print(f"✅ Migrated {migrated_count} PartnerSubscription records")
        else:
            print("ℹ️  No PartnerSubscription records to migrate")
            
    except Exception as e:
        print(f"❌ Error migrating PartnerSubscription records: {e}")
        db.session.rollback()
        return False
    
    print("🎉 Subscription table migration completed successfully!")
    return True

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from app import create_app
    
    app = create_app()
    with app.app_context():
        success = migrate_subscription_table()
        sys.exit(0 if success else 1)
