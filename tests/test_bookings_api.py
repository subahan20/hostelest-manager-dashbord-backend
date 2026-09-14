from datetime import date
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
)


def setup_booking_test_data(session):
    owner_user = User(name="Owner Book", email="owner_book@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel = Hostel(
        owner_id=owner.id,
        name="Booking Test Hostel",
        address="303 Booking Ave",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500040",
        contact_email="book@test.com",
    )
    session.add(hostel)
    session.commit()

    mgr_user = User(name="Manager Book", email="mgr_book@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-BK")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel.id)
    session.add(mh)
    session.commit()

    # Room with capacity 1
    room_1 = Room(hostel_id=hostel.id, room_number="101", capacity=1, rent=9000, status=RoomStatus.AVAILABLE)
    session.add(room_1)
    session.commit()

    student_1 = Student(hostel_id=hostel.id, name="Student One", phone="+919000000011", joining_date=date(2026, 1, 1), status=StudentStatus.INACTIVE)
    student_2 = Student(hostel_id=hostel.id, name="Student Two", phone="+919000000022", joining_date=date(2026, 1, 1), status=StudentStatus.INACTIVE)
    session.add_all([student_1, student_2])
    session.commit()

    return {
        "manager_user": mgr_user,
        "manager": manager,
        "hostel": hostel,
        "room_1": room_1,
        "student_1": student_1,
        "student_2": student_2,
    }


def test_booking_lifecycle_and_actions(app, client, session):
    data = setup_booking_test_data(session)
    mgr_user = data["manager_user"]
    hostel = data["hostel"]
    room_1 = data["room_1"]
    student_1 = data["student_1"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # 1. Create Booking
    payload = {
        "hostel_id": str(hostel.id),
        "room_id": str(room_1.id),
        "student_id": str(student_1.id),
        "check_in_date": "2026-02-01",
        "amount": 9000.0,
        "security_deposit": 5000.0,
    }
    res_create = client.post("/api/manager/bookings", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res_create.status_code == 201
    booking_id = res_create.get_json()["data"]["id"]
    assert res_create.get_json()["data"]["status"] == "pending"

    # 2. Approve Booking
    res_app = client.post(f"/api/manager/bookings/{booking_id}/approve", headers={"Authorization": f"Bearer {token}"})
    assert res_app.status_code == 200
    assert res_app.get_json()["data"]["status"] == "approved"

    # 3. Check-in Booking (ACID transaction)
    res_ci = client.post(f"/api/manager/bookings/{booking_id}/check-in", headers={"Authorization": f"Bearer {token}"})
    assert res_ci.status_code == 200
    assert res_ci.get_json()["data"]["status"] == "checked_in"

    # Verify student is active and assigned to room
    session.refresh(student_1)
    assert student_1.status == StudentStatus.ACTIVE
    assert str(student_1.room_id) == str(room_1.id)

    # Verify room is occupied (capacity 1 is full)
    session.refresh(room_1)
    assert room_1.available_beds == 0
    assert room_1.status == RoomStatus.OCCUPIED

    # 4. Check-out Booking (ACID transaction)
    res_co = client.post(f"/api/manager/bookings/{booking_id}/check-out", headers={"Authorization": f"Bearer {token}"})
    assert res_co.status_code == 200
    assert res_co.get_json()["data"]["status"] == "checked_out"

    # Verify student is checked out and detached from room
    session.refresh(student_1)
    assert student_1.status == StudentStatus.CHECKED_OUT
    assert student_1.room_id is None

    # Verify room is available again
    session.refresh(room_1)
    assert room_1.available_beds == 1
    assert room_1.status == RoomStatus.AVAILABLE


def test_overbooking_prevention_on_checkin(app, client, session):
    data = setup_booking_test_data(session)
    mgr_user = data["manager_user"]
    hostel = data["hostel"]
    room_1 = data["room_1"]
    student_1 = data["student_1"]
    student_2 = data["student_2"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # Create & Check in first student (fills room capacity of 1)
    b1 = Booking(
        hostel_id=hostel.id,
        room_id=room_1.id,
        student_id=student_1.id,
        booking_reference="HST-TEST-001",
        check_in_date=date(2026, 1, 1),
        status=BookingStatus.APPROVED,
    )
    session.add(b1)
    session.commit()

    res_ci1 = client.post(f"/api/manager/bookings/{b1.id}/check-in", headers={"Authorization": f"Bearer {token}"})
    assert res_ci1.status_code == 200

    # Create second booking for the same room
    b2 = Booking(
        hostel_id=hostel.id,
        room_id=room_1.id,
        student_id=student_2.id,
        booking_reference="HST-TEST-002",
        check_in_date=date(2026, 1, 2),
        status=BookingStatus.APPROVED,
    )
    session.add(b2)
    session.commit()

    # Attempt check in on fully occupied room -> Overbooking prevented (409 Conflict)
    res_ci2 = client.post(f"/api/manager/bookings/{b2.id}/check-in", headers={"Authorization": f"Bearer {token}"})
    assert res_ci2.status_code == 409
    assert "Overbooking prevented" in res_ci2.get_json()["message"]


def test_booking_rejection_and_cancellation(app, client, session):
    data = setup_booking_test_data(session)
    mgr_user = data["manager_user"]
    hostel = data["hostel"]
    student_1 = data["student_1"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    b = Booking(
        hostel_id=hostel.id,
        student_id=student_1.id,
        booking_reference="HST-TEST-003",
        check_in_date=date(2026, 1, 1),
        status=BookingStatus.PENDING,
    )
    session.add(b)
    session.commit()

    # Reject booking
    res_rej = client.post(
        f"/api/manager/bookings/{b.id}/reject",
        json={"reason": "No single rooms available for requested dates."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_rej.status_code == 200
    assert res_rej.get_json()["data"]["status"] == "rejected"
