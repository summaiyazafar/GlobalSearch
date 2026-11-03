import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str | None = Field(default=None, max_length=100)
    proficiency: str | None = Field(default=None, max_length=50)
    years_experience: int = Field(default=0, ge=0, le=60)


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    category: str | None = None
    proficiency: str | None = None
    years_experience: int | None = Field(default=None, ge=0, le=60)


class SkillResponse(SkillBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)