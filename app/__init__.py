import os
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors
from app.errors import register_error_handlers
from app.routes import register_routes
from app.utils.responses import error_response


def create_app(config_name: str = None) -> Flask:
    """
    Application factory pattern to create and configure Flask app instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/*": {
                "origins": app.config.get("CORS_ORIGINS", "*"),
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
                "expose_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    # Configure JWT custom error responses
    @jwt.unauthorized_loader
    def custom_unauthorized_response(err_str):
        return error_response(message="Missing or invalid authorization token", status_code=401)

    @jwt.invalid_token_loader
    def custom_invalid_token_response(err_str):
        return error_response(message="Invalid authorization token", status_code=401)

    @jwt.expired_token_loader
    def custom_expired_token_response(jwt_header, jwt_payload):
        return error_response(message="Authorization token has expired", status_code=401)

    @jwt.revoked_token_loader
    def custom_revoked_token_response(jwt_header, jwt_payload):
        return error_response(message="Authorization token has been revoked", status_code=401)

    # Register error handlers
    register_error_handlers(app)

    # Register routes
    register_routes(app)

    # Automatically create tables and seed clean manager accounts if database is empty
    with app.app_context():
        try:
            db.create_all()
            from app.models.user import User
            if not User.query.filter_by(email="manager.hitech@hostelest.com").first():
                from init_clean_db import init_clean_database
                init_clean_database(app)
        except Exception as e:
            app.logger.warning(f"Database bootstrap warning: {e}")

    return app
