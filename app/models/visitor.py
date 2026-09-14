from app.extensions import db
from app.models.base import BaseModel, GUID, utc_now


class VisitorIdType:
    AADHAAR = "aadhaar"
    DRIVING_LICENSE = "driving_license"
    VOTER_ID = "voter_id"
    PASSPORT = "passport"
    STUDENT_ID = "student_id"
    OTHER = "other"

    ALL_TYPES = [
        AADHAAR,
        DRIVING_LICENSE,
        VOTER_ID,
        PASSPORT,
        STUDENT_ID,
        OTHER,
    ]


class Visitor(BaseModel):
    __tablename__ = "visitors"

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
    visitor_name = db.Column(db.String(100), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    id_type = db.Column(db.String(50), nullable=True)
    id_reference = db.Column(db.String(100), nullable=True)
    check_in = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    check_out = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    hostel = db.relationship("Hostel", back_populates="visitors")
    student = db.relationship("Student", back_populates="visitors")

    def to_dict(self, include_student: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "student_id": str(self.student_id),
            "visitor_name": self.visitor_name,
            "phone": self.phone,
            "purpose": self.purpose,
            "id_type": self.id_type,
            "id_reference": self.id_reference,
            "check_in": self.check_in.isoformat() if self.check_in else None,
            "check_out": self.check_out.isoformat() if self.check_out else None,
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
        return f"<Visitor {self.visitor_name} (Hostel: {self.hostel_id})>"
