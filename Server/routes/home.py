from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from models import PatientHomeData
from services import patient_service

router = APIRouter(prefix="/api/home", tags=["Home"])


@router.get("", response_model=PatientHomeData)
async def get_home_dashboard(
    patient_id: Optional[str] = None,
    session: Session = Depends(get_session),
) -> PatientHomeData:
    """
    Get dashboard data for the mobile Home screen:
    - Greeting: 'Good morning, Sarah'
    - Surgery countdown: '21 days away'
    - Today's preparation tasks: Walking, Mindfulness, Nutrition
    """
    return patient_service.get_patient_home_data(session, patient_id)
