from flask import Blueprint
from app.routes.manager.dashboard import dashboard_bp
from app.routes.manager.rooms import rooms_bp
from app.routes.manager.students import students_bp
from app.routes.manager.bookings import bookings_bp
from app.routes.manager.payments import payments_bp
from app.routes.manager.complaints import complaints_bp
from app.routes.manager.maintenance import maintenance_bp
from app.routes.manager.visitors import visitors_bp
from app.routes.manager.notices import notices_bp
from app.routes.manager.reports import reports_bp

manager_bp = Blueprint("manager", __name__)
manager_bp.register_blueprint(dashboard_bp)
manager_bp.register_blueprint(rooms_bp)
manager_bp.register_blueprint(students_bp)
manager_bp.register_blueprint(bookings_bp)
manager_bp.register_blueprint(payments_bp)
manager_bp.register_blueprint(complaints_bp)
manager_bp.register_blueprint(maintenance_bp)
manager_bp.register_blueprint(visitors_bp)
manager_bp.register_blueprint(notices_bp)
manager_bp.register_blueprint(reports_bp)

__all__ = ["manager_bp"]
