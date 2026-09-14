from datetime import date, datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import (
    User,
    UserRole,
    Owner,
    Hostel,
    Room,
    RoomType,
    RoomStatus,
    Student,
    StudentStatus,
    Booking,
    BookingStatus,
    Payment,
    PaymentType,
    PaymentStatus,
    PaymentMethod,
    Complaint,
    ComplaintPriority,
    ComplaintStatus,
    Maintenance,
    MaintenanceCategory,
    MaintenancePriority,
    MaintenanceStatus,
    Visitor,
    VisitorIdType,
    Notice,
    NoticePriority,
    NoticeStatus,
)


@pytest.fixture
def base_hostel_setup(session):
    """Fixture providing a base Owner and Hostel."""
    user = User(name="Owner X", email="ownerx@test.com", role=UserRole.OWNER, is_active=True)
    user.set_password("pass")
    session.add(user)
    session.commit()

    owner = Owner(user_id=user.id)
    session.add(owner)
    session.commit()

    hostel = Hostel(
        owner_id=owner.id,
        name="Hostel Grand",
        address="123 Hitech City Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876543210",
        contact_email="grand@test.com",
    )
    session.add(hostel)
    session.commit()
    return hostel


def test_room_creation_and_occupancy(session, base_hostel_setup):
    """Test Room creation, constraints, and occupancy calculation."""
    hostel = base_hostel_setup

    room = Room(
        hostel_id=hostel.id,
        room_number="101",
        floor=1,
        room_type=RoomType.DOUBLE,
        capacity=2,
        rent=8500.00,
        status=RoomStatus.AVAILABLE,
    )
    session.add(room)
    session.commit()

    assert room.id is not None
    assert room.current_occupancy == 0
    assert room.available_beds == 2

    # Add 1 active student
    student = Student(
        hostel_id=hostel.id,
        room_id=room.id,
        name="Rahul Verma",
        phone="+919988776655",
        joining_date=date(2026, 1, 15),
        status=StudentStatus.ACTIVE,
    )
    session.add(student)
    session.commit()

    session.refresh(room)
    assert room.current_occupancy == 1
    assert room.available_beds == 1
    assert room.to_dict()["current_occupancy"] == 1


