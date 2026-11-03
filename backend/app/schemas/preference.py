import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PreferenceBase(BaseModel):
    job_titles: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)

    employment_types: list[str] = Field(default_factory=list)
    workplace_types: list[str] = Field(default_factory=list)

    remote_only: bool = False
    relocation_willing: bool = False
    visa_sponsorship_required: bool | None = None

    minimum_salary: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, max_length=10)

    minimum_match_score: int = Field(default=60, ge=0, le=100)

    auto_discovery_enabled: bool = True
    auto_apply_enabled: bool = False


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceUpdate(BaseModel):
    job_titles: list[str] | None = None
    countries: list[str] | None = None
    cities: list[str] | None = None
    employment_types: list[str] | None = None
    workplace_types: list[str] | None = None
    remote_only: bool | None = None
    relocation_willing: bool | None = None
    visa_sponsorship_required: bool | None = None
    minimum_salary: int | None = Field(default=None, ge=0)
    salary_currency: str | None = None
    minimum_match_score: int | None = Field(default=None, ge=0, le=100)
    auto_discovery_enabled: bool | None = None
    auto_apply_enabled: bool | None = None


class PreferenceResponse(PreferenceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)