
from app.workers.celery_app import celery_app
from app.workers.discovery_worker import execute_discovery_job


@celery_app.task(
    name="globalsearch.discover_jobs",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def discover_jobs_task(self):
    try:
        return execute_discovery_job()
    except Exception as exc:
        raise self.retry(exc=exc)
