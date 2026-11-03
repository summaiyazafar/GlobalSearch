import uuid

from sqlalchemy import (
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database.base import Base, TimestampMixin


class JobMatch(Base, TimestampMixin):
    __tablename__ = "job_matches"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_job_match_user_job",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)

    eligibility_status: Mapped[str] = mapped_column(
        String(50),
        default="not_assessed",
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(Text)