from datetime import datetime, timezone, date
from flask_jwt_extended import create_access_token
from app.models import (
    User,
    UserRole,
    Owner,
    Manager,
    Hostel,
    ManagerHostel,
    Room,
    Student,
    Visitor,
)


def setup_visitor_test_data(session):
    owner_user = User(name="Owner Vis", email="owner_vis@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel Vis",
        address="101 Vis Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500070",
        contact_email="vis@test.com",
    )
    session.add(hostel_assigned)
    session.commit()

    mgr_user = User(name="Manager Vis", email="mgr_vis@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-VIS")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel_assigned.id)
    session.add(mh)
    session.commit()

    room = Room(hostel_id=hostel_assigned.id, room_number="301", capacity=2, rent=8000)
    session.add(room)
    session.commit()

    student = Student(
        hostel_id=hostel_assigned.id,
        room_id=room.id,
        name="Vis Student",
        phone="+919876543221",
        emergency_contact_phone="+919876543222",
        emergency_contact_name="Vis Guardian",
        joining_date=date.today(),
    )
    session.add(student)
    session.commit()

    v1 = Visitor(
        hostel_id=hostel_assigned.id,
        student_id=student.id,
        visitor_name="Rajesh Sharma",
        phone="+919876543223",
        purpose="Parent visiting",
        id_type="Aadhaar",
        id_reference="XXXX-XXXX-1234",
        check_in=datetime.now(timezone.utc),
    )
    session.add(v1)
    session.commit()

    return {
        "manager_user": mgr_user,
        "hostel": hostel_assigned,
        "student": student,
        "visitor": v1,
    }


def test_list_visitors(client, session):
    data = setup_visitor_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/manager/visitors", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["pagination"]["total"] == 1
    assert len(json_data["data"]) == 1


def test_create_visitor(client, session):
    data = setup_visitor_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "hostel_id": str(data["hostel"].id),
        "student_id": str(data["student"].id),
        "visitor_name": "Anita Sharma",
        "phone": "+919876543224",
        "purpose": "Friend visit",
    }
    res = client.post("/api/manager/visitors", json=payload, headers=headers)
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["visitor_name"] == "Anita Sharma"
    assert json_data["data"]["check_in"] is not None
    assert json_data["data"]["check_out"] is None


def test_checkout_visitor(client, session):
    data = setup_visitor_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(f"/api/manager/visitors/{data['visitor'].id}/checkout", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["check_out"] is not None
