from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.patient import Patient


def get_utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Milestone(SQLModel, table=True):
    """
    Catalog of unlockable clinical, adherence, and preparation milestones.
    """
    __tablename__ = "milestones"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, description="Unique code e.g. first_step, streak_3, quad_master")
    title: str = Field(description="Display title e.g. 5-Day Streak, Quad Master")
    description: str = Field(description="Clinical or adherence description")
    category: str = Field(default="adherence", description="adherence, exercise, mindfulness, nutrition, pre_op")
    icon_name: str = Field(default="trophy", description="Ionicons icon name e.g. fitness, walk, barbell, flame, heart")
    color: str = Field(default="#4F46E5", description="Hex accent color")
    bg_gradient_start: str = Field(default="#E0E7FF", description="Gradient start hex")
    bg_gradient_end: str = Field(default="#C7D2FE", description="Gradient end hex")
    criteria_type: str = Field(description="streak_days, completed_tasks, specific_exercise, check_in_count")
    criteria_threshold: int = Field(default=1, description="Threshold required to unlock")
    created_at: datetime = Field(default_factory=get_utc_now)


class PatientMilestone(SQLModel, table=True):
    """
    Records milestones unlocked by a specific patient with audit timestamps.
    """
    __tablename__ = "patient_milestones"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patients.id", index=True)
    milestone_id: int = Field(foreign_key="milestones.id", index=True)
    unlocked_at: datetime = Field(default_factory=get_utc_now)


class MilestoneDTO(SQLModel):
    """
    Lightweight DTO for mobile and web UI presentation.
    """
    id: str
    code: str
    title: str
    description: Optional[str] = None
    icon_name: str
    color: str
    bg_gradient: List[str]
    unlocked_at: Optional[str] = None
