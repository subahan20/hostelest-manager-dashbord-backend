from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    """Schema for user authentication request payload."""
    email = fields.Email(required=True, error_messages={"required": "Email is required.", "invalid": "Invalid email address format."})
    password = fields.String(required=True, validate=validate.Length(min=1), error_messages={"required": "Password is required."})


class TokenRefreshSchema(Schema):
    """Optional schema if refresh token is passed in body."""
    refresh_token = fields.String(required=False)
