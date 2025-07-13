"""
Tag management routes
"""
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from forms import TagForm, ClaimTagForm, TransferTagForm, ContactOwnerForm

tag = Blueprint('tag', __name__, url_prefix='/tag')


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

    return render_template("tag/claim.html", form=form)


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

    pet = Pet.query.get(tag_obj.pet_id)
    owner = User.query.get(pet.owner_id)

    form = ContactOwnerForm()
    if form.validate_on_submit():
        # Send email to owner
        send_contact_email(
            owner, pet, form.finder_name.data, form.finder_email.data, form.message.data
        )

        flash("Your message has been sent to the pet owner.", "success")
        return redirect(url_for("tag.found_pet", tag_id=tag_id))

    return render_template("found/contact.html", form=form, pet=pet, tag=tag_obj)
