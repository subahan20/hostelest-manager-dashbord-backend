from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone
from app.extensions import db
from app.models import Manager, Notice, NoticeStatus
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class NoticeService:
    """Service handling Notice creation, management, and hostel authorization."""

    @staticmethod
    def get_notices(
        manager: Manager,
        hostel_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List notices with filters and pagination.
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Notice.query.filter(Notice.hostel_id.in_(hostel_ids))

        if status:
            query = query.filter(Notice.status == status.strip().lower())
        if priority:
            query = query.filter(Notice.priority == priority.strip().lower())

        query = query.order_by(Notice.publish_at.desc())

        items, pagination = paginate_query(query)
        data = [item.to_dict(include_author=True) for item in items]

        return data, pagination, None, 200

    @staticmethod
    def get_notice_by_id(manager: Manager, notice_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch single notice by ID."""
        notice = db.session.get(Notice, notice_id)
        if not notice:
            return None, "Notice not found", 404

        if not manager.has_hostel_access(notice.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return notice.to_dict(include_author=True), None, 200

    @staticmethod
    def create_notice(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Create a new notice for an authorized hostel."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        notice = Notice(
            hostel_id=hostel_id,
            created_by=manager.user_id,
            title=data["title"].strip(),
            content=data["content"].strip(),
            priority=data.get("priority", "normal"),
            publish_at=data.get("publish_at") or datetime.now(timezone.utc),
            expires_at=data.get("expires_at"),
            status=data.get("status", NoticeStatus.PUBLISHED),
        )
        db.session.add(notice)
        db.session.commit()

        return notice.to_dict(include_author=True), None, 201

    @staticmethod
    def update_notice(manager: Manager, notice_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update an existing notice."""
        notice = db.session.get(Notice, notice_id)
        if not notice:
            return None, "Notice not found", 404

        if not manager.has_hostel_access(notice.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        for field in ["title", "content", "priority", "publish_at", "expires_at", "status"]:
            if field in data:
                setattr(notice, field, data[field])

        db.session.commit()
        return notice.to_dict(include_author=True), None, 200

    @staticmethod
    def delete_notice(manager: Manager, notice_id: str) -> Tuple[bool, Optional[str], int]:
        """Delete a notice."""
        notice = db.session.get(Notice, notice_id)
        if not notice:
            return False, "Notice not found", 404

        if not manager.has_hostel_access(notice.hostel_id):
            return False, "Access denied. You do not manage this hostel.", 403

        db.session.delete(notice)
        db.session.commit()
        return True, None, 200
