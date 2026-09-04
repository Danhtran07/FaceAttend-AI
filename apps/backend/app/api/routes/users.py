from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


def _create_employee_profile(db: Session, user: User) -> None:
    if user.employee is not None:
        return

    db.add(
        Employee(
            user_id=user.id,
            employee_code=f"EMP-{user.id:04d}",
            full_name=user.username,
            email=f"{user.username}@local.invalid",
        )
    )


@router.get(
    "",
    response_model=list[UserResponse],
)
def get_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return db.query(User).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing_user = (
        db.query(User)
        .filter(User.username == payload.username)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )

    db.add(user)
    db.flush()

    if user.role == UserRole.EMPLOYEE:
        _create_employee_profile(db, user)

    db.commit()
    db.refresh(user)

    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    if "username" in update_data:
        existing_user = (
            db.query(User)
            .filter(
                User.username == update_data["username"],
                User.id != user_id,
            )
            .first()
        )

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

    if "password" in update_data:
        user.password_hash = hash_password(
            update_data.pop("password")
        )

    for field, value in update_data.items():
        setattr(user, field, value)

    if user.role == UserRole.EMPLOYEE:
        _create_employee_profile(db, user)

    db.commit()
    db.refresh(user)

    return user

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()