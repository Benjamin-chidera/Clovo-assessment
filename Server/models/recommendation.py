from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.patient import Patient
    from models.clinical_content import ClinicalContent


class Recommendation(SQLModel, table=True):
    """
    Patient-specific prescription linking a patient to clinical content with custom duration, repetitions, and schedule.
    Serves as the database table model and primary entity.
    """
    __tablename__ = "recommendations"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Links to Patient (Who)
    patient_id: int = Field(foreign_key="patients.id", index=True)

    # Links to Clinical Content (The "What")
    content_id: int = Field(foreign_key="clinical_content.id", index=True)

    # Personalization (The "How Much")
    duration_minutes: int = Field(default=10, description="Prescribed duration in minutes")
    repetitions: Optional[int] = Field(default=None, description="Prescribed repetitions if applicable")

    # Scheduling (The "When")
    scheduled_date: date = Field(default_factory=date.today, index=True)

    # State & Lifecycle
    status: str = Field(default="active", index=True, description="active, completed, missed, skipped")
    completed_at: Optional[datetime] = Field(default=None, description="Exact timestamp when task was completed")

    # Optional specific notes for this patient
    notes: Optional[str] = Field(default=None, description="Custom clinical or coach notes")

    # SQLModel Relationships
    patient: Optional["Patient"] = Relationship(back_populates="recommendations")
    content: Optional["ClinicalContent"] = Relationship(back_populates="recommendations")



class PreparationItem(SQLModel):
    """
    Composite UI presentation DTO for home checklist display with joined content imagery.
    """
    id: int
    title: str
    is_completed: bool
    type: str
    instruction: Optional[str] = None
    rationale: Optional[str] = None
    image_url: Optional[str] = None
    icon_name: Optional[str] = None
    duration_minutes: int = 10
    repetitions: Optional[int] = None
    notes: Optional[str] = None


class TaskItemData(SQLModel):
    """
    Composite UI presentation DTO returned by /api/tasks with formatted labels and media.
    """
    id: int
    title: str
    category: str
    duration: str
    is_completed: bool
    category_label: str
    instruction: Optional[str] = None
    rationale: Optional[str] = None
    image_url: Optional[str] = None
    icon_name: Optional[str] = None
    repetitions: Optional[int] = None
    notes: Optional[str] = None


class RecommendationRead(SQLModel):
    """
    Composite read DTO joining Recommendation with ClinicalContent fields.
    """
    id: int
    patient_id: int
    content_id: int
    title: str
    type: str
    description: str
    rationale: str
    image_url: Optional[str] = None
    icon_name: Optional[str] = None
    duration_minutes: int
    repetitions: Optional[int] = None
    scheduled_date: date
    status: str
    notes: Optional[str] = None
