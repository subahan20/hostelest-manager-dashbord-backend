# HOSTELEST - Manager Backend API

> *"The Fastest and Smartest way to Find Hostels"*  
> Initial market: Hyderabad, India

---

## Overview

Hostelest is a production-grade SaaS platform for hostel discovery, booking, and operations management.  
This service is the **Manager Backend REST API**, built with Python 3.12+, Flask, PostgreSQL, SQLAlchemy, Flask-Migrate, and Flask-JWT-Extended.

---

## Tech Stack (Phase 1)

- **Language:** Python 3.12+ (3.14 compatible)
- **Framework:** Flask 3.x
- **Database ORM:** Flask-SQLAlchemy 3.x with PostgreSQL (native UUIDs & indexing)
- **Database Migrations:** Flask-Migrate (Alembic)
- **Authentication & Security:** Flask-JWT-Extended, Werkzeug Password Hashing
- **CORS:** Flask-CORS
- **Testing:** Pytest

---

## Project Structure (Phase 1)

```
hosteleast-manager-dashbord-back-end/
├── app/
│   ├── __init__.py          # Flask application factory (create_app)
│   ├── config.py            # Environment configurations (Dev, Testing, Prod)
│   ├── errors.py            # Centralized error handlers
│   ├── extensions.py        # SQLAlchemy, Migrate, JWT, CORS instances
│   ├── models/
│   │   ├── __init__.py      # Models export
│   │   ├── base.py          # BaseModel (UUID PK, created_at, updated_at)
│   │   ├── user.py          # User model (super_admin, owner, manager)
│   │   ├── owner.py         # Owner model
│   │   ├── manager.py       # Manager model
│   │   ├── hostel.py        # Hostel model
│   │   ├── manager_hostel.py# ManagerHostel assignment model (M:N)
│   │   ├── room.py          # Room model & occupancy tracking
│   │   ├── student.py       # Student model & personal/emergency profiles
│   │   ├── booking.py       # Booking model & HST-YYYY-XXXXXX ref generator
│   │   ├── payment.py       # Payment model (rent, deposit, maintenance)
│   │   ├── complaint.py     # Complaint model (priority, status, notes)
│   │   ├── maintenance.py   # Maintenance request model & costing
│   │   ├── visitor.py       # Visitor log model (check-in/check-out)
│   │   └── notice.py        # Notice model (priority, publish/expiry)
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py          # @login_required, @manager_required decorators
│   │   └── permissions.py   # @require_hostel_access & get_scoped_hostel_ids
│   ├── routes/
│   │   ├── __init__.py      # Blueprint registration
│   │   ├── health.py        # Health check endpoint (/api/health)
│   │   └── auth/
│   │       ├── __init__.py
│   │       └── auth.py      # Login, refresh, logout, me routes
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── auth_schema.py   # Marshmallow validation schemas
│   └── utils/
│       ├── __init__.py
│       └── responses.py     # Standard API response helpers (success, error)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and in-memory test DB setup
│   ├── test_health.py       # Health check tests
│   └── test_models.py       # Model relationships, constraints, and auth logic tests
├── .env                     # Local environment file
├── .env.example             # Environment template
├── requirements.txt         # Project dependencies
├── run.py                   # Application entrypoint
└── README.md                # Documentation
```

---

## Getting Started

### 1. Prerequisites
- Python 3.12 or newer
- PostgreSQL (14+ recommended)

### 2. Setup Virtual Environment

```bash
# Navigate to the backend directory
cd hosteleast-manager-dashbord-back-end

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and adjust database credentials:

```bash
cp .env.example .env
```

Ensure `DATABASE_URL` is configured for your PostgreSQL instance:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/hostelest_db
```

### 5. Initialize Database Migrations

```bash
# Initialize migration directory (first time only)
flask db init

# Generate initial migration for Phase 1 models
flask db migrate -m "Initial migration: User, Owner, Manager, Hostel, ManagerHostel"

# Apply migrations to database
flask db upgrade
```

### 6. Database Seeding (Sample Data)

To populate the database with realistic Hyderabad hostel management data (Owner, Manager, Hostels, Rooms, Students, Bookings, Payments, Complaints, Maintenance, Visitors, Notices):

```bash
# Option 1: Standalone seed script
python seed.py

# Option 2: Flask CLI command
flask seed
```

