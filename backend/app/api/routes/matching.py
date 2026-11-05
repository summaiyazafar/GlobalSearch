
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.security.auth import get_current_user

from app.models.job import Job
from app.models.job_match import JobMatch

from app.processing_engine.user_matcher import (
    run_matching_for_user,
    build_candidate_text,
)

from app.ai_engine.ranking_engine import (
    rank_job_matches,
    explain_job_match,
)

from app.ai_engine.skill_gap_analyzer import (
    analyze_skill_gaps,
)


router = APIRouter(
    prefix="/matching",
    tags=["Job Matching"],
)


@router.post("/run")
def run_my_job_matching(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        result = run_matching_for_user(
            db=db,
            user_id=current_user.id,
        )

        ranked = rank_job_matches(result.get("results", []))

        return {
            "success": True,
            "user_id": str(current_user.id),
            "matching": {
                **result,
                "results": ranked,
            },
        }

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Job matching could not be completed.",
        ) from exc


@router.get("/ranked")
def get_ranked_jobs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    records = db.execute(
        select(JobMatch, Job)
        .join(Job, Job.id == JobMatch.job_id)
        .where(JobMatch.user_id == current_user.id)
        .where(Job.is_active.is_(True))
    ).all()

    matches = []

    for match, job in records:
        item = {
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "job_url": job.job_url,
            "country": job.country,
            "city": job.city,
            "score": match.score or 0,
            "eligibility_status": (
                match.eligibility_status or "review_required"
            ),
            "matched_skills": match.matched_skills or [],
            "missing_skills": match.missing_skills or [],
        }

        item["explanation"] = explain_job_match(item)
        matches.append(item)

    ranked = rank_job_matches(matches)

    return {
        "total": len(ranked),
        "ranked_jobs": ranked,
        "ranking_method": "eligibility_then_skill_match_score",
    }


@router.get("/skill-gaps")
def get_my_skill_gaps(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    candidate = build_candidate_text(
        db=db,
        user_id=current_user.id,
    )

    jobs = db.scalars(
        select(Job).where(Job.is_active.is_(True))
    ).all()

    descriptions = [
        " ".join(
            str(value or "")
            for value in [
                job.title,
                job.description,
                job.requirements,
            ]
        )
        for job in jobs
    ]

    return {
        "success": True,
        "skill_gap_analysis": analyze_skill_gaps(
            candidate_text=candidate["text"],
            job_descriptions=descriptions,
        ),
    }
