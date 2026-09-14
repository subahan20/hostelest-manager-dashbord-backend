from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token
from app.models import (
    User,
    UserRole,
    Owner,
    Manager,
    Hostel,
    ManagerHostel,
    Notice,
    NoticePriority,
    NoticeStatus,
)


def setup_notice_test_data(session):
    owner_user = User(name="Owner Noti", email="owner_noti@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel Noti",
        address="101 Noti Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500080",
        contact_email="noti@test.com",
    )
    session.add(hostel_assigned)
    session.commit()

    mgr_user = User(name="Manager Noti", email="mgr_noti@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-NOTI")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel_assigned.id)
    session.add(mh)
    session.commit()

    n1 = Notice(
        hostel_id=hostel_assigned.id,
        created_by=mgr_user.id,
        title="Hostel Gate Timing Change",
        content="Main gate will close at 10:30 PM starting this Monday.",
        priority=NoticePriority.HIGH,
        status=NoticeStatus.PUBLISHED,
        publish_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    session.add(n1)
    session.commit()

    return {
        "manager_user": mgr_user,
        "hostel": hostel_assigned,
        "notice": n1,
    }


def test_list_notices(client, session):
    data = setup_notice_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/manager/notices", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["pagination"]["total"] == 1
    assert len(json_data["data"]) == 1


def test_create_notice(client, session):
    data = setup_notice_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "hostel_id": str(data["hostel"].id),
        "title": "Water Tank Cleaning Schedule",
        "content": "Water supply will be suspended between 2 PM and 5 PM on Saturday.",
        "priority": "high",
    }
    res = client.post("/api/manager/notices", json=payload, headers=headers)
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["title"] == "Water Tank Cleaning Schedule"
    assert json_data["data"]["priority"] == "high"


def test_update_notice(client, session):
    data = setup_notice_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "title": "Hostel Gate Timing Update (11 PM)",
        "priority": "urgent",
    }
    res = client.put(f"/api/manager/notices/{data['notice'].id}", json=payload, headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["title"] == "Hostel Gate Timing Update (11 PM)"
    assert json_data["data"]["priority"] == "urgent"


def test_delete_notice(client, session):
    data = setup_notice_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.delete(f"/api/manager/notices/{data['notice'].id}", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "Notice deleted" in json_data["message"]
