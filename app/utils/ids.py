"""Helpers for normalizing identifiers used with GUID/UUID database columns."""
from __future__ import annotations

import uuid
from typing import Iterable, List, Optional


def is_valid_uuid(value) -> bool:
    """Return True when value can be parsed as a UUID."""
    if value is None:
        return False
    try:
        uuid.UUID(str(value).strip())
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def normalize_uuid_str(value) -> Optional[str]:
    """Return canonical UUID string or None if invalid."""
    if not is_valid_uuid(value):
        return None
    return str(uuid.UUID(str(value).strip()))


def filter_valid_uuid_strs(values: Iterable) -> List[str]:
    """Filter/normalize an iterable of values to valid UUID strings (deduped, order preserved)."""
    seen = set()
    result: List[str] = []
    for value in values or []:
        normalized = normalize_uuid_str(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
