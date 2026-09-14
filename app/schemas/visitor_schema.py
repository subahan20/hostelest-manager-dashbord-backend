from marshmallow import Schema, fields, validate
from app.models.visitor import VisitorIdType


class CreateVisitorSchema(Schema):
    """Schema for registering a visitor check-in."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    student_id = fields.UUID(required=True, error_messages={"required": "Student ID is required."})
    visitor_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    phone = fields.String(required=True, validate=validate.Length(min=5, max=20))
    purpose = fields.String(required=True, validate=validate.Length(min=1, max=200))
    id_type = fields.String(
        required=False,
        load_default=VisitorIdType.OTHER,
        validate=validate.OneOf(VisitorIdType.ALL_TYPES),
    )
    id_reference = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    check_in = fields.DateTime(required=False, allow_none=True)


class UpdateVisitorSchema(Schema):
    """Schema for updating visitor details or recording checkout."""
    visitor_name = fields.String(required=False, validate=validate.Length(min=1, max=100))
    phone = fields.String(required=False, validate=validate.Length(min=5, max=20))
    purpose = fields.String(required=False, validate=validate.Length(min=1, max=200))
    id_type = fields.String(required=False, validate=validate.OneOf(VisitorIdType.ALL_TYPES))
    id_reference = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    check_out = fields.DateTime(required=False, allow_none=True)
