from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone, date
from app.extensions import db
from app.models import Manager, Maintenance, MaintenanceStatus, Room, Student
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class MaintenanceService:
    """Service handling Maintenance requests, costing, and technician assignment."""

    @staticmethod
    def get_maintenance_requests(
        manager: Manager,
        hostel_id: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        room_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List maintenance requests with filters and pagination.
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Maintenance.query.filter(Maintenance.hostel_id.in_(hostel_ids))

        if priority:
            query = query.filter(Maintenance.priority == priority.strip().lower())
        if status:
            query = query.filter(Maintenance.status == status.strip().lower())
        if category:
            query = query.filter(Maintenance.category == category.strip().lower())
        if room_id:
            query = query.filter(Maintenance.room_id == room_id)
        if from_date:
            query = query.filter(Maintenance.created_at >= from_date)
        if to_date:
            query = query.filter(Maintenance.created_at <= to_date)

        query = query.order_by(Maintenance.created_at.desc())

        items, pagination = paginate_query(query)
        data = [item.to_dict(include_details=True) for item in items]

        return data, pagination, None, 200

    @staticmethod
    def get_maintenance_by_id(manager: Manager, maintenance_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch single maintenance request by ID."""
        req = db.session.get(Maintenance, maintenance_id)
        if not req:
            return None, "Maintenance request not found", 404

        if not manager.has_hostel_access(req.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return req.to_dict(include_details=True), None, 200

    @staticmethod
    def create_maintenance(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Create a new maintenance request."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        room_id = data.get("room_id")
        if room_id:
            room = db.session.get(Room, str(room_id))
            if not room or str(room.hostel_id) != hostel_id:
                return None, "Invalid room ID for this hostel.", 400

        student_id = data.get("student_id")
        if student_id:
            student = db.session.get(Student, str(student_id))
            if not student or str(student.hostel_id) != hostel_id:
                return None, "Invalid student ID for this hostel.", 400

        req = Maintenance(
            hostel_id=hostel_id,
            room_id=room_id,
            student_id=student_id,
            title=data["title"].strip(),
            description=data["description"].strip(),
            category=data.get("category", "other"),
            priority=data.get("priority", "medium"),
            status=data.get("status", MaintenanceStatus.PENDING),
            assigned_to=data.get("assigned_to"),
            estimated_cost=data.get("estimated_cost", 0.0),
            actual_cost=data.get("actual_cost", 0.0),
            notes=data.get("notes"),
        )
        db.session.add(req)
        db.session.commit()

        return req.to_dict(include_details=True), None, 201

    @staticmethod
    def update_maintenance_status(manager: Manager, maintenance_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update maintenance status, actual cost, and notes."""
        req = db.session.get(Maintenance, maintenance_id)
        if not req:
            return None, "Maintenance request not found", 404

        if not manager.has_hostel_access(req.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        req.status = data["status"]
        if "actual_cost" in data and data["actual_cost"] is not None:
            req.actual_cost = data["actual_cost"]
        if "notes" in data and data["notes"]:
            req.notes = (req.notes or "") + f" {data['notes']}".strip()

        if req.status == MaintenanceStatus.COMPLETED and not req.completed_at:
            req.completed_at = datetime.now(timezone.utc)

        db.session.commit()
        return req.to_dict(include_details=True), None, 200

    @staticmethod
    def assign_maintenance(manager: Manager, maintenance_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Assign maintenance request to technician or vendor."""
        req = db.session.get(Maintenance, maintenance_id)
        if not req:
            return None, "Maintenance request not found", 404

        if not manager.has_hostel_access(req.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        req.assigned_to = data["assigned_to"].strip()
        req.status = MaintenanceStatus.ASSIGNED
        if "estimated_cost" in data and data["estimated_cost"] is not None:
            req.estimated_cost = data["estimated_cost"]
        if "notes" in data and data["notes"]:
            req.notes = (req.notes or "") + f" {data['notes']}".strip()

        db.session.commit()
        return req.to_dict(include_details=True), None, 200
