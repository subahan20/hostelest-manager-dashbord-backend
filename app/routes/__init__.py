from app.routes.health import health_bp
from app.routes.auth import auth_bp
from app.routes.manager import manager_bp


def register_routes(app):
    """Register all route blueprints with the Flask application."""
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(manager_bp, url_prefix="/api/manager")
