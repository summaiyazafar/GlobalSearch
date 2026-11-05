import re
from html import unescape
from typing import Any


def clean_text(value: Any) -> str | None:
    if value is None:
        return None

    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text or None


def normalize_job(raw_job: dict, source_name: str = "") -> dict:
    """
    Convert a source-specific job dictionary into GlobalSearch's
    common job data format.
    """

    title = clean_text(raw_job.get("title"))
    external_id = clean_text(raw_job.get("external_id"))
    job_url = clean_text(raw_job.get("job_url"))

    if not title:
        raise ValueError("Job title is missing.")

    if not external_id:
        raise ValueError("External job ID is missing.")

    if not job_url:
        raise ValueError("Job URL is missing.")

    company = (
        clean_text(raw_job.get("company"))
        or clean_text(source_name)
        or "Unknown Company"
    )

    description = clean_text(raw_job.get("description")) or ""
    requirements = clean_text(raw_job.get("requirements")) or ""

    country = clean_text(raw_job.get("country"))
    city = clean_text(raw_job.get("city"))
    location = clean_text(raw_job.get("location"))

    if not location:
        location = ", ".join(
            part for part in (city, country) if part
        ) or None

    return {
        "external_id": external_id,
        "title": title,
        "company": company,
        "description": description,
        "requirements": requirements,
        "job_url": job_url,
        "country": country,
        "city": city,
        "location": location,
        "employment_type": clean_text(
            raw_job.get("employment_type")
        ),
        "workplace_type": clean_text(   
            raw_job.get("workplace_type")
        ),
        "salary": clean_text(raw_job.get("salary")),
        "is_active": True,
    }
