
import re
from typing import Any


def _value(obj: Any, field: str, default=None):
    """Safely read a field from an SQLAlchemy model or dictionary."""
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


def _first_value(obj: Any, fields: list[str], default=None):
    """Read the first available field from a list of possible names."""
    for field in fields:
        value = _value(obj, field)

        if value is not None:
            return value

    return default


def _normalise(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def _normalise_list(value: Any) -> list[str]:
    if not value:
        return []

    if isinstance(value, str):
        value = [value]

    if not isinstance(value, (list, tuple, set)):
        return []

    return [
        _normalise(item)
        for item in value
        if _normalise(item)
    ]


def _matches_preference(job_value: str, preferences: list[str]) -> bool:
    if not job_value or not preferences:
        return True

    return any(
        preference in job_value or job_value in preference
        for preference in preferences
    )


def _salary_number(value: Any):
    """
    Extract a numeric salary value.
    This does not convert currencies or salary periods.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    numbers = re.findall(
        r"\d+(?:,\d{3})*(?:\.\d+)?",
        str(value),
    )

    if not numbers:
        return None

    try:
        return float(numbers[0].replace(",", ""))
    except ValueError:
        return None


def evaluate_job_eligibility(
    job,
    preference=None,
    education_records=None,
    experience_records=None,
):
    """
    Evaluate job compatibility using known candidate preferences.

    Possible statuses:
        eligible
        review_required
        not_eligible

    This is a screening tool, not a legal or hiring decision.
    Missing information is never treated as confirmed eligibility.
    """

    education_records = education_records or []
    experience_records = experience_records or []

    reasons = []
    warnings = []

    status = "eligible"

    # --------------------------------------------------
    # 1. Read job information
    # --------------------------------------------------

    country = _normalise(_value(job, "country"))
    city = _normalise(_value(job, "city"))
    workplace = _normalise(_value(job, "workplace_type"))
    employment = _normalise(_value(job, "employment_type"))

    job_salary = _value(job, "salary")
    job_currency = _normalise(
        _first_value(job, ["salary_currency", "currency"])
    )

    # --------------------------------------------------
    # 2. Read candidate preferences
    # --------------------------------------------------

    remote_only = bool(
        _value(preference, "remote_only", False)
    )

    preferred_countries = _normalise_list(
        _first_value(
            preference,
            ["preferred_countries", "countries"],
            [],
        )
    )

    preferred_cities = _normalise_list(
        _first_value(
            preference,
            ["preferred_cities", "cities"],
            [],
        )
    )

    preferred_workplaces = _normalise_list(
        _first_value(
            preference,
            ["preferred_workplace_types", "workplace_types"],
            [],
        )
    )

    preferred_employment = _normalise_list(
        _first_value(
            preference,
            ["preferred_employment_types", "employment_types"],
            [],
        )
    )

    relocation_willing = bool(
        _value(preference, "relocation_willing", False)
    )

    visa_sponsorship_required = bool(
        _value(preference, "visa_sponsorship_required", False)
    )

    # --------------------------------------------------
    # 3. Remote and workplace compatibility
    # --------------------------------------------------

    onsite_types = {
        "onsite",
        "on-site",
        "on site",
        "office",
        "office-based",
    }

    if remote_only and workplace in onsite_types:
        status = "not_eligible"
        reasons.append(
            "The job is onsite, but the candidate requires remote work."
        )

    elif remote_only and not workplace:
        warnings.append(
            "The job workplace type is not specified."
        )

    # --------------------------------------------------
    # 4. Country and city preferences
    # --------------------------------------------------

    if preferred_countries:
        if country:
            if not _matches_preference(
                country,
                preferred_countries,
            ):
                if relocation_willing:
                    warnings.append(
                        "The job country differs from preferred countries. "
                        "Candidate has indicated willingness to relocate."
                    )
                else:
                    warnings.append(
                        "The job country is outside preferred countries. "
                        "Check relocation and work eligibility."
                    )
        else:
            warnings.append(
                "Job country is missing and cannot be checked."
            )

    if preferred_cities:
        if city:
            if not _matches_preference(
                city,
                preferred_cities,
            ):
                warnings.append(
                    "The job city differs from preferred cities."
                )
        else:
            warnings.append(
                "Job city is missing."
            )

    # --------------------------------------------------
    # 5. Employment type preference
    # --------------------------------------------------

    if preferred_employment:
        if employment:
            if not _matches_preference(
                employment,
                preferred_employment,
            ):
                warnings.append(
                    "Employment type differs from candidate preferences."
                )
        else:
            warnings.append(
                "Employment type is not specified."
            )

    # --------------------------------------------------
    # 6. Workplace type preference
    # --------------------------------------------------

    if preferred_workplaces:
        if workplace:
            if not _matches_preference(
                workplace,
                preferred_workplaces,
            ):
                warnings.append(
                    "Workplace type differs from candidate preferences."
                )
        else:
            warnings.append(
                "Workplace type is not specified."
            )

    # --------------------------------------------------
    # 7. Salary preference
    # --------------------------------------------------

    minimum_salary = _value(preference, "min_salary")
    preferred_currency = _normalise(
        _value(preference, "salary_currency")
    )

    parsed_job_salary = _salary_number(job_salary)

    if minimum_salary is not None:
        if parsed_job_salary is None:
            warnings.append(
                "Salary is unavailable or cannot be interpreted."
            )

        elif not job_currency or not preferred_currency:
            warnings.append(
                "Salary currency is missing. Salary comparison needs review."
            )

        elif job_currency != preferred_currency:
            warnings.append(
                "Salary currencies differ. Currency conversion is required."
            )

        elif parsed_job_salary < float(minimum_salary):
            warnings.append(
                "Advertised salary may be below the candidate's minimum."
            )

    # --------------------------------------------------
    # 8. Visa sponsorship and work authorization
    # --------------------------------------------------

    sponsorship_available = _first_value(
        job,
        ["visa_sponsorship_available", "sponsorship_available"],
    )

    if visa_sponsorship_required:
        if sponsorship_available is True:
            reasons.append(
                "Job listing indicates visa sponsorship is available."
            )

        elif sponsorship_available is False:
            status = "not_eligible"
            reasons.append(
                "Job listing explicitly states that visa sponsorship "
                "is unavailable."
            )

        else:
            warnings.append(
                "Visa sponsorship is not verified. "
                "Check the employer's official job description."
            )

    work_authorization = _first_value(
        job,
        ["work_authorization_required", "work_authorization"],
    )

    if work_authorization is None:
        warnings.append(
            "Work authorization requirements have not been verified."
        )

    # --------------------------------------------------
    # 9. Education and experience information
    # --------------------------------------------------

    if not education_records:
        warnings.append(
            "Candidate education records are unavailable."
        )

    if not experience_records:
        warnings.append(
            "Candidate experience records are unavailable."
        )

    # Structured minimum education and experience requirements
    # are not currently verified by this screening function.
    required_education = _first_value(
        job,
        ["education_requirement", "required_education"],
    )

    required_experience = _first_value(
        job,
        ["experience_requirement", "required_experience"],
    )

    if required_education:
        warnings.append(
            "Education requirement needs comparison with candidate records."
        )

    if required_experience:
        warnings.append(
            "Experience requirement needs comparison with candidate records."
        )

    # --------------------------------------------------
    # 10. Final status
    # --------------------------------------------------

    if status != "not_eligible" and warnings:
        status = "review_required"

    return {
        "status": status,
        "reasons": reasons,
        "warnings": warnings,
        "checks": {
            "country_checked": bool(country),
            "city_checked": bool(city),
            "workplace_checked": bool(workplace),
            "employment_checked": bool(employment),
            "salary_checked": (
                parsed_job_salary is not None
                and bool(job_currency)
                and bool(preferred_currency)
                and job_currency == preferred_currency
            ),
            "visa_sponsorship_verified": (
                sponsorship_available is True
                or sponsorship_available is False
            ),
            "work_authorization_verified": (
                work_authorization is not None
            ),
            "education_records_found": len(education_records),
            "experience_records_found": len(experience_records),
        },
        "requires_human_review": status == "review_required",
        "is_final_hiring_decision": False,
    }
