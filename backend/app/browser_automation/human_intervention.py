
from playwright.async_api import Page


async def inspect_page_for_human_review(page: Page) -> dict:
    title = await page.title()
    url = page.url

    verification = await page.locator(
        "iframe[src*='captcha'], "
        "[class*='captcha'], "
        "[id*='captcha'], "
        "input[autocomplete='one-time-code']"
    ).count()

    return {
        "page_title": title,
        "current_url": url,
        "human_review_required": verification > 0,
        "message": (
            "Manual verification is required."
            if verification > 0
            else "Review the application before continuing."
        ),
        "automatic_submission_allowed": False,
    }


async def wait_for_manual_review(page: Page):
    """
    Keep the browser open while a human reviews the page.
    This does not bypass CAPTCHA, OTP or website restrictions.
    """
    await page.pause()
