from flask import Blueprint, request, g
from marshmallow import ValidationError
from app.middleware.auth import manager_required
from app.schemas.payment_schema import CreatePaymentSchema, RecordPaymentSchema
from app.services.payment_service import PaymentService
from app.utils.responses import success_response, error_response

payments_bp = Blueprint("payments", __name__)
create_payment_schema = CreatePaymentSchema()
record_payment_schema = RecordPaymentSchema()


@payments_bp.route("/payments", methods=["GET"])
@manager_required
def get_payments():
    """
    List payments with filters and pagination.
    
    Query Params:
        hostel_id, student_id, status, payment_type, from_date, to_date, page, limit
    """
    items, pagination, err_msg, status_code = PaymentService.get_payments(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
        student_id=request.args.get("student_id"),
        status=request.args.get("status"),
        payment_type=request.args.get("payment_type"),
        from_date=request.args.get("from_date"),
        to_date=request.args.get("to_date"),
    )

    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(
        data=items,
        pagination=pagination,
        message="Payments fetched successfully",
        status_code=200,
    )


@payments_bp.route("/payments/pending", methods=["GET"])
@manager_required
def get_pending_payments():
    """List pending payments."""
    items, pagination, err_msg, status_code = PaymentService.get_pending_payments(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=items, pagination=pagination, message="Pending payments fetched successfully")


@payments_bp.route("/payments/overdue", methods=["GET"])
@manager_required
def get_overdue_payments():
    """List overdue payments."""
    items, pagination, err_msg, status_code = PaymentService.get_overdue_payments(
        manager=g.current_manager,
        hostel_id=request.args.get("hostel_id"),
    )
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=items, pagination=pagination, message="Overdue payments fetched successfully")


@payments_bp.route("/payments/<payment_id>", methods=["GET"])
@manager_required
def get_payment(payment_id):
    """Get single payment record details by ID."""
    payment, err_msg, status_code = PaymentService.get_payment_by_id(g.current_manager, payment_id)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=payment, message="Payment details fetched successfully")


@payments_bp.route("/payments", methods=["POST"])
@manager_required
def create_payment():
    """Create a new payment or invoice entry."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = create_payment_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    payment, err_msg, status_code = PaymentService.create_payment(g.current_manager, data)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=payment, message="Payment created successfully", status_code=201)


@payments_bp.route("/payments/<payment_id>/record", methods=["POST"])
@manager_required
def record_payment(payment_id):
    """Record payment collection against an existing invoice."""
    if not request.is_json:
        return error_response(message="Request body must be JSON", status_code=400)

    try:
        data = record_payment_schema.load(request.get_json())
    except ValidationError as err:
        return error_response(message="Validation error", status_code=422, errors=err.messages)

    payment, err_msg, status_code = PaymentService.record_payment(g.current_manager, payment_id, data)
    if err_msg:
        return error_response(message=err_msg, status_code=status_code)

    return success_response(data=payment, message="Payment recorded successfully", status_code=200)
