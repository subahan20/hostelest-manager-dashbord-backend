from marshmallow import Schema, fields, validate
from app.models.payment import PaymentType, PaymentStatus, PaymentMethod


class CreatePaymentSchema(Schema):
    """Schema for creating a new invoice or payment record."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    student_id = fields.UUID(required=True, error_messages={"required": "Student ID is required."})
    booking_id = fields.UUID(required=False, allow_none=True)
    amount = fields.Float(required=True, validate=validate.Range(min=0.01), error_messages={"required": "Amount is required."})
    payment_type = fields.String(
        required=False,
        load_default=PaymentType.RENT,
        validate=validate.OneOf(PaymentType.ALL_TYPES),
    )
    payment_method = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(PaymentMethod.ALL_METHODS),
    )
    transaction_reference = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    due_date = fields.Date(required=False, allow_none=True)
    paid_at = fields.DateTime(required=False, allow_none=True)
    status = fields.String(
        required=False,
        load_default=PaymentStatus.PENDING,
        validate=validate.OneOf(PaymentStatus.ALL_STATUSES),
    )
    notes = fields.String(required=False, allow_none=True)


class RecordPaymentSchema(Schema):
    """Schema for recording a payment received against a pending invoice."""
    amount = fields.Float(required=False, validate=validate.Range(min=0.01))
    payment_method = fields.String(
        required=True,
        validate=validate.OneOf(PaymentMethod.ALL_METHODS),
        error_messages={"required": "Payment method is required."},
    )
    transaction_reference = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    paid_at = fields.DateTime(required=False, allow_none=True)
    notes = fields.String(required=False, allow_none=True)
