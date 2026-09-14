from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.student_schema import (
    CreateStudentSchema,
    UpdateStudentSchema,
    UpdateStudentStatusSchema,
)
from app.services.student_service import StudentService
from app.utils.responses import success_response, error_response

students_bp = Blueprint("students", __name__)
create_student_schema = CreateStudentSchema()
update_student_schema = UpdateStudentSchema()
update_status_schema = UpdateStudentStatusSchema()


@students_bp.route("/students", methods=["GET"])
@manager_required
def get_students():
    """
    List students with search, filters, and pagination.
    
    Query Params:
        hostel_id, room_id, status, search, page, limit
    """
    items, pagination, err_msg, status_code = StudentService.get_students(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        room_id=request.args.get("room_id"),
        status=request.args.get("status"),
        search=request.args.get("search"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Students fetched successfully",
        status_code=200,
    )


@students_bp.route("/students/<student_id>", methods=["GET"])
@manager_required
def get_student(student_id):
    """Get single student details by ID."""
    student, err_msg, status_code = StudentService.get_student_by_id(g.current_manager, student_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=student, message="Student details fetched successfully")


@students_bp.route("/students", methods=["POST"])
@manager_required
def create_student():
    """Register a new student."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_student_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    student, err_msg, status_code = StudentService.create_student(g.current_manager, data)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=student, message="Student registered successfully", status_code=201)


@students_bp.route("/students/<student_id>", methods=["PUT"])
@manager_required
def update_student(student_id):
    """Update student profile details."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_student_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    student, err_msg, status_code = StudentService.update_student(g.current_manager, student_id, data)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=student, message="Student updated successfully", status_code=200)


@students_bp.route("/students/<student_id>/status", methods=["PATCH"])
@manager_required
def update_student_status(student_id):
    """Update student status (e.g. checked_out)."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = update_status_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    student, err_msg, status_code = StudentService.update_student_status(
        g.current_manager, student_id, data["status"]
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=student, message="Student status updated successfully", status_code=200)
