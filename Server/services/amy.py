import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from sqlmodel import Session, select

from models.clinical_content import ClinicalContent
from models.conversation import Conversation
from models.patient import Patient
from models.recommendation import Recommendation
from services.safety_service import safety_service

# Initialize LangChain Chat Model (Gemma 4 via Ollama)
try:
    from langchain_ollama import ChatOllama
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.4, timeout=30)
except Exception:
    llm = None


AMY_SYSTEM_PROMPT = """You are Amy, an empathetic, encouraging, and clinically-grounded AI Recovery Coach at Clovo.
You are assisting surgical and wellness patients (such as Sarah, preparing for Knee Surgery in 21 days).

FORMATTING RULES (VERY IMPORTANT):
- Output ONLY natural, clean plain conversational text.
- DO NOT use markdown symbols like **bold**, *italic*, headers (### or ##), bullet point asterisks (*), or dashes (-).
- Write in warm, clear paragraphs with natural punctuation and friendly emojis (like 💙, 🌟, ✨, 🎉).

DYNAMIC FOLLOW-UP SUGGESTIONS:
- At the very end of your response, on the last line, suggest 3 to 4 short, relevant questions or answers the patient might want to tap next.
- Format that last line strictly as:
QUICK_REPLIES: [Short Option 1] | [Short Option 2] | [Short Option 3]

YOUR RESPONSIBILITIES:
1. Explain the patient's approved daily recommendations and the physiological "Why" using ONLY the clinical library and rationales provided in context.
2. Provide warm encouragement, empathy, and positive reinforcement.
3. Keep responses concise, supportive, and easy to read on mobile.
4. Celebrate completed tasks and progress milestones.

STRICT CLINICAL BOUNDARIES (DO NOT VIOLATE):
1. NEVER invent unapproved exercises, diets, medications, or alternative treatments.
2. NEVER alter prescribed durations or repetitions.
3. NEVER diagnose medical conditions or say "You have a tear/infection".
4. NEVER tell a patient to push through pain, dizziness, or abnormal symptoms.
5. If the user asks for unapproved medical advice, politely explain that you can only guide approved routines and advise them to consult their clinician.

SAFETY PROTOCOL:
If the user mentions dizziness, sharp pain, fever, chest pain, or bleeding:
- Instruct them to stop the activity immediately and rest.
- Direct severe emergencies to 999 or NHS 111.
"""


def clean_plain_text(text: str) -> str:
    """
    Sanitize text to remove markdown formatting symbols (**, *, ###, __)
    so responses display as clean, natural plain text.
    """
    if not text:
        return ""
    # Remove markdown header hashes: ### Header -> Header
    text = re.sub(r'#+\s*', '', text)
    # Remove bold/italic asterisks: **word** -> word, *word* -> word
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
    text = text.replace('*', '')
    # Remove underscores formatting: __word__ -> word
    text = re.sub(r'_+([^_]+)_+', r'\1', text)
    # Remove leading dashes/bullet points from list items
    text = re.sub(r'^\s*[-•]\s+', '', text, flags=re.MULTILINE)
    # Clean multiple consecutive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_quick_replies(raw_text: str) -> tuple[str, List[str]]:
    """
    Extract dynamic quick replies from the LLM output and return the cleaned text and reply list.
    """
    quick_replies = []
    text = raw_text

    match = re.search(r'QUICK_REPLIES:\s*(.+)$', raw_text, re.MULTILINE | re.IGNORECASE)
    if match:
        replies_str = match.group(1)
        # Extract options separated by |
        raw_options = replies_str.split('|')
        for opt in raw_options:
            cleaned = clean_plain_text(opt.strip("[] \t\n\r\"'"))
            if cleaned and len(cleaned) <= 45:
                quick_replies.append(cleaned)
        text = raw_text[:match.start()].strip()

    # Fallback smart contextual quick replies if LLM omitted them
    if not quick_replies:
        lower = text.lower()
        if any(w in lower for w in ["quad", "stretch", "walk", "exercise"]):
            quick_replies = ["How many reps? 🔢", "What if I feel tight? 🧘", "Got it, next activity! 👍"]
        elif any(w in lower for w in ["breath", "anxiety", "calm", "yoga", "stress"]):
            quick_replies = ["Let's do 4-7-8 Breathing 🧘", "I feel more relaxed now 💙", "What else helps nerves?"]
        elif any(w in lower for w in ["protein", "snack", "food", "nutrition"]):
            quick_replies = ["What snacks are best? 🍎", "When should I eat it? ⏱", "Sounds tasty! 😋"]
        else:
            quick_replies = ["Sounds good! 👍", "What's next for today? 🗓", "I have 5 mins ⏱"]

    return clean_plain_text(text), quick_replies[:4]


