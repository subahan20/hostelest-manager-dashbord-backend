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
    Maintenance,
    MaintenanceCategory,
    MaintenancePriority,
    MaintenanceStatus,
)


def setup_maintenance_test_data(session):
    owner_user = User(name="Owner Maint", email="owner_maint@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel Maint",
        address="101 Maint Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500060",
        contact_email="maint@test.com",
    )
    session.add(hostel_assigned)
    session.commit()

    mgr_user = User(name="Manager Maint", email="mgr_maint@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-MAINT")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel_assigned.id)
    session.add(mh)
    session.commit()

    room = Room(hostel_id=hostel_assigned.id, room_number="201", capacity=2, rent=8000)
    session.add(room)
    session.commit()

    m1 = Maintenance(
        hostel_id=hostel_assigned.id,
        room_id=room.id,
        title="AC Gas Refill",
        description="Room 201 AC is blowing warm air",
        category=MaintenanceCategory.APPLIANCE,
        priority=MaintenancePriority.HIGH,
        status=MaintenanceStatus.PENDING,
        estimated_cost=2500.0,
    )
    session.add(m1)
    session.commit()

    return {
        "manager_user": mgr_user,
        "hostel": hostel_assigned,
        "room": room,
        "maintenance": m1,
    }


def test_list_maintenance(client, session):
    data = setup_maintenance_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/manager/maintenance", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["pagination"]["total"] == 1
    assert len(json_data["data"]) == 1


def test_create_maintenance(client, session):
    data = setup_maintenance_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "hostel_id": str(data["hostel"].id),
        "room_id": str(data["room"].id),
        "title": "Geyser Heating Issue",
        "description": "Geyser MCB trips frequently",
        "category": "electrical",
        "priority": "high",
        "estimated_cost": 1200.0,
    }
    res = client.post("/api/manager/maintenance", json=payload, headers=headers)
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["title"] == "Geyser Heating Issue"
    assert json_data["data"]["status"] == "pending"


def test_assign_maintenance(client, session):
    data = setup_maintenance_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "assigned_to": "Urban Company AC Tech",
        "notes": "Technician scheduled for 3 PM",
        "estimated_cost": 2200.0,
    }
    res = client.post(
        f"/api/manager/maintenance/{data['maintenance'].id}/assign",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "assigned"
    assert json_data["data"]["assigned_to"] == "Urban Company AC Tech"


def test_update_maintenance_status_complete(client, session):
    data = setup_maintenance_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "status": "completed",
        "actual_cost": 2300.0,
    }
    res = client.patch(
        f"/api/manager/maintenance/{data['maintenance'].id}/status",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "completed"
    assert json_data["data"]["actual_cost"] == 2300.0
    assert json_data["data"]["completed_at"] is not None
