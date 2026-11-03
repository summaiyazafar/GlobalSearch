from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base


BACKEND_DIR = Path(__file__).resolve().parents[2]

DEFAULT_DATABASE_URL = (
    f"sqlite:///{(BACKEND_DIR / 'globalsearch.db').as_posix()}"
)


def get_database_url() -> str:
    database_url = settings.DATABASE_URL.strip()

    if not database_url:
        return DEFAULT_DATABASE_URL

    if database_url.startswith("postgres://"):
        return database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    if database_url.startswith("postgresql://"):
        return database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return database_url


DATABASE_URL = get_database_url()

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False


engine: Engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=settings.DEBUG and DATABASE_URL.startswith("sqlite"),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def initialize_database() -> None:
    """
    Initialize database tables for local development.

    Production schema changes should be managed through Alembic migrations.
    """
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)