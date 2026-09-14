from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import func, case
from app.extensions import db
from app.models import (
    Manager,
    Hostel,
    Room,
    RoomStatus,
    Student,
    StudentStatus,
    Booking,
    BookingStatus,
    Payment,
    PaymentStatus,
    PaymentType,
    PaymentMethod,
)
from app.middleware.permissions import get_scoped_hostel_ids


def _parse_dates(from_date_str: Optional[str], to_date_str: Optional[str]) -> Tuple[date, date]:
    """Parse string dates to date objects with default fallback (last 30 days)."""
    today = date.today()
    if to_date_str:
        try:
            to_d = datetime.strptime(to_date_str, "%Y-%m-%d").date()
        except ValueError:
            to_d = today
    else:
        to_d = today

    if from_date_str:
        try:
            from_d = datetime.strptime(from_date_str, "%Y-%m-%d").date()
        except ValueError:
            from_d = to_d - timedelta(days=30)
    else:
        from_d = to_d - timedelta(days=30)

    if from_d > to_d:
        from_d, to_d = to_d, from_d

    return from_d, to_d


class ReportService:
    """Service providing chart-friendly analytics and business reports for managers."""

    @staticmethod
    def get_occupancy_report(
        manager: Manager,
        hostel_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Generate room and bed occupancy report.
        """
        scoped_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, err, 403

        if not scoped_ids:
            return {
                "summary": {
                    "total_rooms": 0,
                    "total_capacity": 0,
                    "total_occupied_beds": 0,
                    "total_available_beds": 0,
                    "occupancy_rate": 0.0,
                },
                "by_room_type": [],
                "by_floor": [],
                "by_hostel": [],
            }, None, 200

        # Query all rooms across scoped hostels
        rooms = Room.query.filter(Room.hostel_id.in_(scoped_ids)).all()
        active_students = Student.query.filter(
            Student.hostel_id.in_(scoped_ids),
            Student.status == StudentStatus.ACTIVE,
            Student.room_id.isnot(None),
        ).all()

        total_rooms = len(rooms)
        total_capacity = sum(r.capacity for r in rooms)
        total_occupied = len(active_students)
        total_available = max(0, total_capacity - total_occupied)
        occupancy_rate = round((total_occupied / total_capacity * 100), 2) if total_capacity > 0 else 0.0

        # Breakdown by room type
        room_types_map: Dict[str, Dict[str, Any]] = {}
        for r in rooms:
            rtype = r.room_type or "other"
            if rtype not in room_types_map:
                room_types_map[rtype] = {"room_type": rtype, "rooms_count": 0, "capacity": 0, "occupied": 0}
            room_types_map[rtype]["rooms_count"] += 1
            room_types_map[rtype]["capacity"] += r.capacity

        # Count occupied by room type
        room_lookup = {r.id: r for r in rooms}
        for s in active_students:
            r = room_lookup.get(s.room_id)
            if r:
                rtype = r.room_type or "other"
                if rtype in room_types_map:
                    room_types_map[rtype]["occupied"] += 1

        by_room_type = []
        for rtype, val in room_types_map.items():
            cap = val["capacity"]
            occ = val["occupied"]
            val["available"] = max(0, cap - occ)
            val["occupancy_rate"] = round((occ / cap * 100), 2) if cap > 0 else 0.0
            by_room_type.append(val)

        # Breakdown by floor
        floor_map: Dict[str, Dict[str, Any]] = {}
        for r in rooms:
            fl = str(r.floor) if r.floor is not None else "G"
            if fl not in floor_map:
                floor_map[fl] = {"floor": fl, "rooms_count": 0, "capacity": 0, "occupied": 0}
            floor_map[fl]["rooms_count"] += 1
            floor_map[fl]["capacity"] += r.capacity

        for s in active_students:
            r = room_lookup.get(s.room_id)
            if r:
                fl = str(r.floor) if r.floor is not None else "G"
                if fl in floor_map:
                    floor_map[fl]["occupied"] += 1

        by_floor = []
        for fl, val in sorted(floor_map.items()):
            cap = val["capacity"]
            occ = val["occupied"]
            val["available"] = max(0, cap - occ)
            val["occupancy_rate"] = round((occ / cap * 100), 2) if cap > 0 else 0.0
            by_floor.append(val)

        # Breakdown by hostel
        hostels = Hostel.query.filter(Hostel.id.in_(scoped_ids)).all()
        by_hostel = []
        for h in hostels:
            h_rooms = [r for r in rooms if r.hostel_id == h.id]
            h_students = [s for s in active_students if s.hostel_id == h.id]
            h_cap = sum(r.capacity for r in h_rooms)
            h_occ = len(h_students)
            by_hostel.append({
                "hostel_id": str(h.id),
                "hostel_name": h.name,
                "total_rooms": len(h_rooms),
                "capacity": h_cap,
                "occupied": h_occ,
                "available": max(0, h_cap - h_occ),
                "occupancy_rate": round((h_occ / h_cap * 100), 2) if h_cap > 0 else 0.0,
            })

        return {
            "summary": {
                "total_rooms": total_rooms,
                "total_capacity": total_capacity,
                "total_occupied_beds": total_occupied,
                "total_available_beds": total_available,
                "occupancy_rate": occupancy_rate,
            },
            "by_room_type": by_room_type,
            "by_floor": by_floor,
            "by_hostel": by_hostel,
        }, None, 200

    @staticmethod
    def get_bookings_report(
        manager: Manager,
        hostel_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Generate booking trends, status distribution, and timeline report.
        """
        scoped_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, err, 403

        if not scoped_ids:
            return {
                "date_range": {"from_date": str(from_date), "to_date": str(to_date)},
                "summary": {"total_bookings": 0, "total_revenue": 0.0},
                "by_status": {},
                "timeline": [],
            }, None, 200

        from_d, to_d = _parse_dates(from_date, to_date)

        query = Booking.query.filter(
            Booking.hostel_id.in_(scoped_ids),
            Booking.booking_date >= from_d,
            Booking.booking_date <= to_d,
        )
        bookings = query.all()

        total_bookings = len(bookings)
        total_revenue = sum(float(b.amount) for b in bookings if b.amount is not None and b.status in [BookingStatus.APPROVED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT])

        # By status
        status_counts = {
            BookingStatus.PENDING: 0,
            BookingStatus.APPROVED: 0,
            BookingStatus.CHECKED_IN: 0,
            BookingStatus.CHECKED_OUT: 0,
            BookingStatus.CANCELLED: 0,
            BookingStatus.REJECTED: 0,
        }
        for b in bookings:
            if b.status in status_counts:
                status_counts[b.status] += 1

        # Timeline by date (Daily count suitable for Chart.js/Recharts)
        timeline_map: Dict[str, Dict[str, Any]] = {}
        curr = from_d
        while curr <= to_d:
            d_str = curr.isoformat()
            timeline_map[d_str] = {
                "date": d_str,
                "total": 0,
                "pending": 0,
                "approved": 0,
                "checked_in": 0,
                "cancelled": 0,
            }
            curr += timedelta(days=1)

        for b in bookings:
            d_str = b.booking_date.isoformat() if b.booking_date else None
            if d_str and d_str in timeline_map:
                timeline_map[d_str]["total"] += 1
                if b.status in timeline_map[d_str]:
                    timeline_map[d_str][b.status] += 1

        timeline = sorted(timeline_map.values(), key=lambda x: x["date"])

        return {
            "date_range": {
                "from_date": from_d.isoformat(),
                "to_date": to_d.isoformat(),
            },
            "summary": {
                "total_bookings": total_bookings,
                "total_revenue": round(total_revenue, 2),
                "active_reservations": status_counts[BookingStatus.APPROVED] + status_counts[BookingStatus.CHECKED_IN],
                "cancellation_rate": round((status_counts[BookingStatus.CANCELLED] / total_bookings * 100), 2) if total_bookings > 0 else 0.0,
            },
            "by_status": status_counts,
            "timeline": timeline,
        }, None, 200

    @staticmethod
    def get_payments_report(
        manager: Manager,
        hostel_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Generate financial revenue, collection vs pending, and payment methods report.
        """
        scoped_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, err, 403

        if not scoped_ids:
            return {
                "date_range": {"from_date": str(from_date), "to_date": str(to_date)},
                "summary": {"total_billed": 0.0, "total_collected": 0.0, "total_pending": 0.0, "total_overdue": 0.0, "collection_rate": 0.0},
                "by_type": {},
                "by_method": {},
                "timeline": [],
            }, None, 200

        from_d, to_d = _parse_dates(from_date, to_date)

        # Retrieve payments with created_at in range
        from_dt = datetime.combine(from_d, datetime.min.time()).replace(tzinfo=timezone.utc)
        to_dt = datetime.combine(to_d, datetime.max.time()).replace(tzinfo=timezone.utc)

        payments = Payment.query.filter(
            Payment.hostel_id.in_(scoped_ids),
            Payment.created_at >= from_dt,
            Payment.created_at <= to_dt,
        ).all()

        total_billed = sum(float(p.amount) for p in payments if p.amount is not None)
        total_collected = sum(float(p.amount) for p in payments if p.amount is not None and p.status == PaymentStatus.PAID)
        total_pending = sum(float(p.amount) for p in payments if p.amount is not None and p.status == PaymentStatus.PENDING)
        total_overdue = sum(float(p.amount) for p in payments if p.amount is not None and p.status == PaymentStatus.OVERDUE)
        collection_rate = round((total_collected / total_billed * 100), 2) if total_billed > 0 else 0.0

        # By type
        by_type: Dict[str, Dict[str, Any]] = {
            PaymentType.RENT: {"total": 0.0, "collected": 0.0, "count": 0},
            PaymentType.DEPOSIT: {"total": 0.0, "collected": 0.0, "count": 0},
            PaymentType.MAINTENANCE: {"total": 0.0, "collected": 0.0, "count": 0},
            PaymentType.OTHER: {"total": 0.0, "collected": 0.0, "count": 0},
        }
        for p in payments:
            ptype = p.payment_type or PaymentType.OTHER
            if ptype not in by_type:
                by_type[ptype] = {"total": 0.0, "collected": 0.0, "count": 0}
            amt = float(p.amount) if p.amount is not None else 0.0
            by_type[ptype]["total"] += amt
            by_type[ptype]["count"] += 1
            if p.status == PaymentStatus.PAID:
                by_type[ptype]["collected"] += amt

        # By method
        by_method: Dict[str, Dict[str, Any]] = {
            PaymentMethod.UPI: {"amount": 0.0, "count": 0},
            PaymentMethod.CASH: {"amount": 0.0, "count": 0},
            PaymentMethod.BANK_TRANSFER: {"amount": 0.0, "count": 0},
            PaymentMethod.CARD: {"amount": 0.0, "count": 0},
            PaymentMethod.ONLINE: {"amount": 0.0, "count": 0},
        }
        for p in payments:
            if p.status == PaymentStatus.PAID and p.payment_method:
                pmeth = p.payment_method
                if pmeth not in by_method:
                    by_method[pmeth] = {"amount": 0.0, "count": 0}
                amt = float(p.amount) if p.amount is not None else 0.0
                by_method[pmeth]["amount"] += amt
                by_method[pmeth]["count"] += 1

        # Timeline (Collections over the date range)
        timeline_map: Dict[str, Dict[str, Any]] = {}
        curr = from_d
        while curr <= to_d:
            d_str = curr.isoformat()
            timeline_map[d_str] = {"date": d_str, "billed": 0.0, "collected": 0.0}
            curr += timedelta(days=1)

        for p in payments:
            d_str = p.created_at.date().isoformat() if p.created_at else None
            amt = float(p.amount) if p.amount is not None else 0.0
            if d_str and d_str in timeline_map:
                timeline_map[d_str]["billed"] += amt
                if p.status == PaymentStatus.PAID:
                    timeline_map[d_str]["collected"] += amt

        timeline = sorted(timeline_map.values(), key=lambda x: x["date"])

        return {
            "date_range": {
                "from_date": from_d.isoformat(),
                "to_date": to_d.isoformat(),
            },
            "summary": {
                "total_billed": round(total_billed, 2),
                "total_collected": round(total_collected, 2),
                "total_pending": round(total_pending, 2),
                "total_overdue": round(total_overdue, 2),
                "collection_rate": collection_rate,
            },
            "by_type": by_type,
            "by_method": by_method,
            "timeline": timeline,
        }, None, 200

    @staticmethod
    def get_students_report(
        manager: Manager,
        hostel_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """
        Generate student demographics, college/company affiliation, and admission/checkout report.
        """
        scoped_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, err, 403

        if not scoped_ids:
            return {
                "summary": {"total_active": 0, "total_admissions": 0, "total_checked_out": 0},
                "by_gender": {},
                "top_colleges": [],
                "top_companies": [],
                "by_status": {},
            }, None, 200

        from_d, to_d = _parse_dates(from_date, to_date)

        all_students = Student.query.filter(Student.hostel_id.in_(scoped_ids)).all()

        total_active = sum(1 for s in all_students if s.status == StudentStatus.ACTIVE)
        admissions_in_range = sum(
            1 for s in all_students
            if s.joining_date and from_d <= s.joining_date <= to_d
        )
        checkouts_in_range = sum(
            1 for s in all_students
            if s.leaving_date and from_d <= s.leaving_date <= to_d and s.status == StudentStatus.CHECKED_OUT
        )

        # By status
        by_status = {
            StudentStatus.ACTIVE: 0,
            StudentStatus.INACTIVE: 0,
            StudentStatus.CHECKED_OUT: 0,
            StudentStatus.SUSPENDED: 0,
        }
        for s in all_students:
            if s.status in by_status:
                by_status[s.status] += 1

        # Demographics: Gender (Active students)
        gender_map: Dict[str, int] = {}
        college_map: Dict[str, int] = {}
        company_map: Dict[str, int] = {}

        for s in all_students:
            if s.status == StudentStatus.ACTIVE:
                # Gender
                g = (s.gender or "unspecified").capitalize()
                gender_map[g] = gender_map.get(g, 0) + 1

                # College
                if s.college and s.college.strip():
                    c_name = s.college.strip()
                    college_map[c_name] = college_map.get(c_name, 0) + 1

                # Company
                if s.company and s.company.strip():
                    comp_name = s.company.strip()
                    company_map[comp_name] = company_map.get(comp_name, 0) + 1

        top_colleges = [
            {"college": k, "count": v}
            for k, v in sorted(college_map.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        top_companies = [
            {"company": k, "count": v}
            for k, v in sorted(company_map.items(), key=lambda item: item[1], reverse=True)[:10]
        ]

        return {
            "date_range": {
                "from_date": from_d.isoformat(),
                "to_date": to_d.isoformat(),
            },
            "summary": {
                "total_active": total_active,
                "admissions_in_period": admissions_in_range,
                "checkouts_in_period": checkouts_in_range,
            },
            "by_status": by_status,
            "by_gender": gender_map,
            "top_colleges": top_colleges,
            "top_companies": top_companies,
        }, None, 200
