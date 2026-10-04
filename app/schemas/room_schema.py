from marshmallow import Schema, fields, validate, pre_load
from app.models.room import RoomType, RoomStatus


class CreateRoomSchema(Schema):
    """Schema for creating a new room."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    room_number = fields.String(required=True, validate=validate.Length(min=1, max=50))
    floor = fields.Integer(required=False, load_default=1, validate=validate.Range(min=0, max=100))
    room_type = fields.String(
        required=False,
        load_default=RoomType.DOUBLE,
        validate=validate.OneOf(RoomType.ALL_TYPES),
    )
    capacity = fields.Integer(required=False, load_default=2, validate=validate.Range(min=1, max=20))
    rent = fields.Float(required=True, validate=validate.Range(min=0.0), error_messages={"required": "Rent is required."})
    rent_amount = fields.Float(required=False, validate=validate.Range(min=0.0))
    status = fields.String(
        required=False,
        load_default=RoomStatus.AVAILABLE,
        validate=validate.OneOf(RoomStatus.ALL_STATUSES),
    )

    @pre_load
    def process_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = data.copy()
        if "hostel_id" in data and isinstance(data["hostel_id"], str):
            data["hostel_id"] = data["hostel_id"].strip()
        if "room_number" in data and isinstance(data["room_number"], str):
            data["room_number"] = data["room_number"].strip()
        if "rent_amount" in data and ("rent" not in data or data.get("rent") is None):
            data["rent"] = data["rent_amount"]
        elif "rent" in data and ("rent_amount" not in data or data.get("rent_amount") is None):
            data["rent_amount"] = data["rent"]
        return data


class UpdateRoomSchema(Schema):
    """Schema for updating room details."""
    room_number = fields.String(required=False, validate=validate.Length(min=1, max=50))
    floor = fields.Integer(required=False, validate=validate.Range(min=0, max=100))
    room_type = fields.String(required=False, validate=validate.OneOf(RoomType.ALL_TYPES))
    capacity = fields.Integer(required=False, validate=validate.Range(min=1, max=20))
    rent = fields.Float(required=False, validate=validate.Range(min=0.0))
    rent_amount = fields.Float(required=False, validate=validate.Range(min=0.0))
    status = fields.String(required=False, validate=validate.OneOf(RoomStatus.ALL_STATUSES))

    @pre_load
    def process_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = data.copy()
        if "room_number" in data and isinstance(data["room_number"], str):
            data["room_number"] = data["room_number"].strip()
        if "rent_amount" in data and ("rent" not in data or data.get("rent") is None):
            data["rent"] = data["rent_amount"]
        elif "rent" in data and ("rent_amount" not in data or data.get("rent_amount") is None):
            data["rent_amount"] = data["rent"]
        return data


class UpdateRoomStatusSchema(Schema):
    """Schema for updating room status only."""
    status = fields.String(required=True, validate=validate.OneOf(RoomStatus.ALL_STATUSES))

