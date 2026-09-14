import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import (
    User,
    UserRole,
    Owner,
    Manager,
    Hostel,
    HostelGenderType,
    HostelStatus,
    ManagerHostel,
    ManagerHostelStatus,
)


def test_create_user_with_password_hashing(session):
    """Test User creation and password verification."""
    user = User(
        name="Test Manager",
        email="manager@hostelest.com",
        phone="+919876543210",
        role=UserRole.MANAGER,
    )
    user.set_password("SecurePassword123!")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.check_password("SecurePassword123!") is True
    assert user.check_password("WrongPassword") is False
    assert user.password_hash != "SecurePassword123!"

    user_dict = user.to_dict()
    assert "password_hash" not in user_dict
    assert user_dict["email"] == "manager@hostelest.com"
    assert user_dict["role"] == UserRole.MANAGER


def test_user_email_uniqueness(session):
    """Test that duplicate email raises IntegrityError."""
    user1 = User(
        name="User 1",
        email="duplicate@hostelest.com",
        role=UserRole.MANAGER,
    )
    user1.set_password("pass1")
    session.add(user1)
    session.commit()

    user2 = User(
        name="User 2",
        email="duplicate@hostelest.com",
        role=UserRole.MANAGER,
    )
    user2.set_password("pass2")
    session.add(user2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_owner_and_hostel_relationship(session):
    """Test Owner creation, association with User, and Hostel creation."""
    owner_user = User(
        name="Hostel Owner",
        email="owner@hostelest.com",
        role=UserRole.OWNER,
    )
    owner_user.set_password("OwnerPass123!")
    session.add(owner_user)
    session.commit()

    owner = Owner(
        user_id=owner_user.id,
        business_name="Hostelest Ventures LLP",
        emergency_contact="+919876543211",
    )
    session.add(owner)
    session.commit()

    hostel = Hostel(
        owner_id=owner.id,
        name="Hostelest Madhapur Executive",
        address="Plot 42, Hitech City Main Rd, Madhapur",
        area="Madhapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876543212",
        contact_email="madhapur@hostelest.com",
        gender_type=HostelGenderType.BOYS,
        total_floors=4,
        status=HostelStatus.ACTIVE,
    )
    session.add(hostel)
    session.commit()

    assert hostel.id is not None
    assert hostel.owner_id == owner.id
    assert len(owner.hostels) == 1
    assert owner.hostels[0].name == "Hostelest Madhapur Executive"


def test_manager_hostel_assignment_and_access(session):
    """Test Manager-Hostel assignment and has_hostel_access security helper."""
    # 1. Create Owner & 2 Hostels
    owner_user = User(name="Owner 1", email="owner1@hostelest.com", role=UserRole.OWNER)
    owner_user.set_password("Pass123")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_a = Hostel(
        owner_id=owner.id,
        name="Hostel A - Gachibowli",
        address="Address A",
        area="Gachibowli",
        city="Hyderabad",
        state="Telangana",
        pincode="500032",
        contact_phone="+919800000001",
        contact_email="hostela@hostelest.com",
    )
    hostel_b = Hostel(
        owner_id=owner.id,
        name="Hostel B - Kondapur",
        address="Address B",
        area="Kondapur",
        city="Hyderabad",
        state="Telangana",
        pincode="500084",
        contact_phone="+919800000002",
        contact_email="hostelb@hostelest.com",
    )
    session.add_all([hostel_a, hostel_b])
    session.commit()

    # 2. Create Manager
    mgr_user = User(name="Manager 1", email="mgr1@hostelest.com", role=UserRole.MANAGER)
    mgr_user.set_password("Pass123")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-001")
    session.add(manager)
    session.commit()

    # 3. Assign Manager to Hostel A ONLY
    assignment = ManagerHostel(
        manager_id=manager.id,
        hostel_id=hostel_a.id,
        status=ManagerHostelStatus.ACTIVE,
    )
    session.add(assignment)
    session.commit()

    # Refresh manager to test relationship & authorization helpers
    session.refresh(manager)

    assert manager.has_hostel_access(hostel_a.id) is True
    assert manager.has_hostel_access(hostel_b.id) is False
    assert str(hostel_a.id) in manager.get_assigned_hostel_ids()
    assert str(hostel_b.id) not in manager.get_assigned_hostel_ids()


def test_unique_manager_hostel_constraint(session):
    """Test that assigning the same manager to the same hostel twice violates unique constraint."""
    owner_user = User(name="Owner 2", email="owner2@hostelest.com", role=UserRole.OWNER)
    owner_user.set_password("Pass123")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel = Hostel(
        owner_id=owner.id,
        name="Hostel C",
        address="Address C",
        area="Ameerpet",
        city="Hyderabad",
        state="Telangana",
        pincode="500016",
        contact_phone="+919800000003",
        contact_email="hostelc@hostelest.com",
    )
    mgr_user = User(name="Manager 2", email="mgr2@hostelest.com", role=UserRole.MANAGER)
    mgr_user.set_password("Pass123")
    session.add_all([hostel, mgr_user])
    session.commit()

    manager = Manager(user_id=mgr_user.id, employee_code="MGR-002")
    session.add(manager)
    session.commit()

    # First assignment
    a1 = ManagerHostel(manager_id=manager.id, hostel_id=hostel.id)
    session.add(a1)
    session.commit()

    # Duplicate assignment
    a2 = ManagerHostel(manager_id=manager.id, hostel_id=hostel.id)
    session.add(a2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
