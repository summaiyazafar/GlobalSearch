from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job


def find_existing_job(
    db: Session,
    source_id,
    external_id: str,
) -> Job | None:
    statement = select(Job).where(
        Job.source_id == source_id,
        Job.external_id == external_id,
    )

    return db.scalar(statement)


def upsert_job(
    db: Session,
    source_id,
    normalized_data: dict,
) -> tuple[Job, bool]:
    """
    Insert a new job or update an existing job.

    Returns:
        (job_record, created)
        created=True means a new database record was inserted.
    """

    external_id = normalized_data["external_id"]

    existing_job = find_existing_job(
        db=db,
        source_id=source_id,
        external_id=external_id,
    )

    # Only assign fields that actually exist in the Job model.
    available_columns = set(Job.__table__.columns.keys())

    update_data = {
        key: value
        for key, value in normalized_data.items()
        if key in available_columns and key not in {
            "id",
            "source_id",
            "external_id",
            "created_at",
        }
    }

    if existing_job:
        for field, value in update_data.items():
            setattr(existing_job, field, value)

        return existing_job, False

    new_data = {
        key: value
        for key, value in normalized_data.items()
        if key in available_columns
    }

    new_data["source_id"] = source_id
    new_data["external_id"] = external_id

    new_job = Job(**new_data)
    db.add(new_job)

    return new_job, True