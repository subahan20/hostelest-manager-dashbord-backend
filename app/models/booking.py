import random
from datetime import datetime, timezone
from app.extensions import db
from app.models.base import BaseModel, GUID, utc_now


class BookingStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"

    ALL_STATUSES = [
        PENDING,
        APPROVED,
        REJECTED,
        CANCELLED,
        CHECKED_IN,
        CHECKED_OUT,
    ]


class Booking(BaseModel):
    __tablename__ = "bookings"

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
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    booking_reference = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    booking_date = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    check_in_date = db.Column(db.Date, nullable=False)
    expected_check_out_date = db.Column(db.Date, nullable=True)
    actual_check_out_date = db.Column(db.Date, nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    security_deposit = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    status = db.Column(
        db.String(30),
        nullable=False,
        default=BookingStatus.PENDING,
        index=True,
    )

    # Relationships
    hostel = db.relationship("Hostel", back_populates="bookings")
    room = db.relationship("Room", back_populates="bookings")
    student = db.relationship("Student", back_populates="bookings")
    payments = db.relationship("Payment", back_populates="booking")

    @staticmethod
    def generate_reference() -> str:
        """Generate a formatted unique booking reference: HST-YYYY-XXXXXX."""
        year = datetime.now(timezone.utc).year
        random_num = random.randint(100000, 999999)
        return f"HST-{year}-{random_num}"

    def to_dict(self, include_details: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "room_id": str(self.room_id) if self.room_id else None,
            "student_id": str(self.student_id),
            "booking_reference": self.booking_reference,
            "booking_date": self.booking_date.isoformat() if self.booking_date else None,
            "check_in_date": self.check_in_date.isoformat() if self.check_in_date else None,
            "expected_check_out_date": (
                self.expected_check_out_date.isoformat()
                if self.expected_check_out_date
                else None
            ),
            "actual_check_out_date": (
                self.actual_check_out_date.isoformat()
                if self.actual_check_out_date
                else None
            ),
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "security_deposit": float(self.security_deposit) if self.security_deposit is not None else 0.0,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_details:
            if self.student:
                data["student"] = {
                    "id": str(self.student.id),
                    "name": self.student.name,
                    "phone": self.student.phone,
                    "email": self.student.email,
                }
            if self.room:
                data["room"] = {
                    "id": str(self.room.id),
                    "room_number": self.room.room_number,
                    "floor": self.room.floor,
                    "room_type": self.room.room_type,
                }
        return data

    def __repr__(self) -> str:
        return f"<Booking {self.booking_reference} ({self.status})>"
