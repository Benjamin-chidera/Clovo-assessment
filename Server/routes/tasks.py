from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlmodel import Session

from database import get_session
from models import Recommendation, TaskItemData
from services import recommendation_service

router = APIRouter(tags=["Tasks"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/api/tasks", response_model=List[TaskItemData])
def get_tasks(
    session: SessionDep,
    patient_id: Annotated[Optional[str], Query(description="Optional patient ID or identifier")] = None,
) -> List[TaskItemData]:
    """
    Get daily tasks/preparations for the active user from the database.
    """
    return recommendation_service.get_tasks_for_user(session, patient_id)


@router.get("/api/users/{user_id}/tasks", response_model=List[TaskItemData])
def get_user_tasks(
    user_id: Annotated[int, Path(ge=1, description="Unique user ID")],
    session: SessionDep,
) -> List[TaskItemData]:
    """
    Get daily tasks for a specific user ID.
    """
    return recommendation_service.get_tasks_for_user(session, user_id)


@router.patch("/api/tasks/{task_id}/toggle", response_model=Recommendation)
def toggle_task(
    task_id: Annotated[int, Path(ge=1, description="Unique task ID")],
    session: SessionDep,
) -> Recommendation:
    """
    Toggle task completion status in the database.
    """
    rec = recommendation_service.toggle_status(session, task_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Task not found")
    return rec