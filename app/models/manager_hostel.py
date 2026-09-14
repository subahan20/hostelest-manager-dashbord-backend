from app.extensions import db
from app.models.base import BaseModel, GUID, utc_now


class ManagerHostelStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"

    ALL_STATUSES = [ACTIVE, INACTIVE, REVOKED]


class ManagerHostel(BaseModel):
    __tablename__ = "manager_hostels"

    manager_id = db.Column(
        GUID(),
        db.ForeignKey("managers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hostel_id = db.Column(
        GUID(),
        db.ForeignKey("hostels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    status = db.Column(
        db.String(30),
        default=ManagerHostelStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        db.UniqueConstraint("manager_id", "hostel_id", name="uq_manager_hostel"),
    )

    # Relationships
    manager = db.relationship("Manager", back_populates="manager_hostels")
    hostel = db.relationship("Hostel", back_populates="manager_hostels")

    def to_dict(self, include_hostel: bool = False) -> dict:
        data = {
            "id": str(self.id),
            "manager_id": str(self.manager_id),
            "hostel_id": str(self.hostel_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_hostel and self.hostel:
            data["hostel"] = self.hostel.to_dict()
        return data

    def __repr__(self) -> str:
        return f"<ManagerHostel manager_id={self.manager_id} hostel_id={self.hostel_id}>"
