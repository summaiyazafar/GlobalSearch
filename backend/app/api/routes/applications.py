from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.application_engine.approval_manager import (
    approve_application,
    reject_application,
    request_human_approval,
)
from app.application_engine.duplicate_checker import (
    find_existing_application,
)
from app.database.session import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.security.auth import get_current_user


router = APIRouter(prefix="/applications", tags=["Applications"])


def serialize_application(application: Application) -> dict:
    data = {
        column.name: getattr(application, column.name)
        for column in application.__table__.columns
    }
    return jsonable_encoder(data)


def get_user_application(
    db: Session,
    application_id: UUID,
    user_id: UUID,
) -> Application:
    statement = select(Application).where(
        Application.id == application_id,
        Application.user_id == user_id,
    )

    application = db.scalar(statement)

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    return application


def validate_user_job_and_resume(
    db: Session,
    user_id: UUID,
    job_id: UUID,
    resume_id: UUID,
):
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.is_active.is_(True),
        )
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active job not found.",
        )

    resume = db.scalar(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id,
            Resume.is_active.is_(True),
        )
    )

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your active resume was not found.",
        )

    return job, resume


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_application(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        job_id = UUID(str(payload.get("job_id")))
        resume_id = UUID(str(payload.get("resume_id")))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Valid job_id and resume_id are required.",
        )

    cover_letter = payload.get("cover_letter")

    if cover_letter is not None and not isinstance(cover_letter, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cover_letter must be text.",
        )

    if cover_letter and len(cover_letter) > 20000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cover letter cannot exceed 20,000 characters.",
        )

    validate_user_job_and_resume(
        db=db,
        user_id=current_user.id,
        job_id=job_id,
        resume_id=resume_id,
    )

    existing = find_existing_application(
        db=db,
        user_id=current_user.id,
        job_id=job_id,
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "An active application already exists for this job.",
                "existing_application_id": str(existing.id),
                "existing_status": existing.status,
            },
        )

    application = Application(
        user_id=current_user.id,
        job_id=job_id,
        resume_id=resume_id,
        status="draft",
        cover_letter=cover_letter,
        status_note="Application draft created.",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "message": "Application draft created.",
        "application": serialize_application(application),
    }


@router.get("/")
def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    application_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Application).where(
        Application.user_id == current_user.id
    )

    if application_status:
        statement = statement.where(
            Application.status == application_status.strip().lower()
        )

    statement = statement.order_by(desc(Application.created_at))

    total_statement = select(Application.id).where(
        Application.user_id == current_user.id
    )

    if application_status:
        total_statement = total_statement.where(
            Application.status == application_status.strip().lower()
        )

    total = len(db.scalars(total_statement).all())

    applications = db.scalars(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "applications": [
            serialize_application(item) for item in applications
        ],
    }


@router.get("/{application_id}")
def get_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_user_application(
        db=db,
        application_id=application_id,
        user_id=current_user.id,
    )

    return {
        "success": True,
        "application": serialize_application(application),
    }


@router.patch("/{application_id}")
def update_application(
    application_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_user_application(
        db=db,
        application_id=application_id,
        user_id=current_user.id,
    )

    if application.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft applications can be edited.",
        )

    allowed_fields = {"resume_id", "cover_letter"}
    unknown_fields = set(payload.keys()) - allowed_fields

    if unknown_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Unsupported application fields.",
                "fields": sorted(unknown_fields),
            },
        )

    if "resume_id" in payload:
        try:
            resume_id = UUID(str(payload["resume_id"]))
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A valid resume_id is required.",
            )

        resume = db.scalar(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == current_user.id,
                Resume.is_active.is_(True),
            )
        )

        if resume is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Your active resume was not found.",
            )

        application.resume_id = resume_id

    if "cover_letter" in payload:
        cover_letter = payload["cover_letter"]

        if cover_letter is not None and not isinstance(cover_letter, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="cover_letter must be text.",
            )

        if cover_letter and len(cover_letter) > 20000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cover letter cannot exceed 20,000 characters.",
            )

        application.cover_letter = cover_letter

    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "message": "Application draft updated.",
        "application": serialize_application(application),
    }


@router.post("/{application_id}/request-approval")
def send_for_approval(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_user_application(
        db=db,
        application_id=application_id,
        user_id=current_user.id,
    )

    try:
        request_human_approval(application)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "message": "Application sent for your human review.",
        "application": serialize_application(application),
    }


@router.post("/{application_id}/approve")
def approve_application_for_submission(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_user_application(
        db=db,
        application_id=application_id,
        user_id=current_user.id,
    )

    try:
        approve_application(application)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "message": (
            "Application approved by the user. "
            "It is ready for the authorized submission workflow."
        ),
        "application": serialize_application(application),
    }


@router.post("/{application_id}/reject")
def reject_application_for_submission(
    application_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_user_application(
        db=db,
        application_id=application_id,
        user_id=current_user.id,
    )

    reason = payload.get("reason", "Rejected by the user.")

    if not isinstance(reason, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="reason must be text.",
        )

    try:
        reject_application(application, reason)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "message": "Application rejected.",
        "application": serialize_application(application),
    }