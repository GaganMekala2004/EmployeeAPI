"""Employee CRUD, RBAC, Validation, and Error Handling tests (EMP-TC-009 through EMP-TC-019)."""

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import get_db
from app.main import app
from app.models import Employee


def test_emp_tc_009_create_employee_success_as_admin(client, admin_auth_headers):
    """EMP-TC-009: Admin can create a new employee and receive 201 Created."""
    payload = {
        "name": "Bob Smith",
        "email": "bob.smith@company.com",
        "department": "Finance",
        "salary": 82500.50,
    }
    response = client.post("/employees/", json=payload, headers=admin_auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["id"], int)
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["department"] == payload["department"]
    assert data["salary"] == payload["salary"]


def test_emp_tc_010_create_employee_forbidden_for_non_admin(client, user_auth_headers):
    """EMP-TC-010: Regular (non-admin) user receives 403 Forbidden when creating an employee."""
    payload = {
        "name": "Unauthorized Attempt",
        "email": "unauth@company.com",
        "department": "HR",
        "salary": 60000.0,
    }
    response = client.post("/employees/", json=payload, headers=user_auth_headers)

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "message": "Only administrators can perform this action.",
        "status_code": 403,
    }


def test_emp_tc_011_create_employee_missing_fields_and_empty_body(
    client, admin_auth_headers
):
    """EMP-TC-011: Missing required fields or empty request body returns 422."""
    empty_res = client.post("/employees/", json={}, headers=admin_auth_headers)
    assert empty_res.status_code == 422
    missing_fields = {err["loc"][-1] for err in empty_res.json()["detail"]}
    assert {"name", "email", "department", "salary"}.issubset(missing_fields)

    partial_res = client.post(
        "/employees/",
        json={"name": "Incomplete User", "email": "inc@company.com"},
        headers=admin_auth_headers,
    )
    assert partial_res.status_code == 422


def test_emp_tc_012_create_employee_invalid_data_types(client, admin_auth_headers):
    """EMP-TC-012: Non-numeric salary value fails Pydantic float validation with 422."""
    payload = {
        "name": "Bad Type",
        "email": "badtype@company.com",
        "department": "Engineering",
        "salary": "not-a-number",
    }
    response = client.post("/employees/", json=payload, headers=admin_auth_headers)

    assert response.status_code == 422
    assert any("salary" in err["loc"] for err in response.json()["detail"])


def test_emp_tc_013_create_employee_boundary_salary_values(client, admin_auth_headers):
    """EMP-TC-013: Boundary numeric values for salary (0.0 and large float) are handled accurately."""
    zero_payload = {
        "name": "Intern Zero",
        "email": "intern.zero@company.com",
        "department": "Operations",
        "salary": 0.0,
    }
    res_zero = client.post("/employees/", json=zero_payload, headers=admin_auth_headers)
    assert res_zero.status_code == 201
    assert res_zero.json()["salary"] == 0.0

    high_payload = {
        "name": "Executive High",
        "email": "exec.high@company.com",
        "department": "Executive",
        "salary": 9999999.99,
    }
    res_high = client.post("/employees/", json=high_payload, headers=admin_auth_headers)
    assert res_high.status_code == 201
    assert res_high.json()["salary"] == 9999999.99


