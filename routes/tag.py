"""
Tag management routes
"""
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from forms import TagForm, ClaimTagForm, TransferTagForm, ContactOwnerForm, PurchaseSubscriptionForm

tag = Blueprint('tag', __name__, url_prefix='/tag')


def get_tag_pricing_plans():
    """Get active tag pricing plans."""
    from models.payment.payment import PricingPlan
    
    plans = PricingPlan.query.filter_by(
        plan_type="tag",
        is_active=True
    ).order_by(PricingPlan.sort_order, PricingPlan.price).all()
    
    # Convert to dict for easy template access
    pricing_dict = {}
    for plan in plans:
        pricing_dict[plan.billing_period] = {
            'price': float(plan.price),
            'name': plan.name,
            'description': plan.description
        }
    
    return pricing_dict


@tag.route("/create", methods=["GET", "POST"])
@tag.route("/create/<int:partner_id>", methods=["GET", "POST"])
@login_required
def create_tag(partner_id=None):
    """Create a new tag."""
    from models.models import Partner, Tag
    from extensions import db
    
    if not current_user.has_partner_role():
        flash("Partner access required to create tags.", "error")
        return redirect(url_for("dashboard.dashboard"))

    # Get user's partners to choose from
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    if not owned_partners and not accessible_partners:
        flash("You need access to a partner account to create tags.", "error")
        return redirect(url_for("partner.management_dashboard"))

    # If partner_id provided, validate it
    selected_partner = None
    if partner_id:
        all_partners = owned_partners + accessible_partners
        selected_partner = next((p for p in all_partners if p.id == partner_id), None)
        if not selected_partner:
            flash("Invalid partner selected.", "error")
            return redirect(url_for("partner.management_dashboard"))

    form = TagForm()
    if form.validate_on_submit():
        # Get partner_id from form, URL parameter, or use first available partner
        form_partner_id = request.form.get("partner_id")
        if form_partner_id:
            partner_id = int(form_partner_id)
        elif not partner_id and owned_partners:
            partner_id = owned_partners[0].id
        elif not partner_id and accessible_partners:
            partner_id = accessible_partners[0].id
            
        partner = Partner.query.get(partner_id)
        if not partner or not partner.user_has_access(current_user):
            flash("Invalid partner selected or you don't have access.", "error")
            return render_template("tag/create.html", form=form, 
                                 owned_partners=owned_partners,
                                 accessible_partners=accessible_partners,
                                 selected_partner=selected_partner)
        
        # Check if partner can create tags
        if not partner.can_create_tags():
            flash("This partner cannot create more tags. Check subscription limits.", "error")
            return render_template("tag/create.html", form=form,
                                 owned_partners=owned_partners,
                                 accessible_partners=accessible_partners,
                                 selected_partner=selected_partner)

        tag_obj = Tag(
            tag_id=str(uuid.uuid4())[:8].upper(),
            created_by=current_user.id,
            partner_id=partner.id,
            status="pending",  # Tags start as pending, partners must activate them
        )
        db.session.add(tag_obj)
        db.session.commit()

        flash(
            f"Tag {tag_obj.tag_id} created successfully for {partner.company_name}! You can activate it from your partner dashboard.",
            "success",
        )
        return redirect(url_for("partner.dashboard", partner_id=partner.id))

    return render_template("tag/create.html", form=form,
                         owned_partners=owned_partners,
                         accessible_partners=accessible_partners,
                         selected_partner=selected_partner)


@tag.route("/activate/<int:tag_id>", methods=["POST"])
@login_required
def activate_tag(tag_id):
    """Activate a tag."""
    from models.models import Tag
    from extensions import db
    
    tag_obj = Tag.query.get_or_404(tag_id)

    # Check if current user has access to this tag's partner
    if tag_obj.partner and not tag_obj.partner.user_has_access(current_user):
        flash("You don't have access to this partner account.", "error")
        return redirect(url_for("partner.dashboard"))
    elif not tag_obj.partner and tag_obj.created_by != current_user.id:
        flash("You can only activate tags you created.", "error")
        return redirect(url_for("partner.dashboard"))

    # Check if partner can activate tags (has active subscription)
    if tag_obj.partner and not tag_obj.partner.has_active_subscription():
        flash("Partner needs an active subscription to activate tags.", "error")
        return redirect(url_for("partner.dashboard"))

    # Attempt to activate the tag
    if tag_obj.activate_by_partner():
        db.session.commit()
        flash(
            f"Tag {tag_obj.tag_id} has been activated and is now available for customers to claim!",
            "success",
        )
    else:
        flash(
            f"Unable to activate tag {tag_obj.tag_id}. It may already be activated.",
            "error",
        )

    return redirect(url_for("partner.dashboard"))


