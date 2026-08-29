import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
import socketio
from sqlmodel import Session

from database import engine
from models import MessageCreate
from services import (
    patient_service,
    recommendation_service,
    conversation_service,
)


def register_socket_events(sio: socketio.AsyncServer) -> None:
    """Register all Socket.IO real-time event listeners on the AsyncServer."""

    @sio.event
    async def connect(sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]] = None) -> None:
        """Handle incoming client socket connection with auth handshake."""
        user_id = "patient-sarah"
        if auth and isinstance(auth, dict):
            user_id = auth.get("userId", "patient-sarah")

        user_room = f"user_{user_id}"
        await sio.save_session(sid, {"userId": user_id, "room": user_room})
        await sio.enter_room(sid, user_room)

        print(f"✅ [Socket.IO] Client connected: sid={sid}, userId={user_id}, room={user_room}")

        await sio.emit(
            "session_ready",
            {
                "status": "connected",
                "userId": user_id,
                "connectedAt": datetime.now().isoformat(),
            },
            to=sid,
        )

    @sio.event
    async def disconnect(sid: str) -> None:
        """Handle client disconnection."""
        session = await sio.get_session(sid)
        user_id = session.get("userId", "unknown") if session else "unknown"
        print(f"❌ [Socket.IO] Client disconnected: sid={sid}, userId={user_id}")

    @sio.event
    async def send_message(sid: str, data: Dict[str, Any]) -> None:
        """Receive user chat message, persist to SQLite, and generate Coach Amy response."""
        session = await sio.get_session(sid)
        user_id = session.get("userId", "patient-sarah") if session else "patient-sarah"
        user_text = data.get("text", "")

        print(f"💬 [Message] From {user_id}: {user_text}")

        # Persist message to SQLite database
        with Session(engine) as db_session:
            patient = patient_service.get_patient_by_id(db_session, user_id) or patient_service.get_or_create_default_patient(db_session)
            conv = conversation_service.get_or_create_conversation(db_session, patient.id)
            conversation_service.add_message(
                db_session,
                MessageCreate(conversation_id=conv.id, role="user", content=user_text),
            )

        await asyncio.sleep(0.6)

        timestamp = datetime.now().strftime("%-I:%M %p")
        coach_reply_text = f"Got your check-in, Sarah! I'm personalizing today's recovery flow just for you. How does your body feel right now? 💙"

        with Session(engine) as db_session:
            conv = conversation_service.get_or_create_conversation(db_session, patient.id)
            saved_reply = conversation_service.add_message(
                db_session,
                MessageCreate(conversation_id=conv.id, role="coach", content=coach_reply_text),
            )
            reply_id = saved_reply.id

        coach_reply = {
            "id": reply_id,
            "sender": "coach",
            "text": coach_reply_text,
            "timestamp": timestamp,
        }

        await sio.emit("coach_message", coach_reply, to=sid)

    @sio.event
    async def select_activity(sid: str, data: Dict[str, Any]) -> None:
        """Handle user activity selection from recovery recommendation cards."""
        activity_title = data.get("title", "Selected Activity")
        activity_id = data.get("activityId", "")

        print(f"🎯 [Activity Selected] {activity_title} ({activity_id})")

        await asyncio.sleep(0.4)
        timestamp = datetime.now().strftime("%-I:%M %p")
        confirmation_reply = {
            "id": f"coach-confirm-{int(datetime.now().timestamp() * 1000)}",
            "sender": "coach",
            "text": f"Great choice! '{activity_title}' has been scheduled into your routine. Let's make today a great recovery day! 🌟",
            "timestamp": timestamp,
        }

        await sio.emit("coach_message", confirmation_reply, to=sid)

    @sio.event
    async def task_toggle(sid: str, data: Dict[str, Any]) -> None:
        """Handle synchronization of daily preparation tasks with SQLite persistence."""
        task_id = data.get("taskId", "")
        with Session(engine) as db_session:
            rec = recommendation_service.toggle_status(db_session, task_id)
            is_completed = (rec.status == "completed") if rec else data.get("isCompleted", False)

        print(f"📋 [Task Updated] taskId={task_id}, completed={is_completed}")
        await sio.emit("task_sync", {"taskId": task_id, "isCompleted": is_completed}, to=sid)
