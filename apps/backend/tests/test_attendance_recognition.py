from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.ai import AIRecognitionResult
from app.services.attendance_recognition import (
    AttendancePersistenceError,
    RecognitionRejectedError,
    record_recognition_attendance,
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def employee(db_session):
    user = User(
        username="recognition_employee",
        password_hash="hashed-password",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.flush()
    employee = Employee(
        user_id=user.id,
        employee_code="EMP-REC-001",
        full_name="Recognition Employee",
        email="recognition@example.com",
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture
def recognition(employee):
    return AIRecognitionResult(
        matched=True,
        employee_id=employee.id,
        confidence=0.97,
        liveness=True,
    )


NOW = datetime(2026, 9, 5, 1, 0, tzinfo=timezone.utc)


def test_successful_check_in(db_session, recognition, employee):
    attendance = record_recognition_attendance(db_session, recognition, NOW)

    assert attendance.employee_id == employee.id
    assert attendance.check_in == NOW
    assert attendance.check_out is None


def test_successful_check_out(db_session, recognition, employee):
    first = record_recognition_attendance(db_session, recognition, NOW)
    later = datetime(2026, 9, 5, 9, 0, tzinfo=timezone.utc)

    second = record_recognition_attendance(db_session, recognition, later)

    assert second.id == first.id
    assert second.check_out == later


def test_unknown_face_is_rejected(db_session):
    result = AIRecognitionResult(
        matched=False,
        confidence=0.2,
        liveness=True,
    )

    with pytest.raises(RecognitionRejectedError) as error:
        record_recognition_attendance(db_session, result, NOW)

    assert error.value.status_code == 422
    assert db_session.query(Attendance).count() == 0


def test_liveness_failure_is_rejected(db_session, recognition):
    recognition.liveness = False

    with pytest.raises(RecognitionRejectedError) as error:
        record_recognition_attendance(db_session, recognition, NOW)

    assert error.value.status_code == 422


def test_duplicate_completed_attendance_is_rejected(db_session, recognition):
    record_recognition_attendance(db_session, recognition, NOW)
    record_recognition_attendance(
        db_session,
        recognition,
        datetime(2026, 9, 5, 9, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(RecognitionRejectedError) as error:
        record_recognition_attendance(
            db_session,
            recognition,
            datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
        )

    assert error.value.status_code == 409


def test_employee_not_found_is_rejected(db_session):
    result = AIRecognitionResult(
        matched=True,
        employee_id=999,
        confidence=0.9,
        liveness=True,
    )

    with pytest.raises(RecognitionRejectedError) as error:
        record_recognition_attendance(db_session, result, NOW)

    assert error.value.status_code == 404


def test_database_error_rolls_back(db_session, recognition, monkeypatch):
    def fail_commit():
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    with pytest.raises(AttendancePersistenceError):
        record_recognition_attendance(db_session, recognition, NOW)