# =========================================================================
# 1. State Definition (Simple TypedDict)
# =========================================================================
class CoachState(TypedDict):
    patient_name: str
    procedure_name: str
    days_away: int
    user_message: str
    grounded_library_text: str
    available_options: List[Dict[str, Any]]
    is_safety_alert: bool
    risk_level: Optional[str]
    safety_trigger: Optional[str]
    safety_action: Optional[str]
    response_text: str
    suggested_options: Optional[List[Dict[str, Any]]]
    quick_replies: List[str]


# =========================================================================
# 2. Graph Nodes (Clean & Simple Single-Responsibility Functions)
# =========================================================================
def safety_triage_node(state: CoachState) -> Dict[str, Any]:
    """Node 1: Screen user message for clinical safety red flags."""
    safety_match = safety_service.screen_content(state["user_message"])
    if safety_match:
        trigger, risk_level, action = safety_match
        print(f"🚨 [LangGraph: Safety Triage] FLAGGED! Risk: {risk_level.upper()} | Trigger: '{trigger}'")
        return {
            "is_safety_alert": True,
            "risk_level": risk_level,
            "safety_trigger": trigger,
            "safety_action": action,
        }
    print("✅ [LangGraph: Safety Triage] SAFE (No clinical red flags detected)")
    return {"is_safety_alert": False, "risk_level": None, "safety_trigger": None, "safety_action": None}


def safety_escalation_node(state: CoachState) -> Dict[str, Any]:
    """Node 2: Formulate clinical escalation and emergency de-escalation response."""
    name = state["patient_name"]
    risk = state.get("risk_level", "high")
    trigger = state.get("safety_trigger", "symptoms")
    print(f"⚠️ [LangGraph: Escalation] Generating clinical safety response for {risk} risk")

    if risk == "critical":
        response_text = (
            f"🚨 {name}, this sounds like an urgent medical situation. "
            "Please stop all activity immediately and call 999 or go to your nearest A&E right away. "
            "I have logged this alert for your clinical care team."
        )
        quick_replies = ["I called 999 🚨", "I am sitting down to rest", "Alert my doctor"]
    elif risk == "high":
        response_text = (
            f"I'm so sorry you're experiencing {trigger}, {name}. "
            "Pain or symptoms like this are your body's signal to stop immediately. "
            "Please sit down, rest, and contact your surgical clinic or NHS 111 for clinical advice. "
            "I've flagged this in your clinical record so your care team is aware. 💙"
        )
        quick_replies = ["I have sat down to rest 🧘", "I will call NHS 111 📞", "I'm feeling a bit better"]
    else:
        response_text = (
            f"Recovery is all about listening to your body, {name}. "
            f"If you're feeling {trigger}, take a break and rest. "
            "If it persists, be sure to speak with your physiotherapist or clinical team."
        )
        quick_replies = ["I will take a break 👍", "What gentle stretches can I do?", "I feel okay now"]

    return {
        "response_text": clean_plain_text(response_text),
        "suggested_options": None,
        "quick_replies": quick_replies,
    }


