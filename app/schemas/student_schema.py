from marshmallow import Schema, fields, validate, pre_load
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

    @pre_load
    def process_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = data.copy()

        # Map legacy/frontend aliases
        if "admission_date" in data:
            if not data.get("joining_date"):
                data["joining_date"] = data["admission_date"]
            data.pop("admission_date", None)

        if "dob" in data:
            if not data.get("date_of_birth"):
                data["date_of_birth"] = data["dob"]
            data.pop("dob", None)

        if "guardian_name" in data:
            if not data.get("emergency_contact_name"):
                data["emergency_contact_name"] = data["guardian_name"]
            data.pop("guardian_name", None)

        if "guardian_phone" in data:
            if not data.get("emergency_contact_phone"):
                data["emergency_contact_phone"] = data["guardian_phone"]
            data.pop("guardian_phone", None)

        if "college_or_company" in data:
            val = data.pop("college_or_company")
            if val and not data.get("college"):
                data["college"] = val

        # Normalize empty strings to None for optional typed fields
        for key in ["room_id", "email", "date_of_birth", "leaving_date", "alternate_phone"]:
            if key in data and (data[key] == "" or (isinstance(data[key], str) and not data[key].strip())):
                data[key] = None

        # Clean string inputs
        for key in ["name", "phone", "college", "company", "occupation", "address", "emergency_contact_name", "emergency_contact_phone"]:
            if key in data and isinstance(data[key], str):
                data[key] = data[key].strip()
                if not data[key] and key not in ("name", "phone"):
                    data[key] = None

        if "gender" in data:
            if isinstance(data["gender"], str):
                g = data["gender"].strip().lower()
                data["gender"] = g if g in ("male", "female", "other") else None
            elif data["gender"] is None or data["gender"] == "":
                data["gender"] = None

        if "status" in data and isinstance(data["status"], str):
            data["status"] = data["status"].strip().lower()

        return data


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

    @pre_load
    def process_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = data.copy()

        # Map legacy/frontend aliases
        if "dob" in data:
            if not data.get("date_of_birth"):
                data["date_of_birth"] = data["dob"]
            data.pop("dob", None)

        if "guardian_name" in data:
            if not data.get("emergency_contact_name"):
                data["emergency_contact_name"] = data["guardian_name"]
            data.pop("guardian_name", None)

        if "guardian_phone" in data:
            if not data.get("emergency_contact_phone"):
                data["emergency_contact_phone"] = data["guardian_phone"]
            data.pop("guardian_phone", None)

        if "college_or_company" in data:
            val = data.pop("college_or_company")
            if val and not data.get("college"):
                data["college"] = val

        # Normalize empty strings to None
        for key in ["room_id", "email", "date_of_birth", "leaving_date", "alternate_phone"]:
            if key in data and (data[key] == "" or (isinstance(data[key], str) and not data[key].strip())):
                data[key] = None

        for key in ["name", "phone", "college", "company", "occupation", "address", "emergency_contact_name", "emergency_contact_phone"]:
            if key in data and isinstance(data[key], str):
                data[key] = data[key].strip()
                if not data[key] and key not in ("name", "phone"):
                    data[key] = None

        if "gender" in data:
            if isinstance(data["gender"], str):
                g = data["gender"].strip().lower()
                data["gender"] = g if g in ("male", "female", "other") else None
            elif data["gender"] is None or data["gender"] == "":
                data["gender"] = None

        if "status" in data and isinstance(data["status"], str):
            data["status"] = data["status"].strip().lower()

        return data


class UpdateStudentStatusSchema(Schema):
    """Schema for updating student status."""
    status = fields.String(required=True, validate=validate.OneOf(StudentStatus.ALL_STATUSES))
