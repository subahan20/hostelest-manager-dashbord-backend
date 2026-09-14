from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone, date
from app.extensions import db
from app.models import Manager, Complaint, ComplaintStatus, Student
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class ComplaintService:
    """Service handling Complaints, status updates, and resolution workflows."""

    @staticmethod
    def get_complaints(
        manager: Manager,
        hostel_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List complaints with filters and pagination.
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Complaint.query.filter(Complaint.hostel_id.in_(hostel_ids))

        if student_id:
            query = query.filter(Complaint.student_id == student_id)
        if status:
            query = query.filter(Complaint.status == status.strip().lower())
        if priority:
            query = query.filter(Complaint.priority == priority.strip().lower())
        if from_date:
            query = query.filter(Complaint.created_at >= from_date)
        if to_date:
            query = query.filter(Complaint.created_at <= to_date)

        query = query.order_by(Complaint.created_at.desc())

        items, pagination = paginate_query(query)
        complaints_data = [complaint.to_dict(include_student=True) for complaint in items]

        return complaints_data, pagination, None, 200

    @staticmethod
    def get_complaint_by_id(manager: Manager, complaint_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch single complaint by ID."""
        complaint = db.session.get(Complaint, complaint_id)
        if not complaint:
            return None, "Complaint not found", 404

        if not manager.has_hostel_access(complaint.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return complaint.to_dict(include_student=True), None, 200

    @staticmethod
    def create_complaint(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Create a new complaint."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        student = db.session.get(Student, str(data["student_id"]))
        if not student or str(student.hostel_id) != hostel_id:
            return None, "Invalid student ID for this hostel.", 400

        complaint = Complaint(
            hostel_id=hostel_id,
            student_id=student.id,
            title=data["title"].strip(),
            description=data["description"].strip(),
            priority=data.get("priority", "medium"),
            status=data.get("status", ComplaintStatus.PENDING),
            assigned_to=data.get("assigned_to"),
        )
        db.session.add(complaint)
        db.session.commit()

        return complaint.to_dict(include_student=True), None, 201

    @staticmethod
    def update_complaint_status(manager: Manager, complaint_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update complaint status and assigned technician/staff."""
        complaint = db.session.get(Complaint, complaint_id)
        if not complaint:
            return None, "Complaint not found", 404

        if not manager.has_hostel_access(complaint.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        complaint.status = data["status"]
        if "assigned_to" in data:
            complaint.assigned_to = data["assigned_to"]

        if complaint.status == ComplaintStatus.RESOLVED and not complaint.resolved_at:
            complaint.resolved_at = datetime.now(timezone.utc)

        db.session.commit()
        return complaint.to_dict(include_student=True), None, 200

    @staticmethod
    def resolve_complaint(manager: Manager, complaint_id: str, resolution_notes: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Resolve a complaint with notes."""
        complaint = db.session.get(Complaint, complaint_id)
        if not complaint:
            return None, "Complaint not found", 404

        if not manager.has_hostel_access(complaint.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        complaint.status = ComplaintStatus.RESOLVED
        complaint.resolved_at = datetime.now(timezone.utc)
        complaint.resolution_notes = resolution_notes.strip()

        db.session.commit()
        return complaint.to_dict(include_student=True), None, 200
