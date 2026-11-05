
import re
from datetime import datetime, timezone

from playwright.async_api import Page
from sqlalchemy.orm import Session

from app.models.application import Application


SUCCESS_SELECTORS = [
    "[data-testid*='success']",
    "[class*='application-success']",
    "[class*='confirmation']",
    "#application-success",
]

SUCCESS_PHRASES = [
    "application submitted",
    "application has been submitted",
    "application received",
    "application has been received",
    "successfully submitted",
    "thank you for applying",
    "thank you for your application",
    "your application was received",
]

REFERENCE_PATTERNS = [
    r"(?:confirmation|application)\s*(?:number|id|reference)\s*[:#]?\s*([A-Z0-9-]{5,})",
]


async def verify_submission_confirmation(page: Page) -> dict:
    """
    Look for explicit confirmation that the external website
    received the application.

    A click on Submit alone is never considered confirmation.
    """

    body_text = ""

    try:
        body_text = await page.locator("body").inner_text(timeout=10000)
    except Exception:
        pass

    normalized_text = " ".join(body_text.lower().split())

    matching_phrases = [
        phrase
        for phrase in SUCCESS_PHRASES
        if phrase in normalized_text
    ]

    matching_selectors = []

    for selector in SUCCESS_SELECTORS:
        try:
            locator = page.locator(selector).first

            if await locator.count() and await locator.is_visible():
                matching_selectors.append(selector)
        except Exception:
            continue

    confirmation_reference = None

    for pattern in REFERENCE_PATTERNS:
        match = re.search(pattern, body_text, re.IGNORECASE)

        if match:
            confirmation_reference = match.group(1)
            break

    # Require explicit confirmation text or a visible
    # success element together with application-related text.
    verified = bool(
        matching_phrases
        or (
            matching_selectors
            and "application" in normalized_text
            and any(
                word in normalized_text
                for word in ("received", "submitted", "successful")
            )
        )
    )

    return {
        "verified": verified,
        "page_url": page.url,
        "confirmation_reference": confirmation_reference,
        "matching_phrases": matching_phrases,
        "matching_selectors": matching_selectors,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "message": (
            "External website confirmation detected."
            if verified
            else "Submission could not be verified. Application status unchanged."
        ),
    }


async def mark_application_submitted(
    db: Session,
    application: Application,
    page: Page,
) -> dict:
    """
    Update the local application only after explicit website confirmation.
    """

    if application.status != "ready_for_review":
        return {
            "updated": False,
            "message": (
                "Application must be approved and ready for review "
                "before submission verification."
            ),
        }

    verification = await verify_submission_confirmation(page)

    if not verification["verified"]:
        return {
            "updated": False,
            "verification": verification,
            "message": "No reliable submission confirmation was found.",
        }

    application.status = "submitted"
    application.submitted_at = datetime.now(timezone.utc)

    application.submission_reference = (
        verification["confirmation_reference"]
        or verification["page_url"]
    )

    application.status_note = (
        "External submission confirmation detected and recorded."
    )

    try:
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise

    return {
        "updated": True,
        "application_id": str(application.id),
        "status": application.status,
        "verification": verification,
    }
