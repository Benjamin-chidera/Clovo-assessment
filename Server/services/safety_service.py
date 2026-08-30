import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlmodel import Session, select
from models.safety_event import SafetyEvent

# Deterministic Emergency Fast-Path Regex (Instant Zero-Latency Filter)
CRITICAL_EMERGENCY_PATTERNS = [
    (r"\b(kill myself|suicide|suicidal|end my life|want to die|take my own life)\b", "mental_health", "critical", "Explicit self-harm / suicidal crisis", "Seek immediate emergency mental health crisis support (999 / Samaritans / A&E)"),
    (r"\b(chest pain|heart attack|can't breathe|cannot breathe|severe shortness of breath|passed out|unconscious|heavy bleeding)\b", "acute_medical", "critical", "Severe medical emergency", "Instruct immediate halt and call 999 or proceed to nearest A&E"),
]

# Heuristic Fallback Patterns (Used if LLM is unreachable)
FALLBACK_SAFETY_PATTERNS = [
    (r"\b(hit (my )?head|head injury|concussion|fell (down|over)|fall on|injured my)\b", "acute_medical", "high", "Head trauma or fall reported", "Stop all activity immediately, rest, and contact NHS 111 or surgical clinic"),
    (r"\b(fever|infected|infection|pus|oozing|red streak|hot to (the )?touch|calf swelling|dvt)\b", "acute_medical", "high", "Surgical wound infection / DVT risk", "Alert clinical care team and contact clinic or NHS 111"),
    (r"\b(thrown? (all )?(my )?med|stop(ping)? (my )?med|flushed (my )?pills|skip(ping)? (blood )?thinner|change (my )?dosage|prescribe)\b", "clinical_decision", "low", "Medication discontinuation / out-of-scope request", "Refuse clinical decision-making and advise consulting prescribing doctor"),
    (r"\b(pain (\d{1,2}|is [89]|is 10)|unbearable pain|severe pain|sharp (stabbing )?pain)\b", "severe_pain", "medium", "High / unbearable pain level", "Validate pain, pause joint loading, and advise contacting physiotherapy team"),
    (r"\b(severe dizziness|vertigo|blacking out)\b", "acute_medical", "high", "Severe dizziness / fall risk", "Sit down immediately, rest, and contact NHS 111"),
]

TRIAGE_SYSTEM_PROMPT = """You are an expert Clinical Safety Triage Classifier for an AI Surgical Recovery application (Clovo).
Your job is to screen patient messages and classify them into one of 5 clinical safety categories:

1. "mental_health" (Risk: "critical"):
   - Explicit or implied self-harm, suicidal thoughts, feeling like giving up completely, severe emotional crisis.
   - Examples: "I want to give up", "I can't do this anymore", "I feel suicidal", "I threw my meds in the toilet because I don't care about living".

2. "acute_medical" (Risk: "high"):
   - Acute complications, physical trauma (hit head, fell), wound infection, fever, pus, severe dizziness, chest pain, breathing difficulty, sudden swelling, calf pain (DVT).
   - Examples: "I hit my head on the floor", "I fell down the stairs", "My knee is red, hot, and oozing pus", "I have a high fever".

3. "severe_pain" (Risk: "medium"):
   - Pain rating > 7/10, sudden sharp/unbearable joint pain, worsening acute flare-ups.
   - Examples: "My pain is an 8 out of 10", "Unbearable sharp pain in my joint", "It hurts too much to put any weight down".

4. "clinical_decision" (Risk: "low"):
   - Patient asks Amy to make a medical decision, change a prescription, stop medications (like blood thinners), threw away medications without emergency, or requests a diagnosis.
   - Examples: "I threw my meds in the toilet", "Can I stop taking my blood thinners?", "Should I change my dosage to twice a day?".

5. "safe" (Risk: null):
   - Normal recovery check-ins, routine questions, exercise guidance, nutrition, mild normal soreness, general encouragement.
   - Examples: "What's my plan today?", "How do I do Quad Sets?", "What protein snack helps?", "I'm a bit tired after my walk".

Output strictly valid JSON with no markdown and no extra text:
{
  "is_safety_alert": true or false,
  "category": "mental_health" | "acute_medical" | "severe_pain" | "clinical_decision" | "safe",
  "risk_level": "critical" | "high" | "medium" | "low" | null,
  "trigger": "<concise phrase summarizing the trigger>",
  "action": "<concise clinical action required>"
}
"""


