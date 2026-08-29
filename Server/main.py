from contextlib import asynccontextmanager
from typing import Dict
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_db_and_tables
from routes import api_router, register_socket_events

# Initialize async Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=False,
)

# Register all Socket.IO real-time event handlers from routes/sockets.py
register_socket_events(sio)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for database initialization on startup."""
    create_db_and_tables()
    yield


# Initialize FastAPI application
app = FastAPI(
    title="Clovo API",
    description="Clovo Personalized Wellness & Recovery Coaching Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all modular API routes defined in /routes
app.include_router(api_router)


# --- Root & Health Endpoints (Only endpoints allowed in main.py) ---

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the Clovo backend API."""
    return {"status": "ok", "service": "clovo-server"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to the Clovo API. Use /health to check the health of the server, or /docs for API documentation."
    }


# Combine FastAPI and Socket.IO into single ASGI application
socket_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)


def main() -> None:
    """Run server locally using uvicorn."""
    import uvicorn

    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
