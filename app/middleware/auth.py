from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import User, UserRole, Manager
from app.utils.responses import error_response


def get_current_user() -> User | None:
    """Retrieve the User instance corresponding to current JWT identity."""
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(fn):
    """
    Decorator to enforce valid JWT and active user account.
    Attaches authenticated User model to flask.g.current_user.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)

        if not user:
            return error_response(message="User not found", status_code=401)

        if not user.is_active:
            return error_response(message="Account is disabled", status_code=403)

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def manager_required(fn):
    """
    Decorator enforcing:
    1. Valid JWT token
    2. User exists & is active
    3. Role is manager
    4. Manager profile exists
    
    Attaches user to g.current_user and manager to g.current_manager.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)

        if not user:
            return error_response(message="User not found", status_code=401)

        if not user.is_active:
            return error_response(message="Account is disabled", status_code=403)

        if user.role != UserRole.MANAGER:
            return error_response(
                message="Forbidden - Manager access required",
                status_code=403,
            )

        manager = Manager.query.filter_by(user_id=user.id).first()
        if not manager:
            return error_response(
                message="Forbidden - Manager profile not found",
                status_code=403,
            )

        g.current_user = user
        g.current_manager = manager
        return fn(*args, **kwargs)

    return wrapper
