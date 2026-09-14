from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.booking_schema import CreateBookingSchema, RejectBookingSchema
from app.services.booking_service import BookingService
from app.utils.responses import success_response, error_response

bookings_bp = Blueprint("bookings", __name__)
create_booking_schema = CreateBookingSchema()
reject_booking_schema = RejectBookingSchema()


@bookings_bp.route("/bookings", methods=["GET"])
@manager_required
def get_bookings():
    """
    List bookings with search, status filters, and pagination.
    
    Query Params:
        hostel_id, room_id, student_id, status, search, page, limit
    """
    items, pagination, err_msg, status_code = BookingService.get_bookings(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        room_id=request.args.get("room_id"),
        student_id=request.args.get("student_id"),
        status=request.args.get("status"),
        search=request.args.get("search"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Bookings fetched successfully",
        status_code=200,
    )


@bookings_bp.route("/bookings/<booking_id>", methods=["GET"])
@manager_required
def get_booking(booking_id):
    """Get single booking details by ID."""
    booking, err_msg, status_code = BookingService.get_booking_by_id(g.current_manager, booking_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=booking, message="Booking details fetched successfully")


@bookings_bp.route("/bookings", methods=["POST"])
@manager_required
def create_booking():
    """Create a new booking."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_booking_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    booking, err_msg, status_code = BookingService.create_booking(g.current_manager, data)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=booking, message="Booking created successfully", status_code=201)


@bookings_bp.route("/bookings/<booking_id>/approve", methods=["POST"])
@manager_required
def approve_booking(booking_id):
    """Approve a pending booking after verifying room capacity."""
    booking, err_msg, status_code = BookingService.approve_booking(g.current_manager, booking_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=booking, message="Booking approved successfully", status_code=200)


@bookings_bp.route("/bookings/<booking_id>/reject", methods=["POST"])
@manager_required
def reject_booking(booking_id):
    """Reject a booking."""
    reason = None
    if request.is_json:
        try:
            data = reject_booking_schema.load(request.get_json())
            reason = data.get("reason")
        except ValidationError as err:
            return error_response(message="Validation error", status_code=422, errors=err.messages)

    booking, err_msg, status_code = BookingService.reject_booking(g.current_manager, booking_id, reason)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=booking, message="Booking rejected successfully", status_code=200)


@bookings_bp.route("/bookings/<booking_id>/check-in", methods=["POST"])
@manager_required
def check_in_booking(booking_id):
    """
    Check-in student for a booking using transactional validation to prevent overbooking.
    """
    booking, err_msg, status_code = BookingService.check_in_booking(g.current_manager, booking_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=booking, message="Student checked in successfully", status_code=200)


@bookings_bp.route("/bookings/<booking_id>/check-out", methods=["POST"])
@manager_required
def check_out_booking(booking_id):
    """
    Check-out student, update room availability and booking status.
    """
    booking, err_msg, status_code = BookingService.check_out_booking(g.current_manager, booking_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=booking, message="Student checked out successfully", status_code=200)


@bookings_bp.route("/bookings/<booking_id>/cancel", methods=["POST"])
@manager_required
def cancel_booking(booking_id):
    """Cancel a booking."""
    booking, err_msg, status_code = BookingService.cancel_booking(g.current_manager, booking_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=booking, message="Booking cancelled successfully", status_code=200)
