"""Authentication and Health Check API tests (EMP-TC-001 through EMP-TC-008)."""


def test_emp_tc_001_root_health_check_and_middleware_header(client):
    """EMP-TC-001: Root endpoint returns running status and X-Process-Time header."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Employee Management API is Running"}
    assert "X-Process-Time" in response.headers
    assert float(response.headers["X-Process-Time"]) >= 0.0


def test_emp_tc_002_user_signup_success(client):
    """EMP-TC-002: Valid user registration returns 201 with default role and active flag."""
    payload = {"email": "newuser@example.com", "password": "StrongPassword123!"}
    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert isinstance(data["id"], int)
    assert "password" not in data
    assert "hashed_password" not in data


def test_emp_tc_003_user_signup_duplicate_email(client, regular_user):
    """EMP-TC-003: Registering an already existing email returns 409 with custom error payload."""
    payload = {"email": regular_user.email, "password": "AnotherPassword123!"}
    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 409
    assert response.json() == {
        "success": False,
        "message": "Email already registered.",
        "status_code": 409,
    }


def test_emp_tc_004_user_signup_invalid_email_format(client):
    """EMP-TC-004: Registering with an invalid email format fails Pydantic EmailStr validation."""
    payload = {"email": "not-a-valid-email", "password": "StrongPassword123!"}
    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("email" in err["loc"] for err in errors)


def test_emp_tc_005_user_login_success(client, regular_user):
    """EMP-TC-005: Logging in with valid OAuth2 form credentials returns a Bearer JWT."""
    response = client.post(
        "/auth/login",
        data={"username": regular_user.email, "password": "UserPass123!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 20


def test_emp_tc_006_user_login_invalid_credentials(client, regular_user):
    """EMP-TC-006: Wrong password or non-existent user returns 401 Unauthorized."""
    wrong_pw = client.post(
        "/auth/login",
        data={"username": regular_user.email, "password": "WrongPassword!"},
    )
    assert wrong_pw.status_code == 401
    assert wrong_pw.json() == {
        "success": False,
        "message": "Invalid email or password.",
        "status_code": 401,
    }

    missing_user = client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "AnyPassword123!"},
    )
    assert missing_user.status_code == 401
    assert missing_user.json()["message"] == "Invalid email or password."


def test_emp_tc_007_get_current_user_authenticated_and_unauthenticated(
    client, regular_user, user_auth_headers
):
    """EMP-TC-007: /auth/me returns profile for valid JWT and 401 for missing/invalid JWT."""
    valid_res = client.get("/auth/me", headers=user_auth_headers)
    assert valid_res.status_code == 200
    assert valid_res.json()["email"] == regular_user.email
    assert valid_res.json()["role"] == "user"

    no_token_res = client.get("/auth/me")
    assert no_token_res.status_code == 401

    bad_token_res = client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert bad_token_res.status_code == 401
    assert bad_token_res.json()["message"] == "Could not validate credentials."


def test_emp_tc_008_inactive_user_access_denied(client, inactive_auth_headers):
    """EMP-TC-008: Inactive user with a signed JWT is denied access with 403 Forbidden."""
    response = client.get("/auth/me", headers=inactive_auth_headers)

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "message": "Inactive user.",
        "status_code": 403,
    }
