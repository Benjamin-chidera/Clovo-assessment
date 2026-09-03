from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlmodel import Session

from database import get_session
from models import UserProfileData
from services import patient_service

router = APIRouter(tags=["Users"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/api/user", response_model=UserProfileData)
@router.get("/api/users/me", response_model=UserProfileData)
def get_current_user(
    session: SessionDep,
    patient_id: Annotated[Optional[str], Query(description="Optional patient ID or identifier")] = None,
) -> UserProfileData:
    """
    Get user profile data for the active patient from the database.
    """
    return patient_service.get_user_profile(session, patient_id)


@router.get("/api/users/{user_id}", response_model=UserProfileData)
def get_user_by_id(
    user_id: Annotated[int, Path(ge=1, description="Unique user ID")],
    session: SessionDep,
) -> UserProfileData:
    """
    Get user profile data for a specific user ID.
    """
    return patient_service.get_user_profile(session, user_id)
