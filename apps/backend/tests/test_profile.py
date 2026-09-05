import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.employee import Employee
from app.models.user import User, UserRole


client = TestClient(app)

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield db
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_get_profile_prefills_employee_identity(db_session):
    user = User(
        username="profile_employee",
        password_hash="hashed-password",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        Employee(
            user_id=user.id,
            employee_code="EMP-PROFILE",
            full_name="Profile Employee",
            email="profile@example.com",
        )
    )
    db_session.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    response = client.get(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Profile Employee"
    assert response.json()["email"] == "profile@example.com"