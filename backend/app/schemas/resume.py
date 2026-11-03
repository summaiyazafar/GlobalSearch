import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ResumeCreate(ResumeBase):
    original_filename: str | None = None
    mime_type: str | None = None
    is_original: bool = False


class ResumeUpdate(BaseModel):
    title: str | None = None
    is_active: bool | None = None


class ResumeResponse(ResumeBase):
    id: uuid.UUID
    user_id: uuid.UUID

    original_filename: str | None
    storage_path: str | None
    mime_type: str | None

    version: int
    is_original: bool
    is_active: bool

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)