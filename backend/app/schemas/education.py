import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EducationBase(BaseModel):
    institution: str = Field(min_length=1, max_length=200)
    degree: str | None = Field(default=None, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=150)

    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False

    grade: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date")

        if self.is_current and self.end_date:
            raise ValueError("Current education cannot have an end date")

        return self


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    grade: str | None = None


class EducationResponse(EducationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)