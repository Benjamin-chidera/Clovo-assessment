from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from models import Patient, PatientHomeData, Recommendation
from services import patient_service, recommendation_service

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("", response_model=List[Patient])
async def list_patients(session: Session = Depends(get_session)) -> List[Patient]:
    """List all registered patients."""
    return patient_service.list_patients(session)


@router.get("/{patient_id}/home", response_model=PatientHomeData)
async def get_patient_home(
    patient_id: str,
    session: Session = Depends(get_session),
) -> PatientHomeData:
    """Get home dashboard data for a specific patient ID."""
    return patient_service.get_patient_home_data(session, patient_id)


@router.get("/{patient_id}/recommendations", response_model=List[Recommendation])
async def get_patient_recommendations(
    patient_id: str,
    session: Session = Depends(get_session),
) -> List[Recommendation]:
    """Get all recommendations for a patient."""
    return recommendation_service.get_by_patient(session, patient_id)
