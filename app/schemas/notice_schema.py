from marshmallow import Schema, fields, validate
from app.models.notice import NoticePriority, NoticeStatus


class CreateNoticeSchema(Schema):
    """Schema for creating a new notice announcement."""
    hostel_id = fields.UUID(required=True, error_messages={"required": "Hostel ID is required."})
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    content = fields.String(required=True, validate=validate.Length(min=3))
    priority = fields.String(
        required=False,
        load_default=NoticePriority.NORMAL,
        validate=validate.OneOf(NoticePriority.ALL_PRIORITIES),
    )
    publish_at = fields.DateTime(required=False, allow_none=True)
    expires_at = fields.DateTime(required=False, allow_none=True)
    status = fields.String(
        required=False,
        load_default=NoticeStatus.PUBLISHED,
        validate=validate.OneOf(NoticeStatus.ALL_STATUSES),
    )


class UpdateNoticeSchema(Schema):
    """Schema for updating an existing notice."""
    title = fields.String(required=False, validate=validate.Length(min=3, max=200))
    content = fields.String(required=False, validate=validate.Length(min=3))
    priority = fields.String(required=False, validate=validate.OneOf(NoticePriority.ALL_PRIORITIES))
    publish_at = fields.DateTime(required=False, allow_none=True)
    expires_at = fields.DateTime(required=False, allow_none=True)
    status = fields.String(required=False, validate=validate.OneOf(NoticeStatus.ALL_STATUSES))
