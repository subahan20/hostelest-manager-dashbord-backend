import logging
from flask import Flask
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.utils.responses import error_response

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register application-wide centralized error handlers."""

    @app.errorhandler(400)
    def handle_bad_request(e):
        return error_response(
            message=getattr(e, "description", "Bad request"),
            status_code=400,
        )

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return error_response(
            message=getattr(e, "description", "Unauthorized access"),
            status_code=401,
        )

    @app.errorhandler(403)
    def handle_forbidden(e):
        return error_response(
            message=getattr(e, "description", "Forbidden - access denied"),
            status_code=403,
        )

    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response(
            message="Resource not found",
            status_code=404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response(
            message="Method not allowed for this endpoint",
            status_code=405,
        )

    @app.errorhandler(422)
    def handle_unprocessable_entity(e):
        return error_response(
            message=getattr(e, "description", "Unprocessable entity"),
            status_code=422,
        )

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        logger.error(f"Database Integrity Error: {str(e)}")
        return error_response(
            message="Database constraint violation or duplicate record found",
            status_code=409,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(e):
        logger.error(f"Database Error: {str(e)}")
        return error_response(
            message="A database error occurred while processing your request",
            status_code=500,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return error_response(
            message=e.description,
            status_code=e.code if e.code else 500,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger.exception(f"Unhandled Exception: {str(e)}")
        return error_response(
            message="An unexpected internal server error occurred",
            status_code=500,
        )
