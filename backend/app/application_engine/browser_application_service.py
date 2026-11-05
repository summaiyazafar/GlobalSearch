
from dataclasses import asdict
from typing import Optional

from playwright.async_api import Page

from app.browser_automation.ats_registry import get_ats_adapter


async def prepare_browser_application(
    page: Page,
    job_url: str,
    answers: dict,
    resume_path: Optional[str] = None,
) -> dict:
    """
    Open a supported ATS job page and prepare its application form.
    Does not submit the application.
    """

    adapter = get_ats_adapter(page, job_url)

    page_information = await adapter.open_job(job_url)

    preparation = await adapter.prepare_application(
        answers=answers,
        resume_path=resume_path,
    )

    return {
        "success": True,
        "page": page_information,
        "preparation": asdict(preparation),
        "requires_human_review": True,
        "submission_performed": False,
        "message": (
            "Application prepared. Review every field and submit "
            "only after giving explicit approval."
        ),
    }
