import os
from dotenv import load_dotenv

# Load environment variables (.env) before service initializations
load_dotenv()

from contextlib import asynccontextmanager
from typing import Dict
import socketio
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_db_and_tables
from routes import api_router, register_socket_events
from services import get_socket_manager, redis_cache

# Initialize Sentry Observability if DSN is configured
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENV = os.getenv("SENTRY_ENVIRONMENT", "development")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENV,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            RedisIntegration(),
        ],
        traces_sample_rate=1.0 if SENTRY_ENV == "development" else 0.2,
        profiles_sample_rate=0.2,
        send_default_pii=False,
    ) 
    print(f"🛡️ [Sentry] Server monitoring active in '{SENTRY_ENV}' mode.")

# Initialize async Socket.IO server with ping timeout safeguards
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=get_socket_manager(),
    ping_timeout=60,
    ping_interval=25,
    logger=True,
    engineio_logger=False,
)

# Register all Socket.IO real-time event handlers from routes/sockets.py
register_socket_events(sio)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for database & Redis initialization on startup."""
    create_db_and_tables()
    await redis_cache.init()
    yield
    await redis_cache.close()


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


# --- Root & Health Endpoints ---

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
