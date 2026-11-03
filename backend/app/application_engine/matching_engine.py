from app.ai_engine.skill_extractor import extract_skills


def calculate_skill_match(
    resume_text: str,
    job_text: str,
) -> dict:
    """
    Calculate a transparent skill-overlap score.

    Score = matched required skills / total identified job skills * 100.
    It is a skills-overlap score, not a hiring probability.
    """

    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_text))

    matched = sorted(resume_skills.intersection(job_skills))
    missing = sorted(job_skills.difference(resume_skills))

    if not job_skills:
        score = 0.0
    else:
        score = round(
            len(matched) / len(job_skills) * 100,
            2,
        )

    return {
        "score": score,
        "resume_skills": sorted(resume_skills),
        "required_skills": sorted(job_skills),
        "matched_skills": matched,
        "missing_skills": missing,
        "total_resume_skills": len(resume_skills),
        "total_required_skills": len(job_skills),
        "score_type": "technical_skill_overlap",
        "explanation": (
            "This score measures overlap between recognized skills "
            "in the resume and job description. It is not a hiring "
            "probability or a complete eligibility assessment."
        ),
    }