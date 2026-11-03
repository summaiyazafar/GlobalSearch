import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicationTaskCreate(BaseModel):
    application_id: uuid.UUID | None = None
    task_type: str = Field(min_length=1, max_length=100)
    requires_human_approval: bool = True
    input_data: dict | None = None


class ApplicationTaskUpdate(BaseModel):
    status: str | None = None
    result_data: dict | None = None
    error_message: str | None = None


class ApplicationTaskResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    application_id: uuid.UUID | None
    task_type: str
    status: str
    requires_human_approval: bool
    input_data: dict | None
    result_data: dict | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)