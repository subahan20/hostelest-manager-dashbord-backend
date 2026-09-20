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

        # If user not found in users table, check if Owner Dashboard created it in managers table
        if not user:
            try:
                from sqlalchemy import text
                mgr_row = db.session.execute(
                    text("SELECT id, user_id, name, email, phone, password_hash, hostel_id, is_active FROM managers WHERE lower(email) = :email ORDER BY created_at DESC LIMIT 1"),
                    {"email": email}
                ).mappings().first()

                if mgr_row and mgr_row.get("password_hash"):
                    mgr_hash = mgr_row["password_hash"]
                    valid = False
                    if mgr_hash.startswith(("$2a$", "$2b$", "$2y$")):
                        try:
                            import bcrypt
                            if bcrypt.checkpw(password.encode("utf-8"), mgr_hash.encode("utf-8")):
                                valid = True
                        except Exception:
                            pass
                    if not valid:
                        try:
                            from werkzeug.security import check_password_hash
                            if check_password_hash(mgr_hash, password):
                                valid = True
                        except Exception:
                            pass
                    if not valid and mgr_hash == password:
                        valid = True

                    if valid:
                        # Auto-create User in users table and link
                        import uuid
                        new_user_id = str(uuid.uuid4())
                        user = User(
                            id=new_user_id,
                            name=mgr_row.get("name") or "Staff Manager",
                            email=email,
                            phone=mgr_row.get("phone"),
                            password_hash=mgr_hash,
                            role="manager",
                            is_active=bool(mgr_row.get("is_active", True))
                        )
                        db.session.add(user)
                        db.session.flush()

                        # Update manager row with user_id
                        db.session.execute(
                            text("UPDATE managers SET user_id = :uid WHERE id = :mid OR lower(email) = :email"),
                            {"uid": user.id, "mid": mgr_row["id"], "email": email}
                        )

                        # Create ManagerHostel link if hostel_id is present
                        if mgr_row.get("hostel_id"):
                            from app.models.manager_hostel import ManagerHostel
                            try:
                                mh = ManagerHostel(
                                    manager_id=mgr_row["id"] if mgr_row.get("id") else user.id,
                                    hostel_id=mgr_row["hostel_id"],
                                    status="active"
                                )
                                db.session.add(mh)
                            except Exception:
                                pass

                        db.session.commit()
            except Exception as e:
                db.session.rollback()

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
        role_str = str(user.role or "").lower()

        if role_str in ("manager", "hostel_manager"):
            manager = user.manager
            if not manager:
                manager = Manager.query.filter_by(user_id=user.id).first()
            if not manager:
                try:
                    manager = Manager(user_id=user.id)
                    db.session.add(manager)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    manager = Manager.query.filter_by(user_id=user.id).first()

            if manager:
                user_data["manager_profile"] = manager.to_dict(include_hostels=True)
        elif role_str == "owner" and user.owner:
            user_data["owner_profile"] = user.owner.to_dict()

        return user_data
