from app.extensions import db
from app.models.base import BaseModel, GUID


class StudentStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHECKED_OUT = "checked_out"
    SUSPENDED = "suspended"

    ALL_STATUSES = [ACTIVE, INACTIVE, CHECKED_OUT, SUSPENDED]


class Student(BaseModel):
    __tablename__ = "students"

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
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(150), nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    alternate_phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    college = db.Column(db.String(150), nullable=True)
    company = db.Column(db.String(150), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    joining_date = db.Column(db.Date, nullable=False)
    leaving_date = db.Column(db.Date, nullable=True)
    status = db.Column(
        db.String(30),
        nullable=False,
        default=StudentStatus.ACTIVE,
        index=True,
    )

    # Relationships
    hostel = db.relationship("Hostel", back_populates="students")
    room = db.relationship("Room", back_populates="students")
    bookings = db.relationship("Booking", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    payments = db.relationship("Payment", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    complaints = db.relationship("Complaint", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    visitors = db.relationship("Visitor", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    maintenance_requests = db.relationship("Maintenance", back_populates="student")

    def to_dict(self, include_room: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "room_id": str(self.room_id) if self.room_id else None,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "alternate_phone": self.alternate_phone,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "college": self.college,
            "company": self.company,
            "occupation": self.occupation,
            "address": self.address,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "joining_date": self.joining_date.isoformat() if self.joining_date else None,
            "leaving_date": self.leaving_date.isoformat() if self.leaving_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_room and self.room:
            data["room"] = {
                "id": str(self.room.id),
                "room_number": self.room.room_number,
                "floor": self.room.floor,
                "room_type": self.room.room_type,
            }
        return data

    def __repr__(self) -> str:
        return f"<Student {self.name} ({self.phone})>"
