from flask import Blueprint, g
from app.middleware.auth import manager_required
from app.models.hostel import Hostel
from app.models.manager import Manager
from app.utils.responses import success_response
from sqlalchemy import text
from app.extensions import db

hostels_bp = Blueprint("hostels", __name__)


@hostels_bp.route("/hostels/assigned", methods=["GET"])
@manager_required
def get_assigned_hostels():
    """Retrieve all hostel properties actively assigned to the logged-in manager."""
    manager = g.current_manager
    hostel_ids = manager.get_assigned_hostel_ids() if manager else []
    
    if not hostel_ids and g.current_user:
        mgr_row = db.session.execute(
            text("SELECT hostel_id FROM managers WHERE user_id = :uid OR lower(email) = :email"),
            {"uid": g.current_user.id, "email": g.current_user.email.lower()}
        ).first()
        if mgr_row and mgr_row[0]:
            hostel_ids = [str(mgr_row[0])]

    hostels = []
    if hostel_ids:
        hostel_objs = Hostel.query.filter(Hostel.id.in_(hostel_ids)).all()
        hostels = [h.to_dict() for h in hostel_objs]

    return success_response(
        data=hostels,
        message="Assigned hostels retrieved successfully",
        status_code=200,
    )
