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


def test_user_password_hashing_and_verification():
    """Verify password hashing using Werkzeug check_password_hash."""
    user = User(
        name="Security Test",
        email="security@hostelest.com",
        role=UserRole.MANAGER,
    )
    user.set_password("SecurePassword@2026")
    
    assert user.password_hash != "SecurePassword@2026"
    assert user.check_password("SecurePassword@2026") is True
    assert user.check_password("WrongPassword") is False
    assert user.check_password("") is False


def test_manager_creation_and_login_flow(client, session):
    """
    Test complete flow:
    Manager creation -> User creation -> Password hashing -> Database commit -> Login -> JWT generation
    """
    correct_password = "SecretManagerPass!789"
    wrong_password = "IncorrectPassword"

    user = User(
        name="Fresh Manager",
        email="fresh_manager@hostelest.com",
        phone="+919123456780",
        role="manager",
        is_active=True
    )
    user.set_password(correct_password)
    session.add(user)
    session.commit()

    manager = Manager(
        user_id=user.id,
        name="Fresh Manager",
        email="fresh_manager@hostelest.com",
        phone="+919123456780",
        employee_code="EMP-FRESH-01",
        status="ACTIVE",
        is_active=True
    )
    session.add(manager)
    session.commit()

    # Step 1: Check password verification directly on user model
    assert user.check_password(correct_password) is True
    assert user.check_password(wrong_password) is False

    # Step 2: Login with wrong password returns 401
    wrong_resp = client.post(
        "/api/auth/login",
        json={"email": "fresh_manager@hostelest.com", "password": wrong_password}
    )
    assert wrong_resp.status_code == 401
    assert wrong_resp.get_json()["success"] is False

    # Step 3: Login with correct password returns 200 + tokens
    success_resp = client.post(
        "/api/auth/login",
        json={"email": "fresh_manager@hostelest.com", "password": correct_password}
    )
    assert success_resp.status_code == 200
    res_data = success_resp.get_json()
    assert res_data["success"] is True
    assert "access_token" in res_data["data"]
    assert "refresh_token" in res_data["data"]
    assert res_data["data"]["user"]["email"] == "fresh_manager@hostelest.com"
    assert res_data["data"]["user"]["role"] == "manager"


def test_login_email_normalization(client, session):
    """Test login with uppercase email and leading/trailing whitespace."""
    user = User(
        name="Normalized Manager",
        email="norm_manager@hostelest.com",
        role=UserRole.MANAGER,
        is_active=True
    )
    user.set_password("NormPass12345!")
    session.add(user)
    session.commit()

    manager = Manager(user_id=user.id, email=user.email)
    session.add(manager)
    session.commit()

    # Uppercase and whitespace in request
    resp = client.post(
        "/api/auth/login",
        json={"email": "   NORM_MANAGER@hostelest.com   ", "password": "NormPass12345!"}
    )
    assert resp.status_code == 200
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["user"]["email"] == "norm_manager@hostelest.com"


def test_duplicate_user_email_prevention(session):
    """Test that duplicate email cannot create another user in database."""
    import pytest
    from sqlalchemy.exc import IntegrityError

    u1 = User(
        name="User One",
        email="unique_check@hostelest.com",
        role=UserRole.MANAGER
    )
    u1.set_password("Pass123!")
    session.add(u1)
    session.commit()

    u2 = User(
        name="User Two",
        email="unique_check@hostelest.com",
        role=UserRole.MANAGER
    )
    u2.set_password("Pass456!")
    session.add(u2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_owner_style_bcrypt_manager_login(client, session):
    """
    Reproduce the production bug path:
    Owner Dashboard hashes passwords with bcrypt and writes users + managers.
    Manager Dashboard must accept the same email/password immediately.
    """
    import bcrypt

    email = "manager@test.com"
    password = "Test@12345"
    wrong_password = "WrongPassword"

    pwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = User(
        name="Owner Created Manager",
        email=email,
        phone="+919988776655",
        role="manager",
        is_active=True,
        password_hash=pwd_hash,
    )
    session.add(user)
    session.flush()

    manager = Manager(
        user_id=user.id,
        name=user.name,
        email=email,
        phone=user.phone,
        password_hash=pwd_hash,
        status="ACTIVE",
        is_active=True,
    )
    session.add(manager)
    session.commit()

    assert user.check_password(password) is True
    assert user.check_password(wrong_password) is False

    ok = client.post("/api/auth/login", json={"email": email, "password": password})
    assert ok.status_code == 200
    body = ok.get_json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["user"]["role"] == "manager"

    # whitespace / case normalization
    norm = client.post(
        "/api/auth/login",
        json={"email": "  MANAGER@TEST.COM  ", "password": password},
    )
    assert norm.status_code == 200

    bad = client.post("/api/auth/login", json={"email": email, "password": wrong_password})
    assert bad.status_code == 401
    assert bad.get_json()["success"] is False


def test_managers_table_password_hash_sync_login(client, session):
    """
    When only the managers row has credentials (no users row yet),
    login must verify managers.password_hash and sync a User.
    This is the fallback Manager Dashboard uses for owner-created accounts.
    """
    import bcrypt
    import uuid
    from sqlalchemy import text

    email = "sync_manager@test.com"
    password = "Test@12345"
    pwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    session.execute(
        text(
            """
            INSERT INTO managers (
                id, user_id, name, email, phone, password_hash,
                role, status, is_active, created_at, updated_at
            ) VALUES (
                :id, NULL, :name, :email, :phone, :pwd_hash,
                'manager', 'ACTIVE', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "name": "Sync Manager",
            "email": email,
            "phone": "+919900112233",
            "pwd_hash": pwd_hash,
        },
    )
    session.commit()

    assert User.query.filter_by(email=email).first() is None

    ok = client.post("/api/auth/login", json={"email": email, "password": password})
    assert ok.status_code == 200
    body = ok.get_json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["user"]["email"] == email
    assert body["data"]["user"]["role"] == "manager"

    synced = User.query.filter_by(email=email).first()
    assert synced is not None
    assert synced.check_password(password) is True

    bad = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword"})
    assert bad.status_code == 401


def test_inactive_manager_cannot_login(client, session):
    """Inactive manager accounts must be rejected after password verification."""
    user = User(
        name="Inactive Mgr",
        email="inactive_mgr@test.com",
        role=UserRole.MANAGER,
        is_active=False,
    )
    user.set_password("Test@12345")
    session.add(user)
    session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "inactive_mgr@test.com", "password": "Test@12345"},
    )
    assert resp.status_code == 403
    assert resp.get_json()["success"] is False

