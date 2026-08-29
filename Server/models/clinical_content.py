from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.recommendation import Recommendation


class ClinicalContent(SQLModel, table=True):
    """
    Evidence-based clinical content library: exercises, nutrition protocols, mindfulness.
    Serves as both the database table model and the API schema.
    """
    __tablename__ = "clinical_content"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(index=True, description="Content category: exercise, nutrition, mindfulness")
    title: str = Field(index=True, description="Human-readable title")
    description: str = Field(description="Step-by-step instructions or guidance")
    rationale: str = Field(description="Clinical reason and recovery benefit")
    target_stage: str = Field(index=True, description="Applicable stage: pre-op-21, pre-op-14, pre-op-all, post-op")
    image_url: Optional[str] = Field(default=None, description="Visual thumbnail/photography URL")
    icon_name: Optional[str] = Field(default=None, description="Vector icon symbol name (e.g. fitness, body, nutrition, moon)")

    # Relationship back to personalized recommendations
    recommendations: List["Recommendation"] = Relationship(back_populates="content")
