from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session

from database import get_session
from models import Recommendation
from services import recommendation_service

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.patch("/{recommendation_id}/toggle", response_model=Recommendation)
def toggle_recommendation(
    recommendation_id: Annotated[int, Path(ge=1, description="Unique recommendation ID")],
    session: SessionDep,
) -> Recommendation:
    """Toggle recommendation/preparation task between completed and active."""
    rec = recommendation_service.toggle_status(session, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation task not found")
    return rec
