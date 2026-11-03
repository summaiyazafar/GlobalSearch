from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.models.profile import Profile
from app.models.user import User
from app.security.auth import get_current_user


router = APIRouter(
    prefix="/profile",
    tags=["User Profile"],
)


def serialize_profile(profile: Profile) -> dict:
    return {
        column.name: getattr(profile, column.name)
        for column in Profile.__table__.columns
    }


@router.get("/")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.scalar(
        select(Profile).where(Profile.user_id == current_user.id)
    )

    if profile is None:
        return {
            "success": True,
            "profile": None,
            "message": "Profile has not been created yet.",
        }

    return {
        "success": True,
        "profile": serialize_profile(profile),
    }


@router.put("/")
def save_profile(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_fields = {
        column.name
        for column in Profile.__table__.columns
    } - {
        "id",
        "user_id",
        "created_at",
        "updated_at",
    }

    invalid_fields = set(payload.keys()) - allowed_fields

    if invalid_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Unsupported profile fields.",
                "fields": sorted(invalid_fields),
            },
        )

    profile = db.scalar(
        select(Profile).where(Profile.user_id == current_user.id)
    )

    try:
        if profile is None:
            profile = Profile(
                user_id=current_user.id,
                **payload,
            )
            db.add(profile)
        else:
            for field, value in payload.items():
                setattr(profile, field, value)

        db.commit()
        db.refresh(profile)

        return {
            "success": True,
            "message": "Profile saved successfully.",
            "profile": serialize_profile(profile),
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Profile data conflicts with database constraints.",
        )