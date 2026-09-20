from app.models import (
    User,
    UserRole,
    Manager,
    Hostel,
    Room,
    Student,
    Booking,
    Payment,
    Complaint,
    Maintenance,
    Visitor,
    Notice,
)
from seed import seed_database


def test_seed_database_execution(app):
    with app.app_context():
        seed_database()

        # Verify seeded entities
        users = User.query.all()
        assert len(users) >= 3

        manager = User.query.filter_by(email="manager@hostelest.com").first()
        assert manager is not None
        assert manager.role == UserRole.MANAGER
        assert manager.check_password("Password@123") is True

        hostels = Hostel.query.all()
        assert len(hostels) == 2

        rooms = Room.query.all()
        assert len(rooms) == 13

        students = Student.query.all()
        assert len(students) == 6

        bookings = Booking.query.all()
        assert len(bookings) == 4

        payments = Payment.query.all()
        assert len(payments) == 4

        complaints = Complaint.query.all()
        assert len(complaints) == 3

        maintenance = Maintenance.query.all()
        assert len(maintenance) == 2

        visitors = Visitor.query.all()
        assert len(visitors) == 2

        notices = Notice.query.all()
        assert len(notices) == 2
