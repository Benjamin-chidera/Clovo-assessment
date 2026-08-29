from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from models import UserProfileData
from services import patient_service

router = APIRouter(tags=["Users"])


@router.get("/api/user", response_model=UserProfileData)
@router.get("/api/users/me", response_model=UserProfileData)
async def get_current_user(
    patient_id: Optional[str] = None,
    session: Session = Depends(get_session),
) -> UserProfileData:
    """
    Get user profile data for the active patient from the database.
    """
    return patient_service.get_user_profile(session, patient_id)


@router.get("/api/users/{user_id}", response_model=UserProfileData)
async def get_user_by_id(
    user_id: str,
    session: Session = Depends(get_session),
) -> UserProfileData:
    """
    Get user profile data for a specific user ID.
    """
    return patient_service.get_user_profile(session, user_id)
