from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application


# These statuses represent applications that should prevent
# another active application for the same user and job.
ACTIVE_APPLICATION_STATUSES = {
    "draft",
    "pending_approval",
    "ready_for_review",
    "submitted",
}


def find_existing_application(
    db: Session,
    user_id,
    job_id,
):
    statement = (
        select(Application)
        .where(
            Application.user_id == user_id,
            Application.job_id == job_id,
            Application.status.in_(ACTIVE_APPLICATION_STATUSES),
        )
        .order_by(Application.created_at.desc())
    )

    return db.scalar(statement)


def has_duplicate_application(
    db: Session,
    user_id,
    job_id,
) -> bool:
    return find_existing_application(db, user_id, job_id) is not None