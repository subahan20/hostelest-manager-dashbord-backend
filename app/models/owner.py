from app.extensions import db
from app.models.base import BaseModel, GUID


class Owner(BaseModel):
    __tablename__ = "owners"

    user_id = db.Column(
        GUID(),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    business_name = db.Column(db.String(150), nullable=True)
    pan_number = db.Column(db.String(20), nullable=True)
    gst_number = db.Column(db.String(20), nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="owner")
    hostels = db.relationship(
        "Hostel",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self, include_user: bool = False) -> dict:
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "business_name": self.business_name,
            "pan_number": self.pan_number,
            "gst_number": self.gst_number,
            "emergency_contact": self.emergency_contact,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        return data

    def __repr__(self) -> str:
        return f"<Owner id={self.id} user_id={self.user_id}>"
