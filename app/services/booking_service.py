from typing import Tuple, Optional, Dict, Any, List
from datetime import date
from app.extensions import db
from app.models import (
    Manager,
    Booking,
    BookingStatus,
    Room,
    RoomStatus,
    Student,
    StudentStatus,
)
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class BookingService:
    """Service handling Bookings, transaction consistency, and overbooking prevention."""

    @staticmethod
    def get_bookings(
        manager: Manager,
        hostel_id: Optional[str] = None,
        room_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List bookings with filters, search, and pagination.
        
        Returns:
            (bookings_list, pagination_meta, error_message, status_code)
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Booking.query.filter(Booking.hostel_id.in_(hostel_ids))

        if room_id:
            query = query.filter(Booking.room_id == room_id)
        if student_id:
            query = query.filter(Booking.student_id == student_id)
        if status:
            query = query.filter(Booking.status == status.strip().lower())
        if search:
            search_term = f"%{search.strip()}%"
            query = query.join(Student, Booking.student_id == Student.id).filter(
                db.or_(
                    Booking.booking_reference.ilike(search_term),
                    Student.name.ilike(search_term),
                    Student.phone.ilike(search_term),
                )
            )

        query = query.order_by(Booking.created_at.desc())

        items, pagination = paginate_query(query)
        bookings_data = [booking.to_dict(include_details=True) for booking in items]

        return bookings_data, pagination, None, 200

    @staticmethod
    def get_booking_by_id(manager: Manager, booking_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch single booking by ID if authorized."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found", 404

        if not manager.has_hostel_access(booking.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return booking.to_dict(include_details=True), None, 200

    @staticmethod
    def create_booking(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Create a new booking."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        student = db.session.get(Student, str(data["student_id"]))
        if not student or str(student.hostel_id) != hostel_id:
            return None, "Invalid student ID for this hostel.", 400

        room_id = data.get("room_id")
        if room_id:
            room = db.session.get(Room, str(room_id))
            if not room or str(room.hostel_id) != hostel_id:
                return None, "Invalid room ID for this hostel.", 400

        # Generate unique reference
        ref = Booking.generate_reference()
        while Booking.query.filter_by(booking_reference=ref).first():
            ref = Booking.generate_reference()

        booking = Booking(
            hostel_id=hostel_id,
            room_id=room_id,
            student_id=student.id,
            booking_reference=ref,
            check_in_date=data["check_in_date"],
            expected_check_out_date=data.get("expected_check_out_date"),
            amount=data.get("amount", 0.0),
            security_deposit=data.get("security_deposit", 0.0),
            status=data.get("status", BookingStatus.PENDING),
        )
        db.session.add(booking)
        db.session.commit()

        return booking.to_dict(include_details=True), None, 201

    @staticmethod
    def approve_booking(manager: Manager, booking_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Approve a pending booking with room capacity verification."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found", 404

        if not manager.has_hostel_access(booking.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        if booking.status != BookingStatus.PENDING:
            return None, f"Cannot approve booking in '{booking.status}' status.", 400

        # If room is assigned, verify availability
        if booking.room:
            if booking.room.available_beds <= 0:
                return None, f"Cannot approve: Room {booking.room.room_number} is already at full capacity.", 409

        booking.status = BookingStatus.APPROVED
        db.session.commit()

        return booking.to_dict(include_details=True), None, 200

    @staticmethod
    def reject_booking(manager: Manager, booking_id: str, reason: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Reject a pending or approved booking."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found", 404

        if not manager.has_hostel_access(booking.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        if booking.status in [BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT, BookingStatus.CANCELLED]:
            return None, f"Cannot reject booking in '{booking.status}' status.", 400

        booking.status = BookingStatus.REJECTED
        db.session.commit()

        return booking.to_dict(include_details=True), None, 200

    @staticmethod
    def check_in_booking(manager: Manager, booking_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Execute check-in using an ACID database transaction:
        1. Verify booking & manager authorization
        2. Verify room exists and has available bed
        3. Prevent overbooking
        4. Update booking to checked_in
        5. Assign student to room and set active
        6. Update room occupancy status
        """
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found", 404

        if not manager.has_hostel_access(booking.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        if booking.status == BookingStatus.CHECKED_IN:
            return None, "Booking is already checked in.", 400

        if booking.status in [BookingStatus.REJECTED, BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT]:
            return None, f"Cannot check in booking in '{booking.status}' status.", 400

        if not booking.room_id:
            return None, "Cannot check in: No room has been assigned to this booking.", 400

        room = db.session.get(Room, str(booking.room_id))
        student = db.session.get(Student, str(booking.student_id))

        if not room or not student:
            return None, "Associated room or student record not found.", 404

        # Verify Room status & capacity to prevent overbooking
        if room.status == RoomStatus.MAINTENANCE or room.status == RoomStatus.INACTIVE:
            return None, f"Room {room.room_number} is under '{room.status}' and cannot accept check-ins.", 400

        if room.available_beds <= 0:
            return None, f"Overbooking prevented: Room {room.room_number} is already at maximum capacity ({room.capacity} beds).", 409

        try:
            # Atomic state transition
            booking.status = BookingStatus.CHECKED_IN
            booking.actual_check_out_date = None

            student.room_id = room.id
            student.status = StudentStatus.ACTIVE

            db.session.flush()

            # Update room status based on current active occupants
            active_count = Student.query.filter_by(room_id=room.id, status=StudentStatus.ACTIVE).count()
            if active_count >= room.capacity:
                room.status = RoomStatus.OCCUPIED
            elif active_count > 0:
                room.status = RoomStatus.PARTIALLY_OCCUPIED
            else:
                room.status = RoomStatus.AVAILABLE

            db.session.commit()
            return booking.to_dict(include_details=True), None, 200
        except Exception as e:
            db.session.rollback()
            return None, f"Check-in transaction failed: {str(e)}", 500

    @staticmethod
    def check_out_booking(manager: Manager, booking_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Execute check-out using an ACID database transaction:
        1. Verify booking is checked_in
        2. Update booking to checked_out with today's date
        3. Free student's room assignment and update student status
        4. Recompute room occupancy status
        """
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found", 404

        if not manager.has_hostel_access(booking.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        if booking.status != BookingStatus.CHECKED_IN:
            return None, f"Cannot check out booking with status '{booking.status}'. Must be 'checked_in'.", 400

        room = booking.room
        student = booking.student

        try:
            booking.status = BookingStatus.CHECKED_OUT
            booking.actual_check_out_date = date.today()

            if student:
                student.status = StudentStatus.CHECKED_OUT
                student.room_id = None
                student.leaving_date = date.today()

            db.session.flush()

            if room:
                active_count = Student.query.filter_by(room_id=room.id, status=StudentStatus.ACTIVE).count()
                if active_count == 0:
                    room.status = RoomStatus.AVAILABLE
                elif active_count >= room.capacity:
                    room.status = RoomStatus.OCCUPIED
                else:
                    room.status = RoomStatus.PARTIALLY_OCCUPIED

            db.session.commit()
            return booking.to_dict(include_details=True), None, 200
        except Exception as e:
            db.session.rollback()
            return None, f"Check-out transaction failed: {str(e)}", 500

    @staticmethod
    def cancel_booking(manager: Manager, booking_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Cancel a booking."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found", 404

        if not manager.has_hostel_access(booking.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        if booking.status == BookingStatus.CHECKED_OUT:
            return None, "Cannot cancel an already checked out booking.", 400

        # If it was checked in, free student & room
        if booking.status == BookingStatus.CHECKED_IN:
            if booking.student:
                booking.student.room_id = None
                booking.student.status = StudentStatus.INACTIVE
            if booking.room:
                if booking.room.current_occupancy == 0:
                    booking.room.status = RoomStatus.AVAILABLE
                else:
                    booking.room.status = RoomStatus.PARTIALLY_OCCUPIED

        booking.status = BookingStatus.CANCELLED
        db.session.commit()

        return booking.to_dict(include_details=True), None, 200