**Default Seed Credentials:**
- **Manager Email:** `manager.hitech@hostelest.com`
- **Password:** `Manager@123`
- **Owner Email:** `owner.hyderabad@hostelest.com`
- **Password:** `Owner@123`

---

### 7. Run the Application

```bash
python run.py
```
The server will start at: `http://localhost:5000`

---

## API Endpoints

### Health & System
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status check | No |

### Authentication & User
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate with email & password | No |
| `POST` | `/api/auth/refresh` | Issue new access token using refresh token | Refresh JWT |
| `POST` | `/api/auth/logout` | Terminate session | Access JWT |
| `GET` | `/api/auth/me` | Fetch authenticated user profile & manager data | Access JWT |

### Manager Operations & Dashboard
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/dashboard` | Aggregated dashboard stats for all assigned hostels | Manager JWT |
| `GET` | `/api/manager/dashboard?hostel_id=<id>` | Scoped dashboard stats for a specific hostel | Manager JWT |

### Rooms API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/rooms` | List rooms (filters: `status`, `floor`, `room_type`, `search`, `page`, `limit`) | Manager JWT |
| `GET` | `/api/manager/rooms/<id>` | Fetch single room details and live occupancy | Manager JWT |
| `POST` | `/api/manager/rooms` | Create a new room in an assigned hostel | Manager JWT |
| `PUT` | `/api/manager/rooms/<id>` | Update room details | Manager JWT |
| `PATCH` | `/api/manager/rooms/<id>/status` | Update room operational status (`available`, `occupied`, `maintenance`, etc.) | Manager JWT |

### Students API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/students` | List students (filters: `hostel_id`, `room_id`, `status`, `search`, `page`, `limit`) | Manager JWT |
| `GET` | `/api/manager/students/<id>` | Fetch single student details | Manager JWT |
| `POST` | `/api/manager/students` | Register a new student & assign to room | Manager JWT |
| `PUT` | `/api/manager/students/<id>` | Update student profile and room reassignment | Manager JWT |
| `PATCH` | `/api/manager/students/<id>/status` | Update student status (e.g., `checked_out`) | Manager JWT |

### Bookings API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/bookings` | List bookings (filters: `hostel_id`, `room_id`, `student_id`, `status`, `search`) | Manager JWT |
| `GET` | `/api/manager/bookings/<id>` | Fetch single booking details | Manager JWT |
| `POST` | `/api/manager/bookings` | Create a new booking reservation | Manager JWT |
| `POST` | `/api/manager/bookings/<id>/approve` | Approve a pending booking | Manager JWT |
| `POST` | `/api/manager/bookings/<id>/reject` | Reject a booking | Manager JWT |
| `POST` | `/api/manager/bookings/<id>/check-in` | Transactional check-in with overbooking prevention | Manager JWT |
| `POST` | `/api/manager/bookings/<id>/check-out` | Transactional check-out with automatic room freeing | Manager JWT |
| `POST` | `/api/manager/bookings/<id>/cancel` | Cancel a booking | Manager JWT |

### Payments API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/payments` | List payments with filters (`hostel_id`, `student_id`, `status`, `payment_type`, `from_date`, `to_date`, `page`, `limit`) | Manager JWT |
| `GET` | `/api/manager/payments/pending` | List all pending payments | Manager JWT |
| `GET` | `/api/manager/payments/overdue` | List all overdue payments | Manager JWT |
| `GET` | `/api/manager/payments/<id>` | Fetch single payment record details | Manager JWT |
| `POST` | `/api/manager/payments` | Create payment invoice/demand note | Manager JWT |
| `POST` | `/api/manager/payments/<id>/record` | Record payment collection & transaction reference | Manager JWT |

### Complaints API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/complaints` | List complaints with filters (`status`, `priority`, `date range`, `page`, `limit`) | Manager JWT |
| `GET` | `/api/manager/complaints/<id>` | Fetch single complaint details | Manager JWT |
| `POST` | `/api/manager/complaints` | Create / file a new student complaint | Manager JWT |
| `PATCH` | `/api/manager/complaints/<id>/status` | Update status (`pending`, `in_progress`, `resolved`, `rejected`) and assign technician | Manager JWT |
| `POST` | `/api/manager/complaints/<id>/resolve` | Resolve complaint with required resolution notes | Manager JWT |

