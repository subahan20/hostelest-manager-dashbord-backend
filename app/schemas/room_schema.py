from marshmallow import Schema, EXCLUDE, fields, validate, pre_load, validates_schema, ValidationError
from app.models.room import RoomType, RoomStatus


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _normalize_room_payload(data: dict) -> dict:
    """Shared normalization for create/update room payloads."""
    data = data.copy()

    if "hostel_id" in data and data["hostel_id"] is not None:
        data["hostel_id"] = str(data["hostel_id"]).strip()

    if "room_number" in data and isinstance(data["room_number"], str):
        data["room_number"] = data["room_number"].strip()

    if "room_type" in data and isinstance(data["room_type"], str):
        data["room_type"] = data["room_type"].strip().lower()

    if "status" in data and isinstance(data["status"], str):
        data["status"] = data["status"].strip().lower()

    for int_field in ("floor", "capacity"):
        if int_field in data and not _is_blank(data[int_field]):
            try:
                data[int_field] = int(data[int_field])
            except (TypeError, ValueError):
                pass

    # Accept rent_amount-only payloads and ignore blank rent strings from forms.
    if _is_blank(data.get("rent")) and not _is_blank(data.get("rent_amount")):
        data["rent"] = data["rent_amount"]
    elif _is_blank(data.get("rent_amount")) and not _is_blank(data.get("rent")):
        data["rent_amount"] = data["rent"]

    for money_field in ("rent", "rent_amount"):
        if money_field in data and not _is_blank(data[money_field]):
            try:
                data[money_field] = float(data[money_field])
            except (TypeError, ValueError):
                pass
        elif money_field in data and _is_blank(data[money_field]):
            data.pop(money_field, None)

    return data


class CreateRoomSchema(Schema):
    """Schema for creating a new room."""
    class Meta:
        unknown = EXCLUDE

    # String (not strict UUID) — shared DB / legacy rows may expose non-UUID hostel ids.
    # Authorization still verifies manager assignment in RoomService.
    hostel_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=64),
        error_messages={"required": "Hostel ID is required."},
    )
    room_number = fields.String(required=True, validate=validate.Length(min=1, max=50))
    floor = fields.Integer(required=False, load_default=1, validate=validate.Range(min=0, max=100))
    room_type = fields.String(
        required=False,
        load_default=RoomType.DOUBLE,
        validate=validate.OneOf(RoomType.ALL_TYPES),
    )
    capacity = fields.Integer(required=False, load_default=2, validate=validate.Range(min=1, max=20))
    rent = fields.Float(required=False, validate=validate.Range(min=0.0))
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
        return _normalize_room_payload(data)

    @validates_schema
    def validate_rent_present(self, data, **kwargs):
        if data.get("rent") is None and data.get("rent_amount") is None:
            raise ValidationError({"rent": ["Rent is required."]})


class UpdateRoomSchema(Schema):
    """Schema for updating room details."""
    class Meta:
        unknown = EXCLUDE

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
        return _normalize_room_payload(data)


class UpdateRoomStatusSchema(Schema):
    """Schema for updating room status only."""
    status = fields.String(required=True, validate=validate.OneOf(RoomStatus.ALL_STATUSES))

    @pre_load
    def process_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = data.copy()
        if "status" in data and isinstance(data["status"], str):
            data["status"] = data["status"].strip().lower()
        return data