def test_room_unique_number_per_hostel(session, base_hostel_setup):
    """Test that room numbers must be unique within the same hostel."""
    hostel = base_hostel_setup

    r1 = Room(hostel_id=hostel.id, room_number="201", capacity=2, rent=7000.00)
    session.add(r1)
    session.commit()

    r2 = Room(hostel_id=hostel.id, room_number="201", capacity=3, rent=6000.00)
    session.add(r2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_student_and_booking_lifecycle(session, base_hostel_setup):
    """Test Student creation and linked Booking."""
    hostel = base_hostel_setup

    room = Room(hostel_id=hostel.id, room_number="301", capacity=1, rent=12000.00)
    session.add(room)
    session.commit()

    student = Student(
        hostel_id=hostel.id,
        room_id=room.id,
        name="Priya Sharma",
        email="priya@test.com",
        phone="+919876512345",
        gender="female",
        joining_date=date(2026, 2, 1),
        emergency_contact_name="Sunil Sharma",
        emergency_contact_phone="+919876512346",
        status=StudentStatus.ACTIVE,
    )
    session.add(student)
    session.commit()

    ref = Booking.generate_reference()
    assert ref.startswith("HST-")

    booking = Booking(
        hostel_id=hostel.id,
        room_id=room.id,
        student_id=student.id,
        booking_reference=ref,
        check_in_date=date(2026, 2, 1),
        amount=12000.00,
        security_deposit=5000.00,
        status=BookingStatus.CHECKED_IN,
    )
    session.add(booking)
    session.commit()

    assert booking.id is not None
    assert booking.booking_reference == ref
    assert booking.student.name == "Priya Sharma"
    assert booking.room.room_number == "301"


def test_payment_creation_and_associations(session, base_hostel_setup):
    """Test Payment model creation with rent and deposit."""
    hostel = base_hostel_setup

    student = Student(
        hostel_id=hostel.id,
        name="Anil Kumar",
        phone="+919112233445",
        joining_date=date(2026, 3, 1),
    )
    session.add(student)
    session.commit()

    payment = Payment(
        hostel_id=hostel.id,
        student_id=student.id,
        amount=8500.00,
        payment_type=PaymentType.RENT,
        payment_method=PaymentMethod.UPI,
        transaction_reference="UPI/20260301/998877",
        status=PaymentStatus.PAID,
        paid_at=datetime.now(timezone.utc),
    )
    session.add(payment)
    session.commit()

    assert payment.id is not None
    assert payment.student_id == student.id
    assert payment.status == PaymentStatus.PAID
    assert payment.to_dict()["payment_type"] == "rent"


def test_complaint_and_resolution(session, base_hostel_setup):
    """Test Complaint tracking and resolution."""
    hostel = base_hostel_setup

    student = Student(
        hostel_id=hostel.id,
        name="Vikram Rao",
        phone="+919223344556",
        joining_date=date(2026, 4, 1),
    )
    session.add(student)
    session.commit()

    complaint = Complaint(
        hostel_id=hostel.id,
        student_id=student.id,
        title="Wi-Fi not working on 3rd floor",
        description="Speed is dropping frequently in room 302",
        priority=ComplaintPriority.HIGH,
        status=ComplaintStatus.PENDING,
    )
    session.add(complaint)
    session.commit()

    # Resolve complaint
    complaint.status = ComplaintStatus.RESOLVED
    complaint.resolved_at = datetime.now(timezone.utc)
    complaint.resolution_notes = "Router rebooted and firmware updated."
    session.commit()

    assert complaint.status == ComplaintStatus.RESOLVED
    assert complaint.resolved_at is not None


def test_maintenance_lifecycle(session, base_hostel_setup):
    """Test Maintenance request with costs and status."""
    hostel = base_hostel_setup

    room = Room(hostel_id=hostel.id, room_number="405", capacity=2, rent=9000.00)
    session.add(room)
    session.commit()

    maint = Maintenance(
        hostel_id=hostel.id,
        room_id=room.id,
        title="Geyser leakage repair",
        description="Water leaking from bottom pipe of the bathroom geyser",
        category=MaintenanceCategory.PLUMBING,
        priority=MaintenancePriority.URGENT,
        status=MaintenanceStatus.ASSIGNED,
        assigned_to="QuickPlumb Services",
        estimated_cost=1500.00,
    )
    session.add(maint)
    session.commit()

    assert maint.id is not None
    assert maint.category == MaintenanceCategory.PLUMBING
    assert maint.estimated_cost == 1500.00


def test_visitor_log(session, base_hostel_setup):
    """Test Visitor check-in and check-out tracking."""
    hostel = base_hostel_setup

    student = Student(
        hostel_id=hostel.id,
        name="Karan Patel",
        phone="+919334455667",
        joining_date=date(2026, 5, 1),
    )
    session.add(student)
    session.commit()

    visitor = Visitor(
        hostel_id=hostel.id,
        student_id=student.id,
        visitor_name="Sanjay Patel",
        phone="+919334455668",
        purpose="Parent visiting",
        id_type=VisitorIdType.AADHAAR,
        id_reference="XXXX-XXXX-1234",
    )
    session.add(visitor)
    session.commit()

    assert visitor.id is not None
    assert visitor.check_out is None

    # Check out visitor
    visitor.check_out = datetime.now(timezone.utc)
    session.commit()

    assert visitor.check_out is not None


def test_notice_publishing(session, base_hostel_setup):
    """Test Notice publishing and author association."""
    hostel = base_hostel_setup

    manager_user = User(name="Manager Notice", email="mg_notice@test.com", role=UserRole.MANAGER, is_active=True)
    manager_user.set_password("pass")
    session.add(manager_user)
    session.commit()

    notice = Notice(
        hostel_id=hostel.id,
        created_by=manager_user.id,
        title="Water Tank Cleaning on Sunday",
        content="Water supply will be interrupted between 10 AM and 2 PM on Sunday for maintenance.",
        priority=NoticePriority.HIGH,
        status=NoticeStatus.PUBLISHED,
    )
    session.add(notice)
    session.commit()

    assert notice.id is not None
    assert notice.author.name == "Manager Notice"
    assert notice.to_dict()["title"] == "Water Tank Cleaning on Sunday"
