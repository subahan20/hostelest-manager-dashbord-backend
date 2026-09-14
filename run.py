import os
from app import create_app
from app.models import (  # noqa: F401
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

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)


@app.cli.command("seed")
def seed_cmd():
    """Seed the database with realistic sample development data."""
    from seed import seed_database
    seed_database()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
