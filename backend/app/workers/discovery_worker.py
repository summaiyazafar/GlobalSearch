
import logging

from app.discovery_engine.polling_scheduler import run_discovery_cycle

logger = logging.getLogger(__name__)


def execute_discovery_job() -> dict:
    """
    Execute one complete job-discovery cycle.
    Can be called by Celery or another scheduler.
    """
    logger.info("Starting scheduled job discovery")

    result = run_discovery_cycle()

    logger.info(
        "Discovery finished: checked=%s succeeded=%s failed=%s "
        "created=%s updated=%s",
        result["sources_checked"],
        result["sources_succeeded"],
        result["sources_failed"],
        result["jobs_created"],
        result["jobs_updated"],
    )

    return result
