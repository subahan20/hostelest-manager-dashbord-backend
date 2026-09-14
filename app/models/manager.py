from typing import List
from app.extensions import db
from app.models.base import BaseModel, GUID


class Manager(BaseModel):
    __tablename__ = "managers"

    user_id = db.Column(
        GUID(),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    employee_code = db.Column(db.String(50), unique=True, nullable=True, index=True)
    joining_date = db.Column(db.Date, nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="manager")
    manager_hostels = db.relationship(
        "ManagerHostel",
        back_populates="manager",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def get_assigned_hostel_ids(self) -> List[str]:
        """Return list of string UUIDs of actively assigned hostels."""
        return [
            str(mh.hostel_id)
            for mh in self.manager_hostels
            if mh.status == "active"
        ]

    def has_hostel_access(self, hostel_id) -> bool:
        """Check if manager is actively assigned to the given hostel."""
        hostel_id_str = str(hostel_id)
        return hostel_id_str in self.get_assigned_hostel_ids()

    def to_dict(self, include_user: bool = False, include_hostels: bool = False) -> dict:
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "employee_code": self.employee_code,
            "joining_date": self.joining_date.isoformat() if self.joining_date else None,
            "profile_image": self.profile_image,
            "emergency_contact": self.emergency_contact,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        if include_hostels:
            data["assigned_hostel_ids"] = self.get_assigned_hostel_ids()
        return data

    def __repr__(self) -> str:
        return f"<Manager id={self.id} user_id={self.user_id}>"
