from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session

from database import get_session
from models import Recommendation
from services import recommendation_service

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

SessionDep = Annotated[Session, Depends(get_session)]


from typing import Dict, Any

@router.patch("/{recommendation_id}/toggle")
def toggle_recommendation(
    recommendation_id: Annotated[int, Path(ge=1, description="Unique recommendation ID")],
    session: SessionDep,
) -> Dict[str, Any]:
    """Toggle recommendation/preparation task between completed and active."""
    rec = recommendation_service.toggle_status(session, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation task not found")
    return {
        "id": rec.id,
        "patient_id": rec.patient_id,
        "content_id": rec.content_id,
        "status": rec.status,
        "completed_at": rec.completed_at.isoformat() if rec.completed_at else None,
        "duration_minutes": rec.duration_minutes,
        "repetitions": rec.repetitions,
    }
