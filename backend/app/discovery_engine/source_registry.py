from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_source import JobSource


SUPPORTED_SOURCE_TYPES = {
    "greenhouse",
    "lever",
    "ashby",
}


def validate_source_type(source_type: str) -> str:
    normalized = source_type.strip().lower()

    if normalized not in SUPPORTED_SOURCE_TYPES:
        raise ValueError(
            "Unsupported source type. Supported types: "
            "greenhouse, lever, ashby."
        )

    return normalized


def get_source_by_id(
    db: Session,
    source_id,
) -> JobSource | None:
    return db.scalar(
        select(JobSource).where(JobSource.id == source_id)
    )


def register_company_source(
    db: Session,
    name: str,
    source_type: str,
    base_url: str,
    description: str | None = None,
) -> JobSource:
    name = name.strip()
    base_url = base_url.strip()

    if not name:
        raise ValueError("Company or source name is required.")

    if not base_url:
        raise ValueError("Career-board URL or board identifier is required.")

    source_type = validate_source_type(source_type)

    existing = db.scalar(
        select(JobSource).where(
            JobSource.name == name,
            JobSource.source_type == source_type,
            JobSource.base_url == base_url,
        )
    )

    if existing:
        raise ValueError("This company source is already registered.")

    source = JobSource(
        name=name,
        source_type=source_type,
        base_url=base_url,
        description=description.strip() if description else None,
        is_active=True,
        requires_authentication=False,
    )

    db.add(source)
    db.flush()

    return source


def deactivate_company_source(
    db: Session,
    source: JobSource,
) -> JobSource:
    source.is_active = False
    return source


def activate_company_source(
    db: Session,
    source: JobSource,
) -> JobSource:
    source.is_active = True
    return source