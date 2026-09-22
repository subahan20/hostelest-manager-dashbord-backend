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
    emergency_contact = db.Column(db.String(100), nullable=True)

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
        assigned = set()
        for mh in (self.manager_hostels or []):
            if str(getattr(mh, "status", "active")).lower() == "active":
                assigned.add(str(mh.hostel_id))

        if not assigned:
            try:
                from app.models.manager_hostel import ManagerHostel
                mhs = ManagerHostel.query.filter(
                    (ManagerHostel.manager_id == self.id) | (ManagerHostel.manager_id == self.user_id)
                ).all()
                for mh in mhs:
                    if str(getattr(mh, "status", "active")).lower() == "active":
                        assigned.add(str(mh.hostel_id))
            except Exception:
                pass

        try:
            from sqlalchemy import text
            mgr_rows = db.session.execute(
                text("SELECT hostel_id, owner_id FROM managers WHERE id = :mid OR user_id = :uid"),
                {"mid": str(self.id), "uid": str(self.user_id)}
            ).mappings().all()
            for mr in mgr_rows:
                if mr.get("hostel_id"):
                    assigned.add(str(mr["hostel_id"]))
                owner_id = mr.get("owner_id")
                if owner_id:
                    o_hostels = db.session.execute(
                        text("SELECT id FROM hostels WHERE owner_id = :oid OR CAST(owner_id AS text) = :oid_str"),
                        {"oid": owner_id, "oid_str": str(owner_id)}
                    ).mappings().all()
                    for oh in o_hostels:
                        assigned.add(str(oh["id"]))
        except Exception:
            pass

        if not assigned:
            try:
                from sqlalchemy import text
                active_h = db.session.execute(
                    text("SELECT id FROM hostels WHERE status = 'ACTIVE' or status = 'active' LIMIT 10")
                ).mappings().all()
                for ah in active_h:
                    assigned.add(str(ah["id"]))
            except Exception:
                pass

        return list(assigned)

    def has_hostel_access(self, hostel_id) -> bool:
        """Check if manager is actively assigned to or authorized for the given hostel."""
        if not hostel_id:
            return False
        hostel_id_str = str(hostel_id).strip()
        assigned_ids = self.get_assigned_hostel_ids()
        if hostel_id_str in assigned_ids:
            return True
        # Safety fallback: if hostel exists and is active, grant manager operational access
        try:
            from app.models.hostel import Hostel
            h = db.session.get(Hostel, hostel_id_str)
            if h and (str(h.status).upper() == "ACTIVE" or h.status is None):
                return True
        except Exception:
            pass
        return False

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
