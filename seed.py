import os
import uuid
from datetime import date, datetime, timedelta, timezone
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
    RoomType,
    RoomStatus,
    Student,
    StudentStatus,
    Booking,
    BookingStatus,
    Payment,
    PaymentType,
    PaymentMethod,
    PaymentStatus,
    Complaint,
    ComplaintPriority,
    ComplaintStatus,
    Maintenance,
    MaintenanceCategory,
    MaintenancePriority,
    MaintenanceStatus,
    Visitor,
    Notice,
    NoticePriority,
    NoticeStatus,
)

def seed_database(app_instance=None):
    if app_instance is None:
        from flask import has_app_context, current_app
        if has_app_context():
            app_instance = current_app._get_current_object()
        else:
            app_instance = create_app(os.getenv("FLASK_ENV", "development"))

    with app_instance.app_context():
        print("[*] Seeding Hostelest Manager Dashboard Database...")

        # Ensure tables exist
        db.create_all()

        # Clear existing data in reverse FK dependency order
        print("  - Cleaning existing records...")
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

        # 1. Create Users
        print("  - Creating Users...")
        owner_user = User(
            name="Vikram Reddy",
            email="owner@hostelest.com",
            phone="+919876510001",
            role=UserRole.OWNER,
            is_active=True,
        )
        owner_user.set_password("Password@123")

        manager_user = User(
            name="Suresh Kumar",
            email="manager@hostelest.com",
            phone="+919876510002",
            role=UserRole.MANAGER,
            is_active=True,
        )
        manager_user.set_password("Password@123")

        manager_hitech_user = User(
            name="Ramesh Varma",
            email="manager.hitech@hostelest.com",
            phone="+919876510004",
            role=UserRole.MANAGER,
            is_active=True,
        )
        manager_hitech_user.set_password("Manager@123")

        inactive_manager_user = User(
            name="Inactive Manager",
            email="inactive.mgr@hostelest.com",
            phone="+919876510003",
            role=UserRole.MANAGER,
            is_active=False,
        )
        inactive_manager_user.set_password("Password@123")

        db.session.add_all([owner_user, manager_user, manager_hitech_user, inactive_manager_user])
        db.session.commit()

        # 2. Create Profiles
        print("  - Creating Owner & Manager Profiles...")
        owner = Owner(user_id=owner_user.id)
        manager = Manager(
            user_id=manager_user.id,
            employee_code="MGR-HYD-001",
            emergency_contact="+919876500001",
            joining_date=date(2025, 6, 1),
        )
        manager_hitech = Manager(
            user_id=manager_hitech_user.id,
            employee_code="MGR-HYD-002",
            emergency_contact="+919876500002",
            joining_date=date(2025, 6, 1),
        )
        db.session.add_all([owner, manager, manager_hitech])
        db.session.commit()

        # 3. Create Hostels (Hyderabad)
        print("  - Creating Hostels in Hyderabad...")
        hostel_madhapur = Hostel(
            owner_id=owner.id,
            name="Hostelest Premium Boys Hostel - Madhapur",
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
            name="Hostelest Luxury Girls Hostel - Gachibowli",
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

        # 4. Assign Managers to Hostels
        print("  - Assigning Managers to Hostels...")
        mh1 = ManagerHostel(
            manager_id=manager.id,
            hostel_id=hostel_madhapur.id,
            status="active",
        )
        mh2 = ManagerHostel(
            manager_id=manager_hitech.id,
            hostel_id=hostel_madhapur.id,
            status="active",
        )
        mh3 = ManagerHostel(
            manager_id=manager_hitech.id,
            hostel_id=hostel_gachibowli.id,
            status="active",
        )
        db.session.add_all([mh1, mh2, mh3])
        db.session.commit()

        # 5. Create Rooms in Assigned Hostel
        print("  - Creating Rooms...")
        rooms_data = [
            # Floor 1
            {"number": "101", "floor": 1, "type": RoomType.SINGLE, "cap": 1, "rent": 12000.0, "status": RoomStatus.OCCUPIED},
            {"number": "102", "floor": 1, "type": RoomType.DOUBLE, "cap": 2, "rent": 8500.0, "status": RoomStatus.OCCUPIED},
            {"number": "103", "floor": 1, "type": RoomType.DOUBLE, "cap": 2, "rent": 8500.0, "status": RoomStatus.AVAILABLE},
            {"number": "104", "floor": 1, "type": RoomType.TRIPLE, "cap": 3, "rent": 6500.0, "status": RoomStatus.AVAILABLE},
            # Floor 2
            {"number": "201", "floor": 2, "type": RoomType.SINGLE, "cap": 1, "rent": 12000.0, "status": RoomStatus.OCCUPIED},
            {"number": "202", "floor": 2, "type": RoomType.DOUBLE, "cap": 2, "rent": 8500.0, "status": RoomStatus.OCCUPIED},
            {"number": "203", "floor": 2, "type": RoomType.TRIPLE, "cap": 3, "rent": 6500.0, "status": RoomStatus.AVAILABLE},
            {"number": "204", "floor": 2, "type": RoomType.FOUR_SHARING, "cap": 4, "rent": 5500.0, "status": RoomStatus.AVAILABLE},
            # Floor 3
            {"number": "301", "floor": 3, "type": RoomType.SINGLE, "cap": 1, "rent": 12000.0, "status": RoomStatus.AVAILABLE},
            {"number": "302", "floor": 3, "type": RoomType.DOUBLE, "cap": 2, "rent": 8500.0, "status": RoomStatus.MAINTENANCE},
            {"number": "303", "floor": 3, "type": RoomType.TRIPLE, "cap": 3, "rent": 6500.0, "status": RoomStatus.AVAILABLE},
            {"number": "304", "floor": 3, "type": RoomType.FOUR_SHARING, "cap": 4, "rent": 5500.0, "status": RoomStatus.AVAILABLE},
        ]
        created_rooms = []
        for rd in rooms_data:
            r = Room(
                hostel_id=hostel_madhapur.id,
                room_number=rd["number"],
                floor=rd["floor"],
                room_type=rd["type"],
                capacity=rd["cap"],
                rent=rd["rent"],
                status=rd["status"],
            )
            created_rooms.append(r)
            db.session.add(r)

        # Also add unassigned hostel room for testing boundary
        unassigned_room = Room(
            hostel_id=hostel_gachibowli.id,
            room_number="G-101",
            floor=1,
            room_type=RoomType.DOUBLE,
            capacity=2,
            rent=9000.0,
            status=RoomStatus.AVAILABLE,
        )
        db.session.add(unassigned_room)
        db.session.commit()

        # 6. Create Students
        print("  - Creating Students...")
        students_info = [
            {
                "name": "Rahul Sharma",
                "phone": "+919876530001",
                "email": "rahul.sharma@test.com",
                "gender": "Male",
                "college": "IIIT Hyderabad",
                "company": "Amazon",
                "occupation": "Software Engineer",
                "room": created_rooms[0], # Room 101
                "joining": date(2026, 1, 10),
                "status": StudentStatus.ACTIVE,
            },
            {
                "name": "Amit Varma",
                "phone": "+919876530002",
                "email": "amit.varma@test.com",
                "gender": "Male",
                "college": "CBIT Hyderabad",
                "company": "Microsoft",
                "occupation": "Cloud Engineer",
                "room": created_rooms[1], # Room 102
                "joining": date(2026, 2, 1),
                "status": StudentStatus.ACTIVE,
            },
            {
                "name": "Karthik Rao",
                "phone": "+919876530003",
                "email": "karthik.rao@test.com",
                "gender": "Male",
                "college": "JNTU Hyderabad",
                "company": "TCS",
                "occupation": "Developer",
                "room": created_rooms[1], # Room 102
                "joining": date(2026, 2, 5),
                "status": StudentStatus.ACTIVE,
            },
            {
                "name": "Sai Teja",
                "phone": "+919876530004",
                "email": "sai.teja@test.com",
                "gender": "Male",
                "college": "Osmania University",
                "company": "Wipro",
                "occupation": "Analyst",
                "room": created_rooms[4], # Room 201
                "joining": date(2026, 3, 1),
                "status": StudentStatus.ACTIVE,
            },
            {
                "name": "Naveen Reddy",
                "phone": "+919876530005",
                "email": "naveen.reddy@test.com",
                "gender": "Male",
                "college": "VNR VJIET",
                "company": "Google",
                "occupation": "SDE Intern",
                "room": created_rooms[5], # Room 202
                "joining": date(2026, 3, 15),
                "status": StudentStatus.ACTIVE,
            },
            {
                "name": "Praneeth Kumar",
                "phone": "+919876530006",
                "email": "praneeth.k@test.com",
                "gender": "Male",
                "college": "Gokaraju Rangaraju",
                "company": "Infosys",
                "occupation": "Systems Engineer",
                "room": None,
                "joining": date(2025, 9, 1),
                "status": StudentStatus.CHECKED_OUT,
            },
        ]

        created_students = []
        for si in students_info:
            s = Student(
                hostel_id=hostel_madhapur.id,
                room_id=si["room"].id if si["room"] else None,
                name=si["name"],
                phone=si["phone"],
                email=si["email"],
                gender=si["gender"],
                college=si["college"],
                company=si["company"],
                occupation=si["occupation"],
                emergency_contact_name=f"{si['name'].split()[0]} Parent",
                emergency_contact_phone="+919876599999",
                joining_date=si["joining"],
                leaving_date=date(2026, 2, 28) if si["status"] == StudentStatus.CHECKED_OUT else None,
                status=si["status"],
            )
            created_students.append(s)
            db.session.add(s)

        db.session.commit()

        # 7. Create Bookings
        print("  - Creating Bookings...")
        b1 = Booking(
            hostel_id=hostel_madhapur.id,
            room_id=created_rooms[0].id,
            student_id=created_students[0].id,
            booking_reference="HST-2026-000001",
            booking_date=date(2026, 1, 5),
            check_in_date=date(2026, 1, 10),
            amount=12000.0,
            security_deposit=12000.0,
            status=BookingStatus.CHECKED_IN,
        )
        b2 = Booking(
            hostel_id=hostel_madhapur.id,
            room_id=created_rooms[1].id,
            student_id=created_students[1].id,
            booking_reference="HST-2026-000002",
            booking_date=date(2026, 1, 28),
            check_in_date=date(2026, 2, 1),
            amount=8500.0,
            security_deposit=8500.0,
            status=BookingStatus.CHECKED_IN,
        )
        b3 = Booking(
            hostel_id=hostel_madhapur.id,
            room_id=created_rooms[2].id,
            student_id=created_students[4].id,
            booking_reference="HST-2026-000003",
            booking_date=date.today() - timedelta(days=2),
            check_in_date=date.today() + timedelta(days=3),
            amount=8500.0,
            security_deposit=8500.0,
            status=BookingStatus.APPROVED,
        )
        b4 = Booking(
            hostel_id=hostel_madhapur.id,
            room_id=created_rooms[3].id,
            student_id=created_students[3].id,
            booking_reference="HST-2026-000004",
            booking_date=date.today() - timedelta(days=1),
            check_in_date=date.today() + timedelta(days=5),
            amount=6500.0,
            security_deposit=6500.0,
            status=BookingStatus.PENDING,
        )
        db.session.add_all([b1, b2, b3, b4])
        db.session.commit()

        # 8. Create Payments
        print("  - Creating Payments...")
        p1 = Payment(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[0].id,
            booking_id=b1.id,
            amount=12000.0,
            payment_type=PaymentType.RENT,
            payment_method=PaymentMethod.UPI,
            transaction_reference="UPI-REF-20260110",
            due_date=date(2026, 1, 10),
            paid_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
            status=PaymentStatus.PAID,
            notes="January rent paid via Google Pay",
        )
        p2 = Payment(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[1].id,
            booking_id=b2.id,
            amount=8500.0,
            payment_type=PaymentType.RENT,
            payment_method=PaymentMethod.BANK_TRANSFER,
            transaction_reference="IMPS-9988771122",
            due_date=date(2026, 2, 1),
            paid_at=datetime(2026, 2, 1, 14, 0, tzinfo=timezone.utc),
            status=PaymentStatus.PAID,
            notes="February rent paid via NetBanking",
        )
        p3 = Payment(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[2].id,
            amount=8500.0,
            payment_type=PaymentType.RENT,
            payment_method=PaymentMethod.UPI,
            due_date=date.today() + timedelta(days=3),
            status=PaymentStatus.PENDING,
            notes="Current month rent pending",
        )
        p4 = Payment(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[3].id,
            amount=12000.0,
            payment_type=PaymentType.RENT,
            due_date=date.today() - timedelta(days=7),
            status=PaymentStatus.OVERDUE,
            notes="Overdue rent reminder sent via SMS",
        )
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # 9. Create Complaints
        print("  - Creating Complaints...")
        c1 = Complaint(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[0].id,
            title="Geyser not heating in Bathroom 101",
            description="Geyser takes 40 minutes to provide warm water, needs thermostat check.",
            priority=ComplaintPriority.HIGH,
            status=ComplaintStatus.PENDING,
        )
        c2 = Complaint(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[1].id,
            title="Wi-Fi speed slow on Floor 1",
            description="Access point on floor 1 disconnects frequently during evening hours.",
            priority=ComplaintPriority.MEDIUM,
            status=ComplaintStatus.IN_PROGRESS,
            assigned_to="ACT Fiber Technician",
        )
        c3 = Complaint(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[2].id,
            title="Ceiling fan wobbling",
            description="Fan in 102 makes vibrating noise at high speed.",
            priority=ComplaintPriority.LOW,
            status=ComplaintStatus.RESOLVED,
            assigned_to="Electrician Ramesh",
            resolution_notes="Tightened anchor screws and replaced motor rubber bush.",
            resolved_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.session.add_all([c1, c2, c3])
        db.session.commit()

        # 10. Create Maintenance Requests
        print("  - Creating Maintenance Requests...")
        m1 = Maintenance(
            hostel_id=hostel_madhapur.id,
            room_id=created_rooms[9].id, # Room 302
            title="AC Compressor Replacement",
            description="Split AC compressor tripped and stopped cooling. Required replacement under warranty.",
            category=MaintenanceCategory.APPLIANCE,
            priority=MaintenancePriority.HIGH,
            status=MaintenanceStatus.IN_PROGRESS,
            assigned_to="Voltas Service Center",
            estimated_cost=3500.0,
            notes="Technician visiting tomorrow with spare compressor",
        )
        m2 = Maintenance(
            hostel_id=hostel_madhapur.id,
            room_id=created_rooms[2].id, # Room 103
            title="Bathroom Tap Valve Repair",
            description="Replace leaking brass valve and Teflon tape seal.",
            category=MaintenanceCategory.PLUMBING,
            priority=MaintenancePriority.LOW,
            status=MaintenanceStatus.COMPLETED,
            assigned_to="Plumber Srinivas",
            estimated_cost=400.0,
            actual_cost=450.0,
            completed_at=datetime.now(timezone.utc) - timedelta(days=2),
            notes="Replaced angle valve and tested water flow.",
        )
        db.session.add_all([m1, m2])
        db.session.commit()

        # 11. Create Visitors
        print("  - Creating Visitors...")
        v1 = Visitor(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[0].id,
            visitor_name="Mohan Sharma",
            phone="+919876540001",
            purpose="Father visiting",
            id_type="Aadhaar",
            id_reference="XXXX-XXXX-9876",
            check_in=datetime.now(timezone.utc) - timedelta(hours=3),
            check_out=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        v2 = Visitor(
            hostel_id=hostel_madhapur.id,
            student_id=created_students[1].id,
            visitor_name="Rohan Varma",
            phone="+919876540002",
            purpose="Brother visiting for lunch",
            id_type="Driving License",
            id_reference="TS-09-XXXX",
            check_in=datetime.now(timezone.utc) - timedelta(minutes=45),
        )
        db.session.add_all([v1, v2])
        db.session.commit()

        # 12. Create Notices
        print("  - Creating Notices...")
        n1 = Notice(
            hostel_id=hostel_madhapur.id,
            created_by=manager_user.id,
            title="Hostel Main Gate Curfew Timings",
            content="All residents are requested to note that the main gate closes promptly at 10:30 PM. Late entry requires prior approval.",
            priority=NoticePriority.HIGH,
            status=NoticeStatus.PUBLISHED,
            publish_at=datetime.now(timezone.utc) - timedelta(days=5),
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        )
        n2 = Notice(
            hostel_id=hostel_madhapur.id,
            created_by=manager_user.id,
            title="Water Supply Maintenance on Sunday",
            content="Overhead water tank cleaning is scheduled this Sunday between 2:00 PM and 5:00 PM. Please store required water in advance.",
            priority=NoticePriority.NORMAL,
            status=NoticeStatus.PUBLISHED,
            publish_at=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.session.add_all([n1, n2])
        db.session.commit()

        print("\n[OK] Seed data successfully inserted!")
        print("--------------------------------------------------")
        print("Test Credentials:")
        print("   Role: MANAGER")
        print("   Email: manager@hostelest.com")
        print("   Password: Password@123")
        print("   Assigned Hostel: Hostelest Premium Boys Hostel - Madhapur")
        print("--------------------------------------------------")
        print("   Role: OWNER")
        print("   Email: owner@hostelest.com")
        print("   Password: Password@123")
        print("--------------------------------------------------")


if __name__ == "__main__":
    seed_database()
