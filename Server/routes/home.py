from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from database import get_session
from models import PatientHomeData
from services import patient_service

router = APIRouter(prefix="/api/home", tags=["Home"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=PatientHomeData)
def get_home_dashboard(
    session: SessionDep,
    patient_id: Annotated[Optional[int], Query(description="Optional patient ID")] = None,
) -> PatientHomeData:
    """
    Get dashboard data for the mobile Home screen:
    - Greeting: 'Good morning, Sarah'
    - Surgery countdown: '21 days away'
    - Today's preparation tasks with evidence-based clinical content
    """
    return patient_service.get_patient_home_data(session, patient_id)
