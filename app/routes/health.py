from flask import Blueprint
from app.utils.responses import success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend service status."""
    return success_response(message="Hostelest API is running")


@health_bp.route("/setup-db", methods=["GET", "POST"])
def setup_database():
    """Explicitly create tables and seed manager account if not present."""
    from app.extensions import db
    from app.models.user import User
    from init_clean_db import init_clean_database

    try:
        db.create_all()
        user = User.query.filter_by(email="manager.hitech@hostelest.com").first()
        if not user:
            init_clean_database()
            return success_response(
                message="Database initialized successfully with Manager (manager.hitech@hostelest.com / Manager@123)"
            )
        return success_response(
            message="Database tables verified. Manager account is already present and active."
        )
    except Exception as e:
        from app.utils.responses import error_response
        return error_response(message=f"Database setup error: {str(e)}", status_code=500)

