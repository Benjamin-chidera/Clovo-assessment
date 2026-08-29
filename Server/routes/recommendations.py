from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database import get_session
from models import Recommendation
from services import recommendation_service

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.patch("/{recommendation_id}/toggle", response_model=Recommendation)
async def toggle_recommendation(
    recommendation_id: str,
    session: Session = Depends(get_session),
) -> Recommendation:
    """Toggle recommendation/preparation task between completed and pending."""
    rec = recommendation_service.toggle_status(session, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation task not found")
    return rec
