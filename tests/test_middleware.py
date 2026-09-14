from flask import g
from flask_jwt_extended import create_access_token
from app.models import User, UserRole, Owner, Manager, Hostel, ManagerHostel, ManagerHostelStatus
from app.middleware.auth import manager_required, login_required
from app.middleware.permissions import require_hostel_access, get_scoped_hostel_ids
from app.utils.responses import success_response


def test_manager_required_allowed(app, session):
    """Test manager_required decorator passes for active manager."""
    user = User(name="Manager User", email="mgr@test.com", role=UserRole.MANAGER, is_active=True)
    user.set_password("pass")
    session.add(user)
    session.commit()

    manager = Manager(user_id=user.id)
    session.add(manager)
    session.commit()

    @manager_required
    def sample_manager_endpoint():
        return success_response(message="Manager access granted", data={"manager_id": str(g.current_manager.id)})

    with app.app_context():
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    with app.test_request_context("/api/test-manager-only", headers={"Authorization": f"Bearer {token}"}):
        resp, status_code = sample_manager_endpoint()
        assert status_code == 200
        assert resp.get_json()["success"] is True
        assert resp.get_json()["message"] == "Manager access granted"
        assert resp.get_json()["data"]["manager_id"] == str(manager.id)


def test_manager_required_denies_owner_role(app, session):
    """Test manager_required decorator denies owner user."""
    user = User(name="Owner User", email="owner@test.com", role=UserRole.OWNER, is_active=True)
    user.set_password("pass")
    session.add(user)
    session.commit()

    @manager_required
    def sample_manager_endpoint():
        return success_response(message="Should not reach here")

    with app.app_context():
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    with app.test_request_context("/api/test-manager-only", headers={"Authorization": f"Bearer {token}"}):
        resp, status_code = sample_manager_endpoint()
        assert status_code == 403
        assert resp.get_json()["success"] is False
        assert "Manager access required" in resp.get_json()["message"]


def test_require_hostel_access_authorized_and_denied(app, session):
    """Test require_hostel_access permits assigned hostels and denies unassigned ones."""
    # 1. Owner & 2 Hostels
    owner_user = User(name="Owner", email="owner_h@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    hostel_1 = Hostel(
        owner_id=owner.id,
        name="Assigned Hostel",
        address="Addr 1",
        area="Hitech City",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        contact_phone="+919876543201",
        contact_email="h1@test.com",
    )
    hostel_2 = Hostel(
        owner_id=owner.id,
        name="Unassigned Hostel",
        address="Addr 2",
        area="Gachibowli",
        city="Hyderabad",
        state="Telangana",
        pincode="500032",
        contact_phone="+919876543202",
        contact_email="h2@test.com",
    )
    session.add_all([hostel_1, hostel_2])
    session.commit()

    # 2. Manager assigned only to hostel_1
    mgr_user = User(name="Assigned Mgr", email="assigned_mgr@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id)
    session.add(manager)
    session.commit()

    assignment = ManagerHostel(manager_id=manager.id, hostel_id=hostel_1.id, status=ManagerHostelStatus.ACTIVE)
    session.add(assignment)
    session.commit()

    @manager_required
    @require_hostel_access(param_name="hostel_id")
    def sample_hostel_endpoint(hostel_id):
        return success_response(message=f"Access granted for hostel {hostel_id}")

    with app.app_context():
        token = create_access_token(identity=str(mgr_user.id), additional_claims={"role": mgr_user.role})

    # Access assigned hostel -> 200 OK
    with app.test_request_context(f"/api/hostels/{hostel_1.id}/rooms", headers={"Authorization": f"Bearer {token}"}):
        resp, status_code = sample_hostel_endpoint(hostel_id=str(hostel_1.id))
        assert status_code == 200
        assert resp.get_json()["success"] is True

    # Access unassigned hostel -> 403 Forbidden
    with app.test_request_context(f"/api/hostels/{hostel_2.id}/rooms", headers={"Authorization": f"Bearer {token}"}):
        resp, status_code = sample_hostel_endpoint(hostel_id=str(hostel_2.id))
        assert status_code == 403
        assert resp.get_json()["success"] is False
        assert "Access denied" in resp.get_json()["message"]


def test_get_scoped_hostel_ids_helper(session):
    """Test get_scoped_hostel_ids returns properly scoped hostel lists."""
    owner_user = User(name="Owner Scoped", email="owner_s@test.com", role=UserRole.OWNER, is_active=True)
    owner_user.set_password("pass")
    session.add(owner_user)
    session.commit()

    owner = Owner(user_id=owner_user.id)
    session.add(owner)
    session.commit()

    h1 = Hostel(
        owner_id=owner.id,
        name="H1",
        address="A1",
        area="A",
        city="Hyderabad",
        state="Telangana",
        pincode="500001",
        contact_phone="+919000000001",
        contact_email="h1@s.com",
    )
    h2 = Hostel(
        owner_id=owner.id,
        name="H2",
        address="A2",
        area="B",
        city="Hyderabad",
        state="Telangana",
        pincode="500002",
        contact_phone="+919000000002",
        contact_email="h2@s.com",
    )
    session.add_all([h1, h2])
    session.commit()

    mgr_user = User(name="Mgr S", email="mgr_s@test.com", role=UserRole.MANAGER, is_active=True)
    mgr_user.set_password("pass")
    session.add(mgr_user)
    session.commit()

    manager = Manager(user_id=mgr_user.id)
    session.add(manager)
    session.commit()

    assignment = ManagerHostel(manager_id=manager.id, hostel_id=h1.id)
    session.add(assignment)
    session.commit()

    session.refresh(manager)

    # 1. No hostel specified -> returns all assigned
    scoped_all, err = get_scoped_hostel_ids(manager, None)
    assert err is None
    assert scoped_all == [str(h1.id)]

    # 2. Specific authorized hostel specified -> returns that hostel
    scoped_single, err = get_scoped_hostel_ids(manager, str(h1.id))
    assert err is None
    assert scoped_single == [str(h1.id)]

    # 3. Unauthorized hostel specified -> returns error
    scoped_unauth, err = get_scoped_hostel_ids(manager, str(h2.id))
    assert "Unauthorized" in err
    assert scoped_unauth == []
