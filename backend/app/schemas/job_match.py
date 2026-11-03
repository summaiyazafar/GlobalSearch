import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobMatchCreate(BaseModel):
    job_id: uuid.UUID
    match_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    eligibility_status: str = "not_assessed"
    explanation: str | None = None


class JobMatchResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    eligibility_status: str
    explanation: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)