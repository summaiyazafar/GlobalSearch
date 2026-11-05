
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Page

from app.browser_automation.form_detector import (
    detect_application_forms,
    detect_submit_buttons,
    detect_human_verification,
)
from app.browser_automation.form_filler import (
    fill_application_fields,
)
from app.browser_automation.file_uploader import upload_resume


@dataclass
class ATSPreparationResult:
    platform: str
    page_url: str
    page_title: str
    form_found: bool
    fields_detected: int
    filled_fields: list
    missing_fields: list
    manual_review_fields: list
    verification_required: bool
    ready_for_human_review: bool
    submission_performed: bool = False


class BaseATSAdapter:

    platform = "generic"
    form_selectors = ["form"]

    def __init__(self, page: Page):
        self.page = page

    async def open_job(self, job_url: str):
        if not job_url.startswith(("https://", "http://")):
            raise ValueError("A valid HTTP or HTTPS job URL is required.")

        await self.page.goto(
            job_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await self.page.wait_for_timeout(1500)

        return {
            "platform": self.platform,
            "url": self.page.url,
            "title": await self.page.title(),
        }

    async def locate_application_form(self) -> Optional[str]:
        for selector in self.form_selectors:
            locator = self.page.locator(selector).first

            try:
                if await locator.count() > 0 and await locator.is_visible():
                    return selector
            except Exception:
                continue

        return None

    async def inspect(self) -> dict:
        form_selector = await self.locate_application_form()
        fields = await detect_application_forms(self.page)
        buttons = await detect_submit_buttons(self.page)
        verification = await detect_human_verification(self.page)

        return {
            "platform": self.platform,
            "url": self.page.url,
            "form_selector": form_selector,
            "form_found": form_selector is not None,
            "fields": fields,
            "buttons": buttons,
            "verification": verification,
        }

    async def prepare_application(
        self,
        answers: dict,
        resume_path: Optional[str] = None,
    ) -> ATSPreparationResult:

        inspection = await self.inspect()

        if not inspection["form_found"]:
            raise RuntimeError(
                f"No recognizable application form found on {self.platform}."
            )

        verification = inspection["verification"]

        if verification["requires_human"]:
            return ATSPreparationResult(
                platform=self.platform,
                page_url=self.page.url,
                page_title=await self.page.title(),
                form_found=True,
                fields_detected=len(inspection["fields"]),
                filled_fields=[],
                missing_fields=[],
                manual_review_fields=["Human verification required"],
                verification_required=True,
                ready_for_human_review=True,
            )

        fill_result = await fill_application_fields(
            self.page,
            answers,
        )

        if resume_path:
            try:
                await upload_resume(
                    self.page,
                    resume_path,
                )
                fill_result["filled"].append("resume_upload")
            except Exception as exc:
                fill_result["manual_review"].append(
                    f"resume_upload: {str(exc)}"
                )

        return ATSPreparationResult(
            platform=self.platform,
            page_url=self.page.url,
            page_title=await self.page.title(),
            form_found=True,
            fields_detected=len(inspection["fields"]),
            filled_fields=fill_result["filled"],
            missing_fields=fill_result["missing"],
            manual_review_fields=fill_result["manual_review"],
            verification_required=False,
            ready_for_human_review=True,
            submission_performed=False,
        )


class GreenhouseAdapter(BaseATSAdapter):

    platform = "greenhouse"

    form_selectors = [
        "#application_form",
        "form#application-form",
        "form",
    ]


class LeverAdapter(BaseATSAdapter):

    platform = "lever"

    form_selectors = [
        "form.application-form",
        ".application-form",
        "form",
    ]


class AshbyAdapter(BaseATSAdapter):

    platform = "ashby"

    form_selectors = [
        "form",
        "[data-testid*='application']",
        "[class*='application']",
    ]
