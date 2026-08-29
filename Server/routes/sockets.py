import asyncio
import random
from datetime import datetime
from typing import Any, Dict, Optional
import socketio
from sqlmodel import Session, select

from database import engine
from models import Message, ClinicalContent
from services import (
    patient_service,
    recommendation_service,
    conversation_service,
    coach_service,
    redis_cache,
)


def register_socket_events(sio: socketio.AsyncServer) -> None:
    """Register all Socket.IO real-time event listeners on the AsyncServer."""

    @sio.event
    async def connect(sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]] = None) -> None:
        """Handle incoming client socket connection with auth handshake."""
        user_id = "1"
        if auth and isinstance(auth, dict):
            user_id = str(auth.get("userId", "1"))

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
        """
        Receive user chat message, persist to SQLite, execute Coach Amy's
        clinical decision graph (LangGraph), and stream intelligent response.
        """
        session = await sio.get_session(sid)
        user_id = session.get("userId", "1") if session else "1"
        user_text = data.get("text", "")

        print(f"💬 [Message] From {user_id}: {user_text}")

        # Resolve patient ID
        pid = int(user_id) if str(user_id).isdigit() else 1

        with Session(engine) as db_session:
            patient = patient_service.get_patient_by_id(db_session, pid) or patient_service.get_or_create_default_patient(db_session)
            conv = conversation_service.get_or_create_conversation(db_session, patient.id)
            
            # Persist user message
            conversation_service.add_message(
                db_session,
                Message(conversation_id=conv.id, role="user", content=user_text),
            )

            # Generate intelligent, clinically grounded response via CoachService pipeline
            coach_output = coach_service.generate_coach_response(
                session=db_session,
                patient=patient,
                conversation=conv,
                user_message=user_text,
            )

            coach_reply_text = coach_output["text"]

            # Persist coach response
            saved_reply = conversation_service.add_message(
                db_session,
                Message(conversation_id=conv.id, role="coach", content=coach_reply_text),
            )
            reply_id = saved_reply.id

        await asyncio.sleep(0.4)

        timestamp = datetime.now().strftime("%-I:%M %p")
        coach_reply = {
            "id": reply_id,
            "sender": "coach",
            "text": coach_reply_text,
            "timestamp": timestamp,
            "isSafetyAlert": coach_output.get("is_safety_alert", False),
            "riskLevel": coach_output.get("risk_level"),
            "options": coach_output.get("options"),
            "quickReplies": coach_output.get("quick_replies", []),
        }

        await sio.emit("coach_message", coach_reply, to=sid)

    @sio.event
    async def select_activity(sid: str, data: Dict[str, Any]) -> None:
        """
        Handle user activity selection from recovery recommendation cards.
        Persists both the user choice and Coach Amy's guidance to SQLite,
        and provides clinical instructions and dynamic follow-up quick replies.
        """
        session = await sio.get_session(sid)
        user_id = session.get("userId", "1") if session else "1"
        activity_title = data.get("title", "Selected Activity")
        activity_id = data.get("activityId", "")

        print(f"🎯 [Activity Selected] User={user_id}: '{activity_title}' ({activity_id})")

        # Resolve patient ID
        pid = int(user_id) if str(user_id).isdigit() else 1

        with Session(engine) as db_session:
            patient = patient_service.get_patient_by_id(db_session, pid) or patient_service.get_or_create_default_patient(db_session)
            conv = conversation_service.get_or_create_conversation(db_session, patient.id)

            # 1. Save user selection message to database
            user_select_text = f"Selected: {activity_title}"
            conversation_service.add_message(
                db_session,
                Message(conversation_id=conv.id, role="user", content=user_select_text),
            )

            # 2. Check if Surprise Me was clicked
            is_surprise = "surprise" in activity_id.lower() or "surprise" in activity_title.lower()

            all_content = db_session.exec(select(ClinicalContent)).all()

            if is_surprise:
                # Pick a surprise activity from the clinical content library
                surprise_candidates = [c for c in all_content if c.id in [4, 5, 6, 7]]
                chosen = random.choice(surprise_candidates) if surprise_candidates else all_content[0]
                
                reply_text = (
                    f"Surprise, {patient.name}! 🎁 Today your bonus recovery activity is {chosen.title}!\n\n"
                    f"{chosen.description}\n\n"
                    f"Why this helps: {chosen.rationale} 💙"
                )
                quick_replies = ["I'll do it now! ✅", "How do I do this?", "Give me another surprise 🎁"]
            else:
                # Look up content details
                matching = next(
                    (c for c in all_content if c.title.lower() in activity_title.lower() or f"content-{c.id}" == activity_id),
                    None
                )
                if matching:
                    reply_text = (
                        f"Great choice, {patient.name}! You picked {matching.title}.\n\n"
                        f"{matching.description}\n\n"
                        f"Why this helps: {matching.rationale} 🌟"
                    )
                else:
                    reply_text = f"Great choice, {patient.name}! '{activity_title}' is ready for you. Take your time, listen to your body, and enjoy the routine! 🌟"
                
                quick_replies = ["Mark as completed ✅", "Remind me in 1 hour ⏰", "What else should I do?"]

            # 3. Save Coach Amy reply to database
            saved_reply = conversation_service.add_message(
                db_session,
                Message(conversation_id=conv.id, role="coach", content=reply_text),
            )
            reply_id = saved_reply.id

        await asyncio.sleep(0.3)
        timestamp = datetime.now().strftime("%-I:%M %p")
        coach_reply = {
            "id": reply_id,
            "sender": "coach",
            "text": reply_text,
            "timestamp": timestamp,
            "isSafetyAlert": False,
            "riskLevel": None,
            "options": None,
            "quickReplies": quick_replies,
        }

        await sio.emit("coach_message", coach_reply, to=sid)

    @sio.event
    async def task_toggle(sid: str, data: Dict[str, Any]) -> None:
        """Handle synchronization of daily preparation tasks with SQLite persistence."""
        task_id = data.get("taskId", "")
        tid = int(task_id) if str(task_id).isdigit() else 1
        with Session(engine) as db_session:
            rec = recommendation_service.toggle_status(db_session, tid)
            is_completed = (rec.status == "completed") if rec else data.get("isCompleted", False)

        print(f"📋 [Task Updated] taskId={task_id}, completed={is_completed}")
        await redis_cache.delete_pattern("tasks:*")
        await redis_cache.delete_pattern("home:*")
        await sio.emit("task_sync", {"taskId": task_id, "isCompleted": is_completed}, to=sid)
