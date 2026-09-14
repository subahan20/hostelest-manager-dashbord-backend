from typing import Dict, Any, Tuple, Optional, List
from datetime import date
from sqlalchemy import func
from app.extensions import db
from app.models import (
    Manager,
    Room,
    RoomStatus,
    Student,
    StudentStatus,
    Booking,
    BookingStatus,
    Payment,
    PaymentStatus,
    Complaint,
    ComplaintStatus,
    Maintenance,
    MaintenanceStatus,
)
from app.middleware.permissions import get_scoped_hostel_ids


class DashboardService:
    """Service to aggregate real database metrics for manager dashboard."""

    @staticmethod
    def get_dashboard_metrics(
        manager: Manager,
        requested_hostel_id: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Aggregate overview statistics, room statuses, and recent activity
        scoped to the manager's authorized hostel(s).
        
        Returns:
            (dashboard_data, error_message, status_code)
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, requested_hostel_id)
        if err:
            return None, err, 403

        if not hostel_ids:
            return {
                "overview": {
                    "total_rooms": 0,
                    "occupied_rooms": 0,
                    "available_rooms": 0,
                    "maintenance_rooms": 0,
                    "occupancy_rate": 0.0,
                    "total_students": 0,
                    "pending_bookings": 0,
                    "pending_payments": 0,
                    "overdue_payments": 0,
                    "pending_complaints": 0,
                    "pending_maintenance": 0,
                },
                "room_status": {
                    "occupied": 0,
                    "available": 0,
                    "partially_occupied": 0,
                    "maintenance": 0,
                },
                "recent_bookings": [],
                "recent_students": [],
                "recent_complaints": [],
                "maintenance_requests": [],
                "recent_payments": [],
            }, None, 200

        # 1. Rooms Overview
        rooms_query = Room.query.filter(Room.hostel_id.in_(hostel_ids))
        total_rooms = rooms_query.count()
        occupied_rooms = rooms_query.filter(Room.status == RoomStatus.OCCUPIED).count()
        available_rooms = rooms_query.filter(Room.status == RoomStatus.AVAILABLE).count()
        maintenance_rooms = rooms_query.filter(Room.status == RoomStatus.MAINTENANCE).count()
        partially_occupied_rooms = rooms_query.filter(Room.status == RoomStatus.PARTIALLY_OCCUPIED).count()

        # Calculate total bed capacity for precise occupancy rate
        total_capacity = db.session.query(
            func.coalesce(func.sum(Room.capacity), 0)
        ).filter(Room.hostel_id.in_(hostel_ids)).scalar()

        # 2. Students Count
        total_students = Student.query.filter(
            Student.hostel_id.in_(hostel_ids),
            Student.status == StudentStatus.ACTIVE,
        ).count()

        # Occupancy Rate (percentage of bed capacity filled or room percentage)
        if total_capacity and total_capacity > 0:
            occupancy_rate = round((total_students / total_capacity) * 100, 2)
        elif total_rooms > 0:
            occupancy_rate = round(
                ((occupied_rooms + 0.5 * partially_occupied_rooms) / total_rooms) * 100,
                2,
            )
        else:
            occupancy_rate = 0.0

        # 3. Bookings
        pending_bookings = Booking.query.filter(
            Booking.hostel_id.in_(hostel_ids),
            Booking.status == BookingStatus.PENDING,
        ).count()

        # 4. Payments
        today = date.today()
        pending_payments = Payment.query.filter(
            Payment.hostel_id.in_(hostel_ids),
            Payment.status == PaymentStatus.PENDING,
        ).count()
        overdue_payments = Payment.query.filter(
            Payment.hostel_id.in_(hostel_ids),
            db.or_(
                Payment.status == PaymentStatus.OVERDUE,
                db.and_(
                    Payment.status == PaymentStatus.PENDING,
                    Payment.due_date < today,
                ),
            ),
        ).count()

        # 5. Complaints & Maintenance
        pending_complaints = Complaint.query.filter(
            Complaint.hostel_id.in_(hostel_ids),
            Complaint.status.in_([ComplaintStatus.PENDING, ComplaintStatus.IN_PROGRESS]),
        ).count()

        pending_maintenance = Maintenance.query.filter(
            Maintenance.hostel_id.in_(hostel_ids),
            Maintenance.status.in_([
                MaintenanceStatus.PENDING,
                MaintenanceStatus.ASSIGNED,
                MaintenanceStatus.IN_PROGRESS,
            ]),
        ).count()

        # 6. Recent Activity Feeds (limit to top 5)
        recent_bookings = [
            b.to_dict(include_details=True)
            for b in Booking.query.filter(Booking.hostel_id.in_(hostel_ids))
            .order_by(Booking.created_at.desc())
            .limit(5)
            .all()
        ]

        recent_students = [
            s.to_dict(include_room=True)
            for s in Student.query.filter(Student.hostel_id.in_(hostel_ids))
            .order_by(Student.created_at.desc())
            .limit(5)
            .all()
        ]

        recent_complaints = [
            c.to_dict(include_student=True)
            for c in Complaint.query.filter(Complaint.hostel_id.in_(hostel_ids))
            .order_by(Complaint.created_at.desc())
            .limit(5)
            .all()
        ]

        maintenance_requests = [
            m.to_dict(include_details=True)
            for m in Maintenance.query.filter(Maintenance.hostel_id.in_(hostel_ids))
            .order_by(Maintenance.created_at.desc())
            .limit(5)
            .all()
        ]

        recent_payments = [
            p.to_dict(include_details=True)
            for p in Payment.query.filter(Payment.hostel_id.in_(hostel_ids))
            .order_by(Payment.created_at.desc())
            .limit(5)
            .all()
        ]

        result = {
            "overview": {
                "total_rooms": total_rooms,
                "occupied_rooms": occupied_rooms,
                "available_rooms": available_rooms,
                "maintenance_rooms": maintenance_rooms,
                "occupancy_rate": occupancy_rate,
                "total_students": total_students,
                "pending_bookings": pending_bookings,
                "pending_payments": pending_payments,
                "overdue_payments": overdue_payments,
                "pending_complaints": pending_complaints,
                "pending_maintenance": pending_maintenance,
            },
            "room_status": {
                "occupied": occupied_rooms,
                "available": available_rooms,
                "partially_occupied": partially_occupied_rooms,
                "maintenance": maintenance_rooms,
            },
            "recent_bookings": recent_bookings,
            "recent_students": recent_students,
            "recent_complaints": recent_complaints,
            "maintenance_requests": maintenance_requests,
            "recent_payments": recent_payments,
        }

        return result, None, 200