### Maintenance API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/maintenance` | List maintenance requests (`category`, `priority`, `status`, `page`, `limit`) | Manager JWT |
| `GET` | `/api/manager/maintenance/<id>` | Fetch single maintenance request details | Manager JWT |
| `POST` | `/api/manager/maintenance` | Create a new maintenance request | Manager JWT |
| `POST` | `/api/manager/maintenance/<id>/assign` | Assign maintenance to technician/vendor | Manager JWT |
| `PATCH` | `/api/manager/maintenance/<id>/status` | Update maintenance status, actual cost, notes | Manager JWT |

### Visitors API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/visitors` | List visitor log entries (filters: `student_id`, `search`, `page`, `limit`) | Manager JWT |
| `GET` | `/api/manager/visitors/<id>` | Fetch single visitor entry details | Manager JWT |
| `POST` | `/api/manager/visitors` | Check-in / register a new visitor entry | Manager JWT |
| `PUT` | `/api/manager/visitors/<id>` | Update visitor details | Manager JWT |
| `POST` | `/api/manager/visitors/<id>/checkout` | Record visitor checkout timestamp | Manager JWT |

### Notices API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/notices` | List active notices (`status`, `priority`, `page`, `limit`) | Manager JWT |
| `GET` | `/api/manager/notices/<id>` | Fetch single notice details | Manager JWT |
| `POST` | `/api/manager/notices` | Create and publish a hostel notice | Manager JWT |
| `PUT` | `/api/manager/notices/<id>` | Update notice title, content, or priority | Manager JWT |
| `DELETE` | `/api/manager/notices/<id>` | Delete a notice | Manager JWT |

### Reports & Analytics API
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/manager/reports/occupancy` | Occupancy rates breakdown by room type, floor, & hostel | Manager JWT |
| `GET` | `/api/manager/reports/bookings` | Booking trends, status distribution, & daily timeline for charts | Manager JWT |
| `GET` | `/api/manager/reports/payments` | Revenue, collection rate, payment method breakdown, & timeline | Manager JWT |
| `GET` | `/api/manager/reports/students` | Demographics, top colleges/companies, admissions & checkouts | Manager JWT |

#### Dashboard Response Format:
```json
{
  "success": true,
  "message": "Dashboard metrics fetched successfully",
  "data": {
    "overview": {
      "total_rooms": 12,
      "occupied_rooms": 8,
      "available_rooms": 3,
      "maintenance_rooms": 1,
      "occupancy_rate": 66.67,
      "total_students": 16,
      "pending_bookings": 2,
      "pending_payments": 3,
      "overdue_payments": 1,
      "pending_complaints": 2,
      "pending_maintenance": 1
    },
    "room_status": {
      "occupied": 8,
      "available": 3,
      "partially_occupied": 0,
      "maintenance": 1
    },
    "recent_bookings": [ ... ],
    "recent_students": [ ... ],
    "recent_complaints": [ ... ],
    "maintenance_requests": [ ... ],
    "recent_payments": [ ... ]
  }
}
```

---

## Authorization & Security Pipeline

Every manager-specific endpoint enforces a 5-step security verification:

```
JWT authentication
        ↓
User authentication (User exists & is active)
        ↓
Role verification (User.role == 'manager')
        ↓
Manager-hostel assignment verification (ManagerHostel active status)
        ↓
Hostel-scoped database query (Never trusting client-supplied IDs)
```

Reusable Decorators:
- `@manager_required`: Ensures valid JWT, active account, manager role, and populates `g.current_user` and `g.current_manager`.
- `@require_hostel_access(param_name='hostel_id')`: Enforces that the manager has active assignment to the target hostel (from route params, query string, or body).
- `get_scoped_hostel_ids(manager, requested_hostel_id)`: Resolves verified hostel IDs for database queries.

---

## Running Tests

Run the full automated test suite using `pytest`:

```bash
pytest -v
```

**Test Coverage Summary:** 66/66 automated tests passing across 12 test suites covering:
- Authentication & JWT lifecycles
- Multi-hostel role authorization and scoping
- Capacity locking and overbooking prevention
- Financial tracking, billing, and rent collections
- Complaint and maintenance ticketing workflows
- Visitor gate pass check-ins and check-outs
- Notice board announcements
- Aggregated analytics and reporting
- Seed script execution integrity
