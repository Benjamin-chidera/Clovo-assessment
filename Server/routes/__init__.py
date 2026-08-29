from fastapi import APIRouter

from routes.home import router as home_router
from routes.patients import router as patients_router
from routes.recommendations import router as recommendations_router
from routes.users import router as users_router
from routes.tasks import router as tasks_router
from routes.sockets import register_socket_events

api_router = APIRouter()

api_router.include_router(home_router)
api_router.include_router(patients_router)
api_router.include_router(recommendations_router)
api_router.include_router(users_router)
api_router.include_router(tasks_router)

__all__ = [
    "api_router",
    "home_router",
    "patients_router",
    "recommendations_router",
    "users_router",
    "tasks_router",
    "register_socket_events",
]