def test_emp_tc_014_create_employee_duplicate_email_conflict(
    db_session, sample_employee, admin_auth_headers
):
    """EMP-TC-014: Duplicate employee email violates unique constraint (currently unhandled -> 500)."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            payload = {
                "name": "Duplicate Alice",
                "email": sample_employee.email,
                "department": "Engineering",
                "salary": 90000.0,
            }
            response = safe_client.post(
                "/employees/", json=payload, headers=admin_auth_headers
            )
            # Application does not catch SQLAlchemy IntegrityError, resulting in 500
            assert response.status_code == 500
    finally:
        db_session.rollback()
        app.dependency_overrides.clear()


def test_emp_tc_015_get_all_employees_pagination_filter_and_search(
    client, db_session, user_auth_headers
):
    """EMP-TC-015: GET /employees/ supports default limit=5, skip/limit, department filter, and name search."""
    employees = [
        Employee(name=f"Dev User {i}", email=f"dev{i}@co.com", department="Engineering", salary=80000 + i)
        for i in range(1, 5)
    ] + [
        Employee(name="HR Lead", email="hr1@co.com", department="HR", salary=70000),
        Employee(name="Finance Analyst", email="fin1@co.com", department="Finance", salary=75000),
    ]
    db_session.add_all(employees)
    db_session.commit()

    # Default limit is 5
    default_res = client.get("/employees/", headers=user_auth_headers)
    assert default_res.status_code == 200
    assert len(default_res.json()) == 5

    # Pagination with skip & limit
    paged_res = client.get("/employees/?skip=4&limit=5", headers=user_auth_headers)
    assert paged_res.status_code == 200
    assert len(paged_res.json()) == 2

    # Department filter
    dept_res = client.get("/employees/?department=Engineering&limit=10", headers=user_auth_headers)
    assert dept_res.status_code == 200
    assert len(dept_res.json()) == 4
    assert all(e["department"] == "Engineering" for e in dept_res.json())

    # Case-insensitive search
    search_res = client.get("/employees/?search=finance", headers=user_auth_headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert search_res.json()[0]["name"] == "Finance Analyst"


def test_emp_tc_016_get_employee_by_id_valid_nonexistent_and_invalid(
    client, sample_employee, user_auth_headers
):
    """EMP-TC-016: GET /employees/{id} returns 200 for existing, 404 for missing, 422 for non-int ID."""
    ok_res = client.get(f"/employees/{sample_employee.id}", headers=user_auth_headers)
    assert ok_res.status_code == 200
    assert ok_res.json()["email"] == sample_employee.email

    not_found_res = client.get("/employees/999999", headers=user_auth_headers)
    assert not_found_res.status_code == 404
    assert not_found_res.json() == {
        "success": False,
        "message": "Employee not found",
        "status_code": 404,
    }

    invalid_id_res = client.get("/employees/not-an-id", headers=user_auth_headers)
    assert invalid_id_res.status_code == 422


def test_emp_tc_017_update_employee_partial_not_found_and_rbac(
    client, sample_employee, admin_auth_headers, user_auth_headers
):
    """EMP-TC-017: PUT /employees/{id} performs partial update as admin, returns 404 if missing, 403 for non-admin."""
    # Partial update (only salary and department)
    update_res = client.put(
        f"/employees/{sample_employee.id}",
        json={"department": "Platform Engineering", "salary": 110000.0},
        headers=admin_auth_headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["name"] == sample_employee.name
    assert updated["email"] == sample_employee.email
    assert updated["department"] == "Platform Engineering"
    assert updated["salary"] == 110000.0

    # Non-existent ID
    missing_res = client.put(
        "/employees/999999",
        json={"salary": 120000.0},
        headers=admin_auth_headers,
    )
    assert missing_res.status_code == 404
    assert missing_res.json()["message"] == "Employee not found"

    # Non-admin forbidden
    forbidden_res = client.put(
        f"/employees/{sample_employee.id}",
        json={"salary": 120000.0},
        headers=user_auth_headers,
    )
    assert forbidden_res.status_code == 403


def test_emp_tc_018_delete_employee_success_not_found_and_rbac(
    client, sample_employee, admin_auth_headers, user_auth_headers
):
    """EMP-TC-018: DELETE /employees/{id} removes record as admin, verifies 404 afterward, enforces admin RBAC."""
    # Non-admin cannot delete
    forbidden_res = client.delete(
        f"/employees/{sample_employee.id}", headers=user_auth_headers
    )
    assert forbidden_res.status_code == 403

    # Admin deletes successfully
    del_res = client.delete(
        f"/employees/{sample_employee.id}", headers=admin_auth_headers
    )
    assert del_res.status_code == 200
    assert del_res.json() == {"message": "Employee deleted successfully"}

    # Subsequent GET returns 404
    verify_res = client.get(
        f"/employees/{sample_employee.id}", headers=admin_auth_headers
    )
    assert verify_res.status_code == 404

    # Deleting non-existent ID returns 404
    del_missing_res = client.delete("/employees/999999", headers=admin_auth_headers)
    assert del_missing_res.status_code == 404
    assert del_missing_res.json()["message"] == "Employee not found"


def test_emp_tc_019_database_error_handling(admin_auth_headers):
    """EMP-TC-019: Simulated SQLAlchemy database failure returns 500 Internal Server Error."""

    class FailingSession:
        def query(self, *args, **kwargs):
            raise SQLAlchemyError("Simulated database connection failure")

    def override_failing_db():
        yield FailingSession()

    app.dependency_overrides[get_db] = override_failing_db
    try:
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            response = safe_client.get("/employees/", headers=admin_auth_headers)
            assert response.status_code == 500
    finally:
        app.dependency_overrides.clear()
