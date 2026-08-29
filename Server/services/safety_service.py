from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select
from models.safety_event import SafetyEvent

SAFETY_TRIGGERS: Dict[str, Tuple[str, str]] = {
    # Critical Risk Triggers
    "chest pain": ("critical", "Critical trigger: advise immediate emergency medical contact (999/A&E)"),
    "can't breathe": ("critical", "Critical trigger: severe respiratory distress (999/A&E)"),
    "shortness of breath": ("critical", "Critical trigger: severe respiratory distress (999/A&E)"),
    "passed out": ("critical", "Critical trigger: syncope/collapse (999/A&E)"),
    "collapse": ("critical", "Critical trigger: syncope/collapse (999/A&E)"),
    "heavy bleeding": ("critical", "Critical trigger: severe hemorrhaging (999/A&E)"),
    "suicide": ("critical", "Critical mental health crisis: emergency mental health contact"),
    "kill myself": ("critical", "Critical mental health crisis: emergency mental health contact"),

    # High Risk Triggers
    "severe pain": ("high", "Urgent pain flare detected: halt exercises, rest, and contact clinic or NHS 111"),
    "sharp pain": ("high", "Sharp acute joint/incision pain: halt movement and seek clinical review"),
    "throbbing pain": ("high", "Intense throbbing pain: halt activity and alert care team"),
    "fever": ("high", "Elevated temperature (>38.5C) / infection indicator: notify clinical triage"),
    "infected": ("high", "Potential surgical wound infection: direct clinical evaluation required"),
    "oozing": ("high", "Wound discharge/oozing: inspect dressing and contact clinical team"),
    "pus": ("high", "Wound infection indicator: contact surgical clinic immediately"),
    "calf pain": ("high", "Calf redness/pain (DVT risk): urgent medical assessment"),
    "severe dizziness": ("high", "Severe vertigo/fall risk: sit/lie down and hydrate"),

    # Medium Risk Triggers
    "dizziness": ("medium", "Mild dizziness/lightheadedness: sit down immediately and hydrate"),
    "swelling": ("medium", "Noticeable swelling: elevate limb, apply cold compress, and rest"),
    "soreness": ("medium", "Muscle soreness/fatigue: listen to body, reduce intensity, and rest"),
    "fatigue": ("medium", "Exhaustion/fatigue: prioritize sleep, hydration, and gentle pacing"),
    "overwhelmed": ("medium", "Pre-op anxiety/stress: offer calming mindfulness and support"),
    "nauseous": ("medium", "Post-op/pre-op nausea: hydrate in small sips and rest"),
}


class SafetyService:
    @staticmethod
    def screen_content(content: str) -> Optional[Tuple[str, str, str]]:
        """
        Screen message content for clinical safety triggers.
        Returns (trigger_word, risk_level, clinical_action) or None.
        """
        lower = content.lower()
        for trigger, (risk_level, action) in SAFETY_TRIGGERS.items():
            if trigger in lower:
                return trigger, risk_level, action
        return None

    @staticmethod
    def record_event(
        session: Session,
        conversation_id: str,
        trigger: str,
        risk_level: str,
        action: str,
        patient_id: Optional[int] = None,
        message_id: Optional[str] = None,
    ) -> SafetyEvent:
        """Record and persist a clinical safety event to SQLite."""
        event = SafetyEvent(
            patient_id=patient_id,
            conversation_id=conversation_id,
            message_id=message_id,
            risk_level=risk_level,
            trigger=trigger,
            action=action,
            status="open",
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        print(f"🚨 [Safety Event] Logged: risk={risk_level}, trigger='{trigger}', patient_id={patient_id}")
        return event

    @staticmethod
    def get_by_conversation(session: Session, conversation_id: str) -> List[SafetyEvent]:
        """Fetch all safety events for a given conversation."""
        statement = select(SafetyEvent).where(SafetyEvent.conversation_id == conversation_id)
        return list(session.exec(statement).all())

    @staticmethod
    def get_by_patient(session: Session, patient_id: int) -> List[SafetyEvent]:
        """Fetch all safety events for a patient."""
        statement = (
            select(SafetyEvent)
            .where(SafetyEvent.patient_id == patient_id)
            .order_by(SafetyEvent.created_at.desc())
        )
        return list(session.exec(statement).all())

    @staticmethod
    def get_all(session: Session) -> List[SafetyEvent]:
        """Fetch all safety events for the clinician triage queue."""
        statement = select(SafetyEvent).order_by(SafetyEvent.created_at.desc())
        return list(session.exec(statement).all())


safety_service = SafetyService()