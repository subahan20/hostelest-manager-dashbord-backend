from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone, date
from app.extensions import db
from app.models import Manager, Visitor, Student
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class VisitorService:
    """Service handling Visitor logs and check-in/check-out tracking."""

    @staticmethod
    def get_visitors(
        manager: Manager,
        hostel_id: Optional[str] = None,
        student_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List visitor logs with date filters and pagination.
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Visitor.query.filter(Visitor.hostel_id.in_(hostel_ids))

        if student_id:
            query = query.filter(Visitor.student_id == student_id)
        if from_date:
            query = query.filter(Visitor.check_in >= from_date)
        if to_date:
            query = query.filter(Visitor.check_in <= to_date)

        query = query.order_by(Visitor.check_in.desc())

        items, pagination = paginate_query(query)
        data = [item.to_dict(include_student=True) for item in items]

        return data, pagination, None, 200

    @staticmethod
    def get_visitor_by_id(manager: Manager, visitor_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch single visitor record by ID."""
        visitor = db.session.get(Visitor, visitor_id)
        if not visitor:
            return None, "Visitor record not found", 404

        if not manager.has_hostel_access(visitor.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return visitor.to_dict(include_student=True), None, 200

    @staticmethod
    def create_visitor(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Register a new visitor check-in."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        student = db.session.get(Student, str(data["student_id"]))
        if not student or str(student.hostel_id) != hostel_id:
            return None, "Invalid student ID for this hostel.", 400

        visitor = Visitor(
            hostel_id=hostel_id,
            student_id=student.id,
            visitor_name=data["visitor_name"].strip(),
            phone=data["phone"].strip(),
            purpose=data["purpose"].strip(),
            id_type=data.get("id_type", "other"),
            id_reference=data.get("id_reference"),
            check_in=data.get("check_in") or datetime.now(timezone.utc),
        )
        db.session.add(visitor)
        db.session.commit()

        return visitor.to_dict(include_student=True), None, 201

    @staticmethod
    def update_visitor(manager: Manager, visitor_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update visitor details or checkout timestamp."""
        visitor = db.session.get(Visitor, visitor_id)
        if not visitor:
            return None, "Visitor record not found", 404

        if not manager.has_hostel_access(visitor.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        for field in ["visitor_name", "phone", "purpose", "id_type", "id_reference", "check_out"]:
            if field in data:
                setattr(visitor, field, data[field])

        db.session.commit()
        return visitor.to_dict(include_student=True), None, 200

    @staticmethod
    def checkout_visitor(manager: Manager, visitor_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Record checkout timestamp for a visitor."""
        visitor = db.session.get(Visitor, visitor_id)
        if not visitor:
            return None, "Visitor record not found", 404

        if not manager.has_hostel_access(visitor.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        visitor.check_out = datetime.now(timezone.utc)
        db.session.commit()
        return visitor.to_dict(include_student=True), None, 200
