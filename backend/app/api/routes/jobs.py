from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user import User
from app.security.auth import get_current_user


router = APIRouter(prefix="/jobs", tags=["Jobs"])


def serialize_record(record) -> dict:
    data = {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }
    return jsonable_encoder(data)


def apply_job_filters(
    statement,
    search,
    country,
    city,
    employment_type,
    workplace_type,
):
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Job.title.ilike(term),
                Job.company.ilike(term),
                Job.description.ilike(term),
            )
        )

    if country:
        statement = statement.where(
            Job.country.ilike(f"%{country.strip()}%")
        )

    if city:
        statement = statement.where(
            Job.city.ilike(f"%{city.strip()}%")
        )

    if employment_type:
        statement = statement.where(
            Job.employment_type.ilike(
                f"%{employment_type.strip()}%"
            )
        )

    if workplace_type:
        statement = statement.where(
            Job.workplace_type.ilike(
                f"%{workplace_type.strip()}%"
            )
        )

    return statement


@router.get("/")
def list_jobs(
    search: str | None = Query(default=None, max_length=200),
    country: str | None = Query(default=None, max_length=100),
    city: str | None = Query(default=None, max_length=100),
    employment_type: str | None = Query(default=None, max_length=100),
    workplace_type: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = (
        search,
        country,
        city,
        employment_type,
        workplace_type,
    )

    count_statement = select(func.count(Job.id)).where(
        Job.is_active.is_(True)
    )
    count_statement = apply_job_filters(
        count_statement, *filters
    )

    total = db.scalar(count_statement) or 0

    statement = select(Job).where(
        Job.is_active.is_(True)
    )
    statement = apply_job_filters(statement, *filters)

    statement = (
        statement
        .order_by(desc(Job.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    jobs = db.scalars(statement).all()

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "jobs": [serialize_record(job) for job in jobs],
    }


@router.get("/matches")
def list_my_job_matches(
    min_score: float | None = Query(default=None, ge=0, le=100),
    eligibility_status: str | None = Query(
        default=None,
        max_length=50,
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_statement = (
        select(func.count(JobMatch.id))
        .join(Job, Job.id == JobMatch.job_id)
        .where(JobMatch.user_id == current_user.id)
    )

    statement = (
        select(JobMatch, Job)
        .join(Job, Job.id == JobMatch.job_id)
        .where(JobMatch.user_id == current_user.id)
    )

    if min_score is not None:
        count_statement = count_statement.where(
            JobMatch.score >= min_score
        )
        statement = statement.where(
            JobMatch.score >= min_score
        )

    if eligibility_status:
        count_statement = count_statement.where(
            JobMatch.eligibility_status == eligibility_status
        )
        statement = statement.where(
            JobMatch.eligibility_status == eligibility_status
        )

    total = db.scalar(count_statement) or 0

    rows = db.execute(
        statement
        .order_by(desc(JobMatch.score))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    matches = [
        {
            "match": serialize_record(match),
            "job": serialize_record(job),
        }
        for match, job in rows
    ]

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "matches": matches,
    }


@router.get("/{job_id}")
def get_job_details(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.is_active.is_(True),
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found or no longer active.",
        )

    return {
        "success": True,
        "job": serialize_record(job),
    }