@tag.route("/deactivate/<int:tag_id>", methods=["POST"])
@login_required
def deactivate_tag(tag_id):
    """Deactivate a tag."""
    from models.models import Tag
    from extensions import db
    
    tag_obj = Tag.query.get_or_404(tag_id)

    # Check if current user is the creator of the tag
    if tag_obj.created_by != current_user.id:
        flash("You can only deactivate tags you created.", "error")
        return redirect(url_for("partner.dashboard"))

    # Only allow deactivation if tag is available (not claimed or active)
    if tag_obj.status == "available":
        tag_obj.status = "pending"
        tag_obj.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f"Tag {tag_obj.tag_id} has been deactivated.", "success")
    else:
        flash(
            f"Cannot deactivate tag {tag_obj.tag_id}. It may be claimed or already in use.",
            "error",
        )

    return redirect(url_for("partner.dashboard"))


@tag.route("/claim", methods=["GET", "POST"])
@login_required
def claim_tag():
    """Claim a tag."""
    from models.models import Tag
    from sqlalchemy import func
    
    # All users can claim tags (customer access)
    form = ClaimTagForm()
    if form.validate_on_submit():
        # Case-insensitive tag lookup
        tag_obj = Tag.query.filter(func.upper(Tag.tag_id) == func.upper(form.tag_id.data)).first()

        if not tag_obj:
            flash("Tag not found.", "error")
            return redirect(url_for("tag.claim_tag"))

        if tag_obj.status != "available":
            flash("Tag is not available for claiming.", "error")
            return redirect(url_for("tag.claim_tag"))

        # Store tag_id and subscription_type in session for payment
        session["claiming_tag_id"] = tag_obj.tag_id
        session["subscription_type"] = form.subscription_type.data

        return redirect(url_for("payment.tag_payment"))

    return render_template("tag/claim.html", form=form, pricing_plans=get_tag_pricing_plans())


@tag.route("/transfer/<int:tag_id>", methods=["GET", "POST"])
@login_required
def transfer_tag(tag_id):
    """Transfer a tag to another user."""
    from models.models import Tag, User
    from extensions import db
    
    tag_obj = Tag.query.get_or_404(tag_id)

    if tag_obj.owner_id != current_user.id:
        flash("You can only transfer tags you own.", "error")
        return redirect(url_for("dashboard.customer_dashboard"))

    form = TransferTagForm()
    if form.validate_on_submit():
        new_owner = User.query.filter_by(username=form.new_owner_username.data).first()

        if not new_owner:
            flash("User not found.", "error")
            return redirect(url_for("tag.transfer_tag", tag_id=tag_id))

        # Check if user has the 'user' role (which means they're a customer)
        if not new_owner.has_role("user"):
            flash("Tags can only be transferred to customer accounts.", "error")
            return redirect(url_for("tag.transfer_tag", tag_id=tag_id))

        # Transfer the tag
        tag_obj.owner_id = new_owner.id
        db.session.commit()

        flash(
            f"Tag {tag_obj.tag_id} transferred to {new_owner.username} successfully!",
            "success",
        )
        return redirect(url_for("dashboard.customer_dashboard"))

    return render_template("tag/transfer.html", form=form, tag=tag_obj)


