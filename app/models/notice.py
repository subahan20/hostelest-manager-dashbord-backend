from app.extensions import db
from app.models.base import BaseModel, GUID, utc_now


class NoticePriority:
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

    ALL_PRIORITIES = [LOW, NORMAL, HIGH, URGENT]


class NoticeStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    ALL_STATUSES = [DRAFT, PUBLISHED, ARCHIVED]


class Notice(BaseModel):
    __tablename__ = "notices"

    hostel_id = db.Column(
        GUID(),
        db.ForeignKey("hostels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by = db.Column(
        GUID(),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(
        db.String(30),
        nullable=False,
        default=NoticePriority.NORMAL,
        index=True,
    )
    publish_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(
        db.String(30),
        nullable=False,
        default=NoticeStatus.PUBLISHED,
        index=True,
    )

    # Relationships
    hostel = db.relationship("Hostel", back_populates="notices")
    author = db.relationship("User")

    def to_dict(self, include_author: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "created_by": str(self.created_by) if self.created_by else None,
            "title": self.title,
            "content": self.content,
            "priority": self.priority,
            "publish_at": self.publish_at.isoformat() if self.publish_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_author and self.author:
            data["author"] = {
                "id": str(self.author.id),
                "name": self.author.name,
                "role": self.author.role,
            }
        return data

    def __repr__(self) -> str:
        return f"<Notice {self.title} (Hostel: {self.hostel_id})>"
