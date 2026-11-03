from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.resume import Resume
from app.models.user import User
from app.resume_engine.parser import (
    MAX_RESUME_SIZE,
    ResumeParsingError,
    extract_resume_text,
)
from app.security.auth import get_current_user


router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"],
)


BACKEND_DIR = Path(__file__).resolve().parents[3]
RESUME_STORAGE_DIR = BACKEND_DIR / "storage" / "resumes"

ALLOWED_CONTENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".txt": {"text/plain"},
}


def serialize_resume(resume: Resume) -> dict:
    return {
        "id": str(resume.id),
        "title": resume.title,
        "original_filename": resume.original_filename,
        "mime_type": resume.mime_type,
        "parsed_text": resume.parsed_text,
        "version": resume.version,
        "is_original": resume.is_original,
        "is_active": resume.is_active,
        "created_at": resume.created_at,
        "updated_at": resume.updated_at,
    }


def get_owned_resume(
    resume_id: UUID,
    user_id: UUID,
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

    return resume


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a resume, extract its text, and save it for the current user.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only PDF, DOCX, and TXT files are supported.",
        )

    file_bytes = await file.read(MAX_RESUME_SIZE + 1)
    await file.close()

    if len(file_bytes) > MAX_RESUME_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum resume file size is 10 MB.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # Parse before storing the original file.
    try:
        parsed_text = extract_resume_text(
            file.filename,
            file_bytes,
        )
    except ResumeParsingError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    # Generate a safe server-side filename.
    stored_filename = f"{uuid4().hex}{extension}"

    user_storage_dir = RESUME_STORAGE_DIR / str(current_user.id)
    user_storage_dir.mkdir(parents=True, exist_ok=True)

    storage_path = user_storage_dir / stored_filename

    # Do not trust a browser-supplied MIME type.
    mime_type = {
        ".pdf": "application/pdf",
        ".docx": (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        ".txt": "text/plain",
    }[extension]

    try:
        storage_path.write_bytes(file_bytes)

        resume = Resume(
            user_id=current_user.id,
            title=Path(file.filename).stem[:200],
            original_filename=Path(file.filename).name,
            storage_path=str(
                storage_path.relative_to(BACKEND_DIR)
            ),
            mime_type=mime_type,
            parsed_text=parsed_text,
            version=1,
            is_original=True,
            is_active=True,
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        return {
            "success": True,
            "message": "Resume uploaded and parsed successfully.",
            "resume": serialize_resume(resume),
        }

    except Exception:
        db.rollback()

        if storage_path.exists():
            storage_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Could not save the resume.",
        )


@router.get("/")
def list_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resumes = db.scalars(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(desc(Resume.created_at))
    ).all()

    return {
        "success": True,
        "count": len(resumes),
        "resumes": [
            serialize_resume(resume)
            for resume in resumes
        ],
    }


@router.get("/{resume_id}")
def get_resume_details(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = get_owned_resume(
        resume_id,
        current_user.id,
        db,
    )

    return {
        "success": True,
        "resume": serialize_resume(resume),
    }


@router.get("/{resume_id}/download")
def download_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = get_owned_resume(
        resume_id,
        current_user.id,
        db,
    )

    storage_root = RESUME_STORAGE_DIR.resolve()
    file_path = (BACKEND_DIR / resume.storage_path).resolve()

    # Prevent path traversal and access outside resume storage.
    if not file_path.is_relative_to(storage_root):
        raise HTTPException(
            status_code=403,
            detail="Invalid resume storage location.",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Resume file is missing from storage.",
        )

    return FileResponse(
        path=file_path,
        media_type=resume.mime_type,
        filename=resume.original_filename,
    )


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = get_owned_resume(
        resume_id,
        current_user.id,
        db,
    )

    storage_root = RESUME_STORAGE_DIR.resolve()
    file_path = (BACKEND_DIR / resume.storage_path).resolve()

    if not file_path.is_relative_to(storage_root):
        raise HTTPException(
            status_code=403,
            detail="Invalid resume storage location.",
        )

    db.delete(resume)
    db.commit()

    if file_path.is_file():
        file_path.unlink()

    return {
        "success": True,
        "message": "Resume deleted successfully.",
    }