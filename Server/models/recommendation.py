from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.patient import Patient


def generate_uuid() -> str:
    """Generate a standard UUID string for primary keys."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Recommendation(SQLModel, table=True):
    """
    AI or coach generated recovery recommendations tailored to patient pathway.
    """
    __tablename__ = "recommendations"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    patient_id: str = Field(foreign_key="patients.id", index=True)
    type: str = Field(description="Activity type e.g., walking, mindfulness, nutrition")
    title: str
    instruction: Optional[str] = Field(default=None)
    rationale: Optional[str] = Field(default=None)
    content_id: Optional[str] = Field(default=None)
    version: int = Field(default=1)
    status: str = Field(default="pending", description="Status e.g. pending, completed, skipped")
    created_at: datetime = Field(default_factory=get_utc_now)

    # Relationships
    patient: Optional["Patient"] = Relationship(back_populates="recommendations")


class PreparationItem(SQLModel):
    """
    Preparation item representation for UI checklist display.
    """
    id: str
    title: str
    is_completed: bool
    type: str
    instruction: Optional[str] = None
    rationale: Optional[str] = None


class TaskItemData(SQLModel):
    """
    Formatted daily task data model returned by task API.
    """
    id: str
    title: str
    category: str
    duration: str
    is_completed: bool
    category_label: str
    instruction: Optional[str] = None
    rationale: Optional[str] = None


class RecommendationCreate(SQLModel):
    id: Optional[str] = None
    patient_id: str
    type: str
    title: str
    instruction: Optional[str] = None
    rationale: Optional[str] = None
    content_id: Optional[str] = None
    version: int = 1
    status: str = "pending"


class RecommendationUpdate(SQLModel):
    status: Optional[str] = None
    instruction: Optional[str] = None
    rationale: Optional[str] = None
