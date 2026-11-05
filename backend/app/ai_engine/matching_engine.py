
from app.ai_engine.skill_extractor import extract_skills


def calculate_skill_match(resume_text: str, job_text: str) -> dict:
    """
    Calculate transparent keyword-based skill overlap.

    The score is not a hiring probability or an AI prediction.
    """

    candidate_skills = set(extract_skills(resume_text or ""))
    required_skills = set(extract_skills(job_text or ""))

    matched_skills = sorted(candidate_skills & required_skills)
    missing_skills = sorted(required_skills - candidate_skills)

    if not required_skills:
        score = 0.0
    else:
        score = round(
            len(matched_skills) / len(required_skills) * 100,
            2,
        )

    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "candidate_skill_count": len(candidate_skills),
        "required_skill_count": len(required_skills),
        "scoring_method": "keyword_skill_overlap",
        "is_hiring_probability": False,
    }
