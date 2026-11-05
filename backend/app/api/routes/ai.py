from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai_engine.job_analyzer import analyze_job
from app.ai_engine.matching_engine import calculate_skill_match
from app.database.session import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.resume_engine.exporters.docx_exporter import (
    export_resume_to_docx,
)
from app.resume_engine.formatter import (
    build_cover_letter,
    build_tailored_resume_text,
)
from app.security.auth import get_current_user


router = APIRouter(
    prefix="/ai",
    tags=["AI Resume and Job Analysis"],
)


BACKEND_DIR = Path(__file__).resolve().parents[3]
RESUME_STORAGE_DIR = BACKEND_DIR / "storage" / "resumes"


def get_owned_resume(
    resume_id,
    user_id,
    db: Session,
) -> Resume:
    resume = db.scalar(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        )
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found.",
        )

    if not resume.parsed_text:
        raise HTTPException(
            status_code=422,
            detail="Resume has no extracted text.",
        )

    return resume


def get_active_job(job_id, db: Session) -> Job:
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.is_active.is_(True),
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found or inactive.",
        )

    return job


def get_job_text(job: Job) -> str:
    description = getattr(job, "description", None) or ""
    requirements = getattr(job, "requirements", None) or ""

    return f"{description}\n{requirements}"


@router.post("/resumes/{resume_id}/analyze/{job_id}")
def analyze_resume_for_job(
    resume_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a user's resume against a selected active job.
    """

    resume = get_owned_resume(
        resume_id,
        current_user.id,
        db,
    )

    job = get_active_job(job_id, db)

    job_analysis = analyze_job(job)

    match_result = calculate_skill_match(
        resume.parsed_text,
        get_job_text(job),
    )

    return {
        "success": True,
        "job_analysis": job_analysis,
        "resume_match": match_result,
        "notice": (
            "The score measures recognized technical skill overlap. "
            "It does not determine visa eligibility, work authorization, "
            "or guarantee selection."
        ),
    }


@router.post("/resumes/{resume_id}/tailor/{job_id}")
def tailor_resume_for_job(
    resume_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a DOCX resume copy for a selected job.

    Original resume remains unchanged.
    """

    resume = get_owned_resume(
        resume_id,
        current_user.id,
        db,
    )

    job = get_active_job(job_id, db)

    match_result = calculate_skill_match(
        resume.parsed_text,
        get_job_text(job),
    )

    tailored = build_tailored_resume_text(
        original_text=resume.parsed_text,
        job_title=job.title,
        company=job.company,
    )

    document_bytes = export_resume_to_docx(
        tailored["content"],
        document_title="Job-Specific Resume",
    )

    user_storage_dir = (
        RESUME_STORAGE_DIR / str(current_user.id)
    )
    user_storage_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_filename = f"{uuid4().hex}_tailored.docx"
    storage_path = user_storage_dir / stored_filename

    relative_path = str(
        storage_path.relative_to(BACKEND_DIR)
    )

    try:
        storage_path.write_bytes(document_bytes)

        latest_version = db.scalar(
            select(func.max(Resume.version)).where(
                Resume.user_id == current_user.id
            )
        ) or 0

        tailored_resume = Resume(
            user_id=current_user.id,
            title=tailored["title"][:200],
            original_filename=stored_filename,
            storage_path=relative_path,
            mime_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            parsed_text=tailored["content"],
            version=latest_version + 1,
            is_original=False,
            is_active=True,
        )

        db.add(tailored_resume)
        db.commit()
        db.refresh(tailored_resume)

        return {
            "success": True,
            "message": "Job-specific resume copy created.",
            "resume": {
                "id": str(tailored_resume.id),
                "title": tailored_resume.title,
                "version": tailored_resume.version,
                "is_original": tailored_resume.is_original,
                "download_endpoint": (
                    f"/api/v1/resumes/"
                    f"{tailored_resume.id}/download"
                ),
            },
            "match_analysis": match_result,
            "preservation_note": tailored["preservation_note"],
            "review_required": True,
        }

    except Exception:
        db.rollback()

        if storage_path.exists():
            storage_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Could not generate the tailored resume.",
        )


@router.post("/resumes/{resume_id}/cover-letter/{job_id}")
def generate_job_cover_letter(
    resume_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a draft cover letter based on the resume and job.
    """

    resume = get_owned_resume(
        resume_id,
        current_user.id,
        db,
    )

    job = get_active_job(job_id, db)

    match_result = calculate_skill_match(
        resume.parsed_text,
        get_job_text(job),
    )

    cover_letter = build_cover_letter(
        job_title=job.title,
        company=job.company,
        resume_text=resume.parsed_text,
        matched_skills=match_result["matched_skills"],
    )

    return {
        "success": True,
        "job_title": job.title,
        "company": job.company,
        "cover_letter": cover_letter,
        "matched_skills": match_result["matched_skills"],
        "review_required": True,
        "notice": (
            "This is a draft. Review the content and replace "
            "[Your Name] before using it."
        ),
    }