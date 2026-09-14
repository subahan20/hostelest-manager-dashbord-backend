import pytest
from app import create_app
from app.extensions import db
from app.models import (
    User,
    Owner,
    Manager,
    Hostel,
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


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask application instance for testing."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="function")
def session(app):
    """Creates a clean database session for a test."""
    with app.app_context():
        # Clear database state before each test in FK dependency order
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
        yield db.session
        db.session.rollback()
