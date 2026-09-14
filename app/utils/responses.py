from typing import Any, Optional, Dict
from flask import jsonify, Response


def success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status_code: int = 200,
    pagination: Optional[Dict[str, Any]] = None,
) -> tuple[Response, int]:
    """
    Format a standardized successful JSON API response.
    
    Example:
    {
        "success": True,
        "message": "...",
        "data": ...,
        "pagination": { ... } # optional
    }
    """
    payload: Dict[str, Any] = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    if pagination is not None:
        payload["pagination"] = pagination

    return jsonify(payload), status_code


def error_response(
    message: str = "An error occurred",
    status_code: int = 400,
    errors: Optional[Any] = None,
) -> tuple[Response, int]:
    """
    Format a standardized error JSON API response.
    
    Example:
    {
        "success": False,
        "message": "...",
        "errors": ... # optional
    }
    """
    payload: Dict[str, Any] = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        payload["errors"] = errors

    return jsonify(payload), status_code
