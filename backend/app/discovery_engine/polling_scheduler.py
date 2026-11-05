
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.discovery_engine.job_discovery import discover_jobs_from_source
from app.models.job_source import JobSource

logger = logging.getLogger(__name__)


def run_discovery_cycle() -> dict:
    """
    Run one discovery cycle for all active registered sources.
    This function is intended for a scheduler or background worker.
    """
    db: Session = SessionLocal()

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "sources_checked": 0,
        "sources_succeeded": 0,
        "sources_failed": 0,
        "jobs_created": 0,
        "jobs_updated": 0,
        "errors": [],
    }

    try:
        sources = db.scalars(
            select(JobSource).where(JobSource.is_active.is_(True))
        ).all()

        for source in sources:
            report["sources_checked"] += 1

            try:
                result = discover_jobs_from_source(db, source)

                report["sources_succeeded"] += 1
                report["jobs_created"] += int(result.get("created", 0))
                report["jobs_updated"] += int(result.get("updated", 0))

            except Exception as exc:
                db.rollback()
                report["sources_failed"] += 1
                report["errors"].append({
                    "source": source.name,
                    "error": str(exc),
                })
                logger.exception(
                    "Discovery failed for source %s",
                    source.name,
                )

        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        return report

    finally:
        db.close()
