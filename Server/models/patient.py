from datetime import datetime, timezone, date
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from models.recommendation import PreparationItem
from models.milestone import MilestoneDTO

if TYPE_CHECKING:
    from models.recommendation import Recommendation
    from models.conversation import Conversation


def get_utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Patient(SQLModel, table=True):
    """
    Patient profile table holding clinical pathway, procedure details, preferences, and app stats.
    Serves as the database table model and primary entity.
    """
    __tablename__ = "patients"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: Optional[str] = Field(default="sarah@clovo.app")
    avatar_uri: Optional[str] = Field(
        default="https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80"
    )
    plan: Optional[str] = Field(default="Pre-Op Preparation")
    streak_count: int = Field(default=0)
    last_active_date: Optional[date] = Field(default=None, description="Last date patient completed a task or checked in")
    total_completed_tasks: int = Field(default=0, description="Total lifetime completed tasks")
    age: Optional[int] = Field(default=None)
    pathway: Optional[str] = Field(default=None)
    procedure: Optional[str] = Field(default=None)
    procedure_date: Optional[datetime] = Field(default=None)
    preferences: Optional[str] = Field(default=None, description="Serialized preferences or clinical notes")
    created_at: datetime = Field(default_factory=get_utc_now)

    # Relationships
    recommendations: List["Recommendation"] = Relationship(back_populates="patient")
    conversations: List["Conversation"] = Relationship(back_populates="patient")


class UserProfileData(SQLModel):
    """
    Composite DTO payload returned for /api/user with computed countdown, streak, and milestones.
    """
    id: int
    name: str
    email: Optional[str] = None
    avatar_uri: Optional[str] = None
    plan: Optional[str] = None
    streak_count: int = 0
    greeting: str
    surgery_title: str
    days_away: int
    procedure_name: Optional[str] = None
    procedure_date: Optional[datetime] = None
    milestones: List[MilestoneDTO] = Field(default_factory=list)
    additional_milestones_count: int = 0
    total_completed_tasks: int = 0


class PatientHomeData(SQLModel):
    """
    Composite aggregated dashboard DTO for the mobile Home screen.
    """
    greeting: str
    patient_name: str
    surgery_title: str
    days_away: int
    procedure_name: Optional[str] = None
    procedure_date: Optional[datetime] = None
    streak_count: int = 0
    milestones: List[MilestoneDTO] = Field(default_factory=list)
    additional_milestones_count: int = 0
    total_completed_tasks: int = 0
    preparations: List[PreparationItem]


