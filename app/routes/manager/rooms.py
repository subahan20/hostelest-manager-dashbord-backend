from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.room_schema import CreateRoomSchema, UpdateRoomSchema, UpdateRoomStatusSchema
from app.services.room_service import RoomService
from app.utils.responses import success_response, error_response

rooms_bp = Blueprint("rooms", __name__)
create_room_schema = CreateRoomSchema()
update_room_schema = UpdateRoomSchema()
update_status_schema = UpdateRoomStatusSchema()


@rooms_bp.route("/rooms", methods=["GET"])
@manager_required
def get_rooms():
    """
    List rooms with search, filters, and pagination.
    
    Query Params:
        hostel_id, status, floor, room_type, search, page, limit
    """
    floor = request.args.get("floor", type=int)

    items, pagination, err_msg, status_code = RoomService.get_rooms(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        status=request.args.get("status"),
        floor=floor,
        room_type=request.args.get("room_type"),
        search=request.args.get("search"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Rooms fetched successfully",
        status_code=200,
    )


@rooms_bp.route("/rooms/<room_id>", methods=["GET"])
@manager_required
def get_room(room_id):
    """Get single room details by ID."""
    room, err_msg, status_code = RoomService.get_room_by_id(g.current_manager, room_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=room, message="Room details fetched successfully")


@rooms_bp.route("/rooms", methods=["POST"])
@manager_required
def create_room():
    """Create a new room."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_room_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    room, err_msg, status_code = RoomService.create_room(g.current_manager, data)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=room, message="Room created successfully", status_code=201)


@rooms_bp.route("/rooms/<room_id>", methods=["PUT"])
@manager_required
def update_room(room_id):
    """Update room details."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_room_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    room, err_msg, status_code = RoomService.update_room(g.current_manager, room_id, data)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=room, message="Room updated successfully", status_code=200)


@rooms_bp.route("/rooms/<room_id>/status", methods=["PATCH"])
@manager_required
def update_room_status(room_id):
    """Update room operational status."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_status_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    room, err_msg, status_code = RoomService.update_room_status(
        g.current_manager, room_id, data["status"]
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=room, message="Room status updated successfully", status_code=200)
