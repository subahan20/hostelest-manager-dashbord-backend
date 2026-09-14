from flask import Blueprint, request, g
from app.middleware.auth import manager_required
from app.services.report_service import ReportService
from app.utils.responses import success_response, error_response

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports/occupancy", methods=["GET"])
@manager_required
def get_occupancy_report():
    """
    Get occupancy analytics breakdown by room type, floor, and hostel.
    
    Query Params:
        hostel_id (optional), from_date (optional), to_date (optional)
    """
    data, err_msg, status_code = ReportService.get_occupancy_report(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=data, message="Occupancy report fetched successfully")


@reports_bp.route("/reports/bookings", methods=["GET"])
@manager_required
def get_bookings_report():
    """
    Get booking trends, status distribution, and daily timeline for charts.
    
    Query Params:
        hostel_id (optional), from_date (optional), to_date (optional)
    """
    data, err_msg, status_code = ReportService.get_bookings_report(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=data, message="Bookings report fetched successfully")


@reports_bp.route("/reports/payments", methods=["GET"])
@manager_required
def get_payments_report():
    """
    Get financial revenue, collection vs pending, payment methods, and revenue timeline.
    
    Query Params:
        hostel_id (optional), from_date (optional), to_date (optional)
    """
    data, err_msg, status_code = ReportService.get_payments_report(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=data, message="Payments report fetched successfully")


@reports_bp.route("/reports/students", methods=["GET"])
@manager_required
def get_students_report():
    """
    Get student demographics, top colleges/companies, and admission/checkout counts.
    
    Query Params:
        hostel_id (optional), from_date (optional), to_date (optional)
    """
    data, err_msg, status_code = ReportService.get_students_report(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=data, message="Students report fetched successfully")
