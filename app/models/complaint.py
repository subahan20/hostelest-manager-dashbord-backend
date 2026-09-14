from app.extensions import db
from app.models.base import BaseModel, GUID


class ComplaintPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    ALL_PRIORITIES = [LOW, MEDIUM, HIGH, URGENT]


class ComplaintStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"

    ALL_STATUSES = [PENDING, IN_PROGRESS, RESOLVED, REJECTED]


class Complaint(BaseModel):
    __tablename__ = "complaints"

    hostel_id = db.Column(
        GUID(),
        db.ForeignKey("hostels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = db.Column(
        GUID(),
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(
        db.String(30),
        nullable=False,
        default=ComplaintPriority.MEDIUM,
        index=True,
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default=ComplaintStatus.PENDING,
        index=True,
    )
    assigned_to = db.Column(db.String(100), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    # Relationships
    hostel = db.relationship("Hostel", back_populates="complaints")
    student = db.relationship("Student", back_populates="complaints")

    def to_dict(self, include_student: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "student_id": str(self.student_id),
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_student and self.student:
            data["student"] = {
                "id": str(self.student.id),
                "name": self.student.name,
                "phone": self.student.phone,
                "room_number": self.student.room.room_number if self.student.room else None,
            }
        return data

    def __repr__(self) -> str:
        return f"<Complaint {self.title} ({self.status})>"
