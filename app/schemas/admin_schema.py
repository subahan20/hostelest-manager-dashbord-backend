from marshmallow import Schema, fields, validate, pre_load
from app.models.user import UserRole


class CreateAdminSchema(Schema):
    """Schema for super admin creating a new platform user / admin / manager."""
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "Name is required."},
    )
    email = fields.Email(
        required=True,
        validate=validate.Length(max=150),
        error_messages={"required": "Email is required."},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, max=100),
        error_messages={"required": "Password must be at least 6 characters."},
    )
    phone = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=5, max=50),
    )
    role = fields.String(
        required=False,
        load_default=UserRole.SUPER_ADMIN,
        validate=validate.OneOf(UserRole.ALL_ROLES),
    )
    is_active = fields.Boolean(
        required=False,
        load_default=True,
    )

    @pre_load
    def process_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = data.copy()

        # Handle aliases
        if "full_name" in data and not data.get("name"):
            data["name"] = data["full_name"]
            data.pop("full_name", None)

        if "phone_number" in data and not data.get("phone"):
            data["phone"] = data["phone_number"]
            data.pop("phone_number", None)

        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].strip()

        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].strip().lower()

        if "phone" in data:
            if isinstance(data["phone"], str):
                p = data["phone"].strip()
                data["phone"] = p if p else None
            elif data["phone"] == "":
                data["phone"] = None

        if "role" in data and isinstance(data["role"], str):
            data["role"] = data["role"].strip().lower()

        return data
