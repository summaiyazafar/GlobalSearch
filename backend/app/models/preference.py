import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database.base import Base, TimestampMixin


class Preference(Base, TimestampMixin):
    __tablename__ = "preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    job_titles: Mapped[list] = mapped_column(JSON, default=list)
    countries: Mapped[list] = mapped_column(JSON, default=list)
    cities: Mapped[list] = mapped_column(JSON, default=list)

    employment_types: Mapped[list] = mapped_column(JSON, default=list)
    workplace_types: Mapped[list] = mapped_column(JSON, default=list)

    remote_only: Mapped[bool] = mapped_column(default=False, nullable=False)
    relocation_willing: Mapped[bool] = mapped_column(default=False, nullable=False)
    visa_sponsorship_required: Mapped[bool | None] = mapped_column(nullable=True)

    minimum_salary: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(10))

    minimum_match_score: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )

    auto_discovery_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    auto_apply_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )