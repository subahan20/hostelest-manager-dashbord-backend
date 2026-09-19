from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models import User, UserRole, Manager


class AuthService:
    """Service handling authentication, token issuing, and profile queries."""

    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Authenticate user credentials and generate JWT tokens.
        
        Returns:
            (payload, error_message, status_code)
        """
        email = email.strip().lower()
        try:
            user = User.query.filter(User.email.ilike(email)).first()
        except Exception:
            db.session.rollback()
            try:
                db.create_all()
                from init_clean_db import init_clean_database
                init_clean_database()
                user = User.query.filter(User.email.ilike(email)).first()
            except Exception as e:
                return None, f"Database table initialization failed: {str(e)}", 500

        if not user or not user.check_password(password):
            return None, "Invalid email or password", 401

        if not user.is_active:
            return None, "Account is disabled. Please contact administrator.", 403

        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        # Generate JWT tokens with role claims
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

        user_data = AuthService.format_user_profile(user)

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data,
        }
        return response_data, None, 200

    @staticmethod
    def refresh_access_token(user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Issue a fresh access token for a valid active user.
        
        Returns:
            (payload, error_message, status_code)
        """
        user = db.session.get(User, user_id)
        if not user:
            return None, "User not found", 404

        if not user.is_active:
            return None, "Account is disabled", 403

        additional_claims = {"role": user.role}
        new_access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)

        return {"access_token": new_access_token}, None, 200

    @staticmethod
    def get_current_user_profile(user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Fetch the current user's profile with detailed role information.
        
        Returns:
            (payload, error_message, status_code)
        """
        user = db.session.get(User, user_id)
        if not user:
            return None, "User not found", 404

        if not user.is_active:
            return None, "Account is disabled", 403

        return AuthService.format_user_profile(user), None, 200

    @staticmethod
    def format_user_profile(user: User) -> Dict[str, Any]:
        """Format user model and any attached role profile into clean dictionary."""
        user_data = user.to_dict()

        if user.role == UserRole.MANAGER and user.manager:
            user_data["manager_profile"] = user.manager.to_dict(include_hostels=True)
        elif user.role == UserRole.OWNER and user.owner:
            user_data["owner_profile"] = user.owner.to_dict()

        return user_data
