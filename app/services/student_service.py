from typing import Tuple, Optional, Dict, Any, List
from app.extensions import db
from app.models import Manager, Student, StudentStatus, Room, RoomStatus
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class StudentService:
    """Service handling Student operations and room assignment."""

    @staticmethod
    def get_students(
        manager: Manager,
        hostel_id: Optional[str] = None,
        room_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List students with search, filters, and pagination.
        
        Returns:
            (students_list, pagination_meta, error_message, status_code)
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Student.query.filter(Student.hostel_id.in_(hostel_ids))

        if room_id:
            query = query.filter(Student.room_id == room_id)
        if status:
            query = query.filter(Student.status == status.strip().lower())
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                db.or_(
                    Student.name.ilike(search_term),
                    Student.phone.ilike(search_term),
                    Student.email.ilike(search_term),
                )
            )

        query = query.order_by(Student.created_at.desc())

        items, pagination = paginate_query(query)
        students_data = [student.to_dict(include_room=True) for student in items]

        return students_data, pagination, None, 200

    @staticmethod
    def get_student_by_id(manager: Manager, student_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch single student by ID if authorized."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "Student not found", 404

        if not manager.has_hostel_access(student.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return student.to_dict(include_room=True), None, 200

    @staticmethod
    def create_student(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Register a new student and optionally assign to a room."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        room = None
        room_id = data.get("room_id")
        if room_id:
            room = db.session.get(Room, str(room_id))
            if not room or str(room.hostel_id) != hostel_id:
                return None, "Invalid room ID for this hostel.", 400

            if room.status == RoomStatus.MAINTENANCE or room.status == RoomStatus.INACTIVE:
                return None, f"Cannot assign student to room in '{room.status}' status.", 400

            if room.available_beds <= 0:
                return None, f"Room {room.room_number} is already fully occupied.", 400

        student = Student(
            hostel_id=hostel_id,
            room_id=room.id if room else None,
            name=data["name"].strip(),
            email=data.get("email"),
            phone=data["phone"].strip(),
            alternate_phone=data.get("alternate_phone"),
            gender=data.get("gender"),
            date_of_birth=data.get("date_of_birth"),
            college=data.get("college"),
            company=data.get("company"),
            occupation=data.get("occupation"),
            address=data.get("address"),
            emergency_contact_name=data.get("emergency_contact_name"),
            emergency_contact_phone=data.get("emergency_contact_phone"),
            joining_date=data["joining_date"],
            leaving_date=data.get("leaving_date"),
            status=data.get("status", StudentStatus.ACTIVE),
        )
        db.session.add(student)
        db.session.flush()

        # Update room status if assigned
        if room and student.status == StudentStatus.ACTIVE:
            if room.available_beds <= 0:
                room.status = RoomStatus.OCCUPIED
            else:
                room.status = RoomStatus.PARTIALLY_OCCUPIED

        db.session.commit()
        return student.to_dict(include_room=True), None, 201

    @staticmethod
    def update_student(manager: Manager, student_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update student profile details and room reassignment."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "Student not found", 404

        if not manager.has_hostel_access(student.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        # Room reassignment logic
        if "room_id" in data:
            new_room_id = data["room_id"]
            if new_room_id is None:
                student.room_id = None
            elif str(new_room_id) != str(student.room_id):
                new_room = db.session.get(Room, str(new_room_id))
                if not new_room or str(new_room.hostel_id) != str(student.hostel_id):
                    return None, "Invalid room ID for this hostel.", 400
                if new_room.available_beds <= 0:
                    return None, f"Room {new_room.room_number} is already fully occupied.", 400
                student.room_id = new_room.id

        for field in [
            "name", "email", "phone", "alternate_phone", "gender",
            "date_of_birth", "college", "company", "occupation",
            "address", "emergency_contact_name", "emergency_contact_phone",
            "leaving_date", "status",
        ]:
            if field in data:
                setattr(student, field, data[field])

        db.session.commit()
        return student.to_dict(include_room=True), None, 200

    @staticmethod
    def update_student_status(manager: Manager, student_id: str, new_status: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update student status (e.g. checked_out, active)."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "Student not found", 404

        if not manager.has_hostel_access(student.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        student.status = new_status.strip().lower()
        if student.status == StudentStatus.CHECKED_OUT:
            # Check room occupancy
            room = student.room
            student.room_id = None
            db.session.flush()
            if room:
                if room.current_occupancy == 0:
                    room.status = RoomStatus.AVAILABLE
                else:
                    room.status = RoomStatus.PARTIALLY_OCCUPIED

        db.session.commit()
        return student.to_dict(include_room=True), None, 200
