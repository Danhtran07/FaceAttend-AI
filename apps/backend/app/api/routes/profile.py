from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileResponse, ProfileUpdate


router = APIRouter(
    prefix="/api/profile",
    tags=["Profile"],
)

MAX_AVATAR_SIZE = 5 * 1024 * 1024
AVATAR_TYPES = {
    "image/jpeg": (".jpg", lambda content: content.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda content: content.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (".webp", lambda content: content[:4] == b"RIFF" and content[8:12] == b"WEBP"),
}


def _get_or_create_profile(db: Session, user: User) -> UserProfile:
    if user.profile is None:
        user.profile = UserProfile()
        db.flush()

    if user.employee is not None:
        if user.profile.full_name is None:
            user.profile.full_name = user.employee.full_name
        if user.profile.email is None:
            user.profile.email = user.employee.email

    return user.profile


@router.get("", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(db, current_user)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(db, current_user)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/avatar", response_model=ProfileResponse)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_type = AVATAR_TYPES.get(file.content_type or "")
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Avatar must be a JPEG, PNG, or WebP image",
        )

    content = file.file.read(MAX_AVATAR_SIZE + 1)
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Avatar must be 5 MB or smaller",
        )
    if not file_type[1](content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image",
        )

    avatar_dir = Path(__file__).resolve().parents[3] / "uploads" / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    avatar_path = avatar_dir / f"{uuid4().hex}{file_type[0]}"
    avatar_path.write_bytes(content)

    profile = _get_or_create_profile(db, current_user)
    previous_avatar_url = profile.avatar_url
    profile.avatar_url = f"/uploads/avatars/{avatar_path.name}"
    db.commit()
    db.refresh(profile)

    if previous_avatar_url and previous_avatar_url.startswith("/uploads/avatars/"):
        previous_path = avatar_dir / Path(previous_avatar_url).name
        if previous_path != avatar_path and previous_path.is_file():
            previous_path.unlink()

    return profile
