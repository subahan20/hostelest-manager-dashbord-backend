from typing import Tuple, Dict, Any, List
from flask import request
from sqlalchemy.orm import Query


def paginate_query(
    query: Query,
    default_limit: int = 20,
    max_limit: int = 100,
) -> Tuple[List[Any], Dict[str, int]]:
    """
    Paginate a SQLAlchemy query using page and limit from request query parameters.
    
    Returns:
        (items, pagination_dict)
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = min(max_limit, max(1, int(request.args.get("limit", default_limit))))
    except (ValueError, TypeError):
        limit = default_limit

    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    pages = (total + limit - 1) // limit if total > 0 else 1

    pagination = {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
    }
    return items, pagination
