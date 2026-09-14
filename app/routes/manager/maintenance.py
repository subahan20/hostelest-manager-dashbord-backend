from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.maintenance_schema import (
    CreateMaintenanceSchema,
    UpdateMaintenanceStatusSchema,
    AssignMaintenanceSchema,
)
from app.services.maintenance_service import MaintenanceService
from app.utils.responses import success_response, error_response

maintenance_bp = Blueprint("maintenance", __name__)
create_maintenance_schema = CreateMaintenanceSchema()
update_status_schema = UpdateMaintenanceStatusSchema()
assign_schema = AssignMaintenanceSchema()


@maintenance_bp.route("/maintenance", methods=["GET"])
@manager_required
def get_maintenance_requests():
    """
    List maintenance requests with category, priority, status, and room filters.
    
    Query Params:
        hostel_id, priority, status, category, room_id, from_date, to_date, page, limit
    """
    items, pagination, err_msg, status_code = MaintenanceService.get_maintenance_requests(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        priority=request.args.get("priority"),
        status=request.args.get("status"),
        category=request.args.get("category"),
        room_id=request.args.get("room_id"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Maintenance requests fetched successfully",
        status_code=200,
    )


@maintenance_bp.route("/maintenance/<maintenance_id>", methods=["GET"])
@manager_required
def get_maintenance(maintenance_id):
    """Get single maintenance request details by ID."""
    req, err_msg, status_code = MaintenanceService.get_maintenance_by_id(
        g.current_manager, maintenance_id
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=req, message="Maintenance request details fetched successfully")


@maintenance_bp.route("/maintenance", methods=["POST"])
@manager_required
def create_maintenance():
    """Create a new maintenance request."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_maintenance_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    req, err_msg, status_code = MaintenanceService.create_maintenance(
        g.current_manager, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=req, message="Maintenance request created successfully", status_code=201)


@maintenance_bp.route("/maintenance/<maintenance_id>/status", methods=["PATCH"])
@manager_required
def update_maintenance_status(maintenance_id):
    """Update maintenance status, actual cost, and notes."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_status_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    req, err_msg, status_code = MaintenanceService.update_maintenance_status(
        g.current_manager, maintenance_id, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=req, message="Maintenance status updated successfully", status_code=200)


@maintenance_bp.route("/maintenance/<maintenance_id>/assign", methods=["POST"])
@manager_required
def assign_maintenance(maintenance_id):
    """Assign maintenance request to a vendor or technician."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = assign_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    req, err_msg, status_code = MaintenanceService.assign_maintenance(
        g.current_manager, maintenance_id, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=req, message="Maintenance request assigned successfully", status_code=200)
