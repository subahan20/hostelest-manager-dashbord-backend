from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.schemas.auth_schema import LoginSchema
from app.services.auth_service import AuthService
from app.utils.responses import success_response, error_response

auth_bp = Blueprint("auth", __name__)
login_schema = LoginSchema()


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user with email & password.
    Returns access and refresh JWT tokens alongside user profile.
    """
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = login_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(
            message="Validation error",
            status_code=422,
            errors=err.messages,
        )

    result, error_msg, status_code = AuthService.authenticate_user(
        email=data["email"],
        password=data["password"],
    )

    if error_msg:
        return error_response(message=error_msg, status_code=status_code)

    return success_response(
        data=result,
        message="Login successful",
        status_code=200,
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Generate a new access token using a valid refresh token.
    """
    user_id = get_jwt_identity()
    result, error_msg, status_code = AuthService.refresh_access_token(user_id)

    if error_msg:
        return error_response(message=error_msg, status_code=status_code)

    return success_response(
        data=result,
        message="Token refreshed successfully",
        status_code=200,
    )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Log out the current user session.
    """
    return success_response(message="Logged out successfully", status_code=200)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Retrieve authenticated user's current profile and role information.
    """
    user_id = get_jwt_identity()
    result, error_msg, status_code = AuthService.get_current_user_profile(user_id)

    if error_msg:
        return error_response(message=error_msg, status_code=status_code)

    return success_response(
        data=result,
        message="User profile retrieved successfully",
        status_code=200,
    )
