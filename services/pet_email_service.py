"""
Pet Email Service for background processing of pet-related email notifications
"""
from typing import Dict, Any, Optional
from extensions import db, logger
from models.email.email_models import EmailQueue, EmailTemplate, EmailStatus
from services.enhanced_email_service import EmailTemplateManager
from models.models import Pet, User
from email_utils import send_email


class PetEmailService:
    """Service for processing pet-related email notifications"""
    
    @staticmethod
    def process_pet_email(queue_item: EmailQueue, email_type: str, metadata: Dict[str, Any]) -> bool:
        """Process a pet-related email from the queue"""
        try:
            if email_type == "pet_search_notification":
                return PetEmailService._process_search_notification(queue_item, metadata)
            elif email_type == "pet_found_contact":
                return PetEmailService._process_found_contact(queue_item, metadata)
            else:
                logger.warning(f"Unknown pet email type: {email_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing pet email {email_type}: {e}")
            return False
    
    @staticmethod
    def _process_search_notification(queue_item: EmailQueue, metadata: Dict[str, Any]) -> bool:
        """Process pet search notification email"""
        try:
            # Get template
            template = EmailTemplate.query.filter_by(
                name='pet_search_notification',
                is_active=True
            ).first()
            
            if not template:
                logger.error("Pet search notification template not found")
                return False
            
            # Load pet and owner data
            pet = Pet.query.get(metadata.get('pet_id'))
            owner = User.query.get(queue_item.user_id)
            
            if not pet or not owner:
                logger.error(f"Pet {metadata.get('pet_id')} or owner {queue_item.user_id} not found")
                return False
            
            # Prepare template inputs
            inputs = {
                'pet_name': pet.name,
                'pet_id': pet.id,
                'owner_name': owner.first_name,
                'tag_id': metadata.get('tag_id'),
                'search_timestamp': metadata.get('search_timestamp'),
                'system': {
                    'app_name': 'LTFPQRR',
                    'site_url': 'https://ltfpqrr.com',  # TODO: Get from config
                    'support_email': 'support@ltfpqrr.com'  # TODO: Get from config
                }
            }
            
            # Render template
            rendered = template.render_content(inputs, {'pet': pet, 'owner': owner})
            
            # Update queue item with rendered content
            queue_item.html_body = rendered['html_content']
            queue_item.text_body = rendered['text_content']
            queue_item.subject = rendered['subject']
            
            # Send email
            success = send_email(
                to_email=queue_item.to_email,
                subject=rendered['subject'],
                html_body=rendered['html_content'],
                text_body=rendered['text_content']
            )
            
            if success:
                queue_item.mark_sent()
                logger.info(f"Pet search notification email sent to {queue_item.to_email}")
            else:
                error_msg = "Failed to send pet search notification email"
                queue_item.mark_failed(error_msg)
                logger.error(error_msg)
            
            db.session.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error processing pet search notification: {e}")
            queue_item.mark_failed(str(e))
            db.session.commit()
            return False
    
    @staticmethod
    def _process_found_contact(queue_item: EmailQueue, metadata: Dict[str, Any]) -> bool:
        """Process pet found contact email"""
        try:
            # Get template
            template = EmailTemplate.query.filter_by(
                name='pet_found_contact',
                is_active=True
            ).first()
            
            if not template:
                logger.error("Pet found contact template not found")
                return False
            
            # Load pet and owner data
            pet = Pet.query.get(metadata.get('pet_id'))
            owner = User.query.get(queue_item.user_id)
            
            if not pet or not owner:
                logger.error(f"Pet {metadata.get('pet_id')} or owner {queue_item.user_id} not found")
                return False
            
            # Prepare template inputs
            inputs = {
                'pet_name': pet.name,
                'pet_id': pet.id,
                'owner_name': owner.first_name,
                'finder_name': metadata.get('finder_name'),
                'finder_email': metadata.get('finder_email'),
                'message': metadata.get('message'),
                'system': {
                    'app_name': 'LTFPQRR',
                    'site_url': 'https://ltfpqrr.com',  # TODO: Get from config
                    'support_email': 'support@ltfpqrr.com'  # TODO: Get from config
                }
            }
            
            # Render template
            rendered = template.render_content(inputs, {'pet': pet, 'owner': owner})
            
            # Update queue item with rendered content
            queue_item.html_body = rendered['html_content']
            queue_item.text_body = rendered['text_content']
            queue_item.subject = rendered['subject']
            
            # Send email with finder's email as reply-to
            success = send_email(
                to_email=queue_item.to_email,
                subject=rendered['subject'],
                html_body=rendered['html_content'],
                text_body=rendered['text_content'],
                reply_to=metadata.get('finder_email')
            )
            
            if success:
                queue_item.mark_sent()
                logger.info(f"Pet found contact email sent to {queue_item.to_email}")
            else:
                error_msg = "Failed to send pet found contact email"
                queue_item.mark_failed(error_msg)
                logger.error(error_msg)
            
            db.session.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error processing pet found contact: {e}")
            queue_item.mark_failed(str(e))
            db.session.commit()
            return False


def register_pet_email_processor():
    """Register pet email processor with the main email service"""
    try:
        from services.email_service import EmailManager
        
        # Add custom processor for pet emails
        if hasattr(EmailManager, 'custom_processors'):
            EmailManager.custom_processors['pet_search_notification'] = PetEmailService.process_pet_email
            EmailManager.custom_processors['pet_found_contact'] = PetEmailService.process_pet_email
        else:
            logger.warning("EmailManager doesn't support custom processors")
            
    except Exception as e:
        logger.error(f"Error registering pet email processor: {e}")
