from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.skill import Skill
from app.models.education import Education
from app.models.experience import Experience
from app.models.project import Project
from app.models.certification import Certification
from app.security.auth import get_current_user


router = APIRouter(
    prefix="/profile-data",
    tags=["Profile Information"],
)


def serialize_record(record):
    data = {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }
    return jsonable_encoder(data)


def register_resource(resource_name: str, model):
    """
    Register secure CRUD endpoints for a user's profile resource.
    All database queries are scoped to the authenticated user.
    """

    base_path = f"/{resource_name}"

    @router.get(base_path, name=f"list_{resource_name}")
    def list_records(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        records = db.scalars(
            select(model).where(model.user_id == current_user.id)
        ).all()

        return {
            "success": True,
            "count": len(records),
            "items": [serialize_record(item) for item in records],
        }

    @router.post(base_path, name=f"create_{resource_name}")
    def create_record(
        payload: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        allowed_fields = {
            column.name
            for column in model.__table__.columns
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
                    "message": "Unsupported fields.",
                    "fields": sorted(invalid_fields),
                },
            )

        try:
            record = model(
                user_id=current_user.id,
                **payload,
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                "success": True,
                "message": f"{resource_name} record created.",
                "item": serialize_record(record),
            }

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Record conflicts with database constraints.",
            )

    @router.patch(
        f"{base_path}/{{record_id}}",
        name=f"update_{resource_name}",
    )
    def update_record(
        record_id: UUID,
        payload: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        record = db.scalar(
            select(model).where(
                model.id == record_id,
                model.user_id == current_user.id,
            )
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Record not found.",
            )

        allowed_fields = {
            column.name
            for column in model.__table__.columns
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
                    "message": "Unsupported fields.",
                    "fields": sorted(invalid_fields),
                },
            )

        try:
            for field, value in payload.items():
                setattr(record, field, value)

            db.commit()
            db.refresh(record)

            return {
                "success": True,
                "message": f"{resource_name} record updated.",
                "item": serialize_record(record),
            }

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Updated record conflicts with database constraints.",
            )

    @router.delete(
        f"{base_path}/{{record_id}}",
        name=f"delete_{resource_name}",
    )
    def delete_record(
        record_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        record = db.scalar(
            select(model).where(
                model.id == record_id,
                model.user_id == current_user.id,
            )
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Record not found.",
            )

        db.delete(record)
        db.commit()

        return {
            "success": True,
            "message": f"{resource_name} record deleted.",
        }


register_resource("skills", Skill)
register_resource("education", Education)
register_resource("experience", Experience)
register_resource("projects", Project)
register_resource("certifications", Certification)