@tag.route("/purchase_subscription/<int:tag_id>", methods=["GET", "POST"])
@login_required
def purchase_subscription(tag_id):
    """Purchase a subscription for an existing owned tag."""
    from models.models import Tag
    from forms import PurchaseSubscriptionForm
    
    tag_obj = Tag.query.get_or_404(tag_id)

    # Ensure user owns this tag
    if tag_obj.owner_id != current_user.id:
        flash("You can only purchase subscriptions for tags you own.", "error")
        return redirect(url_for("dashboard.customer_dashboard"))

    # Check if tag already has an active subscription
    active_subscriptions = [sub for sub in tag_obj.subscriptions if sub.is_active()]
    if active_subscriptions:
        flash("This tag already has an active subscription.", "info")
        return redirect(url_for("customer.manage_subscription", subscription_id=active_subscriptions[0].id))

    # Use the purchase subscription form
    form = PurchaseSubscriptionForm()
    
    if form.validate_on_submit():
        # Store tag_id and subscription_type in session for payment
        session["claiming_tag_id"] = tag_obj.tag_id
        session["subscription_type"] = form.subscription_type.data

        return redirect(url_for("payment.tag_payment"))

    return render_template("tag/purchase_subscription.html", form=form, tag=tag_obj, pricing_plans=get_tag_pricing_plans())


