from marshmallow import Schema, fields, validate
from app.models.maintenance import (
    MaintenanceCategory,
    MaintenancePriority,
    MaintenanceStatus,
)


class CreateMaintenanceSchema(Schema):
    """Schema for creating a maintenance request."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    room_id = fields.UUID(required=False, allow_none=True)
    student_id = fields.UUID(required=False, allow_none=True)
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(required=True, validate=validate.Length(min=3))
    category = fields.String(
        required=False,
        load_default=MaintenanceCategory.OTHER,
        validate=validate.OneOf(MaintenanceCategory.ALL_CATEGORIES),
    )
    priority = fields.String(
        required=False,
        load_default=MaintenancePriority.MEDIUM,
        validate=validate.OneOf(MaintenancePriority.ALL_PRIORITIES),
    )
    status = fields.String(
        required=False,
        load_default=MaintenanceStatus.PENDING,
        validate=validate.OneOf(MaintenanceStatus.ALL_STATUSES),
    )
    assigned_to = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    estimated_cost = fields.Float(required=False, load_default=0.0, validate=validate.Range(min=0.0))
    actual_cost = fields.Float(required=False, load_default=0.0, validate=validate.Range(min=0.0))
    notes = fields.String(required=False, allow_none=True)


class UpdateMaintenanceStatusSchema(Schema):
    """Schema for updating maintenance status and actual cost."""
    status = fields.String(required=True, validate=validate.OneOf(MaintenanceStatus.ALL_STATUSES))
    actual_cost = fields.Float(required=False, validate=validate.Range(min=0.0))
    notes = fields.String(required=False, allow_none=True)


class AssignMaintenanceSchema(Schema):
    """Schema for assigning maintenance to a vendor or technician."""
    assigned_to = fields.String(required=True, validate=validate.Length(min=1, max=100), error_messages={"required": "Assigned technician/vendor is required."})
    estimated_cost = fields.Float(required=False, validate=validate.Range(min=0.0))
    notes = fields.String(required=False, allow_none=True)
