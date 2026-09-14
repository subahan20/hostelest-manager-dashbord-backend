from datetime import date, timedelta, datetime, timezone
from flask_jwt_extended import create_access_token
from app.models import (
    User,
    UserRole,
    Owner,
    Manager,
    Hostel,
    ManagerHostel,
    Room,
    RoomStatus,
    Student,
    StudentStatus,
    Booking,
    BookingStatus,
    Payment,
    PaymentType,
    PaymentMethod,
    PaymentStatus,
)


def setup_report_test_data(session):
    owner_user = User(name="Owner Rep", email="owner_rep@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel Rep",
        address="101 Report Way",
        area="Hitec City",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500090",
        contact_email="rep@test.com",
    )
    hostel_unassigned = Hostel(
        owner_id=owner.id,
        name="Unassigned Hostel Rep",
        address="102 Report Way",
        area="Gachibowli",
        city="Hyderabad",
        state="Telangana",
        pincode="500032",
        contact_phone="+919876500091",
        contact_email="unassigned_rep@test.com",
    )
    session.add_all([hostel_assigned, hostel_unassigned])
    session.commit()

    mgr_user = User(name="Manager Rep", email="mgr_rep@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-REP")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel_assigned.id)
    session.add(mh)
    session.commit()

    # Create Rooms
    r1 = Room(hostel_id=hostel_assigned.id, room_number="101", floor=1, room_type="single", capacity=1, rent=12000, status=RoomStatus.OCCUPIED)
    r2 = Room(hostel_id=hostel_assigned.id, room_number="102", floor=1, room_type="double", capacity=2, rent=8000, status=RoomStatus.AVAILABLE)
    session.add_all([r1, r2])
    session.commit()

    # Create Students
    s1 = Student(
        hostel_id=hostel_assigned.id,
        room_id=r1.id,
        name="Student Alpha",
        phone="+919876543301",
        gender="Male",
        college="IIIT Hyderabad",
        company="Microsoft",
        joining_date=date.today() - timedelta(days=10),
        status=StudentStatus.ACTIVE,
    )
    s2 = Student(
        hostel_id=hostel_assigned.id,
        room_id=r2.id,
        name="Student Beta",
        phone="+919876543302",
        gender="Female",
        college="CBIT",
        company="Google",
        joining_date=date.today() - timedelta(days=5),
        status=StudentStatus.ACTIVE,
    )
    session.add_all([s1, s2])
    session.commit()

    # Create Bookings
    b1 = Booking(
        hostel_id=hostel_assigned.id,
        room_id=r1.id,
        student_id=s1.id,
        booking_reference="HST-2026-REP001",
        booking_date=date.today() - timedelta(days=10),
        check_in_date=date.today() - timedelta(days=10),
        amount=12000.0,
        status=BookingStatus.CHECKED_IN,
    )
    b2 = Booking(
        hostel_id=hostel_assigned.id,
        room_id=r2.id,
        student_id=s2.id,
        booking_reference="HST-2026-REP002",
        booking_date=date.today() - timedelta(days=5),
        check_in_date=date.today() - timedelta(days=5),
        amount=8000.0,
        status=BookingStatus.APPROVED,
    )
    session.add_all([b1, b2])
    session.commit()

    # Create Payments
    p1 = Payment(
        hostel_id=hostel_assigned.id,
        student_id=s1.id,
        amount=12000.0,
        payment_type=PaymentType.RENT,
        payment_method=PaymentMethod.UPI,
        due_date=date.today(),
        paid_at=datetime.now(timezone.utc),
        transaction_reference="REP-TXN-1",
        status=PaymentStatus.PAID,
    )
    p2 = Payment(
        hostel_id=hostel_assigned.id,
        student_id=s2.id,
        amount=8000.0,
        payment_type=PaymentType.RENT,
        payment_method=PaymentMethod.CASH,
        due_date=date.today() + timedelta(days=5),
        status=PaymentStatus.PENDING,
    )
    session.add_all([p1, p2])
    session.commit()

    return {
        "manager_user": mgr_user,
        "hostel": hostel_assigned,
        "unassigned_hostel": hostel_unassigned,
    }


def test_occupancy_report(client, session):
    data = setup_report_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/manager/reports/occupancy", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True

    summary = json_data["data"]["summary"]
    assert summary["total_rooms"] == 2
    assert summary["total_capacity"] == 3
    assert summary["total_occupied_beds"] == 2
    assert summary["total_available_beds"] == 1
    assert summary["occupancy_rate"] == 66.67

    assert len(json_data["data"]["by_room_type"]) > 0
    assert len(json_data["data"]["by_floor"]) > 0
    assert len(json_data["data"]["by_hostel"]) == 1


def test_bookings_report(client, session):
    data = setup_report_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    from_d = (date.today() - timedelta(days=30)).isoformat()
    to_d = date.today().isoformat()
    res = client.get(f"/api/manager/reports/bookings?from_date={from_d}&to_date={to_d}", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True

    summary = json_data["data"]["summary"]
    assert summary["total_bookings"] == 2
    assert summary["total_revenue"] == 20000.0
    assert len(json_data["data"]["timeline"]) > 0


def test_payments_report(client, session):
    data = setup_report_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    from_d = (date.today() - timedelta(days=30)).isoformat()
    to_d = date.today().isoformat()
    res = client.get(f"/api/manager/reports/payments?from_date={from_d}&to_date={to_d}", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True

    summary = json_data["data"]["summary"]
    assert summary["total_billed"] == 20000.0
    assert summary["total_collected"] == 12000.0
    assert summary["total_pending"] == 8000.0
    assert summary["collection_rate"] == 60.0

    assert "by_type" in json_data["data"]
    assert "by_method" in json_data["data"]
    assert len(json_data["data"]["timeline"]) > 0


def test_students_report(client, session):
    data = setup_report_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    from_d = (date.today() - timedelta(days=30)).isoformat()
    to_d = date.today().isoformat()
    res = client.get(f"/api/manager/reports/students?from_date={from_d}&to_date={to_d}", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True

    summary = json_data["data"]["summary"]
    assert summary["total_active"] == 2
    assert summary["admissions_in_period"] == 2

    assert json_data["data"]["by_gender"]["Male"] == 1
    assert json_data["data"]["by_gender"]["Female"] == 1
    assert len(json_data["data"]["top_colleges"]) == 2
    assert len(json_data["data"]["top_companies"]) == 2


def test_reports_unauthorized_hostel_forbidden(client, session):
    data = setup_report_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Requesting report for unassigned hostel
    unauth_id = data["unassigned_hostel"].id
    res = client.get(f"/api/manager/reports/occupancy?hostel_id={unauth_id}", headers=headers)
    assert res.status_code == 403
    json_data = res.get_json()
    assert json_data["success"] is False
    assert "permission" in json_data["message"].lower()
