import os

# Set isolated test environment variables BEFORE importing application modules,
# since app.database and app.security read environment variables at import time.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-employee-api-qa-suite"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models import Employee, User
from app.security import create_access_token, hash_password


@pytest.fixture()
def db_session():
    """Provide an isolated in-memory SQLite database session per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """Provide a FastAPI TestClient wired to the isolated test DB session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def regular_user(db_session):
    """Create a standard active user in the test database."""
    user = User(
        email="user@example.com",
        hashed_password=hash_password("UserPass123!"),
        role="user",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_user(db_session):
    """Create an active admin user in the test database."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def inactive_user(db_session):
    """Create an inactive user in the test database."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("InactivePass123!"),
        role="user",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def user_auth_headers(regular_user):
    token = create_access_token({"sub": regular_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_auth_headers(admin_user):
    token = create_access_token({"sub": admin_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def inactive_auth_headers(inactive_user):
    token = create_access_token({"sub": inactive_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_employee(db_session):
    """Seed a single employee record in the test database."""
    emp = Employee(
        name="Alice Johnson",
        email="alice.johnson@company.com",
        department="Engineering",
        salary=95000.0,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return emp
