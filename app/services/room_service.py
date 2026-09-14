from typing import Tuple, Optional, Dict, Any, List
from app.extensions import db
from app.models import Manager, Room, RoomStatus
from app.middleware.permissions import get_scoped_hostel_ids
from app.utils.pagination import paginate_query


class RoomService:
    """Service handling Room operations and hostel access validation."""

    @staticmethod
    def get_rooms(
        manager: Manager,
        hostel_id: Optional[str] = None,
        status: Optional[str] = None,
        floor: Optional[int] = None,
        room_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]], Optional[str], int]:
        """
        List rooms with filtering, search, and pagination.
        
        Returns:
            (room_list, pagination_meta, error_message, status_code)
        """
        hostel_ids, err = get_scoped_hostel_ids(manager, hostel_id)
        if err:
            return None, None, err, 403

        if not hostel_ids:
            return [], {"page": 1, "limit": 20, "total": 0, "pages": 1}, None, 200

        query = Room.query.filter(Room.hostel_id.in_(hostel_ids))

        if status:
            query = query.filter(Room.status == status.strip().lower())
        if floor is not None:
            query = query.filter(Room.floor == floor)
        if room_type:
            query = query.filter(Room.room_type == room_type.strip().lower())
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(Room.room_number.ilike(search_term))

        query = query.order_by(Room.floor.asc(), Room.room_number.asc())

        items, pagination = paginate_query(query)
        rooms_data = [room.to_dict(include_occupancy=True) for room in items]

        return rooms_data, pagination, None, 200

    @staticmethod
    def get_room_by_id(manager: Manager, room_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Fetch a single room by ID if authorized."""
        room = db.session.get(Room, room_id)
        if not room:
            return None, "Room not found", 404

        if not manager.has_hostel_access(room.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        return room.to_dict(include_occupancy=True), None, 200

    @staticmethod
    def create_room(manager: Manager, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Create a new room in an assigned hostel."""
        hostel_id = str(data["hostel_id"])
        if not manager.has_hostel_access(hostel_id):
            return None, "Access denied. You do not manage the specified hostel.", 403

        # Check for duplicate room number in this hostel
        existing = Room.query.filter_by(
            hostel_id=hostel_id,
            room_number=data["room_number"].strip(),
        ).first()
        if existing:
            return None, f"Room '{data['room_number']}' already exists in this hostel.", 409

        room = Room(
            hostel_id=hostel_id,
            room_number=data["room_number"].strip(),
            floor=data.get("floor", 1),
            room_type=data.get("room_type", "double"),
            capacity=data.get("capacity", 2),
            rent=data["rent"],
            status=data.get("status", RoomStatus.AVAILABLE),
        )
        db.session.add(room)
        db.session.commit()

        return room.to_dict(include_occupancy=True), None, 201

    @staticmethod
    def update_room(manager: Manager, room_id: str, data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update room attributes."""
        room = db.session.get(Room, room_id)
        if not room:
            return None, "Room not found", 404

        if not manager.has_hostel_access(room.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        # If changing room number, ensure no conflict
        if "room_number" in data and data["room_number"].strip() != room.room_number:
            existing = Room.query.filter(
                Room.hostel_id == room.hostel_id,
                Room.room_number == data["room_number"].strip(),
                Room.id != room.id,
            ).first()
            if existing:
                return None, f"Room '{data['room_number']}' already exists in this hostel.", 409
            room.room_number = data["room_number"].strip()

        if "floor" in data:
            room.floor = data["floor"]
        if "room_type" in data:
            room.room_type = data["room_type"]
        if "capacity" in data:
            room.capacity = data["capacity"]
        if "rent" in data:
            room.rent = data["rent"]
        if "status" in data:
            room.status = data["status"]

        db.session.commit()
        return room.to_dict(include_occupancy=True), None, 200

    @staticmethod
    def update_room_status(manager: Manager, room_id: str, new_status: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
        """Update room status only."""
        room = db.session.get(Room, room_id)
        if not room:
            return None, "Room not found", 404

        if not manager.has_hostel_access(room.hostel_id):
            return None, "Access denied. You do not manage this hostel.", 403

        room.status = new_status.strip().lower()
        db.session.commit()
        return room.to_dict(include_occupancy=True), None, 200
