
from collections import Counter

from app.ai_engine.skill_extractor import extract_skills


def analyze_skill_gaps(
    candidate_text: str,
    job_descriptions: list[str],
) -> dict:
    """
    Compare candidate skills with skills found in supplied job descriptions.
    Reports recurring missing skills across the supplied jobs.
    """

    candidate_skills = set(
        extract_skills(candidate_text or "")
    )

    required_skill_counts = Counter()
    matched_skill_counts = Counter()
    missing_skill_counts = Counter()

    processed_jobs = 0

    for description in job_descriptions:
        if not description:
            continue

        processed_jobs += 1

        job_skills = set(extract_skills(description))

        for skill in job_skills:
            required_skill_counts[skill] += 1

            if skill in candidate_skills:
                matched_skill_counts[skill] += 1
            else:
                missing_skill_counts[skill] += 1

    recurring_gaps = [
        {
            "skill": skill,
            "jobs_requiring_skill": count,
        }
        for skill, count in missing_skill_counts.most_common()
    ]

    return {
        "jobs_analyzed": processed_jobs,
        "candidate_skills": sorted(candidate_skills),
        "candidate_skill_count": len(candidate_skills),
        "required_skills": [
            {
                "skill": skill,
                "jobs_requiring_skill": count,
            }
            for skill, count in required_skill_counts.most_common()
        ],
        "recurring_missing_skills": recurring_gaps,
        "matched_skills": [
            {
                "skill": skill,
                "jobs_matching_skill": count,
            }
            for skill, count in matched_skill_counts.most_common()
        ],
        "method": "keyword_skill_extraction",
        "note": (
            "Skill gaps are based only on skills detected in the supplied "
            "job descriptions and candidate text. They are not a measure "
            "of actual professional ability."
        ),
    }
