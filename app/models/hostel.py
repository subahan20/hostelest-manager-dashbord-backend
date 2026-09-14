from app.extensions import db
from app.models.base import BaseModel, GUID


class HostelGenderType:
    MENS = "mens"
    WOMENS = "womens"
    COLIVING = "coliving"
    BOYS = "boys"
    GIRLS = "girls"
    CO_LIVING = "co-living"

    ALL_TYPES = [MENS, WOMENS, COLIVING, BOYS, GIRLS, CO_LIVING]


class HostelStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_MAINTENANCE = "under_maintenance"

    ALL_STATUSES = [ACTIVE, INACTIVE, UNDER_MAINTENANCE]


class Hostel(BaseModel):
    __tablename__ = "hostels"

    owner_id = db.Column(
        GUID(),
        db.ForeignKey("owners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False, index=True)
    address = db.Column(db.Text, nullable=False)
    area = db.Column(db.String(100), nullable=False, index=True)
    city = db.Column(db.String(100), nullable=False, default="Hyderabad", index=True)
    state = db.Column(db.String(100), nullable=False, default="Telangana")
    pincode = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=False)
    contact_email = db.Column(db.String(150), nullable=False)
    gender_type = db.Column(
        db.String(20),
        nullable=False,
        default=HostelGenderType.CO_LIVING,
    )
    total_floors = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(
        db.String(30),
        nullable=False,
        default=HostelStatus.ACTIVE,
        index=True,
    )

    # Relationships
    owner = db.relationship("Owner", back_populates="hostels")
    manager_hostels = db.relationship(
        "ManagerHostel",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    rooms = db.relationship(
        "Room",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    students = db.relationship(
        "Student",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    bookings = db.relationship(
        "Booking",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    payments = db.relationship(
        "Payment",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    complaints = db.relationship(
        "Complaint",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    maintenance_requests = db.relationship(
        "Maintenance",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    visitors = db.relationship(
        "Visitor",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notices = db.relationship(
        "Notice",
        back_populates="hostel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "owner_id": str(self.owner_id),
            "name": self.name,
            "address": self.address,
            "area": self.area,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "gender_type": self.gender_type,
            "total_floors": self.total_floors,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Hostel {self.name} ({self.city})>"
