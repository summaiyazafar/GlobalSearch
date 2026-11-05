
from typing import Any

from app.ai_engine.skill_extractor import extract_skills


def get_value(record: Any, *names: str) -> str:
    for name in names:
        value = (
            record.get(name)
            if isinstance(record, dict)
            else getattr(record, name, None)
        )

        if value is not None and str(value).strip():
            return str(value).strip()

    return ""


def build_skill_evidence(
    skills: list,
    education: list,
    experience: list,
    projects: list,
    certifications: list,
) -> dict:
    """
    Build evidence showing where a candidate's skills come from.

    Evidence is extracted from user-provided profile records.
    It does not verify the truth of those claims.
    """

    evidence = {}

    collections = [
        ("profile_skill", skills),
        ("education", education),
        ("experience", experience),
        ("project", projects),
        ("certification", certifications),
    ]

    for source_type, records in collections:
        for record in records:
            if source_type == "profile_skill":
                content = " ".join([
                    get_value(record, "name", "skill_name"),
                    get_value(record, "category"),
                    get_value(record, "proficiency", "level"),
                ])
            elif source_type == "education":
                content = " ".join([
                    get_value(record, "degree"),
                    get_value(record, "field_of_study", "field"),
                    get_value(record, "institution", "school"),
                ])
            elif source_type == "experience":
                content = " ".join([
                    get_value(record, "job_title", "title", "position"),
                    get_value(record, "company"),
                    get_value(record, "description", "responsibilities"),
                ])
            elif source_type == "project":
                content = " ".join([
                    get_value(record, "name", "title"),
                    get_value(record, "description"),
                    get_value(record, "technologies", "tech_stack"),
                ])
            else:
                content = " ".join([
                    get_value(record, "name", "title"),
                    get_value(record, "provider", "issuer"),
                    get_value(record, "description"),
                ])

            detected = extract_skills(content)

            for skill in detected:
                evidence.setdefault(skill, [])

                item = {
                    "source": source_type,
                    "title": (
                        get_value(record, "name", "title", "job_title")
                        or source_type.replace("_", " ").title()
                    ),
                }

                if item not in evidence[skill]:
                    evidence[skill].append(item)

    return evidence


def explain_skill_evidence(
    matched_skills: list,
    evidence: dict,
) -> list:
    explanations = []

    for skill in matched_skills:
        explanations.append({
            "skill": skill,
            "evidence": evidence.get(skill, []),
            "evidence_found": bool(evidence.get(skill)),
        })

    return explanations
