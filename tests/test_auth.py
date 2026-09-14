import json
from app.models import User, UserRole, Manager


def test_login_success(client, session):
    """Test login with valid manager credentials."""
    user = User(
        name="John Manager",
        email="john@hostelest.com",
        phone="+919876500001",
        role=UserRole.MANAGER,
        is_active=True,
    )
    user.set_password("ManagerSecret123!")
    session.add(user)
    session.commit()

    manager = Manager(user_id=user.id, employee_code="EMP-101")
    session.add(manager)
    session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "john@hostelest.com", "password": "ManagerSecret123!"},
    )
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["message"] == "Login successful"
    assert "access_token" in res_data["data"]
    assert "refresh_token" in res_data["data"]
    assert res_data["data"]["user"]["email"] == "john@hostelest.com"
    assert res_data["data"]["user"]["role"] == "manager"
    assert "manager_profile" in res_data["data"]["user"]
    assert res_data["data"]["user"]["manager_profile"]["employee_code"] == "EMP-101"


def test_login_invalid_password(client, session):
    """Test login with incorrect password returns 401."""
    user = User(
        name="Jane Manager",
        email="jane@hostelest.com",
        role=UserRole.MANAGER,
        is_active=True,
    )
    user.set_password("CorrectPassword123")
    session.add(user)
    session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "jane@hostelest.com", "password": "WrongPassword456"},
    )
    assert response.status_code == 401
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["message"] == "Invalid email or password"


def test_login_nonexistent_email(client):
    """Test login with unregistered email returns 401."""
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@hostelest.com", "password": "AnyPassword"},
    )
    assert response.status_code == 401
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["message"] == "Invalid email or password"


def test_login_inactive_user(client, session):
    """Test login with inactive/disabled account returns 403."""
    user = User(
        name="Disabled Manager",
        email="disabled@hostelest.com",
        role=UserRole.MANAGER,
        is_active=False,
    )
    user.set_password("Secret123!")
    session.add(user)
    session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "disabled@hostelest.com", "password": "Secret123!"},
    )
    assert response.status_code == 403
    res_data = response.get_json()
    assert res_data["success"] is False
    assert "disabled" in res_data["message"].lower()


def test_login_validation_errors(client):
    """Test login with invalid payload returns 422 validation error."""
    response = client.post(
        "/api/auth/login",
        json={"email": "not-a-valid-email", "password": ""},
    )
    assert response.status_code == 422
    res_data = response.get_json()
    assert res_data["success"] is False
    assert "errors" in res_data


def test_token_refresh(client, session):
    """Test token refresh using valid refresh token."""
    user = User(
        name="Refresh Test",
        email="refresh@hostelest.com",
        role=UserRole.MANAGER,
        is_active=True,
    )
    user.set_password("Password123!")
    session.add(user)
    session.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "refresh@hostelest.com", "password": "Password123!"},
    )
    refresh_token = login_resp.get_json()["data"]["refresh_token"]

    # Use refresh token to get new access token
    refresh_resp = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert refresh_resp.status_code == 200
    ref_data = refresh_resp.get_json()
    assert ref_data["success"] is True
    assert "access_token" in ref_data["data"]


def test_auth_me_endpoint(client, session):
    """Test GET /api/auth/me with valid access token."""
    user = User(
        name="Current User Test",
        email="me@hostelest.com",
        role=UserRole.MANAGER,
        is_active=True,
    )
    user.set_password("Password123!")
    session.add(user)
    session.commit()

    manager = Manager(user_id=user.id, employee_code="EMP-ME")
    session.add(manager)
    session.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "me@hostelest.com", "password": "Password123!"},
    )
    access_token = login_resp.get_json()["data"]["access_token"]

    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.get_json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == "me@hostelest.com"
    assert me_data["data"]["manager_profile"]["employee_code"] == "EMP-ME"


def test_logout_endpoint(client, session):
    """Test POST /api/auth/logout with valid token."""
    user = User(
        name="Logout User",
        email="logout@hostelest.com",
        role=UserRole.MANAGER,
        is_active=True,
    )
    user.set_password("Password123!")
    session.add(user)
    session.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "logout@hostelest.com", "password": "Password123!"},
    )
    access_token = login_resp.get_json()["data"]["access_token"]

    logout_resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.get_json()["success"] is True
