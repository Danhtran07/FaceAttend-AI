from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.user import User, UserRole

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)



@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers(db_session):
    user = User(
        username="admin_attendance_test",
        password_hash="hashed-password",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        {"sub": str(user.id), "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def employee(db_session):
    user = User(
        username="employee_attendance_test",
        password_hash="hashed-password",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_code="EMP-ATT-001",
        full_name="Nguyen Van A",
        email="employee.attendance@example.com",
        department="IT",
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture
def employee_user_headers(db_session):
    user = User(
        username="employee_self_attendance",
        password_hash="hashed-password",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_code="EMP-ATT-SELF",
        full_name="Employee Self",
        email="self.attendance@example.com",
        department="Finance",
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}, user, employee


client = TestClient(app)


def test_get_attendance_returns_list(db_session, auth_headers, employee):
    record = Attendance(
        employee_id=employee.id,
        date=date(2026, 9, 2),
        check_in=datetime(2026, 9, 2, 8, 30, 0),
        check_out=datetime(2026, 9, 2, 17, 30, 0),
        status=AttendanceStatus.PRESENT,
    )
    db_session.add(record)
    db_session.commit()

    response = client.get("/api/attendance", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["employee_id"] == employee.id
    assert data[0]["status"] == "PRESENT"


def test_get_attendance_calendar_returns_every_day_of_month(
    db_session,
    auth_headers,
    employee,
):
    record = Attendance(
        employee_id=employee.id,
        date=date(2026, 9, 2),
        check_in=datetime(2026, 9, 2, 8, 15, 0),
        status=AttendanceStatus.PRESENT,
    )
    db_session.add(record)
    db_session.commit()

    response = client.get(
        "/api/attendance/calendar",
        params={"year": 2026, "month": 9, "employee_id": employee.id},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_days"] == 30
    assert len(data["days"]) == 30
    assert data["days"][1]["date"] == "2026-09-02"
    assert data["days"][1]["status"] == "PRESENT"
    assert data["days"][1]["has_record"] is True
    assert data["days"][0]["status"] == "ABSENT"
    assert data["days"][0]["has_record"] is False


def test_employee_can_only_view_own_attendance_calendar(
    db_session,
    employee_user_headers,
    employee,
):
    headers, _, own_employee = employee_user_headers

    response = client.get(
        "/api/attendance/calendar",
        params={"year": 2026, "month": 9, "employee_id": employee.id},
        headers=headers,
    )

    assert own_employee.id != employee.id
    assert response.status_code == 403


def test_create_attendance_success(db_session, auth_headers, employee):
    payload = {
        "employee_id": employee.id,
        "date": "2026-09-03",
        "check_in": "2026-09-03T08:15:00",
        "check_out": "2026-09-03T17:10:00",
        "status": "LATE",
    }

    response = client.post(
        "/api/attendance",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == employee.id
    assert data["date"] == "2026-09-03"
    assert data["status"] == "LATE"


def test_create_attendance_auto_sets_late_status_when_check_in_is_late(
    db_session,
    auth_headers,
    employee,
):
    payload = {
        "employee_id": employee.id,
        "date": "2026-09-08",
        "check_in": "2026-09-08T09:30:00",
    }

    response = client.post(
        "/api/attendance",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "LATE"


def test_attendance_response_uses_vietnam_timezone(db_session, auth_headers, employee):
    record = Attendance(
        employee_id=employee.id,
        date=date(2026, 9, 2),
        check_in=datetime(2026, 9, 2, 8, 30, 0, tzinfo=timezone.utc),
        status=AttendanceStatus.PRESENT,
        created_at=datetime(2026, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    response = client.get("/api/attendance", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()[0]
    assert data["check_in"] == "2026-09-02T15:30:00+07:00"
    assert data["created_at"] == "2026-09-02T15:00:00+07:00"


def test_create_attendance_conflict_for_same_employee_and_date(
    db_session,
    auth_headers,
    employee,
):
    payload = {
        "employee_id": employee.id,
        "date": "2026-09-04",
        "status": "ABSENT",
    }

    first_response = client.post(
        "/api/attendance",
        json=payload,
        headers=auth_headers,
    )
    second_response = client.post(
        "/api/attendance",
        json=payload,
        headers=auth_headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["detail"]


def test_update_attendance_success(db_session, auth_headers, employee):
    record = Attendance(
        employee_id=employee.id,
        date=date(2026, 9, 5),
        check_in=datetime(2026, 9, 5, 8, 0, 0),
        status=AttendanceStatus.ABSENT,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    response = client.put(
        f"/api/attendance/{record.id}",
        json={"status": "PRESENT", "check_in": "2026-09-05T08:15:00"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PRESENT"
    assert data["check_in"] == "2026-09-05T15:15:00+07:00"


def test_update_attendance_rejects_check_out_before_check_in(
    db_session,
    auth_headers,
    employee,
):
    record = Attendance(
        employee_id=employee.id,
        date=date(2026, 9, 7),
        check_in=datetime(2026, 9, 7, 8, 30, 0),
        status=AttendanceStatus.PRESENT,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    response = client.put(
        f"/api/attendance/{record.id}",
        json={"check_out": "2026-09-07T07:45:00"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "check_out" in response.json()["detail"]


def test_employee_can_only_view_own_attendance_records(
    db_session,
    employee_user_headers,
    employee,
):
    headers, _, own_employee = employee_user_headers

    own_record = Attendance(
        employee_id=own_employee.id,
        date=date(2026, 9, 9),
        check_in=datetime(2026, 9, 9, 8, 0, 0),
        status=AttendanceStatus.PRESENT,
    )
    other_record = Attendance(
        employee_id=employee.id,
        date=date(2026, 9, 10),
        check_in=datetime(2026, 9, 10, 8, 0, 0),
        status=AttendanceStatus.PRESENT,
    )
    db_session.add_all([own_record, other_record])
    db_session.commit()

    response = client.get("/api/attendance", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["employee_id"] == own_employee.id


def test_delete_attendance_success(db_session, auth_headers, employee):
    record = Attendance(
        employee_id=employee.id,
        date=date(2026, 9, 6),
        status=AttendanceStatus.ABSENT,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    response = client.delete(
        f"/api/attendance/{record.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""


def test_delete_user_with_employee_success(db_session, auth_headers, employee):
    user = db_session.query(User).filter(
        User.username == "employee_attendance_test"
    ).one()

    response = client.delete(
        f"/api/users/{user.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""
    assert db_session.query(User).filter(User.id == user.id).first() is None
    assert db_session.query(Employee).filter(Employee.id == employee.id).first() is None
