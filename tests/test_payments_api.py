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
    Student,
    Payment,
    PaymentType,
    PaymentMethod,
    PaymentStatus,
)


def setup_payment_test_data(session):
    owner_user = User(name="Owner Pay", email="owner_pay@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_assigned = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel Pay",
        address="101 Pay Rd",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876500040",
        contact_email="pay@test.com",
    )
    hostel_unassigned = Hostel(
        owner_id=owner.id,
        name="Unassigned Hostel Pay",
        address="102 Pay Rd",
        area="Gachibowli",
        city="Hyderabad",
        state="Telangana",
        pincode="500032",
        contact_phone="+919876500041",
        contact_email="unassigned_pay@test.com",
    )
    session.add_all([hostel_assigned, hostel_unassigned])
    session.commit()

    mgr_user = User(name="Manager Pay", email="mgr_pay@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-PAY")
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
        name="Pay Student",
        phone="+919876543201",
        emergency_contact_phone="+919876543202",
        emergency_contact_name="Pay Guardian",
        joining_date=date.today(),
    )
    session.add(student)
    session.commit()

    p1 = Payment(
        hostel_id=hostel_assigned.id,
        student_id=student.id,
        amount=8000.0,
        payment_type=PaymentType.RENT,
        payment_method=PaymentMethod.UPI,
        due_date=date.today() + timedelta(days=5),
        status=PaymentStatus.PENDING,
    )
    p2 = Payment(
        hostel_id=hostel_assigned.id,
        student_id=student.id,
        amount=500.0,
        payment_type=PaymentType.MAINTENANCE,
        payment_method=PaymentMethod.CASH,
        due_date=date.today() - timedelta(days=10),
        status=PaymentStatus.OVERDUE,
    )
    p3 = Payment(
        hostel_id=hostel_assigned.id,
        student_id=student.id,
        amount=8000.0,
        payment_type=PaymentType.RENT,
        payment_method=PaymentMethod.UPI,
        due_date=date.today() - timedelta(days=35),
        paid_at=datetime.now(timezone.utc) - timedelta(days=34),
        transaction_reference="TXN-12345",
        status=PaymentStatus.PAID,
    )
    session.add_all([p1, p2, p3])
    session.commit()

    return {
        "manager_user": mgr_user,
        "hostel": hostel_assigned,
        "unassigned_hostel": hostel_unassigned,
        "student": student,
        "pending_payment": p1,
        "overdue_payment": p2,
        "paid_payment": p3,
    }


def test_list_payments(client, session):
    data = setup_payment_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/manager/payments", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["pagination"]["total"] == 3
    assert len(json_data["data"]) == 3


def test_list_pending_and_overdue_payments(client, session):
    data = setup_payment_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Pending
    res = client.get("/api/manager/payments/pending", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["pagination"]["total"] == 1
    assert json_data["data"][0]["status"] == "pending"

    # Overdue
    res = client.get("/api/manager/payments/overdue", headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["pagination"]["total"] == 1
    assert json_data["data"][0]["status"] == "overdue"


def test_create_payment_invoice(client, session):
    data = setup_payment_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "hostel_id": str(data["hostel"].id),
        "student_id": str(data["student"].id),
        "amount": 2000.0,
        "payment_type": "deposit",
        "payment_method": "cash",
        "due_date": str(date.today() + timedelta(days=2)),
        "notes": "Admission security deposit",
    }
    res = client.post("/api/manager/payments", json=payload, headers=headers)
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["amount"] == 2000.0
    assert json_data["data"]["status"] == "pending"


def test_record_payment_collection(client, session):
    data = setup_payment_test_data(session)
    token = create_access_token(
        identity=str(data["manager_user"].id),
        additional_claims={"role": "MANAGER", "email": data["manager_user"].email},
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "payment_method": "upi",
        "transaction_reference": "UPI-REF-998877",
        "notes": "Paid via PhonePe",
    }
    res = client.post(
        f"/api/manager/payments/{data['pending_payment'].id}/record",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "paid"
    assert json_data["data"]["transaction_reference"] == "UPI-REF-998877"
