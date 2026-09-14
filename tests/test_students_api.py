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
)


def setup_student_test_data(session):
    owner_user = User(name="Owner Stu", email="owner_stu@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel Stu",
        address="101 Student Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500030",
        contact_email="stu@test.com",
    )
    session.add(hostel_assigned)
    session.commit()

    mgr_user = User(name="Manager Stu", email="mgr_stu@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-STU")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel_assigned.id)
    session.add(mh)
    session.commit()

    # Room with capacity 1
    room_single = Room(hostel_id=hostel_assigned.id, room_number="101", capacity=1, rent=10000, status=RoomStatus.AVAILABLE)
    # Room with capacity 2
    room_double = Room(hostel_id=hostel_assigned.id, room_number="102", capacity=2, rent=7000, status=RoomStatus.AVAILABLE)
    session.add_all([room_single, room_double])
    session.commit()

    # Student 1
    s1 = Student(
        hostel_id=hostel_assigned.id,
        room_id=room_single.id,
        name="Rahul Sharma",
        phone="+919876543201",
        email="rahul@test.com",
        joining_date=date(2026, 1, 1),
        status=StudentStatus.ACTIVE,
    )
    session.add(s1)
    session.commit()

    return {
        "manager_user": mgr_user,
        "manager": manager,
        "hostel": hostel_assigned,
        "room_single": room_single,
        "room_double": room_double,
        "student_1": s1,
    }


def test_list_students_and_search(app, client, session):
    data = setup_student_test_data(session)
    mgr_user = data["manager_user"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # List all
    res = client.get("/api/manager/students", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["success"] is True
    assert len(res_json["data"]) == 1

    # Search by name "Rahul"
    res_search = client.get("/api/manager/students?search=rahul", headers={"Authorization": f"Bearer {token}"})
    assert len(res_search.get_json()["data"]) == 1

    # Search non-matching
    res_none = client.get("/api/manager/students?search=nomatch", headers={"Authorization": f"Bearer {token}"})
    assert len(res_none.get_json()["data"]) == 0


def test_create_student_and_capacity_check(app, client, session):
    data = setup_student_test_data(session)
    mgr_user = data["manager_user"]
    hostel = data["hostel"]
    room_single = data["room_single"]
    room_double = data["room_double"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # Try assigning to room_single which is already full (capacity 1, 1 active student) -> 400
    payload_full = {
        "hostel_id": str(hostel.id),
        "room_id": str(room_single.id),
        "name": "Amit Shah",
        "phone": "+919876543202",
        "joining_date": "2026-02-01",
    }
    res_full = client.post("/api/manager/students", json=payload_full, headers={"Authorization": f"Bearer {token}"})
    assert res_full.status_code == 400
    assert "fully occupied" in res_full.get_json()["message"]

    # Assign to room_double which has available bed -> 201
    payload_ok = {
        "hostel_id": str(hostel.id),
        "room_id": str(room_double.id),
        "name": "Amit Shah",
        "phone": "+919876543202",
        "joining_date": "2026-02-01",
    }
    res_ok = client.post("/api/manager/students", json=payload_ok, headers={"Authorization": f"Bearer {token}"})
    assert res_ok.status_code == 201
    assert res_ok.get_json()["data"]["name"] == "Amit Shah"


def test_update_student_status_checkout_frees_room(app, client, session):
    data = setup_student_test_data(session)
    mgr_user = data["manager_user"]
    s1 = data["student_1"]
    room_single = data["room_single"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # Check out student 1
    res_co = client.patch(
        f"/api/manager/students/{s1.id}/status",
        json={"status": "checked_out"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_co.status_code == 200
    assert res_co.get_json()["data"]["status"] == "checked_out"

    # Verify room is now available
    session.refresh(room_single)
    assert room_single.available_beds == 1
    assert room_single.status == RoomStatus.AVAILABLE
