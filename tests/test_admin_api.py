from flask_jwt_extended import create_access_token
from app.models import User, UserRole, Manager


def setup_admin_test_data(session):
    super_admin_user = User(
        name="Super Admin",
        email="super_admin@hostelest.com",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    super_admin_user.set_password("Admin@123456")
    session.add(super_admin_user)
    session.commit()

    manager_user = User(
        name="Regular Manager",
        email="manager_user@hostelest.com",
        role=UserRole.MANAGER,
        is_active=True,
    )
    manager_user.set_password("Manager@123456")
    session.add(manager_user)
    session.commit()

    manager = Manager(user_id=manager_user.id, employee_code="MGR-001")
    session.add(manager)
    session.commit()

    return {
        "super_admin": super_admin_user,
        "manager_user": manager_user,
        "manager": manager,
    }


def test_create_admin_success(app, client, session):
    data = setup_admin_test_data(session)
    admin_user = data["super_admin"]

    with app.app_context():
        token = create_access_token(identity=str(admin_user.id), additional_claims={"role": admin_user.role})

    payload = {
        "name": "New Platform Admin",
        "email": "new_admin@hostelest.com",
        "password": "SecurePassword@123",
        "phone": "+919876543299",
        "role": "super_admin",
    }

    res = client.post(
        "/api/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    res_data = res.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["name"] == "New Platform Admin"
    assert res_data["data"]["email"] == "new_admin@hostelest.com"
    assert res_data["data"]["role"] == "super_admin"
    assert "password_hash" not in res_data["data"]


def test_create_admin_unauthorized_manager_forbidden(app, client, session):
    data = setup_admin_test_data(session)
    manager_user = data["manager_user"]

    with app.app_context():
        token = create_access_token(identity=str(manager_user.id), additional_claims={"role": manager_user.role})

    payload = {
        "name": "Elevated User",
        "email": "elevated@hostelest.com",
        "password": "Password123",
        "role": "super_admin",
    }

    res = client.post(
        "/api/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    res_data = res.get_json()
    assert res_data["success"] is False
    assert "Super Admin access required" in res_data["message"]


def test_create_admin_unauthenticated(client):
    payload = {
        "name": "Anonymous User",
        "email": "anon@hostelest.com",
        "password": "Password123",
    }
    res = client.post("/api/admin/users", json=payload)
    assert res.status_code == 401


def test_create_admin_duplicate_email_conflict(app, client, session):
    data = setup_admin_test_data(session)
    admin_user = data["super_admin"]

    with app.app_context():
        token = create_access_token(identity=str(admin_user.id), additional_claims={"role": admin_user.role})

    payload = {
        "name": "Duplicate Admin",
        "email": "super_admin@hostelest.com",  # Already exists
        "password": "Password123",
        "role": "super_admin",
    }

    res = client.post(
        "/api/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 409
    res_data = res.get_json()
    assert res_data["success"] is False
    assert "already exists" in res_data["message"]


def test_create_admin_missing_fields_validation_error(app, client, session):
    data = setup_admin_test_data(session)
    admin_user = data["super_admin"]

    with app.app_context():
        token = create_access_token(identity=str(admin_user.id), additional_claims={"role": admin_user.role})

    # Missing email & password too short
    payload = {
        "name": "Incomplete Admin",
        "password": "123",
    }

    res = client.post(
        "/api/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422
    res_data = res.get_json()
    assert res_data["success"] is False
    assert "errors" in res_data
    assert "email" in res_data["errors"]
    assert "password" in res_data["errors"]
