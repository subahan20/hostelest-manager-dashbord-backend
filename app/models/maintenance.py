from app.extensions import db
from app.models.base import BaseModel, GUID


class MaintenanceCategory:
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    CARPENTRY = "carpentry"
    CLEANING = "cleaning"
    APPLIANCE = "appliance"
    PAINTING = "painting"
    OTHER = "other"

    ALL_CATEGORIES = [
        PLUMBING,
        ELECTRICAL,
        CARPENTRY,
        CLEANING,
        APPLIANCE,
        PAINTING,
        OTHER,
    ]


class MaintenancePriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    ALL_PRIORITIES = [LOW, MEDIUM, HIGH, URGENT]


class MaintenanceStatus:
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ALL_STATUSES = [
        PENDING,
        ASSIGNED,
        IN_PROGRESS,
        COMPLETED,
        CANCELLED,
    ]


class Maintenance(BaseModel):
    __tablename__ = "maintenance"

    hostel_id = db.Column(
        GUID(),
        db.ForeignKey("hostels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_id = db.Column(
        GUID(),
        db.ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    student_id = db.Column(
        GUID(),
        db.ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(
        db.String(50),
        nullable=False,
        default=MaintenanceCategory.OTHER,
        index=True,
    )
    priority = db.Column(
        db.String(30),
        nullable=False,
        default=MaintenancePriority.MEDIUM,
        index=True,
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default=MaintenanceStatus.PENDING,
        index=True,
    )
    assigned_to = db.Column(db.String(100), nullable=True)
    estimated_cost = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    actual_cost = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    hostel = db.relationship("Hostel", back_populates="maintenance_requests")
    room = db.relationship("Room", back_populates="maintenance_requests")
    student = db.relationship("Student", back_populates="maintenance_requests")

    def to_dict(self, include_details: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "room_id": str(self.room_id) if self.room_id else None,
            "student_id": str(self.student_id) if self.student_id else None,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost is not None else 0.0,
            "actual_cost": float(self.actual_cost) if self.actual_cost is not None else 0.0,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_details:
            if self.room:
                data["room"] = {
                    "id": str(self.room.id),
                    "room_number": self.room.room_number,
                    "floor": self.room.floor,
                }
            if self.student:
                data["student"] = {
                    "id": str(self.student.id),
                    "name": self.student.name,
                    "phone": self.student.phone,
                }
        return data

    def __repr__(self) -> str:
        return f"<Maintenance {self.title} ({self.status})>"
