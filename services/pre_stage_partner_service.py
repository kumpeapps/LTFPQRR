"""
Pre-stage Partner Service for LTFPQRR application.
Handles automatic role assignment and management based on pre-stage partner status.
"""

from models.models import User, Role, PreStagePartner
from extensions import db
import logging

logger = logging.getLogger(__name__)


class PreStagePartnerService:
    """Service for managing pre-stage partner functionality"""
    
    @staticmethod
    def process_user_for_partner_role(user_email, user_id=None):
        """
        Process a user's email against the pre-stage partner list.
        
        Args:
            user_email: Email address to check
            user_id: Optional user ID if checking existing user
            
        Returns:
            dict: Result of processing with status and message
        """
        pre_stage_partner = PreStagePartner.get_by_email(user_email)
        
        if not pre_stage_partner:
            return {
                'status': 'no_action',
                'message': 'Email not in pre-stage partner list'
            }
        
        if user_id:
            user = User.query.get(user_id)
            if not user:
                return {
                    'status': 'error',
                    'message': 'User not found'
                }
        else:
            user = User.query.filter_by(email=user_email).first()
            if not user:
                return {
                    'status': 'no_action',
                    'message': 'User not found'
                }
        
        partner_role = Role.query.filter_by(name="partner").first()
        if not partner_role:
            logger.error("Partner role not found in database")
            return {
                'status': 'error',
                'message': 'Partner role not found'
            }
        
        has_partner_role = partner_role in user.roles
        
        if pre_stage_partner.status == 'pre-approved':
            if not has_partner_role:
                user.roles.append(partner_role)
                db.session.commit()
                logger.info(f"Added partner role to user {user.username} ({user.email})")
                return {
                    'status': 'role_added',
                    'message': 'Partner role added to user'
                }
            else:
                return {
                    'status': 'no_action',
                    'message': 'User already has partner role'
                }
        
        elif pre_stage_partner.status == 'blocked':
            if has_partner_role:
                user.roles.remove(partner_role)
                db.session.commit()
                logger.info(f"Removed partner role from user {user.username} ({user.email})")
                return {
                    'status': 'role_removed',
                    'message': 'Partner role removed from user due to blocked status'
                }
            else:
                return {
                    'status': 'no_action',
                    'message': 'User does not have partner role to remove'
                }
        
        elif pre_stage_partner.status == 'restricted':
            # Restricted means no new partner creation but existing partners can continue
            # No role changes needed for existing users
            return {
                'status': 'no_action',
                'message': 'User status is restricted - no role changes'
            }
        
        return {
            'status': 'no_action',
            'message': f'Unknown pre-stage partner status: {pre_stage_partner.status}'
        }
    
    @staticmethod
    def can_user_create_partner(user_email):
        """
        Check if a user can create a new partner based on pre-stage status.
        
        Args:
            user_email: Email address to check
            
        Returns:
            tuple: (can_create: bool, reason: str)
        """
        pre_stage_partner = PreStagePartner.get_by_email(user_email)
        
        if not pre_stage_partner:
            # If not in pre-stage list, follow normal partner creation rules
            return True, "Not in pre-stage list"
        
        if pre_stage_partner.status == 'pre-approved':
            return True, "Pre-approved for partner creation"
        
        elif pre_stage_partner.status == 'restricted':
            return False, "Email is restricted from creating new partners"
        
        elif pre_stage_partner.status == 'blocked':
            return False, "Email is blocked from partner access"
        
        return False, f"Unknown pre-stage status: {pre_stage_partner.status}"
    
    @staticmethod
    def enforce_blocked_status():
        """
        Enforce blocked status for all users with blocked emails.
        This can be run periodically or when pre-stage status changes.
        
        Returns:
            dict: Summary of actions taken
        """
        blocked_partners = PreStagePartner.query.filter_by(status='blocked').all()
        results = {
            'processed': 0,
            'roles_removed': 0,
            'errors': []
        }
        
        partner_role = Role.query.filter_by(name="partner").first()
        if not partner_role:
            results['errors'].append("Partner role not found")
            return results
        
        for blocked_partner in blocked_partners:
            results['processed'] += 1
            
            # Find all users with this email
            users = User.query.filter_by(email=blocked_partner.email).all()
            
            for user in users:
                if partner_role in user.roles:
                    try:
                        user.roles.remove(partner_role)
                        db.session.commit()
                        results['roles_removed'] += 1
                        logger.info(f"Removed partner role from blocked user {user.username} ({user.email})")
                    except Exception as e:
                        error_msg = f"Error removing role from {user.username}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        db.session.rollback()
        
        return results
    
    @staticmethod
    def sync_all_pre_approved():
        """
        Sync all pre-approved users to ensure they have partner role.
        Useful for batch processing or fixing inconsistencies.
        
        Returns:
            dict: Summary of actions taken
        """
        pre_approved_partners = PreStagePartner.query.filter_by(status='pre-approved').all()
        results = {
            'processed': 0,
            'roles_added': 0,
            'errors': []
        }
        
        partner_role = Role.query.filter_by(name="partner").first()
        if not partner_role:
            results['errors'].append("Partner role not found")
            return results
        
        for pre_approved_partner in pre_approved_partners:
            results['processed'] += 1
            
            # Find all users with this email
            users = User.query.filter_by(email=pre_approved_partner.email).all()
            
            for user in users:
                if partner_role not in user.roles:
                    try:
                        user.roles.append(partner_role)
                        db.session.commit()
                        results['roles_added'] += 1
                        logger.info(f"Added partner role to pre-approved user {user.username} ({user.email})")
                    except Exception as e:
                        error_msg = f"Error adding role to {user.username}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        db.session.rollback()
        
        return results
