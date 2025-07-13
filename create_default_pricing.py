#!/usr/bin/env python3
"""
Create default pricing plans for the system
"""

from app import app, db
from models.models import PricingPlan

def create_default_pricing_plans():
    with app.app_context():
        # Check if pricing plans already exist
        if PricingPlan.query.count() > 0:
            print('Pricing plans already exist')
            return

        # Create basic pricing plans
        plans = [
            {
                'name': 'Basic',
                'price': 9.99,
                'billing_period': 'monthly',
                'description': 'Perfect for individual pet owners',
                'features': 'QR Tag Generation\nPet Profile Management\nLost Pet Alerts\nEmail Support',
                'is_featured': False,
                'is_active': True
            },
            {
                'name': 'Premium',
                'price': 19.99,
                'billing_period': 'monthly',
                'description': 'Best value for families with multiple pets',
                'features': 'QR Tag Generation\nPet Profile Management\nLost Pet Alerts\n24/7 Support\nMultiple Pet Profiles\nPriority Notifications',
                'is_featured': True,
                'is_active': True
            },
            {
                'name': 'Annual Basic',
                'price': 99.99,
                'billing_period': 'annually',
                'description': 'Save 17% with annual billing',
                'features': 'QR Tag Generation\nPet Profile Management\nLost Pet Alerts\nEmail Support\n2 Months Free',
                'is_featured': False,
                'is_active': True
            },
            {
                'name': 'Annual Premium',
                'price': 199.99,
                'billing_period': 'annually',
                'description': 'Maximum savings for premium features',
                'features': 'QR Tag Generation\nPet Profile Management\nLost Pet Alerts\n24/7 Support\nMultiple Pet Profiles\nPriority Notifications\n2 Months Free',
                'is_featured': False,
                'is_active': True
            }
        ]

        for plan_data in plans:
            plan = PricingPlan(**plan_data)
            db.session.add(plan)
        
        db.session.commit()
        print(f'Created {len(plans)} default pricing plans')

if __name__ == '__main__':
    create_default_pricing_plans()
