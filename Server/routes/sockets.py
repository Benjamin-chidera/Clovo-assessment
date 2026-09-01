import asyncio
import random
from datetime import datetime, timezone
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
        clinical decision graph (LangGraph) in a worker thread, and stream intelligent response.
        """
        session = await sio.get_session(sid)
        user_id = session.get("userId", "1") if session else "1"
        user_text = data.get("text", "")

        # Voice session trigger: when the patient taps the mic, the app sends
        # this special signal. We translate it into a natural greeting request
        # so Amy speaks first before the patient starts talking.
        VOICE_SESSION_TRIGGER = "[VOICE_SESSION_START]"
        is_voice_session = user_text.strip() == VOICE_SESSION_TRIGGER
        if is_voice_session:
            user_text = "Hi Amy, I just started a voice conversation with you. Please greet me warmly and ask how I'm feeling today. Keep it brief and conversational since we're talking by voice."

        print(f"💬 [Message] From {user_id}: {user_text}")
        pid = int(user_id) if str(user_id).isdigit() else 1

        def _process_sync():
            with Session(engine) as db_session:
                patient = patient_service.get_patient_by_id(db_session, pid) or patient_service.get_or_create_default_patient(db_session)
                conv = conversation_service.get_or_create_conversation(db_session, patient.id)

                # 1. Persist user message
                conversation_service.add_message(
                    db_session,
                    Message(conversation_id=conv.id, role="user", content=user_text),
                )

                # 2. Generate intelligent, clinically grounded response via CoachService pipeline
                coach_output = coach_service.generate_coach_response(
                    session=db_session,
                    patient=patient,
                    conversation=conv,
                    user_message=user_text,
                )

                # 3. Persist coach response
                saved_reply = conversation_service.add_message(
                    db_session,
                    Message(conversation_id=conv.id, role="coach", content=coach_output["text"]),
                )
                return coach_output, saved_reply.id

        # Offload synchronous SQLite queries and LLM generation to background threadpool
        coach_output, reply_id = await asyncio.to_thread(_process_sync)

        timestamp = datetime.now().strftime("%-I:%M %p")
        coach_reply = {
            "id": reply_id,
            "sender": "coach",
            "text": coach_output["text"],
            "timestamp": timestamp,
            "isSafetyAlert": coach_output.get("is_safety_alert", False),
            "riskLevel": coach_output.get("risk_level"),
            "options": coach_output.get("options"),
            "quickReplies": coach_output.get("quick_replies", []),
        }

        await sio.emit("coach_message", coach_reply, to=sid)

        # Broadcast real-time task sync (completion/unmarking) event to Mobile Home and Chat stores
        completed_task_data = coach_output.get("completed_task")
        if completed_task_data:
            # Normalise to a list — single-task completions arrive as a dict, bulk resets as a list
            task_list = completed_task_data if isinstance(completed_task_data, list) else [completed_task_data]

            await redis_cache.delete_pattern("tasks:*")
            await redis_cache.delete_pattern("home:*")

            def _get_stats():
                with Session(engine) as db_session:
                    p = patient_service.get_patient_by_id(db_session, pid)
                    milestones, add_count = patient_service.get_patient_milestones(db_session, pid)
                    streak = p.streak_count if p else 0
                    m_dump = [m.model_dump() for m in milestones]
                    return streak, m_dump, add_count

            streak_count, milestones_data, add_count = await asyncio.to_thread(_get_stats)

            for task_info in task_list:
                task_id = task_info.get("taskId")
                is_comp = task_info.get("isCompleted", True)
                action_label = "completed" if is_comp else "reset to pending"
                print(f"📡 [Socket.IO] Broadcasting task_sync for task #{task_id} ({action_label})")
                await sio.emit("task_sync", {
                    "taskId": task_id,
                    "isCompleted": is_comp,
                    "streakCount": streak_count,
                    "milestones": milestones_data,
                    "additionalMilestonesCount": add_count,
                }, to=f"user_{user_id}")

            await sio.emit("user_stats_updated", {
                "streakCount": streak_count,
                "milestones": milestones_data,
                "additionalMilestonesCount": add_count,
            }, to=f"user_{user_id}")


        # Broadcast real-time safety alert to Admin Clinician Portal
        if coach_output.get("is_safety_alert"):
            alert_payload = {
                "id": reply_id,
                "patient_id": pid,
                "patient_name": "Sarah Jenkins",
                "procedure": "Knee Surgery",
                "conversation_id": "conv-1",
                "risk_level": coach_output.get("risk_level", "high"),
                "trigger": user_text,
                "action": "Alert care team and advise immediate rest",
                "status": "open",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await sio.emit("new_safety_event", alert_payload)

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
        pid = int(user_id) if str(user_id).isdigit() else 1

        def _process_activity_sync():
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
                    chosen = recommendation_service.get_safe_surprise_activity(db_session, patient.id)
                    reply_text = (
                        f"Surprise, {patient.name}! 🎁 Today your bonus recovery activity is {chosen.title}!\n\n"
                        f"{chosen.description}\n\n"
                        f"Why this helps: {chosen.rationale} 💙"
                    )
                    quick_replies = ["I'll do it now! ✅", "How do I do this?", "Give me another surprise 🎁"]
                else:
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
                return reply_text, saved_reply.id, quick_replies

        reply_text, reply_id, quick_replies = await asyncio.to_thread(_process_activity_sync)

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
        """Handle synchronization of daily preparation tasks with SQLite persistence and milestone recalculation."""
        session = await sio.get_session(sid)
        user_id = session.get("userId", "1") if session else "1"
        task_id = data.get("taskId", "")
        tid = int(task_id) if str(task_id).isdigit() else 1

        def _toggle_sync():
            with Session(engine) as db_session:
                rec = recommendation_service.toggle_status(db_session, tid)
                is_comp = (rec.status == "completed") if rec else data.get("isCompleted", False)
                pid = rec.patient_id if rec else (int(user_id) if str(user_id).isdigit() else 1)
                patient = patient_service.get_patient_by_id(db_session, pid)
                milestones, add_count = patient_service.get_patient_milestones(db_session, pid)
                streak = patient.streak_count if patient else 5
                m_dump = [m.model_dump() for m in milestones]
                return is_comp, streak, m_dump, add_count

        is_completed, streak_count, milestones_data, add_count = await asyncio.to_thread(_toggle_sync)

        print(f"📋 [Task Updated] taskId={task_id}, completed={is_completed}, streak={streak_count}, milestones={len(milestones_data)}")
        await redis_cache.delete_pattern("tasks:*")
        await redis_cache.delete_pattern("home:*")
        
        # Broadcast to room and direct sid
        target_room = f"user_{user_id}"
        payload = {
            "taskId": task_id,
            "isCompleted": is_completed,
            "streakCount": streak_count,
            "milestones": milestones_data,
            "additionalMilestonesCount": add_count,
        }
        await sio.emit("task_sync", payload, to=target_room)
        await sio.emit("user_stats_updated", {
            "streakCount": streak_count,
            "milestones": milestones_data,
            "additionalMilestonesCount": add_count,
        }, to=target_room)

