from typing import Annotated, List
from fastapi import APIRouter, Depends, Path
from sqlmodel import Session

from database import get_session
from models import Patient, PatientHomeData, RecommendationRead
from services import patient_service, recommendation_service

router = APIRouter(prefix="/api/patients", tags=["Patients"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=List[Patient])
def list_patients(session: SessionDep) -> List[Patient]:
    """List all registered patients."""
    return patient_service.list_patients(session)


@router.get("/{patient_id}/home", response_model=PatientHomeData)
def get_patient_home(
    patient_id: Annotated[int, Path(ge=1, description="Unique patient ID")],
    session: SessionDep,
) -> PatientHomeData:
    """Get home dashboard data for a specific patient ID."""
    return patient_service.get_patient_home_data(session, patient_id)


@router.get("/{patient_id}/recommendations", response_model=List[RecommendationRead])
def get_patient_recommendations(
    patient_id: Annotated[int, Path(ge=1, description="Unique patient ID")],
    session: SessionDep,
) -> List[RecommendationRead]:
    """Get all recommendations for a patient with joined clinical content."""
    return recommendation_service.get_by_patient(session, patient_id)
