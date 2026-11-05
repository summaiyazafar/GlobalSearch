
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.discovery_engine.job_discovery import discover_jobs_from_source
from app.models.job_source import JobSource
from app.security.auth import get_current_user


router = APIRouter(
    prefix="/discovery",
    tags=["Job Discovery"],
)


def require_admin(current_user):
    admin_emails = {
        email.strip().lower()
        for email in settings.ADMIN_EMAILS
        if email.strip()
    }

    user_email = (current_user.email or "").strip().lower()

    if not admin_emails or user_email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is required to run job discovery.",
        )

    return current_user


@router.get("/sources")
def list_discovery_sources(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    sources = db.scalars(
        select(JobSource).order_by(JobSource.name.asc())
    ).all()

    return {
        "total": len(sources),
        "sources": [
            {
                "id": str(source.id),
                "name": source.name,
                "source_type": source.source_type,
                "base_url": source.base_url,
                "is_active": source.is_active,
            }
            for source in sources
        ],
    }


@router.post("/sources/{source_id}/run")
def run_source_discovery(
    source_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    source = db.scalar(
        select(JobSource).where(JobSource.id == source_id)
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job source not found.",
        )

    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job source is inactive.",
        )

    try:
        result = discover_jobs_from_source(db, source)

        return {
            "success": True,
            "source": source.name,
            "source_type": source.source_type,
            "result": result,
        }

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Job discovery failed: {str(exc)}",
        ) from exc


@router.get("/health")
def discovery_health():
    return {
        "service": "job_discovery",
        "status": "available",
        "supported_sources": ["greenhouse", "lever", "ashby"],
    }
