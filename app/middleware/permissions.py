from functools import wraps
from typing import List, Optional, Tuple
from flask import g, request
from app.models import Manager
from app.utils.ids import filter_valid_uuid_strs, normalize_uuid_str
from app.utils.responses import error_response


def get_scoped_hostel_ids(manager: Manager, requested_hostel_id: Optional[str] = None) -> Tuple[List[str], Optional[str]]:
    """
    Determine the authorized hostel IDs for database queries.
    
    If requested_hostel_id is provided, verify manager has access.
    If no requested_hostel_id, return all actively assigned hostel IDs.

    Only valid UUID hostel IDs are returned. Non-UUID values (e.g. legacy integer
    ids stored on managers.hostel_id) must never reach GUID columns — they cause
    PostgreSQL DataError and HTTP 500 on dashboard/rooms queries.
    
    Returns:
        (hostel_ids_list, error_message)
    """
    assigned_ids = filter_valid_uuid_strs(manager.get_assigned_hostel_ids() or [])

    if requested_hostel_id:
        req_id_str = normalize_uuid_str(requested_hostel_id)
        if not req_id_str:
            return [], f"Unauthorized: Invalid hostel id '{requested_hostel_id}'"
        if req_id_str not in assigned_ids and not manager.has_hostel_access(req_id_str):
            return [], f"Unauthorized: You do not have permission to access hostel '{requested_hostel_id}'"
        return [req_id_str], None

    return assigned_ids, None


def require_hostel_access(param_name: str = "hostel_id"):
    """
    Decorator to verify that the authenticated manager has access
    to the hostel ID passed via URL path parameters, query string, or request body.
    
    Requires manager_required to be executed first.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            manager = getattr(g, "current_manager", None)
            if not manager:
                return error_response(message="Manager context missing", status_code=403)

            # 1. Check URL route kwargs
            hostel_id = kwargs.get(param_name)

            # 2. Check query params if not in route
            if not hostel_id:
                hostel_id = request.args.get(param_name)

            # 3. Check JSON body if not in query or route
            if not hostel_id and request.is_json:
                body = request.get_json(silent=True) or {}
                hostel_id = body.get(param_name)

            if hostel_id:
                if not manager.has_hostel_access(hostel_id):
                    return error_response(
                        message=f"Access denied. You are not assigned to hostel ID {hostel_id}",
                        status_code=403,
                    )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