@tag.route("/found/<tag_id>")
def found_pet(tag_id):
    """Display found pet information."""
    from models.models import Tag, Pet, User, SearchLog, NotificationPreference
    from extensions import db
    from utils import send_notification_email
    from sqlalchemy import func
    
    # Case-insensitive tag lookup
    tag_obj = Tag.query.filter(func.upper(Tag.tag_id) == func.upper(tag_id)).first()

    if not tag_obj:
        return render_template("found/invalid_tag.html", tag_id=tag_id)

    if not tag_obj.pet_id:
        return render_template("found/not_registered.html", tag_id=tag_id)

    # Check if tag has an active subscription
    if not tag_obj.has_active_subscription():
        # Log the search even without active subscription
        search_log = SearchLog(
            tag_id=tag_obj.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
        db.session.add(search_log)
        db.session.commit()
        
        # Get owner and send notification about expired subscription access
        pet = Pet.query.get(tag_obj.pet_id)
        owner = User.query.get(pet.owner_id)
        
        # Check if owner wants notifications
        notification_pref = NotificationPreference.query.filter_by(
            user_id=owner.id, notification_type="tag_search"
        ).first()

        if notification_pref and notification_pref.enabled:
            send_notification_email(owner, tag_obj, pet, expired_subscription=True)
        
        return render_template("found/subscription_expired.html", tag_id=tag_id, tag=tag_obj)

    pet = Pet.query.get(tag_obj.pet_id)
    owner = User.query.get(pet.owner_id)

    # Log the search
    search_log = SearchLog(
        tag_id=tag_obj.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
    )
    db.session.add(search_log)
    db.session.commit()

    # Check if owner wants notifications
    notification_pref = NotificationPreference.query.filter_by(
        user_id=owner.id, notification_type="tag_search"
    ).first()

    if notification_pref and notification_pref.enabled:
        send_notification_email(owner, tag_obj, pet)

    return render_template("found/pet_info.html", pet=pet, owner=owner, tag=tag_obj)


@tag.route("/found/<tag_id>/contact", methods=["GET", "POST"])
def contact_owner(tag_id):
    """Contact pet owner."""
    from models.models import Tag, Pet, User
    from utils import send_contact_email
    from sqlalchemy import func
    
    # Case-insensitive tag lookup
    tag_obj = Tag.query.filter(func.upper(Tag.tag_id) == func.upper(tag_id)).first()

    if not tag_obj:
        return render_template("found/invalid_tag.html", tag_id=tag_id)

    if not tag_obj.pet_id:
        flash("This tag is not registered to a pet.", "error")
        return redirect(url_for("tag.found_pet", tag_id=tag_id))

    # Check if tag has an active subscription
    if not tag_obj.has_active_subscription():
        flash("This tag's subscription has expired and contact information is not available.", "error")
        return redirect(url_for("tag.found_pet", tag_id=tag_id))

    pet = Pet.query.get(tag_obj.pet_id)
    owner = User.query.get(pet.owner_id)

    form = ContactOwnerForm()
    if form.validate_on_submit():
        try:
            # Queue email for background processing
            send_contact_email(
                owner, pet, form.finder_name.data, form.finder_email.data, form.message.data
            )
            
            flash("Your message has been sent to the pet owner.", "success")
                
        except Exception as e:
            flash("There was an error sending your message. Please try again later.", "error")
            
        return redirect(url_for("tag.found_pet", tag_id=tag_id))

    return render_template("found/contact.html", form=form, pet=pet, tag=tag_obj)

# Batch Operations Routes
@tag.route("/batch/create", methods=["GET", "POST"])
@login_required
def batch_create():
    """Create multiple tags at once."""
    from models.models import Partner, Tag
    from forms import BatchTagCreateForm
    from extensions import db
    import uuid
    
    if not current_user.has_partner_role():
        flash("Partner access required to create tags.", "error")
        return redirect(url_for("dashboard.dashboard"))

    # Get user's partners to choose from
    owned_partners = current_user.get_owned_partners()
    accessible_partners = current_user.get_accessible_partners()
    
    if not owned_partners and not accessible_partners:
        flash("You need access to a partner account to create tags.", "error")
        return redirect(url_for("partner.management_dashboard"))

    form = BatchTagCreateForm()
    # Populate partner choices
    all_partners = owned_partners + accessible_partners
    form.partner_id.choices = [(p.id, p.company_name) for p in all_partners]
    
    if form.validate_on_submit():
        partner = Partner.query.get(form.partner_id.data)
        if not partner or not partner.user_has_access(current_user):
            flash("Invalid partner selected or you don't have access.", "error")
            return redirect(url_for("tag.batch_create"))
        
        # Check if partner can create the requested number of tags
        if not partner.can_create_tags():
            flash("This partner cannot create more tags. Check subscription limits.", "error")
            return redirect(url_for("tag.batch_create"))
        
        # Check specific quantity limits
        subscription = partner.get_active_subscription()
        if subscription:
            current_tag_count = partner.tags.count()
            # Only check if max_tags is positive (0 means unlimited)
            if subscription.max_tags > 0 and current_tag_count + form.quantity.data > subscription.max_tags:
                flash(f"Cannot create {form.quantity.data} tags. Partner subscription allows maximum {subscription.max_tags} tags. Currently have {current_tag_count} tags.", "error")
                return redirect(url_for("tag.batch_create"))
        
        # Create the tags
        created_tags = []
        try:
            for i in range(form.quantity.data):
                tag_obj = Tag(
                    tag_id=str(uuid.uuid4())[:8].upper(),
                    created_by=current_user.id,
                    partner_id=partner.id,
                    status="pending",
                )
                db.session.add(tag_obj)
                created_tags.append(tag_obj)
            
            db.session.commit()
            flash(f"Successfully created {len(created_tags)} tags for {partner.company_name}!", "success")
            return redirect(url_for("partner.dashboard", partner_id=partner.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating tags: {str(e)}", "error")
    
    return render_template("tag/batch_create.html", form=form, 
                         owned_partners=owned_partners,
                         accessible_partners=accessible_partners)

@tag.route("/batch/action", methods=["POST"])
@login_required 
def batch_action():
    """Perform bulk actions on multiple tags."""
    from models.models import Tag
    from forms import BatchTagActionForm
    from extensions import db
    from datetime import datetime
    import json
    import zipfile
    import tempfile
    import os
    import qrcode
    from io import BytesIO
    from flask import make_response
    
    if not current_user.has_partner_role():
        flash("Partner access required.", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    form = BatchTagActionForm()
    
    # Handle the case where there are multiple selected_tags fields (one empty, one with data)
    selected_tags_values = request.form.getlist('selected_tags')
    selected_tags_data = None
    for value in selected_tags_values:
        if value and value.strip():  # Find the non-empty value
            selected_tags_data = value
            break
    
    if not selected_tags_data:
        flash("No tags selected.", "error")
        return redirect(request.referrer or url_for("partner.dashboard"))
    
    # Override the form's selected_tags data with our found value
    form.selected_tags.data = selected_tags_data
    
    # Now validate just the action field since we handled selected_tags manually
    if form.action.data and selected_tags_data:
        try:
            # Parse selected tag IDs
            selected_tag_ids = json.loads(selected_tags_data)
            if not selected_tag_ids:
                flash("No tags selected.", "error")
                return redirect(request.referrer or url_for("partner.dashboard"))
            
            # Get the tags and verify access
            tags = Tag.query.filter(Tag.id.in_(selected_tag_ids)).all()
            if not tags:
                flash("No valid tags found.", "error")
                return redirect(request.referrer or url_for("partner.dashboard"))
            
            # Verify user has access to all tags
            for tag_obj in tags:
                if tag_obj.partner and not tag_obj.partner.user_has_access(current_user):
                    flash("You don't have access to some of the selected tags.", "error")
                    return redirect(request.referrer or url_for("partner.dashboard"))
                elif not tag_obj.partner and tag_obj.created_by != current_user.id:
                    flash("You don't have access to some of the selected tags.", "error")
                    return redirect(request.referrer or url_for("partner.dashboard"))
            
            # Perform the requested action
            if form.action.data == "activate":
                activated_count = 0
                for tag_obj in tags:
                    if tag_obj.status == "pending" and tag_obj.can_be_activated_by_partner():
                        if tag_obj.activate_by_partner():
                            activated_count += 1
                
                if activated_count > 0:
                    db.session.commit()
                    flash(f"Successfully activated {activated_count} tags.", "success")
                else:
                    flash("No tags were activated. Check that tags are pending and partner has active subscription.", "warning")
            
            elif form.action.data == "deactivate":
                deactivated_count = 0
                for tag_obj in tags:
                    if tag_obj.status == "available":
                        tag_obj.status = "pending"
                        tag_obj.updated_at = datetime.utcnow()
                        deactivated_count += 1
                
                if deactivated_count > 0:
                    db.session.commit()
                    flash(f"Successfully deactivated {deactivated_count} tags.", "success")
                else:
                    flash("No tags were deactivated. Only available tags can be deactivated.", "warning")
            
            elif form.action.data == "download_qr":
                return _generate_qr_zip(tags)
            
        except json.JSONDecodeError:
            flash("Invalid tag selection.", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error performing batch action: {str(e)}", "error")
    else:
        # Debug form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Form validation error in {field}: {error}", "error")
    
    return redirect(request.referrer or url_for("partner.dashboard"))

def _generate_qr_zip(tags):
    """Generate a ZIP file containing QR codes for the selected tags."""
    import zipfile
    import tempfile
    import os
    import qrcode
    from io import BytesIO
    from flask import make_response, current_app
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "qr_codes.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for tag_obj in tags:
                # Generate QR code
                qr_url = f"{request.host_url}found/{tag_obj.tag_id}"
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)
                
                # Create QR code image
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Save to bytes
                img_bytes = BytesIO()
                qr_img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Add to ZIP
                filename = f"QR_{tag_obj.tag_id}.png"
                zip_file.writestr(filename, img_bytes.getvalue())
        
        # Read the ZIP file and return as response
        with open(zip_path, 'rb') as zip_data:
            response = make_response(zip_data.read())
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename=qr_codes_{len(tags)}_tags.zip'
            return response

@tag.route("/qr/<int:tag_id>")
@login_required
def download_qr(tag_id):
    """Download QR code for individual tag."""
    from models.models import Tag
    import qrcode
    from io import BytesIO
    from flask import make_response
    
    tag_obj = Tag.query.get_or_404(tag_id)
    
    # Check if current user has access to this tag
    if tag_obj.partner and not tag_obj.partner.user_has_access(current_user):
        flash("You don't have access to this tag.", "error")
        return redirect(url_for("partner.dashboard"))
    elif not tag_obj.partner and tag_obj.created_by != current_user.id:
        flash("You can only download QR codes for tags you created.", "error")
        return redirect(url_for("partner.dashboard"))
    
    # Generate QR code
    qr_url = f"{request.host_url}found/{tag_obj.tag_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to bytes
    img_bytes = BytesIO()
    qr_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Return as downloadable file
    response = make_response(img_bytes.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'attachment; filename=QR_{tag_obj.tag_id}.png'
    return response
