import os
from datetime import date
from app import create_app
from app.extensions import db
from app.models import (
    User,
    UserRole,
    Owner,
    Manager,
    Hostel,
    HostelGenderType,
    HostelStatus,
    ManagerHostel,
    Room,
    Student,
    Booking,
    Payment,
    Complaint,
    Maintenance,
    Visitor,
    Notice,
)


def init_clean_database(app_instance=None):
    """
    Initialize a completely clean production-ready database.
    Contains ONLY authentic Manager & Owner accounts with their assigned Hostels.
    Zero static rooms, zero static students, zero dummy bookings/payments/complaints/visitors/notices.
    All operational data must be created dynamically by the manager through the dashboard.
    """
    if app_instance is None:
        from flask import has_app_context, current_app
        if has_app_context():
            app_instance = current_app._get_current_object()
        else:
            app_instance = create_app(os.getenv("FLASK_ENV", "development"))

    with app_instance.app_context():
        print("[*] Initializing Clean Hostelest Database (No static data)...")

        # Create all tables
        db.create_all()

        # Delete all existing data
        print("  - Clearing all existing operational records...")
        db.session.query(Notice).delete()
        db.session.query(Visitor).delete()
        db.session.query(Maintenance).delete()
        db.session.query(Complaint).delete()
        db.session.query(Payment).delete()
        db.session.query(Booking).delete()
        db.session.query(Student).delete()
        db.session.query(Room).delete()
        db.session.query(ManagerHostel).delete()
        db.session.query(Hostel).delete()
        db.session.query(Manager).delete()
        db.session.query(Owner).delete()
        db.session.query(User).delete()
        db.session.commit()

        # 1. Create Core Owner & Manager Users
        print("  - Creating Manager & Owner accounts...")
        owner_user = User(
            name="Vikram Reddy",
            email="owner@hostelest.com",
            phone="+919876510001",
            role=UserRole.OWNER,
            is_active=True,
        )
        owner_user.set_password("Owner@123")

        manager_user = User(
            name="Ramesh Varma",
            email="manager.hitech@hostelest.com",
            phone="+919876510004",
            role=UserRole.MANAGER,
            is_active=True,
        )
        manager_user.set_password("Manager@123")

        db.session.add_all([owner_user, manager_user])
        db.session.commit()

        # 2. Create Profiles
        owner = Owner(user_id=owner_user.id)
        manager = Manager(
            user_id=manager_user.id,
            employee_code="MGR-HYD-001",
            emergency_contact="+919876500001",
            joining_date=date(2025, 6, 1),
        )
        db.session.add_all([owner, manager])
        db.session.commit()

        # 3. Create Properties (Hyderabad)
        print("  - Creating Assigned Hostel Properties...")
        hostel_madhapur = Hostel(
            owner_id=owner.id,
            name="Hostelest Grand Hitech - Madhapur",
            address="Plot 42, Silicon Valley Rd, Madhapur",
            area="Madhapur",
            city="Hyderabad",
            state="Telangana",
            pincode="500081",
            latitude=17.4483,
            longitude=78.3915,
            contact_phone="+919876520001",
            contact_email="madhapur@hostelest.com",
            gender_type=HostelGenderType.BOYS,
            total_floors=4,
            status=HostelStatus.ACTIVE,
        )

        hostel_gachibowli = Hostel(
            owner_id=owner.id,
            name="Hostelest Elite - Gachibowli",
            address="Plot 108, Financial District, Gachibowli",
            area="Gachibowli",
            city="Hyderabad",
            state="Telangana",
            pincode="500032",
            latitude=17.4401,
            longitude=78.3489,
            contact_phone="+919876520002",
            contact_email="gachibowli@hostelest.com",
            gender_type=HostelGenderType.GIRLS,
            total_floors=3,
            status=HostelStatus.ACTIVE,
        )
        db.session.add_all([hostel_madhapur, hostel_gachibowli])
        db.session.commit()

        # 4. Assign Manager to Properties
        print("  - Assigning Manager to Properties...")
        mh1 = ManagerHostel(
            manager_id=manager.id,
            hostel_id=hostel_madhapur.id,
            status="active",
        )
        mh2 = ManagerHostel(
            manager_id=manager.id,
            hostel_id=hostel_gachibowli.id,
            status="active",
        )
        db.session.add_all([mh1, mh2])
        db.session.commit()

        print("[OK] Database is clean and ready!")
        print("--------------------------------------------------")
        print("Manager Login:")
        print("  Email: manager.hitech@hostelest.com")
        print("  Password: Manager@123")
        print("  Assigned Properties:")
        print("    1. Hostelest Grand Hitech - Madhapur")
        print("    2. Hostelest Elite - Gachibowli")
        print("  Rooms: 0 (Add rooms via Dashboard)")
        print("  Students: 0 (Admit students via Dashboard)")
        print("  Bookings: 0 (Create bookings via Dashboard)")
        print("--------------------------------------------------")


if __name__ == "__main__":
    init_clean_database()
