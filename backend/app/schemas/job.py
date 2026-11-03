import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    company_name: str = Field(min_length=1, max_length=250)

    description: str | None = None
    requirements: str | None = None

    job_url: str = Field(min_length=1, max_length=1000)

    country: str | None = None
    city: str | None = None
    location: str | None = None

    employment_type: str | None = None
    workplace_type: str | None = None

    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_currency: str | None = None

    posted_at: datetime | None = None
    expires_at: datetime | None = None

    is_active: bool = True


class JobCreate(JobBase):
    source_id: uuid.UUID | None = None
    external_id: str | None = None


class JobUpdate(BaseModel):
    title: str | None = None
    company_name: str | None = None
    description: str | None = None
    requirements: str | None = None
    job_url: str | None = None
    country: str | None = None
    city: str | None = None
    location: str | None = None
    employment_type: str | None = None
    workplace_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class JobResponse(JobBase):
    id: uuid.UUID
    source_id: uuid.UUID | None
    external_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int