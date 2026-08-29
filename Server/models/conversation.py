from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.patient import Patient
    from models.safety_event import SafetyEvent


def generate_uuid() -> str:
    """Generate a standard UUID string for primary keys."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """
    Coaching conversation sessions between patient and AI coach Amy.
    """
    __tablename__ = "conversations"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    patient_id: int = Field(foreign_key="patients.id", index=True)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    # Relationships
    patient: Optional["Patient"] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")
    safety_events: List["SafetyEvent"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """
    Individual chat messages in a conversation.
    """
    __tablename__ = "messages"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: str = Field(description="Role: 'user', 'coach', 'assistant', 'system'")
    content: str
    created_at: datetime = Field(default_factory=get_utc_now)

    # Relationships
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")
    safety_events: List["SafetyEvent"] = Relationship(back_populates="message")
