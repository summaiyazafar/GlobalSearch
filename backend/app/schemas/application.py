import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ApplicationStatus = Literal[
    "draft",
    "pending_approval",
    "ready_for_review",
    "submitted",
    "submission_failed",
    "rejected",
    "withdrawn",
]


class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    resume_id: uuid.UUID | None = None
    cover_letter: str | None = None


class ApplicationUpdate(BaseModel):
    resume_id: uuid.UUID | None = None
    cover_letter: str | None = None
    status_note: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    status_note: str | None = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID | None

    status: str
    cover_letter: str | None
    submission_reference: str | None
    submitted_at: datetime | None
    status_note: str | None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)