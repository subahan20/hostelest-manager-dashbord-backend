from marshmallow import Schema, fields, validate
from app.models.student import StudentStatus


class CreateStudentSchema(Schema):
    """Schema for registering a new student."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    room_id = fields.UUID(required=False, allow_none=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=False, allow_none=True)
    phone = fields.String(required=True, validate=validate.Length(min=5, max=20))
    alternate_phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    gender = fields.String(required=False, allow_none=True, validate=validate.OneOf(["male", "female", "other"]))
    date_of_birth = fields.Date(required=False, allow_none=True)
    college = fields.String(required=False, allow_none=True, validate=validate.Length(max=150))
    company = fields.String(required=False, allow_none=True, validate=validate.Length(max=150))
    occupation = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    address = fields.String(required=False, allow_none=True)
    emergency_contact_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    emergency_contact_phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    joining_date = fields.Date(required=True, error_messages={"required": "Joining date is required."})
    leaving_date = fields.Date(required=False, allow_none=True)
    status = fields.String(
        required=False,
        load_default=StudentStatus.ACTIVE,
        validate=validate.OneOf(StudentStatus.ALL_STATUSES),
    )


class UpdateStudentSchema(Schema):
    """Schema for updating student information."""
    room_id = fields.UUID(required=False, allow_none=True)
    name = fields.String(required=False, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=False, allow_none=True)
    phone = fields.String(required=False, validate=validate.Length(min=5, max=20))
    alternate_phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    gender = fields.String(required=False, allow_none=True, validate=validate.OneOf(["male", "female", "other"]))
    date_of_birth = fields.Date(required=False, allow_none=True)
    college = fields.String(required=False, allow_none=True, validate=validate.Length(max=150))
    company = fields.String(required=False, allow_none=True, validate=validate.Length(max=150))
    occupation = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    address = fields.String(required=False, allow_none=True)
    emergency_contact_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    emergency_contact_phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    leaving_date = fields.Date(required=False, allow_none=True)
    status = fields.String(required=False, validate=validate.OneOf(StudentStatus.ALL_STATUSES))


class UpdateStudentStatusSchema(Schema):
    """Schema for updating student status."""
    status = fields.String(required=True, validate=validate.OneOf(StudentStatus.ALL_STATUSES))
