from app.extensions import db
from app.models.base import BaseModel, GUID


class PaymentStatus:
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    FAILED = "failed"
    REFUNDED = "refunded"

    ALL_STATUSES = [
        PENDING,
        PAID,
        PARTIALLY_PAID,
        OVERDUE,
        FAILED,
        REFUNDED,
    ]


class PaymentType:
    RENT = "rent"
    DEPOSIT = "deposit"
    MAINTENANCE = "maintenance"
    OTHER = "other"

    ALL_TYPES = [RENT, DEPOSIT, MAINTENANCE, OTHER]


class PaymentMethod:
    CASH = "cash"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    ONLINE = "online"

    ALL_METHODS = [CASH, UPI, BANK_TRANSFER, CARD, ONLINE]


class Payment(BaseModel):
    __tablename__ = "payments"

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
    booking_id = db.Column(
        GUID(),
        db.ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_type = db.Column(
        db.String(50),
        nullable=False,
        default=PaymentType.RENT,
        index=True,
    )
    payment_method = db.Column(
        db.String(50),
        nullable=True,
    )
    transaction_reference = db.Column(
        db.String(100),
        nullable=True,
        index=True,
    )
    due_date = db.Column(db.Date, nullable=True, index=True)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(
        db.String(30),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    hostel = db.relationship("Hostel", back_populates="payments")
    student = db.relationship("Student", back_populates="payments")
    booking = db.relationship("Booking", back_populates="payments")

    def to_dict(self, include_details: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "student_id": str(self.student_id),
            "booking_id": str(self.booking_id) if self.booking_id else None,
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "payment_type": self.payment_type,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_details and self.student:
            data["student"] = {
                "id": str(self.student.id),
                "name": self.student.name,
                "phone": self.student.phone,
            }
        return data

    def __repr__(self) -> str:
        return f"<Payment {self.id} ({self.amount} - {self.status})>"
