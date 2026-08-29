from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel
from models.recommendation import PreparationItem

if TYPE_CHECKING:
    from models.recommendation import Recommendation
    from models.conversation import Conversation


def generate_uuid() -> str:
    """Generate a standard UUID string for primary keys."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Patient(SQLModel, table=True):
    """
    Patient profile table holding clinical pathway, procedure details, preferences, and app stats.
    """
    __tablename__ = "patients"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    name: str = Field(index=True)
    email: Optional[str] = Field(default="sarah@clovo.app")
    avatar_uri: Optional[str] = Field(
        default="https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80"
    )
    plan: Optional[str] = Field(default="Pre-Op Preparation")
    streak_count: int = Field(default=5)
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
    User profile payload returned for user route.
    """
    id: str
    name: str
    email: Optional[str] = None
    avatar_uri: Optional[str] = None
    plan: Optional[str] = None
    streak_count: int = 5
    greeting: str
    surgery_title: str
    days_away: int
    procedure_name: Optional[str] = None
    procedure_date: Optional[datetime] = None


class PatientHomeData(SQLModel):
    """
    Aggregated dashboard view for the home page.
    """
    greeting: str
    patient_name: str
    surgery_title: str
    days_away: int
    procedure_name: Optional[str] = None
    procedure_date: Optional[datetime] = None
    preparations: List[PreparationItem]


class PatientCreate(SQLModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = "sarah@clovo.app"
    avatar_uri: Optional[str] = None
    plan: Optional[str] = "Pre-Op Preparation"
    streak_count: int = 5
    age: Optional[int] = None
    pathway: Optional[str] = None
    procedure: Optional[str] = None
    procedure_date: Optional[datetime] = None
    preferences: Optional[str] = None


class PatientUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_uri: Optional[str] = None
    plan: Optional[str] = None
    streak_count: Optional[int] = None
    age: Optional[int] = None
    pathway: Optional[str] = None
    procedure: Optional[str] = None
    procedure_date: Optional[datetime] = None
    preferences: Optional[str] = None
