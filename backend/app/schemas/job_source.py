import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobSourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    source_type: str = Field(min_length=1, max_length=50)
    base_url: str | None = None
    description: str | None = None
    is_active: bool = True
    requires_authentication: bool = False


class JobSourceCreate(JobSourceBase):
    pass


class JobSourceUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = None
    base_url: str | None = None
    description: str | None = None
    is_active: bool | None = None
    requires_authentication: bool | None = None


class JobSourceResponse(JobSourceBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)