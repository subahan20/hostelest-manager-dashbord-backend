from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.extensions import db
from app.models import User, UserRole, Manager, Owner
from app.middleware.auth import super_admin_required
from app.schemas.admin_schema import CreateAdminSchema
from app.utils.responses import success_response, error_response

admin_bp = Blueprint("admin", __name__)
create_admin_schema = CreateAdminSchema()


@admin_bp.route("/users", methods=["POST"])
@admin_bp.route("/admins", methods=["POST"])
@super_admin_required
def create_admin():
    """
    Create a new platform user / admin / manager.
    Protected by super_admin_required.
    Managers or unauthorized users will receive 403 Forbidden.
    Duplicate email returns 409 Conflict.
    """
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_admin_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(
            message="Validation error",
            status_code=422,
            errors=err.messages,
        )

    clean_email = data["email"].strip().lower()

    # Check for duplicate email
    existing_user = User.query.filter(User.email.ilike(clean_email)).first()
    if existing_user:
        return error_response(
            message="A user with this email already exists",
            status_code=409,
        )

    # Check for duplicate phone if provided
    phone = data.get("phone")
    if phone:
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            return error_response(
                message="A user with this phone number already exists",
                status_code=409,
            )

    try:
        user = User(
            name=data["name"].strip(),
            email=clean_email,
            phone=phone,
            role=data.get("role", UserRole.SUPER_ADMIN),
            is_active=data.get("is_active", True),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.flush()

        # Create corresponding profile if manager or owner
        if user.role == UserRole.MANAGER:
            manager = Manager(user_id=user.id)
            db.session.add(manager)
        elif user.role == UserRole.OWNER:
            owner = Owner(user_id=user.id)
            db.session.add(owner)

        db.session.commit()

        return success_response(
            data=user.to_dict(),
            message="User created successfully",
            status_code=201,
        )
    except Exception as e:
        db.session.rollback()
        return error_response(
            message=f"Failed to create user: {str(e)}",
            status_code=500,
        )
