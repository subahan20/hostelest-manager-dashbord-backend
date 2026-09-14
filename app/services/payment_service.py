from typing import Tuple, Optional, Dict, Any, List
from datetime import date, datetime, timezone
from app.extensions import db
from app.models import Manager, Payment, PaymentStatus, Student
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class PaymentService:
    """Service handling Payments, invoicing, pending & overdue tracking."""

    @staticmethod
    def get_payments(
        manager: Manager,
        hostel_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
        payment_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List payments with filters and pagination.
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Payment.query.filter(Payment.hostel_id.in_(hostel_ids))

        if student_id:
            query = query.filter(Payment.student_id == student_id)
        if status:
            query = query.filter(Payment.status == status.strip().lower())
        if payment_type:
            query = query.filter(Payment.payment_type == payment_type.strip().lower())
        if from_date:
            query = query.filter(Payment.created_at >= from_date)
        if to_date:
            query = query.filter(Payment.created_at <= to_date)

        query = query.order_by(Payment.created_at.desc())

        items, pagination = paginate_query(query)
        payments_data = [payment.to_dict(include_details=True) for payment in items]

        return payments_data, pagination, None, 200

    @staticmethod
    def get_payment_by_id(manager: Manager, payment_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch single payment record by ID."""
        payment = db.session.get(Payment, payment_id)
        if not payment:
            return None, "Payment record not found", 404

        if not manager.has_hostel_access(payment.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return payment.to_dict(include_details=True), None, 200

    @staticmethod
    def get_pending_payments(
        manager: Manager,
        hostel_id: Optional[str] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch pending payments."""
        return PaymentService.get_payments(manager, hostel_id=hostel_id, status=PaymentStatus.PENDING)

    @staticmethod
    def get_overdue_payments(
        manager: Manager,
        hostel_id: Optional[str] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch overdue payments."""
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        today = date.today()
        query = Payment.query.filter(
            Payment.hostel_id.in_(hostel_ids),
            db.or_(
                Payment.status == PaymentStatus.OVERDUE,
                db.and_(
                    Payment.status == PaymentStatus.PENDING,
                    Payment.due_date < today,
                ),
            ),
        ).order_by(Payment.due_date.asc())

        items, pagination = paginate_query(query)
        payments_data = [payment.to_dict(include_details=True) for payment in items]

        return payments_data, pagination, None, 200

    @staticmethod
    def create_payment(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Create a new payment or invoice entry."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        student = db.session.get(Student, str(data["student_id"]))
        if not student or str(student.hostel_id) != hostel_id:
            return None, "Invalid student ID for this hostel.", 400

        payment = Payment(
            hostel_id=hostel_id,
            student_id=student.id,
            booking_id=data.get("booking_id"),
            amount=data["amount"],
            payment_type=data.get("payment_type", "rent"),
            payment_method=data.get("payment_method"),
            transaction_reference=data.get("transaction_reference"),
            due_date=data.get("due_date"),
            paid_at=data.get("paid_at") or (datetime.now(timezone.utc) if data.get("status") == PaymentStatus.PAID else None),
            status=data.get("status", PaymentStatus.PENDING),
            notes=data.get("notes"),
        )
        db.session.add(payment)
        db.session.commit()

        return payment.to_dict(include_details=True), None, 201

    @staticmethod
    def record_payment(manager: Manager, payment_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Record payment collection against an invoice."""
        payment = db.session.get(Payment, payment_id)
        if not payment:
            return None, "Payment record not found", 404

        if not manager.has_hostel_access(payment.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        if "amount" in data and data["amount"] is not None:
            payment.amount = data["amount"]
        payment.payment_method = data["payment_method"]
        payment.transaction_reference = data.get("transaction_reference")
        payment.paid_at = data.get("paid_at") or datetime.now(timezone.utc)
        payment.status = PaymentStatus.PAID
        if "notes" in data and data["notes"]:
            payment.notes = (payment.notes or "") + f" {data['notes']}".strip()

        db.session.commit()
        return payment.to_dict(include_details=True), None, 200
