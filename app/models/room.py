from app.extensions import db
from app.models.base import BaseModel, GUID


class RoomType:
    AC = "ac"
    NON_AC = "non_ac"
    AC_SINGLE = "ac_single"
    AC_DOUBLE = "ac_double"
    AC_TRIPLE = "ac_triple"
    AC_FOUR_SHARING = "ac_four_sharing"
    NON_AC_SINGLE = "non_ac_single"
    NON_AC_DOUBLE = "non_ac_double"
    NON_AC_TRIPLE = "non_ac_triple"
    NON_AC_FOUR_SHARING = "non_ac_four_sharing"
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    FOUR_SHARING = "four_sharing"
    FIVE_SHARING = "five_sharing"
    SIX_SHARING = "six_sharing"

    ALL_TYPES = [
        AC, NON_AC,
        AC_SINGLE, AC_DOUBLE, AC_TRIPLE, AC_FOUR_SHARING,
        NON_AC_SINGLE, NON_AC_DOUBLE, NON_AC_TRIPLE, NON_AC_FOUR_SHARING,
        SINGLE, DOUBLE, TRIPLE, FOUR_SHARING, FIVE_SHARING, SIX_SHARING
    ]


class RoomStatus:
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    PARTIALLY_OCCUPIED = "partially_occupied"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"

    ALL_STATUSES = [AVAILABLE, OCCUPIED, PARTIALLY_OCCUPIED, MAINTENANCE, INACTIVE]


class Room(BaseModel):
    __tablename__ = "rooms"

    hostel_id = db.Column(
        GUID(),
        db.ForeignKey("hostels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_number = db.Column(db.String(50), nullable=False, index=True)
    floor = db.Column(db.Integer, nullable=False, default=1)
    room_type = db.Column(
        db.String(50),
        nullable=False,
        default=RoomType.DOUBLE,
    )
    capacity = db.Column(db.Integer, nullable=False, default=2)
    rent = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    status = db.Column(
        db.String(30),
        nullable=False,
        default=RoomStatus.AVAILABLE,
        index=True,
    )

    __table_args__ = (
        db.UniqueConstraint("hostel_id", "room_number", name="uq_hostel_room_number"),
    )

    # Relationships
    hostel = db.relationship("Hostel", back_populates="rooms")
    students = db.relationship("Student", back_populates="room", lazy="selectin")
    bookings = db.relationship("Booking", back_populates="room")
    maintenance_requests = db.relationship("Maintenance", back_populates="room")

    @property
    def current_occupancy(self) -> int:
        """Calculate number of active students currently staying in this room."""
        if not self.students:
            return 0
        return sum(1 for s in self.students if s.status == "active")

    @property
    def available_beds(self) -> int:
        """Calculate available bed capacity."""
        return max(0, self.capacity - self.current_occupancy)

    def to_dict(self, include_occupancy: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "hostel_id": str(self.hostel_id),
            "room_number": self.room_number,
            "floor": self.floor,
            "room_type": self.room_type,
            "capacity": self.capacity,
            "rent": float(self.rent) if self.rent is not None else 0.0,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_occupancy:
            data["current_occupancy"] = self.current_occupancy
            data["available_beds"] = self.available_beds
        return data

    def __repr__(self) -> str:
        return f"<Room {self.room_number} (Hostel: {self.hostel_id})>"
