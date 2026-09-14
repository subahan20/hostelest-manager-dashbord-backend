from flask import Blueprint, request, g
from app.middleware.auth import manager_required
from app.services.dashboard_service import DashboardService
from app.utils.responses import success_response, error_response

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
@manager_required
def get_dashboard():
    """
    Retrieve real aggregated operational metrics for the manager dashboard.
    
    Query Parameters:
        hostel_id (optional): Specific hostel UUID.
            - If provided: returns metrics for that hostel (403 if unassigned).
            - If omitted: returns aggregated metrics across all assigned hostels.
    """
    requested_hostel_id = request.args.get("hostel_id")

    data, err_msg, status_code = DashboardService.get_dashboard_metrics(
        manager=g.current_manager,
        requested_hostel_id=requested_hostel_id,
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=data,
        message="Dashboard metrics fetched successfully",
        status_code=200,
    )
