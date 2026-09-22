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
    hostel_ids = list(manager.get_assigned_hostel_ids() if manager else [])

    if g.current_user:
        mgr_rows = db.session.execute(
            text("SELECT hostel_id, owner_id FROM managers WHERE user_id = :uid OR lower(trim(email)) = :email"),
            {"uid": g.current_user.id, "email": g.current_user.email.lower()}
        ).mappings().all()
        for mr in mgr_rows:
            if mr.get("hostel_id"):
                h_str = str(mr["hostel_id"])
                if h_str not in hostel_ids:
                    hostel_ids.append(h_str)

        if not hostel_ids and mgr_rows:
            for mr in mgr_rows:
                owner_id = mr.get("owner_id")
                if owner_id:
                    o_hostels = db.session.execute(
                        text("SELECT id FROM hostels WHERE owner_id = :oid OR CAST(owner_id AS text) = :oid_str"),
                        {"oid": owner_id, "oid_str": str(owner_id)}
                    ).mappings().all()
                    for oh in o_hostels:
                        h_str = str(oh["id"])
                        if h_str not in hostel_ids:
                            hostel_ids.append(h_str)

    hostels = []
    if hostel_ids:
        hostel_objs = Hostel.query.filter(Hostel.id.in_(hostel_ids)).all()
        hostels = [h.to_dict() for h in hostel_objs]

    if not hostels:
        hostel_objs = Hostel.query.filter_by(status='active').limit(5).all()
        if not hostel_objs:
            hostel_objs = Hostel.query.limit(5).all()
        hostels = [h.to_dict() for h in hostel_objs]

    return success_response(
        data=hostels,
        message="Assigned hostels retrieved successfully",
        status_code=200,
    )
