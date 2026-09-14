from marshmallow import Schema, fields, validate
from app.models.complaint import ComplaintPriority, ComplaintStatus


class CreateComplaintSchema(Schema):
    """Schema for creating a new complaint."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    student_id = fields.UUID(required=True, error_messages={"required": "Student ID is required."})
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(required=True, validate=validate.Length(min=3))
    priority = fields.String(
        required=False,
        load_default=ComplaintPriority.MEDIUM,
        validate=validate.OneOf(ComplaintPriority.ALL_PRIORITIES),
    )
    status = fields.String(
        required=False,
        load_default=ComplaintStatus.PENDING,
        validate=validate.OneOf(ComplaintStatus.ALL_STATUSES),
    )
    assigned_to = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))


class UpdateComplaintStatusSchema(Schema):
    """Schema for updating complaint status."""
    status = fields.String(required=True, validate=validate.OneOf(ComplaintStatus.ALL_STATUSES))
    assigned_to = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))


class ResolveComplaintSchema(Schema):
    """Schema for resolving a complaint."""
    resolution_notes = fields.String(required=True, validate=validate.Length(min=1), error_messages={"required": "Resolution notes are required."})
