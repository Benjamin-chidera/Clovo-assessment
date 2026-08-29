from typing import Annotated, Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Body
from sqlmodel import Session, select

from database import get_session
from models.clinical_content import ClinicalContent
from models.conversation import Message
from models.recommendation import Recommendation
from services import patient_service, conversation_service, coach_service

router = APIRouter(tags=["Conversations"])

SessionDep = Annotated[Session, Depends(get_session)]


def build_options_from_db(session: Session, patient_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Query clinical recommendations and content dynamically from the SQLite database.
    Pulls patient's assigned recommendations or active clinical content library items.
    """
    options = []

    # 1. Fetch patient's personalized recommendations joined with clinical content
    if patient_id:
        statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == patient_id)
            .order_by(Recommendation.scheduled_date.asc())
        )
        results = session.exec(statement).all()
        for rec, content in results:
            options.append({
                "id": f"content-{content.id}",
                "title": content.title,
                "subtitle": content.description,
                "durationMinutes": rec.duration_minutes,
                "durationLabel": f"{rec.duration_minutes} minutes",
                "intensity": "Low" if content.type in ["mindfulness", "nutrition"] else "Medium",
                "imageUri": content.image_url,
                "tag": content.type.capitalize(),
                "rationale": content.rationale,
            })

    # 2. If no patient-specific recommendations found, fall back to all ClinicalContent in DB
    if not options:
        all_content = session.exec(select(ClinicalContent).order_by(ClinicalContent.id.asc())).all()
        for content in all_content:
            duration = 10
            if "5" in content.description or "breathing" in content.title.lower():
                duration = 5
            elif "20" in content.description:
                duration = 20

            options.append({
                "id": f"content-{content.id}",
                "title": content.title,
                "subtitle": content.description,
                "durationMinutes": duration,
                "durationLabel": f"{duration} minutes",
                "intensity": "Low" if content.type in ["mindfulness", "nutrition"] else "Medium",
                "imageUri": content.image_url,
                "tag": content.type.capitalize(),
                "rationale": content.rationale,
            })

    # 3. Add surprise card option
    options.append({
        "id": "content-surprise",
        "title": "Surprise Me! 🎁",
        "subtitle": "Let's See What You Get",
        "imageUri": "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?auto=format&fit=crop&w=300&q=80",
        "isSpecial": True,
    })

    return options


@router.get("/api/conversations/messages")
def get_conversation_messages(
    session: SessionDep,
    patient_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Get all chat messages for the patient's active conversation from the database.
    If no messages exist, seed a welcoming intro message from Coach Amy.
    """
    if patient_id is None:
        patient = patient_service.get_or_create_default_patient(session)
    else:
        patient = patient_service.get_patient_by_id(session, patient_id) or patient_service.get_or_create_default_patient(session)

    conv = conversation_service.get_or_create_conversation(session, patient.id)
    messages = conversation_service.get_messages(session, conv.id)

    # Query options dynamically from SQLite for this patient
    db_options = build_options_from_db(session, patient.id)

    # If new conversation has no messages, create initial greeting with today's options
    if not messages:
        welcome_text = (
            f"Hi {patient.name}! 👋 I'm Amy, your AI Recovery Coach. "
            f"I'm here to support your preparation for your {patient.procedure or 'surgery'}. "
            "How does your body feel today? Here are today's approved routines from your care team—pick what feels best to start! 💙"
        )
        welcome_msg = conversation_service.add_message(
            session,
            Message(conversation_id=conv.id, role="coach", content=welcome_text),
        )
        messages = [welcome_msg]

    # Format for mobile client
    formatted_messages = []
    for m in messages:
        created_time = m.created_at.strftime("%-I:%M %p") if m.created_at else datetime.now().strftime("%-I:%M %p")

        # Check if message warrants displaying the clinical activity options from DB
        has_options = m.role == "coach" and any(
            phrase in (m.content or "").lower()
            for phrase in [
                "approved routines",
                "options to keep things light",
                "switched up your options",
                "surprise",
                "quad sets",
                "pick what feels best",
                "ready to jump into your routine",
                "how does your body feel",
            ]
        )

        formatted_messages.append({
            "id": m.id,
            "sender": "user" if m.role == "user" else "coach",
            "text": m.content,
            "timestamp": created_time,
            "options": db_options if has_options else None,
        })

    return formatted_messages


@router.post("/api/conversations/messages")
def send_chat_message(
    session: SessionDep,
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    HTTP REST endpoint to send a user message and receive Coach Amy's intelligent response.
    Used when Socket.IO is disconnected or in REST mode.
    """
    user_text = payload.get("text", "")
    patient_id = payload.get("patient_id")

    if patient_id is None:
        patient = patient_service.get_or_create_default_patient(session)
    else:
        patient = patient_service.get_patient_by_id(session, patient_id) or patient_service.get_or_create_default_patient(session)

    conv = conversation_service.get_or_create_conversation(session, patient.id)

    # 1. Save user message to DB
    conversation_service.add_message(
        session,
        Message(conversation_id=conv.id, role="user", content=user_text),
    )

    # 2. Run through CoachService LangGraph pipeline
    coach_output = coach_service.generate_coach_response(
        session=session,
        patient=patient,
        conversation=conv,
        user_message=user_text,
    )

    # 3. Save Coach response to DB
    coach_msg = conversation_service.add_message(
        session,
        Message(conversation_id=conv.id, role="coach", content=coach_output["text"]),
    )

    timestamp = coach_msg.created_at.strftime("%-I:%M %p") if coach_msg.created_at else datetime.now().strftime("%-I:%M %p")

    return {
        "id": coach_msg.id,
        "sender": "coach",
        "text": coach_output["text"],
        "timestamp": timestamp,
        "isSafetyAlert": coach_output.get("is_safety_alert", False),
        "riskLevel": coach_output.get("risk_level"),
        "options": coach_output.get("options"),
        "quickReplies": coach_output.get("quick_replies", []),
    }
