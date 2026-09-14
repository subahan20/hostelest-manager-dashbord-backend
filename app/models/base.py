import uuid
from datetime import datetime, timezone
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.extensions import db


class GUID(TypeDecorator):
    """
    Platform-independent GUID/UUID type.
    Uses PostgreSQL's native UUID type when on PostgreSQL,
    otherwise uses CHAR(36), storing as stringified hex UUIDs.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


def utc_now():
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class BaseModel(db.Model):
    """Abstract base model with UUID primary key and timestamps."""
    __abstract__ = True

    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
