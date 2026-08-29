"""
Database configuration and session management for SQLite using SQLModel.
"""

from pathlib import Path
from typing import Generator
from sqlmodel import Session, SQLModel, create_engine

# Database file path resolution (saved in Server directory as clovo.db)
BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "clovo.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Engine creation with SQLite thread safety setting
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """
    Create SQLite database and all registered SQLModel tables, then seed default data if needed.
    """
    import models  # noqa: F401

    SQLModel.metadata.create_all(engine)

    # Seed initial patient (Sarah) with 21-day surgery countdown and today's preparations
    with Session(engine) as session:
        from services.patient_service import patient_service

        patient_service.get_or_create_default_patient(session)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and safely closes it upon completion.
    """
    with Session(engine) as session:
        yield session
