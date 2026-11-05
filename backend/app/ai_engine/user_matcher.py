
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_engine.matching_engine import calculate_skill_match
from app.ai_engine.eligibility_engine import evaluate_job_eligibility

from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.preference import Preference
from app.models.resume import Resume
from app.models.skill import Skill
from app.models.education import Education
from app.models.experience import Experience
from app.models.profile import Profile


def _record_text(record, fields):
    values = []

    for field in fields:
        value = getattr(record, field, None)

        if value:
            values.append(str(value))

    return " ".join(values)


def build_candidate_text(db: Session, user_id) -> dict:
    parts = []

    profile = db.scalar(
        select(Profile).where(Profile.user_id == user_id)
    )

    if profile:
        parts.append(
            _record_text(
                profile,
                ["professional_summary", "summary", "headline"],
            )
        )

    resumes = db.scalars(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.is_active.is_(True),
        )
    ).all()

    for resume in resumes:
        if resume.parsed_text:
            parts.append(resume.parsed_text)

    skills = db.scalars(
        select(Skill).where(Skill.user_id == user_id)
    ).all()

    for skill in skills:
        parts.append(
            _record_text(
                skill,
                ["name", "category", "proficiency"],
            )
        )

    education = db.scalars(
        select(Education).where(Education.user_id == user_id)
    ).all()

    for item in education:
        parts.append(
            _record_text(
                item,
                ["institution", "degree", "field_of_study", "grade"],
            )
        )

    experience = db.scalars(
        select(Experience).where(Experience.user_id == user_id)
    ).all()

    for item in experience:
        parts.append(
            _record_text(
                item,
                ["company", "job_title", "description"],
            )
        )

    return {
        "text": "\n".join(part for part in parts if part),
        "education": education,
        "experience": experience,
    }


def run_matching_for_user(
    db: Session,
    user_id,
) -> dict:
    """
    Match one user's candidate information against active jobs.
    Existing user/job match records are updated instead of duplicated.
    """

    candidate = build_candidate_text(db, user_id)

    preference = db.scalar(
        select(Preference).where(Preference.user_id == user_id)
    )

    jobs = db.scalars(
        select(Job).where(Job.is_active.is_(True))
    ).all()

    created = 0
    updated = 0
    results = []

    try:
        for job in jobs:
            job_text = " ".join(
                str(value or "")
                for value in [
                    job.title,
                    job.description,
                    job.requirements,
                    job.company,
                ]
            )

            skill_result = calculate_skill_match(
                candidate["text"],
                job_text,
            )

            eligibility = evaluate_job_eligibility(
                job=job,
                preference=preference,
                education_records=candidate["education"],
                experience_records=candidate["experience"],
            )

            explanation_parts = [
                f"Skill overlap: {skill_result['score']}%."
            ]

            if eligibility["reasons"]:
                explanation_parts.extend(eligibility["reasons"])

            if eligibility["warnings"]:
                explanation_parts.extend(eligibility["warnings"])

            existing = db.scalar(
                select(JobMatch).where(
                    JobMatch.user_id == user_id,
                    JobMatch.job_id == job.id,
                )
            )

            if existing:
                match_record = existing
                updated += 1
            else:
                match_record = JobMatch(
                    user_id=user_id,
                    job_id=job.id,
                )
                db.add(match_record)
                created += 1

            match_record.score = skill_result["score"]
            match_record.matched_skills = skill_result["matched_skills"]
            match_record.missing_skills = skill_result["missing_skills"]
            match_record.eligibility_status = eligibility["status"]
            match_record.explanation = " ".join(explanation_parts)

            results.append({
                "job_id": str(job.id),
                "title": job.title,
                "company": job.company,
                "score": skill_result["score"],
                "eligibility_status": eligibility["status"],
                "matched_skills": skill_result["matched_skills"],
                "missing_skills": skill_result["missing_skills"],
                "warnings": eligibility["warnings"],
            })

        db.commit()

    except Exception:
        db.rollback()
        raise

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "jobs_processed": len(jobs),
        "matches_created": created,
        "matches_updated": updated,
        "results": results,
        "scoring_method": "keyword_skill_overlap",
    }
