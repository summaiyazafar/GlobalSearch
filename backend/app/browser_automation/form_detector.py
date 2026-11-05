
from playwright.async_api import Page


async def detect_application_forms(page: Page) -> list[dict]:
    fields = await page.locator(
        "input, textarea, select"
    ).evaluate_all(
        """elements => elements.map((element, index) => {
            const id = element.id;
            const label = id
                ? document.querySelector(`label[for="${CSS.escape(id)}"]`)
                : null;

            const parentLabel = element.closest("label");

            return {
                index: index,
                tag: element.tagName.toLowerCase(),
                type: element.type || "",
                name: element.name || "",
                id: id || "",
                label: label?.innerText?.trim()
                    || parentLabel?.innerText?.trim()
                    || "",
                placeholder: element.placeholder || "",
                required: element.required || false,
                disabled: element.disabled || false,
                options: element.tagName === "SELECT"
                    ? Array.from(element.options).map(option => ({
                        text: option.text,
                        value: option.value
                    }))
                    : []
            };
        })"""
    )

    return fields


async def detect_submit_buttons(page: Page) -> list[dict]:
    return await page.locator(
        "button, input[type='submit']"
    ).evaluate_all(
        """elements => elements.map((element, index) => ({
            index: index,
            text: (element.innerText || element.value || "").trim(),
            type: element.type || "",
            disabled: element.disabled || false
        }))"""
    )


async def detect_human_verification(page: Page) -> dict:
    captcha_count = await page.locator(
        "iframe[src*='captcha'], "
        "[class*='captcha'], "
        "[id*='captcha']"
    ).count()

    otp_fields = await page.locator(
        "input[autocomplete='one-time-code'], "
        "input[name*='otp' i], "
        "input[name*='verification' i]"
    ).count()

    return {
        "captcha_detected": captcha_count > 0,
        "otp_field_detected": otp_fields > 0,
        "requires_human": captcha_count > 0 or otp_fields > 0,
    }
