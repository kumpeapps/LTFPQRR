"""
Pet management routes
"""
import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from forms import PetForm

pet = Blueprint('pet', __name__, url_prefix='/pet')

def handle_file_upload(file_data):
    """
    Handle file upload data that might be a single file or a list of files.
    Returns the filename if successful, None otherwise.
    """
    if not file_data:
        return None
    
    try:
        # Handle case where file_data is a list
        if isinstance(file_data, list):
            if len(file_data) == 0:
                return None
            file_obj = file_data[0]  # Take the first file
        else:
            file_obj = file_data
        
        # Check if file object has filename attribute
        if not hasattr(file_obj, "filename") or not file_obj.filename:
            current_app.logger.warning("File object missing filename attribute")
            return None
        
        # Generate secure filename
        photo_filename = secure_filename(file_obj.filename)
        if not photo_filename:  # secure_filename returned empty string
            current_app.logger.warning("Secure filename returned empty string")
            return None
            
        photo_filename = f"{uuid.uuid4()}_{photo_filename}"
        
        # Save the file
        file_obj.save(
            os.path.join(current_app.config["UPLOAD_FOLDER"], photo_filename)
        )
        
        return photo_filename
        
    except Exception as e:
        current_app.logger.error(f"Error handling file upload: {str(e)}")
        return None



@pet.route("/create", methods=["GET", "POST"])
@login_required
def create_pet():
    """Create a new pet."""
    from models.models import Tag, Pet
    from extensions import db
    
    # All users can create pets (customer access)
    form = PetForm()

    # Get user's available tags
    available_tags = Tag.query.filter_by(owner_id=current_user.id, pet_id=None).all()
    form.tag_id.choices = [(0, 'No Tag')] + [(tag.id, tag.tag_id) for tag in available_tags]

    if form.validate_on_submit():
        # Handle file upload
        photo_filename = handle_file_upload(form.photo.data)

        pet_obj = Pet(
            name=form.name.data,
            species=form.species.data,
            breed=form.breed.data,
            date_of_birth=form.date_of_birth.data,
            color=form.color.data,
            photo=photo_filename,
            vet_name=form.vet_name.data,
            vet_phone=form.vet_phone.data,
            vet_address=form.vet_address.data,
            vet_info_public=form.vet_info_public.data,
            groomer_name=form.groomer_name.data,
            groomer_phone=form.groomer_phone.data,
            groomer_address=form.groomer_address.data,
            groomer_info_public=form.groomer_info_public.data,
            phone_public=form.phone_public.data,
            owner_id=current_user.id,
        )

        db.session.add(pet_obj)
        db.session.commit()

        # Assign tag to pet
        if form.tag_id.data and form.tag_id.data != 0:
            tag = Tag.query.get(form.tag_id.data)
            if tag and tag.owner_id == current_user.id:
                tag.pet_id = pet_obj.id
                db.session.commit()

        flash("Pet created successfully!", "success")
        return redirect(url_for("dashboard.customer_dashboard"))

    return render_template("pet/create.html", form=form)


@pet.route("/edit/<int:pet_id>", methods=["GET", "POST"])
@login_required
def edit_pet(pet_id):
    """Edit an existing pet."""
    from models.models import Tag, Pet, Subscription
    from extensions import db
    
    pet_obj = Pet.query.get_or_404(pet_id)

    if pet_obj.owner_id != current_user.id:
        flash("You can only edit your own pets.", "error")
        return redirect(url_for("dashboard.customer_dashboard"))

    # Check if pet is on a lifetime subscription and restrictions apply
    tag = Tag.query.filter_by(pet_id=pet_obj.id).first()
    if tag:
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            tag_id=tag.id,
            subscription_type="lifetime",
            status="active",
        ).first()

        if subscription and subscription.restrictions_active:
            flash(
                "Pet name and details cannot be changed on active lifetime subscription.",
                "warning",
            )
            return redirect(url_for("dashboard.customer_dashboard"))

    # Get user's available tags for the dropdown first
    available_tags = Tag.query.filter_by(owner_id=current_user.id, pet_id=None).all()
    # Include the currently assigned tag if there is one
    current_tag = Tag.query.filter_by(pet_id=pet_obj.id).first()
    if current_tag:
        available_tags.append(current_tag)
    
    form = PetForm(obj=pet_obj)
    # Set choices before validation
    form.tag_id.choices = [(0, 'No Tag')] + [(tag.id, tag.tag_id) for tag in available_tags]
    
    # Set the current tag as selected if this is a GET request
    if request.method == 'GET':
        if current_tag:
            form.tag_id.data = current_tag.id
        else:
            form.tag_id.data = 0

    if form.validate_on_submit():
        print(f"DEBUG: Form validated - tag_id.data: {form.tag_id.data}")
        # Handle file upload
        photo_filename = handle_file_upload(form.photo.data)
        
        if photo_filename:
            # Delete old photo if it exists
            if pet_obj.photo:
                old_photo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], pet_obj.photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)

            pet_obj.photo = photo_filename

        pet_obj.name = form.name.data
        pet_obj.species = form.species.data
        pet_obj.breed = form.breed.data
        pet_obj.date_of_birth = form.date_of_birth.data
        pet_obj.color = form.color.data
        pet_obj.vet_name = form.vet_name.data
        pet_obj.vet_phone = form.vet_phone.data
        pet_obj.vet_address = form.vet_address.data
        pet_obj.vet_info_public = form.vet_info_public.data
        pet_obj.groomer_name = form.groomer_name.data
        pet_obj.groomer_phone = form.groomer_phone.data
        pet_obj.groomer_address = form.groomer_address.data
        pet_obj.groomer_info_public = form.groomer_info_public.data
        pet_obj.phone_public = form.phone_public.data

        # Handle tag assignment
        # First, remove pet from any existing tag
        existing_tag = Tag.query.filter_by(pet_id=pet_obj.id).first()
        if existing_tag:
            existing_tag.pet_id = None
            print(f"DEBUG: Removed pet {pet_obj.id} from existing tag {existing_tag.tag_id}")
        
        # Assign to new tag if selected
        if form.tag_id.data and form.tag_id.data != 0:
            new_tag = Tag.query.get(form.tag_id.data)
            if new_tag and new_tag.owner_id == current_user.id:
                new_tag.pet_id = pet_obj.id
                print(f"DEBUG: Assigned pet {pet_obj.id} to new tag {new_tag.tag_id}")
            else:
                print(f"DEBUG: Failed to assign tag - new_tag: {new_tag}, owner_id: {new_tag.owner_id if new_tag else 'N/A'}, current_user.id: {current_user.id}")
        else:
            print(f"DEBUG: No tag selected - form.tag_id.data: {form.tag_id.data}")

        db.session.commit()

        flash("Pet updated successfully!", "success")
        return redirect(url_for("dashboard.customer_dashboard"))
    else:
        if request.method == 'POST':
            print(f"DEBUG: Form validation failed. Errors: {form.errors}")
            print(f"DEBUG: tag_id choices: {form.tag_id.choices}")
            print(f"DEBUG: tag_id data: {form.tag_id.data}")

    return render_template("pet/edit.html", form=form, pet=pet_obj)
