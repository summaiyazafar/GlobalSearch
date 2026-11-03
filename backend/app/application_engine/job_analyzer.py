from app.ai_engine.skill_extractor import extract_skills


def _to_text(value) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (list, tuple, set)):
        return " ".join(str(item) for item in value)

    if isinstance(value, dict):
        return " ".join(
            f"{key}: {item}"
            for key, item in value.items()
        )

    return str(value)


def analyze_job(job) -> dict:
    """
    Analyze a job record and return a structured description.

    The analysis is based only on information stored in the job record.
    """

    description = _to_text(getattr(job, "description", None))
    requirements = _to_text(getattr(job, "requirements", None))

    combined_text = f"{description}\n{requirements}"

    return {
        "job_id": str(job.id),
        "title": getattr(job, "title", None),
        "company": getattr(job, "company", None),
        "country": getattr(job, "country", None),
        "city": getattr(job, "city", None),
        "employment_type": getattr(job, "employment_type", None),
        "workplace_type": getattr(job, "workplace_type", None),
        "required_skills": extract_skills(combined_text),
        "description_available": bool(description.strip()),
        "requirements_available": bool(requirements.strip()),
        "job_url": getattr(job, "job_url", None),
    }