from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.notice_schema import CreateNoticeSchema, UpdateNoticeSchema
from app.services.notice_service import NoticeService
from app.utils.responses import success_response, error_response

notices_bp = Blueprint("notices", __name__)
create_notice_schema = CreateNoticeSchema()
update_notice_schema = UpdateNoticeSchema()


@notices_bp.route("/notices", methods=["GET"])
@manager_required
def get_notices():
    """
    List notices with status and priority filters.
    
    Query Params:
        hostel_id, status, priority, page, limit
    """
    items, pagination, err_msg, status_code = NoticeService.get_notices(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        status=request.args.get("status"),
        priority=request.args.get("priority"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Notices fetched successfully",
        status_code=200,
    )


@notices_bp.route("/notices/<notice_id>", methods=["GET"])
@manager_required
def get_notice(notice_id):
    """Get single notice details by ID."""
    notice, err_msg, status_code = NoticeService.get_notice_by_id(
        g.current_manager, notice_id
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=notice, message="Notice details fetched successfully")


@notices_bp.route("/notices", methods=["POST"])
@manager_required
def create_notice():
    """Create a new notice."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_notice_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    notice, err_msg, status_code = NoticeService.create_notice(
        g.current_manager, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=notice, message="Notice created successfully", status_code=201)


@notices_bp.route("/notices/<notice_id>", methods=["PUT"])
@manager_required
def update_notice(notice_id):
    """Update an existing notice."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_notice_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    notice, err_msg, status_code = NoticeService.update_notice(
        g.current_manager, notice_id, data
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=notice, message="Notice updated successfully", status_code=200)


@notices_bp.route("/notices/<notice_id>", methods=["DELETE"])
@manager_required
def delete_notice(notice_id):
    """Delete a notice."""
    ok, err_msg, status_code = NoticeService.delete_notice(
        g.current_manager, notice_id
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(message="Notice deleted successfully", status_code=200)
