from datetime import date, datetime, timezone, timedelta
from flask_jwt_extended import create_access_token
from app.models import (
    User,
    UserRole,
    Owner,
    Manager,
    Hostel,
    ManagerHostel,
    ManagerHostelStatus,
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
    Complaint,
    ComplaintPriority,
    ComplaintStatus,
    Maintenance,
    MaintenanceCategory,
    MaintenancePriority,
    MaintenanceStatus,
)


def setup_dashboard_test_data(session):
    """Helper to set up 2 assigned hostels and 1 unassigned hostel with rich operational data."""
    # 1. Owner
    owner_user = User(name="Owner Dash", email="owner_dash@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    # 2. Hostels
    hostel_a = Hostel(
        owner_id=owner.id,
        name="Hostel Alpha - Madhapur",
        address="100 Hitech City Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500001",
        contact_email="alpha@test.com",
    )
    hostel_b = Hostel(
        owner_id=owner.id,
        name="Hostel Beta - Gachibowli",
        address="200 DLF Rd",
        area="Gachibowli",
        city="Hyderabad",
        state="Telangana",
        pincode="500032",
        contact_phone="+919876500002",
        contact_email="beta@test.com",
    )
    hostel_unassigned = Hostel(
        owner_id=owner.id,
        name="Hostel Gamma - Ameerpet",
        address="300 Metro Rd",
        area="Ameerpet",
        city="Hyderabad",
        state="Telangana",
        pincode="500016",
        contact_phone="+919876500003",
        contact_email="gamma@test.com",
    )
    session.add_all([hostel_a, hostel_b, hostel_unassigned])
    session.commit()

    # 3. Manager
    mgr_user = User(name="Manager Dash", email="manager_dash@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-DASH")
    session.add(manager)
    session.commit()

    # Assign Manager to Hostel A & Hostel B (NOT Hostel Gamma)
    mh_a = ManagerHostel(manager_id=manager.id, hostel_id=hostel_a.id, status=ManagerHostelStatus.ACTIVE)
    mh_b = ManagerHostel(manager_id=manager.id, hostel_id=hostel_b.id, status=ManagerHostelStatus.ACTIVE)
    session.add_all([mh_a, mh_b])
    session.commit()

    # 4. Rooms in Hostel A (2 rooms: 1 occupied, 1 available; capacity total: 3)
    r_a1 = Room(hostel_id=hostel_a.id, room_number="A-101", capacity=2, rent=8000, status=RoomStatus.OCCUPIED)
    r_a2 = Room(hostel_id=hostel_a.id, room_number="A-102", capacity=1, rent=10000, status=RoomStatus.AVAILABLE)
    # Rooms in Hostel B (2 rooms: 1 maintenance, 1 available; capacity total: 4)
    r_b1 = Room(hostel_id=hostel_b.id, room_number="B-201", capacity=2, rent=7000, status=RoomStatus.MAINTENANCE)
    r_b2 = Room(hostel_id=hostel_b.id, room_number="B-202", capacity=2, rent=7000, status=RoomStatus.AVAILABLE)
    # Room in Unassigned Hostel Gamma
    r_g1 = Room(hostel_id=hostel_unassigned.id, room_number="G-301", capacity=3, rent=6000, status=RoomStatus.OCCUPIED)
    session.add_all([r_a1, r_a2, r_b1, r_b2, r_g1])
    session.commit()

    # 5. Students
    # Hostel A: 2 active students
    s_a1 = Student(hostel_id=hostel_a.id, room_id=r_a1.id, name="Student A1", phone="+919000000001", joining_date=date(2026, 1, 1), status=StudentStatus.ACTIVE)
    s_a2 = Student(hostel_id=hostel_a.id, room_id=r_a1.id, name="Student A2", phone="+919000000002", joining_date=date(2026, 1, 1), status=StudentStatus.ACTIVE)
    # Hostel B: 1 active student
    s_b1 = Student(hostel_id=hostel_b.id, room_id=r_b2.id, name="Student B1", phone="+919000000003", joining_date=date(2026, 2, 1), status=StudentStatus.ACTIVE)
    # Hostel Gamma: 1 student
    s_g1 = Student(hostel_id=hostel_unassigned.id, room_id=r_g1.id, name="Student G1", phone="+919000000004", joining_date=date(2026, 3, 1), status=StudentStatus.ACTIVE)
    session.add_all([s_a1, s_a2, s_b1, s_g1])
    session.commit()

    # 6. Bookings
    b_a = Booking(hostel_id=hostel_a.id, room_id=r_a2.id, student_id=s_a1.id, booking_reference="HST-2026-001", check_in_date=date(2026, 4, 1), status=BookingStatus.PENDING)
    b_b = Booking(hostel_id=hostel_b.id, room_id=r_b2.id, student_id=s_b1.id, booking_reference="HST-2026-002", check_in_date=date(2026, 4, 1), status=BookingStatus.APPROVED)
    session.add_all([b_a, b_b])
    session.commit()

    # 7. Payments
    # 1 pending, 1 overdue in Hostel A
    p_a1 = Payment(hostel_id=hostel_a.id, student_id=s_a1.id, amount=8000, payment_type=PaymentType.RENT, status=PaymentStatus.PENDING, due_date=date.today() + timedelta(days=5))
    p_a2 = Payment(hostel_id=hostel_a.id, student_id=s_a2.id, amount=8000, payment_type=PaymentType.RENT, status=PaymentStatus.PENDING, due_date=date.today() - timedelta(days=2))
    # 1 paid in Hostel B
    p_b1 = Payment(hostel_id=hostel_b.id, student_id=s_b1.id, amount=7000, payment_type=PaymentType.RENT, status=PaymentStatus.PAID, paid_at=datetime.now(timezone.utc))
    session.add_all([p_a1, p_a2, p_b1])
    session.commit()

    # 8. Complaints
    c_a = Complaint(hostel_id=hostel_a.id, student_id=s_a1.id, title="Water issue", description="Low pressure", priority=ComplaintPriority.HIGH, status=ComplaintStatus.PENDING)
    c_b = Complaint(hostel_id=hostel_b.id, student_id=s_b1.id, title="AC remote", description="Missing batteries", priority=ComplaintPriority.LOW, status=ComplaintStatus.IN_PROGRESS)
    session.add_all([c_a, c_b])
    session.commit()

    # 9. Maintenance
    m_b = Maintenance(hostel_id=hostel_b.id, room_id=r_b1.id, title="Wall painting", description="Paint flaking off", category=MaintenanceCategory.PAINTING, priority=MaintenancePriority.MEDIUM, status=MaintenanceStatus.IN_PROGRESS)
    session.add(m_b)
    session.commit()

    return {
        "manager_user": mgr_user,
        "manager": manager,
        "hostel_a": hostel_a,
        "hostel_b": hostel_b,
        "hostel_unassigned": hostel_unassigned,
    }


def test_dashboard_aggregated_all_assigned_hostels(app, client, session):
    """Test GET /api/manager/dashboard returns aggregated metrics for all assigned hostels."""
    data = setup_dashboard_test_data(session)
    mgr_user = data["manager_user"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    res = client.get("/api/manager/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["success"] is True

    overview = res_json["data"]["overview"]
    # Total rooms across Hostel A (2) + Hostel B (2) = 4
    assert overview["total_rooms"] == 4
    assert overview["occupied_rooms"] == 1
    assert overview["available_rooms"] == 2
    assert overview["maintenance_rooms"] == 1
    # Total students across A (2) + B (1) = 3
    assert overview["total_students"] == 3
    # Total capacity = 3 (A) + 4 (B) = 7 -> Occupancy = round(3/7*100, 2) = 42.86%
    assert overview["occupancy_rate"] == 42.86
    assert overview["pending_bookings"] == 1
    assert overview["pending_payments"] == 2
    assert overview["overdue_payments"] == 1
    assert overview["pending_complaints"] == 2
    assert overview["pending_maintenance"] == 1

    room_status = res_json["data"]["room_status"]
    assert room_status["occupied"] == 1
    assert room_status["available"] == 2
    assert room_status["maintenance"] == 1

    # Feeds
    assert len(res_json["data"]["recent_bookings"]) == 2
    assert len(res_json["data"]["recent_students"]) == 3
    assert len(res_json["data"]["recent_complaints"]) == 2
    assert len(res_json["data"]["maintenance_requests"]) == 1
    assert len(res_json["data"]["recent_payments"]) == 3


def test_dashboard_filtered_by_specific_hostel(app, client, session):
    """Test GET /api/manager/dashboard?hostel_id=<id> returns single hostel metrics."""
    data = setup_dashboard_test_data(session)
    mgr_user = data["manager_user"]
    hostel_a = data["hostel_a"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    res = client.get(f"/api/manager/dashboard?hostel_id={hostel_a.id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    res_json = res.get_json()

    overview = res_json["data"]["overview"]
    # Hostel A only has 2 rooms
    assert overview["total_rooms"] == 2
    assert overview["occupied_rooms"] == 1
    assert overview["available_rooms"] == 1
    assert overview["maintenance_rooms"] == 0
    # Hostel A has 2 students, capacity 3 -> 66.67%
    assert overview["total_students"] == 2
    assert overview["occupancy_rate"] == 66.67
    assert overview["pending_bookings"] == 1
    assert overview["pending_payments"] == 2
    assert overview["pending_complaints"] == 1
    assert overview["pending_maintenance"] == 0


def test_dashboard_unauthorized_hostel_forbidden(app, client, session):
    """Test GET /api/manager/dashboard?hostel_id=<unassigned_id> returns HTTP 403."""
    data = setup_dashboard_test_data(session)
    mgr_user = data["manager_user"]
    hostel_unassigned = data["hostel_unassigned"]

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    res = client.get(
        f"/api/manager/dashboard?hostel_id={hostel_unassigned.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    res_json = res.get_json()
    assert res_json["success"] is False
    assert "Unauthorized" in res_json["message"] or "permission" in res_json["message"]


def test_dashboard_manager_no_assigned_hostels(app, client, session):
    """Test manager with 0 assigned hostels gets clean empty statistics with 200 OK."""
    user = User(name="Solo Manager", email="solo@test.com", role=UserRole.MANAGER, is_active=True)
    user.set_password("pass")
    session.add(user)
    session.commit()

    manager = Manager(user_id=user.id)
    session.add(manager)
    session.commit()

    with app.app_context():
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    res = client.get("/api/manager/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["success"] is True
    assert res_json["data"]["overview"]["total_rooms"] == 0
    assert res_json["data"]["overview"]["occupancy_rate"] == 0.0
    assert res_json["data"]["recent_bookings"] == []