def coaching_node(state: CoachState) -> Dict[str, Any]:
    """Node 3: Generate personalized, clinically-grounded Coach Amy response using LangChain LLM."""
    name = state["patient_name"]
    procedure = state["procedure_name"]
    days = state["days_away"]
    user_msg = state["user_message"]
    msg_lower = user_msg.lower()
    clinical_library = state.get("grounded_library_text", "")
    db_options = state.get("available_options", [])

    # Check if the user is asking for activity options, low energy, schedule, or surprises
    option_keywords = [
        "energy", "low", "tired", "light", "gentle", "exhausted", "lazy",
        "surprise", "recommend", "activity", "activities", "exercise", "routine",
        "schedule", "today", "plan", "options", "what should i do", "what am i working on",
        "workout", "stretch", "mins", "minute"
    ]
    should_show_options = any(w in msg_lower for w in option_keywords)
    suggested_options = db_options if should_show_options else None

    # 1. Primary Generation: LangChain LLM Grounded Inference (Gemma 4 via Ollama)
    if llm:
        try:
            print(f"🧠 [LangGraph: Coaching] Invoking LangChain LLM ({OLLAMA_MODEL}) with grounded context...")
            prompt_context = (
                f"Patient Profile: {name} (Preparing for {procedure} in {days} days).\n\n"
                f"Approved Clinical Content & Physiological Rationales (From Database):\n"
                f"{clinical_library}\n\n"
                f"Patient says: \"{user_msg}\""
            )

            prompt_messages = [
                SystemMessage(content=AMY_SYSTEM_PROMPT),
                HumanMessage(content=prompt_context),
            ]

            ai_reply = llm.invoke(prompt_messages)
            if ai_reply and ai_reply.content:
                reply_text, dynamic_replies = extract_quick_replies(str(ai_reply.content).strip())
                print(f"✨ [LangGraph: Coaching] LLM Generated Response ({len(reply_text)} chars) with {len(dynamic_replies)} dynamic replies")
                return {
                    "response_text": reply_text,
                    "suggested_options": suggested_options,
                    "quick_replies": dynamic_replies,
                }
        except Exception as e:
            print(f"⚠️ [LangChain LLM Fallback] {e}")

    # 2. Resilient Fallback: Grounded Dynamic Database Template
    print("📝 [LangGraph: Coaching] Using Grounded DB Fallback Template...")
    if "surprise" in msg_lower or any(w in msg_lower for w in ["energy", "low", "tired", "light", "gentle"]):
        response_text = (
            f"Great attitude, {name}! Since today's a lower-energy day, I've switched up your options to keep things light. "
            "Pick what feels best—something to stretch, move, or just reset. 💙"
        )
        quick_replies = ["Gentle stretch sounds great! 🧘", "I'll do the 15 min walk 🚶", "Can we do 5 mins? ⏱"]
    elif any(w in msg_lower for w in ["done", "completed", "finished", "did my", "walked"]):
        response_text = (
            f"Fantastic job completing your preparation, {name}! 🎉 "
            f"Every bit of daily consistency adds up. You're {days} days away from your {procedure}, "
            "and your body is getting stronger and more prepared every day. How are you feeling right now?"
        )
        quick_replies = ["Feeling good! 😊", "A bit sore but okay", "What's my next task? 📋"]
    else:
        response_text = (
            f"Hello {name}! I'm here to support and guide your recovery journey. "
            f"With your {procedure} {days} days away, consistent pre-operative preparation builds joint stability and smooths post-op recovery. "
            "What can I help you with today? 🌟"
        )
        quick_replies = ["What is the point of quad sets? 💡", "Show me today's routine 🗓", "Surprise me! 🎁"]

    return {
        "response_text": clean_plain_text(response_text),
        "suggested_options": suggested_options,
        "quick_replies": quick_replies,
    }


# =========================================================================
# 3. Graph Assembly (Simple & Explicit)
# =========================================================================
def route_safety(state: CoachState) -> str:
    """Conditional routing based on safety alert detection."""
    return "safety_escalation" if state.get("is_safety_alert") else "coaching"


def build_coach_graph():
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(CoachState)

    # Add Nodes
    graph.add_node("safety_triage", safety_triage_node)
    graph.add_node("safety_escalation", safety_escalation_node)
    graph.add_node("coaching", coaching_node)

    # Add Edges
    graph.add_edge(START, "safety_triage")
    graph.add_conditional_edges(
        "safety_triage",
        route_safety,
        {
            "safety_escalation": "safety_escalation",
            "coaching": "coaching",
        },
    )
    graph.add_edge("safety_escalation", END)
    graph.add_edge("coaching", END)

    return graph.compile()


