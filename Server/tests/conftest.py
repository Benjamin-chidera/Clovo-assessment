import os
import pytest
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

# Set testing environment variable
os.environ["TESTING"] = "1"
os.environ["OPENAI_API_KEY"] = "mock-test-key"

from database import seed_clinical_content, seed_milestones
from services.patient_service import patient_service
from models.patient import Patient
from models.recommendation import Recommendation
from models.conversation import Conversation, Message
from models.safety_event import SafetyEvent


@pytest.fixture(name="db_session")
def db_session_fixture() -> Generator[Session, None, None]:
    """
    Creates an isolated, in-memory SQLite database session per test with StaticPool.
    Ensures zero state leakage between individual tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Seed clinical content and milestone catalogs
        seed_clinical_content(session)
        seed_milestones(session)

        # Seed default patient Sarah and her 4 personalized recommendations
        patient = patient_service.get_or_create_default_patient(session)

        # Seed active conversation
        conversation = Conversation(
            id="test-conv-1",
            patient_id=patient.id,
        )
        session.add(conversation)
        session.commit()

        yield session
