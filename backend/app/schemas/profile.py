import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProfileBase(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)

    phone: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)

    address: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)

    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None

    professional_summary: str | None = None

    preferred_job_title: str | None = Field(default=None, max_length=200)
    preferred_locations: str | None = None
    remote_preference: str | None = Field(default=None, max_length=30)

    relocation_willing: bool = False


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    postal_code: str | None = None
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    professional_summary: str | None = None
    preferred_job_title: str | None = None
    preferred_locations: str | None = None
    remote_preference: str | None = None
    relocation_willing: bool | None = None


class ProfileResponse(ProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)