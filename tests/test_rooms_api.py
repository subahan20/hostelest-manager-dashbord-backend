from flask_jwt_extended import create_access_token
from app.models import (
    User,
    UserRole,
    Owner,
    Manager,
    Hostel,
    ManagerHostel,
    Room,
    RoomType,
    RoomStatus,
)


def setup_room_test_data(session):
    owner_user = User(name="Owner Room", email="owner_room@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel",
        address="101 Tech Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500010",
        contact_email="assigned@test.com",
    )
    hostel_unassigned = Hostel(
        owner_id=owner.id,
        name="Unassigned Hostel",
        address="202 Tech Rd",
        area="Kondapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500084",
        contact_phone="+919876500020",
        contact_email="unassigned@test.com",
    )
    session.add_all([hostel_assigned, hostel_unassigned])
    session.commit()

    mgr_user = User(name="Manager Room", email="mgr_room@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-RM")
    session.add(manager)
    session.commit()

    mh = ManagerHostel(manager_id=manager.id, hostel_id=hostel_assigned.id)
    session.add(mh)
    session.commit()

    # Create rooms in assigned hostel
    r1 = Room(hostel_id=hostel_assigned.id, room_number="101", floor=1, room_type=RoomType.DOUBLE, capacity=2, rent=8000, status=RoomStatus.AVAILABLE)
    r2 = Room(hostel_id=hostel_assigned.id, room_number="102", floor=1, room_type=RoomType.TRIPLE, capacity=3, rent=6500, status=RoomStatus.OCCUPIED)
    r3 = Room(hostel_id=hostel_assigned.id, room_number="201", floor=2, room_type=RoomType.SINGLE, capacity=1, rent=12000, status=RoomStatus.AVAILABLE)
    # Room in unassigned hostel
    r_unauth = Room(hostel_id=hostel_unassigned.id, room_number="999", floor=9, capacity=1, rent=9000)
    session.add_all([r1, r2, r3, r_unauth])
    session.commit()

    return {
        "manager_user": mgr_user,
        "manager": manager,
        "hostel_assigned": hostel_assigned,
        "hostel_unassigned": hostel_unassigned,
        "room_1": r1,
        "room_unauth": r_unauth,
    }


def test_list_rooms_with_pagination_and_filters(app, client, session):
    data = setup_room_test_data(session)
    mgr_user = data["manager_user"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # List all rooms
    res = client.get("/api/manager/rooms", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["success"] is True
    assert len(res_json["data"]) == 3
    assert res_json["pagination"]["total"] == 3

    # Filter by floor=1
    res_floor = client.get("/api/manager/rooms?floor=1", headers={"Authorization": f"Bearer {token}"})
    assert len(res_floor.get_json()["data"]) == 2

    # Filter by status=occupied
    res_status = client.get("/api/manager/rooms?status=occupied", headers={"Authorization": f"Bearer {token}"})
    assert len(res_status.get_json()["data"]) == 1
    assert res_status.get_json()["data"][0]["room_number"] == "102"

    # Search by room_number="201"
    res_search = client.get("/api/manager/rooms?search=201", headers={"Authorization": f"Bearer {token}"})
    assert len(res_search.get_json()["data"]) == 1
    assert res_search.get_json()["data"][0]["room_number"] == "201"


def test_get_room_by_id_authorized_and_unauthorized(app, client, session):
    data = setup_room_test_data(session)
    mgr_user = data["manager_user"]
    r1 = data["room_1"]
    r_unauth = data["room_unauth"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # Authorized room -> 200
    res_auth = client.get(f"/api/manager/rooms/{r1.id}", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    assert res_auth.get_json()["data"]["room_number"] == "101"

    # Unauthorized room -> 403
    res_unauth = client.get(f"/api/manager/rooms/{r_unauth.id}", headers={"Authorization": f"Bearer {token}"})
    assert res_unauth.status_code == 403


def test_create_room_success_and_conflict(app, client, session):
    data = setup_room_test_data(session)
    mgr_user = data["manager_user"]
    hostel_assigned = data["hostel_assigned"]
    hostel_unassigned = data["hostel_unassigned"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # Create room successfully
    payload = {
        "hostel_id": str(hostel_assigned.id),
        "room_number": "301",
        "floor": 3,
        "room_type": "double",
        "capacity": 2,
        "rent": 9000.0,
        "status": "available",
    }
    res_create = client.post("/api/manager/rooms", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res_create.status_code == 201
    assert res_create.get_json()["data"]["room_number"] == "301"

    # Duplicate room number -> 409
    res_dup = client.post("/api/manager/rooms", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res_dup.status_code == 409

    # Unassigned hostel -> 403
    payload_unauth = {**payload, "hostel_id": str(hostel_unassigned.id), "room_number": "302"}
    res_unauth = client.post("/api/manager/rooms", json=payload_unauth, headers={"Authorization": f"Bearer {token}"})
    assert res_unauth.status_code == 403


def test_update_room_and_status(app, client, session):
    data = setup_room_test_data(session)
    mgr_user = data["manager_user"]
    r1 = data["room_1"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # Update rent and capacity
    res_up = client.put(
        f"/api/manager/rooms/{r1.id}",
        json={"rent": 9500.0, "capacity": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_up.status_code == 200
    assert res_up.get_json()["data"]["rent"] == 9500.0
    assert res_up.get_json()["data"]["capacity"] == 3

    # Update status only
    res_status = client.patch(
        f"/api/manager/rooms/{r1.id}/status",
        json={"status": "maintenance"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_status.status_code == 200
    assert res_status.get_json()["data"]["status"] == "maintenance"
