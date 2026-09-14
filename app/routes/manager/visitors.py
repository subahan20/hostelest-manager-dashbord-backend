from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.visitor_schema import CreateVisitorSchema, UpdateVisitorSchema
from app.services.visitor_service import VisitorService
from app.utils.responses import success_response, error_response

visitors_bp = Blueprint("visitors", __name__)
create_visitor_schema = CreateVisitorSchema()
update_visitor_schema = UpdateVisitorSchema()


@visitors_bp.route("/visitors", methods=["GET"])
@manager_required
def get_visitors():
    """
    List visitor logs with date range and student filters.
    
    Query Params:
        hostel_id, student_id, from_date, to_date, page, limit
    """
    items, pagination, err_msg, status_code = VisitorService.get_visitors(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        student_id=request.args.get("student_id"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Visitor logs fetched successfully",
        status_code=200,
    )


@visitors_bp.route("/visitors/<visitor_id>", methods=["GET"])
@manager_required
def get_visitor(visitor_id):
    """Get single visitor record details by ID."""
    visitor, err_msg, status_code = VisitorService.get_visitor_by_id(
        g.current_manager, visitor_id
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=visitor, message="Visitor log details fetched successfully")


@visitors_bp.route("/visitors", methods=["POST"])
@manager_required
def create_visitor():
    """Register a new visitor check-in."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_visitor_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    visitor, err_msg, status_code = VisitorService.create_visitor(
        g.current_manager, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=visitor, message="Visitor check-in registered successfully", status_code=201)


@visitors_bp.route("/visitors/<visitor_id>", methods=["PUT"])
@manager_required
def update_visitor(visitor_id):
    """Update visitor log details."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_visitor_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    visitor, err_msg, status_code = VisitorService.update_visitor(
        g.current_manager, visitor_id, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=visitor, message="Visitor log updated successfully", status_code=200)


@visitors_bp.route("/visitors/<visitor_id>/checkout", methods=["POST"])
@manager_required
def checkout_visitor(visitor_id):
    """Record checkout for a visitor."""
    visitor, err_msg, status_code = VisitorService.checkout_visitor(
        g.current_manager, visitor_id
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=visitor, message="Visitor checkout recorded successfully", status_code=200)
