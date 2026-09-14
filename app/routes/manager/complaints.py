from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.complaint_schema import (
    CreateComplaintSchema,
    UpdateComplaintStatusSchema,
    ResolveComplaintSchema,
)
from app.services.complaint_service import ComplaintService
from app.utils.responses import success_response, error_response

complaints_bp = Blueprint("complaints", __name__)
create_complaint_schema = CreateComplaintSchema()
update_status_schema = UpdateComplaintStatusSchema()
resolve_schema = ResolveComplaintSchema()


@complaints_bp.route("/complaints", methods=["GET"])
@manager_required
def get_complaints():
    """
    List complaints with status, priority, and date range filters.
    
    Query Params:
        hostel_id, student_id, status, priority, from_date, to_date, page, limit
    """
    items, pagination, err_msg, status_code = ComplaintService.get_complaints(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        student_id=request.args.get("student_id"),
        status=request.args.get("status"),
        priority=request.args.get("priority"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Complaints fetched successfully",
        status_code=200,
    )


@complaints_bp.route("/complaints/<complaint_id>", methods=["GET"])
@manager_required
def get_complaint(complaint_id):
    """Get single complaint details by ID."""
    complaint, err_msg, status_code = ComplaintService.get_complaint_by_id(
        g.current_manager, complaint_id
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=complaint, message="Complaint details fetched successfully")


@complaints_bp.route("/complaints", methods=["POST"])
@manager_required
def create_complaint():
    """Create a new complaint."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_complaint_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    complaint, err_msg, status_code = ComplaintService.create_complaint(
        g.current_manager, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=complaint, message="Complaint registered successfully", status_code=201)


@complaints_bp.route("/complaints/<complaint_id>/status", methods=["PATCH"])
@manager_required
def update_complaint_status(complaint_id):
    """Update complaint status and assigned staff."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_status_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    complaint, err_msg, status_code = ComplaintService.update_complaint_status(
        g.current_manager, complaint_id, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=complaint, message="Complaint status updated successfully", status_code=200)


@complaints_bp.route("/complaints/<complaint_id>/resolve", methods=["POST"])
@manager_required
def resolve_complaint(complaint_id):
    """Mark complaint as resolved with resolution notes."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = resolve_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    complaint, err_msg, status_code = ComplaintService.resolve_complaint(
        g.current_manager, complaint_id, data["resolution_notes"]
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=complaint, message="Complaint resolved successfully", status_code=200)