# =========================================================================
# 4. Service Wrapper
# =========================================================================
class AmyCoachService:
    """Intelligent AI Recovery Coach 'Amy' engine."""

    def __init__(self) -> None:
        self.graph = build_coach_graph()

    def generate_coach_response(
        self,
        session: Session,
        patient: Patient,
        conversation: Conversation,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Execute Coach Amy's response via the compiled LangGraph pipeline.
        Pulls all content dynamically from the SQLite clinical database.
        """
        print(f"\n💬 [Coach Amy Pipeline] Incoming from Patient: '{user_message}'")

        # Calculate days away
        days_away = 21
        if patient.procedure_date:
            now = datetime.now(timezone.utc)
            proc_date = patient.procedure_date
            if proc_date.tzinfo is None:
                proc_date = proc_date.replace(tzinfo=timezone.utc)
            days_diff = (proc_date.date() - now.date()).days
            days_away = max(0, days_diff)

        # 1. Build grounded clinical knowledge library text directly from SQLite
        all_content = session.exec(select(ClinicalContent)).all()
        library_lines = []
        for c in all_content:
            library_lines.append(f"- {c.title} ({c.type.capitalize()}): {c.description}\n  Clinical Rationale: {c.rationale}")
        grounded_library_text = "\n\n".join(library_lines)

        # 2. Build activity options dynamically from SQLite recommendations & clinical content
        available_options = []
        rec_statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == patient.id)
            .order_by(Recommendation.scheduled_date.asc())
        )
        rec_results = session.exec(rec_statement).all()

        if rec_results:
            for rec, c in rec_results:
                available_options.append({
                    "id": f"content-{c.id}",
                    "title": c.title,
                    "subtitle": c.description,
                    "durationMinutes": rec.duration_minutes,
                    "durationLabel": f"{rec.duration_minutes} minutes",
                    "intensity": "Low" if c.type in ["mindfulness", "nutrition"] else "Medium",
                    "imageUri": c.image_url,
                    "tag": c.type.capitalize(),
                })
        else:
            for c in all_content:
                duration = 10
                if "5" in c.description or "breathing" in c.title.lower():
                    duration = 5
                elif "20" in c.description:
                    duration = 20

                available_options.append({
                    "id": f"content-{c.id}",
                    "title": c.title,
                    "subtitle": c.description,
                    "durationMinutes": duration,
                    "durationLabel": f"{duration} minutes",
                    "intensity": "Low" if c.type in ["mindfulness", "nutrition"] else "Medium",
                    "imageUri": c.image_url,
                    "tag": c.type.capitalize(),
                })

        # Add surprise option card
        available_options.append({
            "id": "content-surprise",
            "title": "Surprise Me! 🎁",
            "subtitle": "Let's See What You Get",
            "imageUri": "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?auto=format&fit=crop&w=300&q=80",
            "isSpecial": True,
        })

        # Execute through compiled LangGraph
        initial_state: CoachState = {
            "patient_name": patient.name or "Sarah",
            "procedure_name": patient.procedure or "Knee Surgery",
            "days_away": days_away,
            "user_message": user_message,
            "grounded_library_text": grounded_library_text,
            "available_options": available_options,
            "is_safety_alert": False,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }

        result_state: CoachState = self.graph.invoke(initial_state)

        # If safety alert triggered, record to SQLite database for clinician triage
        if result_state.get("is_safety_alert"):
            safety_service.record_event(
                session=session,
                conversation_id=conversation.id,
                patient_id=patient.id,
                trigger=result_state.get("safety_trigger", "safety_alert"),
                risk_level=result_state.get("risk_level", "high"),
                action=result_state.get("safety_action", "Alert care team and advise rest"),
            )

        final_clean_text = clean_plain_text(result_state["response_text"])
        print(f"📤 [Coach Amy Response Ready] Clean text length: {len(final_clean_text)} chars | Options: {bool(result_state.get('suggested_options'))} | Replies: {result_state.get('quick_replies')}\n")

        return {
            "text": final_clean_text,
            "is_safety_alert": result_state.get("is_safety_alert", False),
            "risk_level": result_state.get("risk_level"),
            "options": result_state.get("suggested_options"),
            "quick_replies": result_state.get("quick_replies", []),
        }


amy_service = AmyCoachService()
coach_service = amy_service  # Alias for compatibility