class SafetyService:
    @staticmethod
    def _check_deterministic_fast_path(text: str) -> Optional[Dict[str, Any]]:
        """Fast-path regex filter for unambiguous critical emergencies."""
        lower = text.lower()
        for pattern, category, risk, trigger, action in CRITICAL_EMERGENCY_PATTERNS:
            if re.search(pattern, lower):
                return {
                    "is_safety_alert": True,
                    "category": category,
                    "risk_level": risk,
                    "trigger": trigger,
                    "action": action,
                }
        return None

    @staticmethod
    def _check_heuristic_fallback(text: str) -> Optional[Dict[str, Any]]:
        """Fallback heuristic regex patterns when LLM is offline or times out."""
        lower = text.lower()
        for pattern, category, risk, trigger, action in FALLBACK_SAFETY_PATTERNS:
            if re.search(pattern, lower):
                return {
                    "is_safety_alert": True,
                    "category": category,
                    "risk_level": risk,
                    "trigger": trigger,
                    "action": action,
                }
        return None

    def screen_message_semantic(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        llm_instance: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Screen message for clinical safety using LLM semantic classification
        with instant deterministic fast-paths and resilient fallbacks.
        """
        # 1. Check instant critical emergency fast-path (< 1ms)
        fast_match = self._check_deterministic_fast_path(user_message)
        if fast_match:
            print(f"🚨 [Safety Fast-Path] Emergency Trigger Detected: {fast_match['trigger']}")
            return fast_match

        # 2. Semantic LLM Classification
        if llm_instance:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage

                history_context = ""
                if conversation_history:
                    recent = conversation_history[-4:]
                    history_lines = [f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in recent]
                    history_context = f"\nRecent Conversation Context:\n" + "\n".join(history_lines) + "\n"

                prompt = f"{history_context}Patient Message: \"{user_message}\"\n\nClassify the safety category:"
                messages = [
                    SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]

                result = llm_instance.invoke(messages)
                if result and result.content:
                    raw_text = str(result.content).strip()
                    # Clean markdown formatting if present
                    if "```json" in raw_text:
                        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_text:
                        raw_text = raw_text.split("```")[1].split("```")[0].strip()

                    parsed = json.loads(raw_text)
                    is_alert = parsed.get("is_safety_alert", False)
                    category = parsed.get("category", "safe")
                    risk = parsed.get("risk_level")

                    if is_alert and category != "safe":
                        print(f"🛡️ [Safety LLM Classifier] ALERT! Category: {category.upper()} | Risk: {str(risk).upper()} | Trigger: {parsed.get('trigger')}")
                        return {
                            "is_safety_alert": True,
                            "category": category,
                            "risk_level": risk or "medium",
                            "trigger": parsed.get("trigger", "Clinical safety issue detected"),
                            "action": parsed.get("action", "Alert care team and provide supportive clinical guidance"),
                        }
                    else:
                        print("✅ [Safety LLM Classifier] SAFE (No clinical red flags detected)")
                        return {
                            "is_safety_alert": False,
                            "category": "safe",
                            "risk_level": None,
                            "trigger": None,
                            "action": None,
                        }
            except Exception as e:
                print(f"⚠️ [Safety LLM Classifier] LLM triage error ({e}), falling back to heuristic rules...")

        # 3. Fallback Heuristics
        fallback_match = self._check_heuristic_fallback(user_message)
        if fallback_match:
            print(f"🚨 [Safety Fallback] Heuristic Trigger Detected: {fallback_match['trigger']}")
            return fallback_match

        return {
            "is_safety_alert": False,
            "category": "safe",
            "risk_level": None,
            "trigger": None,
            "action": None,
        }

    # Backward-compatible method
    def screen_content(self, content: str) -> Optional[Tuple[str, str, str]]:
        """Legacy helper returning (trigger, risk_level, action) or None."""
        res = self.screen_message_semantic(content)
        if res.get("is_safety_alert"):
            return res.get("trigger", "Safety alert"), res.get("risk_level", "high"), res.get("action", "Alert care team")
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