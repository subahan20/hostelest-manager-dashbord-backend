from marshmallow import Schema, fields, validate
from app.models.booking import BookingStatus


class CreateBookingSchema(Schema):
    """Schema for creating a new booking."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    room_id = fields.UUID(required=False, allow_none=True)
    student_id = fields.UUID(required=True, error_messages={"required": "Student ID is required."})
    check_in_date = fields.Date(required=True, error_messages={"required": "Check-in date is required."})
    expected_check_out_date = fields.Date(required=False, allow_none=True)
    amount = fields.Float(required=False, load_default=0.0, validate=validate.Range(min=0.0))
    security_deposit = fields.Float(required=False, load_default=0.0, validate=validate.Range(min=0.0))
    status = fields.String(
        required=False,
        load_default=BookingStatus.PENDING,
        validate=validate.OneOf(BookingStatus.ALL_STATUSES),
    )


class RejectBookingSchema(Schema):
    """Schema for rejecting a booking."""
    reason = fields.String(required=False, allow_none=True)
