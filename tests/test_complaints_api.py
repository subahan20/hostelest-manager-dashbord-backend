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
    Student,
    Complaint,
    ComplaintStatus,
    ComplaintPriority,
)


def setup_complaint_test_data(session):
    owner_user = User(name="Owner Comp", email="owner_comp@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel Comp",
        address="101 Comp Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500050",
        contact_email="comp@test.com",
    )
    session.add(hostel_assigned)
    session.commit()

    mgr_user = User(name="Manager Comp", email="mgr_comp@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-COMP")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel_assigned.id)
    session.add(mh)
    session.commit()

    room = Room(hostel_id=hostel_assigned.id, room_number="101", capacity=2, rent=8000)
    session.add(room)
    session.commit()

    student = Student(
        hostel_id=hostel_assigned.id,
        room_id=room.id,
        name="Comp Student",
        phone="+919876543211",
        emergency_contact_phone="+919876543212",
        emergency_contact_name="Comp Guardian",
        joining_date=date.today(),
    )
    session.add(student)
    session.commit()

    c1 = Complaint(
        hostel_id=hostel_assigned.id,
        student_id=student.id,
        title="Fan not working",
        description="Ceiling fan in room 101 stopped spinning",
        priority=ComplaintPriority.HIGH,
        status=ComplaintStatus.PENDING,
    )
    session.add(c1)
    session.commit()

    return {
        "manager_user": mgr_user,
        "hostel": hostel_assigned,
        "student": student,
        "complaint": c1,
    }


def test_list_complaints(client, session):
    data = setup_complaint_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/manager/complaints", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["pagination"]["total"] == 1
    assert len(json_data["data"]) == 1


def test_create_complaint(client, session):
    data = setup_complaint_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "hostel_id": str(data["hostel"].id),
        "student_id": str(data["student"].id),
        "title": "Water leakage in bathroom",
        "description": "Tap is leaking continuously",
        "priority": "medium",
    }
    res = client.post("/api/manager/complaints", json=payload, headers=headers)
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["title"] == "Water leakage in bathroom"
    assert json_data["data"]["status"] == "pending"


def test_update_complaint_status(client, session):
    data = setup_complaint_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "status": "in_progress",
        "assigned_to": "Electrician Suresh",
    }
    res = client.patch(
        f"/api/manager/complaints/{data['complaint'].id}/status",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "in_progress"
    assert json_data["data"]["assigned_to"] == "Electrician Suresh"


def test_resolve_complaint(client, session):
    data = setup_complaint_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "resolution_notes": "Replaced the capacitor in ceiling fan. Working properly now.",
    }
    res = client.post(
        f"/api/manager/complaints/{data['complaint'].id}/resolve",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "resolved"
    assert json_data["data"]["resolution_notes"] is not None
    assert json_data["data"]["resolved_at"] is not None
