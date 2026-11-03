import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CertificationBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)

    issuing_organization: str | None = Field(default=None, max_length=200)
    credential_id: str | None = Field(default=None, max_length=200)
    credential_url: str | None = Field(default=None, max_length=500)

    issue_date: date | None = None
    expiry_date: date | None = None
    does_not_expire: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.issue_date and self.expiry_date:
            if self.expiry_date < self.issue_date:
                raise ValueError("Expiry date cannot be before issue date")

        if self.does_not_expire and self.expiry_date:
            raise ValueError("Non-expiring certification cannot have expiry date")

        return self


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: str | None = None
    issuing_organization: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    does_not_expire: bool | None = None


class CertificationResponse(CertificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)