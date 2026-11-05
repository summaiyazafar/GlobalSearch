
from playwright.async_api import Page


async def fill_application_fields(
    page: Page,
    answers: dict,
) -> dict:

    results = {
        "filled": [],
        "missing": [],
        "manual_review": [],
    }

    fields = await page.locator(
        "input, textarea, select"
    ).evaluate_all(
        """elements => elements.map(element => ({
            name: element.name || "",
            id: element.id || "",
            type: element.type || "",
            tag: element.tagName.toLowerCase(),
            placeholder: element.placeholder || "",
            required: element.required || false,
            disabled: element.disabled || false
        }))"""
    )

    for field in fields:
        field_name = field["name"] or field["id"]

        if not field_name or field["disabled"]:
            continue

        answer = answers.get(field_name)

        if answer is None:
            results["missing"].append(field_name)
            continue

        field_type = field["type"].lower()

        # Never automatically answer legal declarations,
        # consent questions, CAPTCHA or OTP fields.
        restricted_words = (
            "consent",
            "declaration",
            "authorize",
            "authorization",
            "captcha",
            "otp",
            "verification",
            "signature",
        )

        if any(word in field_name.lower() for word in restricted_words):
            results["manual_review"].append(field_name)
            continue

        locator = (
            page.locator(f"#{field['id']}")
            if field["id"]
            else page.locator(
                f"[name='{field_name}']"
            ).first
        )

        try:
            if field_type in ("hidden", "submit", "button", "reset"):
                continue

            if field_type in ("checkbox", "radio"):
                results["manual_review"].append(field_name)
                continue

            if field["tag"] == "select":
                await locator.select_option(label=str(answer))

            else:
                await locator.fill(str(answer))

            results["filled"].append(field_name)

        except Exception:
            results["manual_review"].append(field_name)

    return results
