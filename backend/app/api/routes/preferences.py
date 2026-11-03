from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.preference import Preference
from app.models.user import User
from app.security.auth import get_current_user


router = APIRouter(
    prefix="/preferences",
    tags=["Job Preferences"],
)


def serialize_preferences(preference: Preference) -> dict:
    return {
        column.name: getattr(preference, column.name)
        for column in Preference.__table__.columns
    }


@router.get("/")
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preference = db.scalar(
        select(Preference).where(
            Preference.user_id == current_user.id
        )
    )

    if preference is None:
        return {
            "success": True,
            "preferences": None,
            "message": "Job preferences have not been saved yet.",
        }

    return {
        "success": True,
        "preferences": serialize_preferences(preference),
    }


@router.put("/")
def save_preferences(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_fields = {
        column.name
        for column in Preference.__table__.columns
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
                "message": "Unsupported preference fields.",
                "fields": sorted(invalid_fields),
            },
        )

    preference = db.scalar(
        select(Preference).where(
            Preference.user_id == current_user.id
        )
    )

    try:
        if preference is None:
            preference = Preference(
                user_id=current_user.id,
                **payload,
            )
            db.add(preference)
        else:
            for field, value in payload.items():
                setattr(preference, field, value)

        db.commit()
        db.refresh(preference)

        return {
            "success": True,
            "message": "Job preferences saved successfully.",
            "preferences": serialize_preferences(preference),
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Preferences conflict with database constraints.",
        )