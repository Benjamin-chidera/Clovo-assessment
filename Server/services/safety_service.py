from typing import List, Optional, Tuple
from sqlmodel import Session, select
from models.safety_event import SafetyEvent, SafetyEventCreate

SAFETY_TRIGGERS = {
    "severe pain": ("high", "Urgent pain flare detected - recommend resting and contacting clinical care team"),
    "chest pain": ("critical", "Critical trigger: advise immediate emergency medical contact"),
    "shortness of breath": ("critical", "Critical trigger: advise immediate emergency medical contact"),
    "fever": ("medium", "Elevated temperature/infection risk: monitor and notify nurse triage"),
    "swelling": ("medium", "Noticeable swelling: check compression and elevate limb"),
    "bleeding": ("high", "Wound site concern: recommend direct medical evaluation"),
    "dizziness": ("medium", "Fall risk precaution: sit down immediately and hydrate"),
}


class SafetyService:
    @staticmethod
    def screen_content(content: str) -> Optional[Tuple[str, str, str]]:
        """
        Screen message content for clinical safety triggers.
        Returns (trigger, risk_level, action) or None.
        """
        lower = content.lower()
        for trigger, (risk_level, action) in SAFETY_TRIGGERS.items():
            if trigger in lower:
                return trigger, risk_level, action
        return None

    @staticmethod
    def record_event(session: Session, data: SafetyEventCreate) -> SafetyEvent:
        event = SafetyEvent(
            conversation_id=data.conversation_id,
            message_id=data.message_id,
            risk_level=data.risk_level,
            trigger=data.trigger,
            action=data.action,
            status=data.status,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event

    @staticmethod
    def get_by_conversation(session: Session, conversation_id: str) -> List[SafetyEvent]:
        statement = select(SafetyEvent).where(SafetyEvent.conversation_id == conversation_id)
        return list(session.exec(statement).all())


safety_service = SafetyService()
