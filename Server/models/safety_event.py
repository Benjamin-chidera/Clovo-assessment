from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.conversation import Conversation, Message
    from models.patient import Patient


def generate_uuid() -> str:
    """Generate a standard UUID string for primary keys."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class SafetyEvent(SQLModel, table=True):
    """
    Safety triggers, symptom flags, and clinical escalation events detected during conversations.
    """
    __tablename__ = "safety_events"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    patient_id: Optional[int] = Field(default=None, foreign_key="patients.id", index=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    message_id: Optional[str] = Field(default=None, foreign_key="messages.id", index=True)
    risk_level: str = Field(description="Risk severity: 'low', 'medium', 'high', 'critical'")
    trigger: str = Field(description="Detected trigger words or clinical condition")
    action: str = Field(description="Recommended or taken action e.g. alert nurse, emergency contact")
    status: str = Field(default="open", description="Triage status: 'open', 'reviewed', 'resolved'")
    created_at: datetime = Field(default_factory=get_utc_now)

    # Relationships
    conversation: Optional["Conversation"] = Relationship(back_populates="safety_events")
    message: Optional["Message"] = Relationship(back_populates="safety_events")
