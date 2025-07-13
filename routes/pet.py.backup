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
    form.tag_id.choices = [(tag.id, tag.tag_id) for tag in available_tags]

    if form.validate_on_submit():
        # Handle file upload
        photo_filename = None
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_filename = f"{uuid.uuid4()}_{photo_filename}"
            form.photo.data.save(
                os.path.join(current_app.config["UPLOAD_FOLDER"], photo_filename)
            )

        pet_obj = Pet(
            name=form.name.data,
            breed=form.breed.data,
            color=form.color.data,
            photo=photo_filename,
            vet_name=form.vet_name.data,
            vet_phone=form.vet_phone.data,
            vet_address=form.vet_address.data,
            groomer_name=form.groomer_name.data,
            groomer_phone=form.groomer_phone.data,
            groomer_address=form.groomer_address.data,
            owner_id=current_user.id,
        )

        db.session.add(pet_obj)
        db.session.commit()

        # Assign tag to pet
        if form.tag_id.data:
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

    form = PetForm(obj=pet_obj)

    if form.validate_on_submit():
        # Handle file upload
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_filename = f"{uuid.uuid4()}_{photo_filename}"
            form.photo.data.save(
                os.path.join(current_app.config["UPLOAD_FOLDER"], photo_filename)
            )

            # Delete old photo if it exists
            if pet_obj.photo:
                old_photo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], pet_obj.photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)

            pet_obj.photo = photo_filename

        pet_obj.name = form.name.data
        pet_obj.breed = form.breed.data
        pet_obj.color = form.color.data
        pet_obj.vet_name = form.vet_name.data
        pet_obj.vet_phone = form.vet_phone.data
        pet_obj.vet_address = form.vet_address.data
        pet_obj.groomer_name = form.groomer_name.data
        pet_obj.groomer_phone = form.groomer_phone.data
        pet_obj.groomer_address = form.groomer_address.data

        db.session.commit()

        flash("Pet updated successfully!", "success")
        return redirect(url_for("dashboard.customer_dashboard"))

    return render_template("pet/edit.html", form=form, pet=pet_obj)
