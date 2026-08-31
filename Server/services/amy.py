import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlmodel import Session, select

from models.clinical_content import ClinicalContent
from models.conversation import Conversation
from models.patient import Patient
from models.recommendation import Recommendation
from services.safety_service import safety_service
from services.recommendation_service import recommendation_service

# Initialize Langfuse Observability
try:
    from dotenv import load_dotenv
    load_dotenv()
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    langfuse_client = Langfuse()
except Exception:
    def observe(*args, **kwargs):
        def decorator(f):
            return f
        return decorator
    langfuse_context = None
    langfuse_client = None

# Initialize LangChain Chat Model (Gemma 4 via Ollama)
try:
    from langchain_ollama import ChatOllama
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.4, timeout=10)
except Exception:
    llm = None


AMY_SYSTEM_PROMPT = """You are Amy, an empathetic, encouraging, and clinically-grounded AI Recovery Coach at Clovo.
You are assisting surgical and wellness patients.

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
3. Celebrate completed tasks and progress milestones with enthusiasm.
4. Keep responses concise, supportive, and easy to read on mobile.

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
# 1. State Definition (TypedDict)
# =========================================================================
class CoachState(TypedDict):
    patient_id: int
    patient_name: str
    procedure_name: str
    days_away: Optional[int]
    user_message: str
    conversation_history: List[Dict[str, str]]
    grounded_library_text: str
    available_options: List[Dict[str, Any]]
    active_recommendations: List[Dict[str, Any]]
    # Safety triage fields
    is_safety_alert: bool
    safety_category: Optional[str]
    risk_level: Optional[str]
    safety_trigger: Optional[str]
    safety_action: Optional[str]
    # Task completion intent fields
    is_task_completion: bool
    completed_activity_name: Optional[str]
    completed_task: Optional[Dict[str, Any]]
    # Output fields
    response_text: str
    suggested_options: Optional[List[Dict[str, Any]]]
    quick_replies: List[str]


# =========================================================================
# 2. Graph Nodes
# =========================================================================
@observe(name="safety_triage")
def safety_triage_node(state: CoachState) -> Dict[str, Any]:
    """Node 1: Screen user message for clinical safety using semantic intent classifier."""
    triage = safety_service.screen_message_semantic(
        user_message=state["user_message"],
        conversation_history=state.get("conversation_history", []),
        llm_instance=llm,
    )
    if triage.get("is_safety_alert"):
        category = triage.get("category", "acute_medical")
        risk = triage.get("risk_level", "high")
        trigger = triage.get("trigger", "Clinical safety issue detected")
        action = triage.get("action", "Alert care team and advise rest")
        print(f"🚨 [LangGraph: Safety Triage] FLAGGED! Category: {category.upper()} | Risk: {str(risk).upper()} | Trigger: '{trigger}'")
        return {
            "is_safety_alert": True,
            "safety_category": category,
            "risk_level": risk,
            "safety_trigger": trigger,
            "safety_action": action,
        }
    print("✅ [LangGraph: Safety Triage] SAFE (No clinical red flags detected)")
    return {
        "is_safety_alert": False,
        "safety_category": "safe",
        "risk_level": None,
        "safety_trigger": None,
        "safety_action": None,
    }


@observe(name="safety_escalation")
def safety_escalation_node(state: CoachState) -> Dict[str, Any]:
    """Node 2: Formulate customized clinical escalation and de-escalation response."""
    name = state["patient_name"]
    category = state.get("safety_category", "acute_medical")
    risk = state.get("risk_level", "high")
    trigger = state.get("safety_trigger", "your symptoms")
    print(f"⚠️ [LangGraph: Escalation] Generating clinical safety response for category='{category}', risk='{risk}'")

    if category == "mental_health" or risk == "critical":
        response_text = (
            f"🚨 {name}, I hear how overwhelmed you are feeling, and your safety is the absolute top priority right now. "
            "Please stop all activity and reach out for immediate support. "
            "You can call 999 for emergency help, call 111 for urgent mental health support, or call Samaritans free on 116 123 (available 24/7). "
            "I have also flagged an urgent alert for your clinical care team."
        )
        quick_replies = ["I called 999 / 111 🚨", "I am sitting down to rest", "Alert my doctor"]

    elif category == "acute_medical":
        response_text = (
            f"I'm so sorry you're experiencing this with {trigger}, {name}. "
            "Because this could indicate an acute complication or injury, please stop all physical exercises and activities immediately. "
            "Sit or lie down in a safe, comfortable position. Please contact your surgical clinic or call NHS 111 right away for clinical guidance. "
            "I have logged this alert in your clinical record so your care team is aware. 💙"
        )
        quick_replies = ["I have sat down to rest 🧘", "I will call NHS 111 📞", "I will call my clinic"]

    elif category == "severe_pain":
        response_text = (
            f"That sounds very painful, {name}. Sharp or severe pain is your body's signal to pause. "
            "Please stop your current exercises and rest your joint immediately without putting weight on it. "
            "If this is new or worsening pain that doesn't ease after resting, please contact your surgical clinic or NHS 111. "
            "I have recorded this pain report for your care team. 💙"
        )
        quick_replies = ["I've stopped to rest 🧘", "It's new sharp pain", "I will call my clinic"]

    elif category == "clinical_decision":
        response_text = (
            f"I understand your concerns about your treatment, {name}, but as your AI Recovery Coach, I cannot make decisions about your medications or alter prescriptions. "
            "Stopping, discarding, or altering medications (like blood thinners or pain relief) can be dangerous and requires your doctor's explicit guidance. "
            "Please contact your primary care clinician or NHS 111 immediately to discuss how you're feeling and get safe medical guidance. "
            "I have notified your care team about your message so they can follow up with you."
        )
        quick_replies = ["I will call NHS 111 📞", "I will contact my doctor", "I will take a rest"]

    else:
        response_text = (
            f"Recovery is all about listening to your body, {name}. "
            f"If you're feeling {trigger}, please take a break and rest. "
            "If it persists, be sure to speak with your physiotherapist or clinical team."
        )
        quick_replies = ["I will take a break 👍", "What gentle stretches can I do?", "I feel okay now"]

    return {
        "response_text": clean_plain_text(response_text),
        "suggested_options": None,
        "quick_replies": quick_replies,
    }


@observe(name="intent_classification")
def intent_classification_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 3: Classify user intent for task completion vs general conversation.
    Accurately handles negations ('haven't done it yet') and semantic activity extraction.
    """
    user_msg = state["user_message"]
    msg_lower = user_msg.lower().strip()
    history = state.get("conversation_history", [])
    active_recs = state.get("active_recommendations", [])

    # 1. Negation detection
    negation_patterns = [
        "haven't", "have not", "didn't", "did not", "not yet", "not done",
        "couldn't", "could not", "can't", "unable to", "haven’t", "didn’t",
        "no i didn't", "no,"
    ]
    is_negated = any(p in msg_lower for p in negation_patterns)

    # 2. Affirmative completion phrases
    completion_triggers = [
        "done", "finished", "completed", "did my", "did the", "knocked out",
        "just finished", "all done", "marked as complete", "mark as complete",
        "i did it", "i did them", "i did", "yes i did", "yes completed", "yes finished",
        "yes", "yeah", "yep", "i did the quad", "i did quad", "i have completed",
        "i completed", "completed it"
    ]
    has_completion_intent = any(t in msg_lower for t in completion_triggers)

    if has_completion_intent and not is_negated:
        # Match activity entity
        matched_activity = None
        if "quad" in msg_lower:
            matched_activity = "Quad Sets"
        elif "leg" in msg_lower or "raise" in msg_lower:
            matched_activity = "Straight Leg Raise"
        elif "snack" in msg_lower or "protein" in msg_lower:
            matched_activity = "Protein Power Snack"
        elif "breath" in msg_lower:
            matched_activity = "4-7-8 Breathing"
        elif "all" in msg_lower or "everything" in msg_lower or "both" in msg_lower:
            matched_activity = "all"
        else:
            # Check if previous coach message asked about a specific exercise
            if history:
                last_coach_msg = next((m.get("content", "").lower() for m in reversed(history) if m.get("role") in ["coach", "assistant"]), "")
                if "quad" in last_coach_msg:
                    matched_activity = "Quad Sets"
                elif "leg" in last_coach_msg or "raise" in last_coach_msg:
                    matched_activity = "Straight Leg Raise"
                elif "snack" in last_coach_msg or "protein" in last_coach_msg:
                    matched_activity = "Protein Power Snack"
                elif "breath" in last_coach_msg:
                    matched_activity = "4-7-8 Breathing"

            if not matched_activity and active_recs:
                matched_activity = active_recs[0].get("title", "Quad Sets")

        print(f"🎯 [LangGraph: Intent] Task completion confirmed for activity='{matched_activity}'")
        return {
            "is_task_completion": True,
            "completed_activity_name": matched_activity,
        }

    return {
        "is_task_completion": False,
        "completed_activity_name": None,
    }


@observe(as_type="generation", name="coach_amy_llm_inference")
def invoke_coach_llm(prompt_messages: List[Any], model_name: str) -> Optional[str]:
    """Invoke Ollama LLM and record Generation metrics in Langfuse."""
    if not llm:
        return None

    prompt_str = "\n".join([str(m.content) for m in prompt_messages])
    ai_reply = llm.invoke(prompt_messages)
    if ai_reply and ai_reply.content:
        content = str(ai_reply.content).strip()
        if langfuse_context:
            try:
                input_tokens = max(1, len(prompt_str.split()))
                output_tokens = max(1, len(content.split()))
                langfuse_context.update_current_observation(
                    model=model_name,
                    input={"prompt": prompt_str},
                    output=content,
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens,
                        "unit": "TOKENS",
                    },
                )
            except Exception:
                pass
        return content
    return None


@observe(name="amy_coaching")
def coaching_node(state: CoachState) -> Dict[str, Any]:
    """
    Generate grounded, empathetic coaching response using SQLite knowledge library.
    Celebrates completed tasks and falls back gracefully to rich grounded templates.
    """
    name = state["patient_name"]
    procedure = state["procedure_name"]
    days = state["days_away"]
    user_msg = state["user_message"]
    msg_lower = user_msg.lower()
    clinical_library = state.get("grounded_library_text", "")
    db_options = state.get("available_options", [])
    completed_task = state.get("completed_task")

    time_context = f"in {days} days" if days is not None else "in your recovery journey"

    # Check if the user is asking for activity options
    option_keywords = [
        "energy", "low", "tired", "light", "gentle", "exhausted", "lazy",
        "surprise", "recommend", "activity", "activities", "exercise", "routine",
        "schedule", "today", "plan", "options", "what should i do", "what am i working on",
        "workout", "stretch", "mins", "minute"
    ]
    should_show_options = any(w in msg_lower for w in option_keywords)
    suggested_options = db_options if should_show_options else None

    # Handle explicit task completion celebration
    if completed_task:
        task_title = completed_task.get("title", "your recovery routine")
        if llm:
            try:
                prompt_context = (
                    f"Patient Profile: {name} (Preparing for {procedure} {time_context}).\n"
                    f"EVENT: The patient has just confirmed completing their routine: '{task_title}'.\n"
                    f"Approved Clinical Content & Physiological Rationales:\n{clinical_library}\n\n"
                    f"INSTRUCTIONS: Enthusiastically celebrate their achievement in 2-3 warm, clear sentences. "
                    f"Explain how completing {task_title} helps their surgical recovery, and ask how they're feeling or suggest their next step."
                )
                prompt_messages: List[Any] = [
                    SystemMessage(content=AMY_SYSTEM_PROMPT),
                    HumanMessage(content=prompt_context),
                    HumanMessage(content=f"Patient says: \"{user_msg}\""),
                ]
                llm_text = invoke_coach_llm(prompt_messages, OLLAMA_MODEL)
                if llm_text:
                    reply_text, dynamic_replies = extract_quick_replies(llm_text)
                    return {
                        "response_text": reply_text,
                        "suggested_options": None,
                        "quick_replies": dynamic_replies or ["What's my next task? 📋", "Feeling good! 😊", "How did that help me? 💡"],
                    }
            except Exception as e:
                print(f"⚠️ [LangChain LLM Completion Fallback] {e}")

        # Deterministic Grounded Celebration Fallback
        response_text = (
            f"Awesome job, {name}! 🎉 I've marked {task_title} as completed in your daily recovery checklist. "
            f"Every bit of preparation strengthens your body and brings you one step closer to a smooth {procedure} recovery 💙. "
            "How are you feeling right now?"
        )
        return {
            "response_text": clean_plain_text(response_text),
            "suggested_options": None,
            "quick_replies": ["Feeling good! 😊", "A bit tired but okay 👍", "What's my next task? 📋"],
        }

    # 1. Primary LLM Grounded Generation
    if llm:
        try:
            prompt_context = (
                f"Patient Profile: {name} (Preparing for {procedure} {time_context}).\n\n"
                f"Approved Clinical Content & Physiological Rationales (From Database):\n"
                f"{clinical_library}"
            )
            prompt_messages = [
                SystemMessage(content=AMY_SYSTEM_PROMPT),
                HumanMessage(content=prompt_context),
            ]

            history = state.get("conversation_history", [])
            if history:
                for turn in history[-6:]:
                    role = turn.get("role", "user")
                    content = turn.get("content", "")
                    if content and content != user_msg:
                        if role == "user":
                            prompt_messages.append(HumanMessage(content=content))
                        elif role in ["coach", "assistant"]:
                            prompt_messages.append(AIMessage(content=content))

            prompt_messages.append(HumanMessage(content=f"Patient says: \"{user_msg}\""))

            llm_text = invoke_coach_llm(prompt_messages, OLLAMA_MODEL)
            if llm_text:
                reply_text, dynamic_replies = extract_quick_replies(llm_text)
                return {
                    "response_text": reply_text,
                    "suggested_options": suggested_options,
                    "quick_replies": dynamic_replies,
                }
        except Exception as e:
            print(f"⚠️ [LangChain LLM Fallback] {e}")

    # 2. Grounded DB Fallback Template
    if "surprise" in msg_lower or any(w in msg_lower for w in ["energy", "low", "tired", "light", "gentle"]):
        response_text = (
            f"Great attitude, {name}! Since today's a lower-energy day, I've switched up your options to keep things light. "
            "Pick what feels best—something to stretch, move, or just reset. 💙"
        )
        quick_replies = ["Gentle stretch sounds great! 🧘", "I'll do the 15 min walk 🚶", "Can we do 5 mins? ⏱"]
    else:
        time_msg = f"With your {procedure} {days} days away, consistent" if days is not None else f"For your {procedure} preparation, consistent"
        response_text = (
            f"Hello {name}! I'm here to support and guide your recovery journey. "
            f"{time_msg} pre-operative preparation builds joint stability and smooths post-op recovery. "
            "What can I help you with today? 🌟"
        )
        quick_replies = ["What is the point of quad sets? 💡", "Show me today's routine 🗓", "Surprise me! 🎁"]

    return {
        "response_text": clean_plain_text(response_text),
        "suggested_options": suggested_options,
        "quick_replies": quick_replies,
    }


# =========================================================================
# 3. Graph Assembly
# =========================================================================
def route_safety(state: CoachState) -> str:
    """Conditional routing based on safety alert detection."""
    return "safety_escalation" if state.get("is_safety_alert") else "intent_classification"


def build_coach_graph():
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(CoachState)

    # Add Nodes
    graph.add_node("safety_triage", safety_triage_node)
    graph.add_node("safety_escalation", safety_escalation_node)
    graph.add_node("intent_classification", intent_classification_node)
    graph.add_node("coaching", coaching_node)

    # Add Edges
    graph.add_edge(START, "safety_triage")
    graph.add_conditional_edges(
        "safety_triage",
        route_safety,
        {
            "safety_escalation": "safety_escalation",
            "intent_classification": "intent_classification",
        },
    )
    graph.add_edge("intent_classification", "coaching")
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

    @observe(name="coach_amy_response")
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

        # Enrich Langfuse trace with session, user, and clinical tags
        if langfuse_context:
            try:
                langfuse_context.update_current_trace(
                    name=f"Amy Coaching Session: {patient.name or 'Sarah'}",
                    session_id=f"conv-{conversation.id}",
                    user_id=f"patient-{patient.id}",
                    tags=["amy_coach", patient.procedure or "wellness", f"phase_{patient.phase or 'active'}"],
                    metadata={
                        "patient_id": patient.id,
                        "patient_name": patient.name,
                        "conversation_id": conversation.id,
                        "procedure": patient.procedure,
                        "procedure_date": str(patient.procedure_date) if patient.procedure_date else None,
                    },
                )
                langfuse_context.update_current_observation(
                    input={"user_message": user_message}
                )
            except Exception:
                pass

        days_away: Optional[int] = None
        if patient.procedure_date:
            now = datetime.now(timezone.utc)
            proc_date = patient.procedure_date
            if proc_date.tzinfo is None:
                proc_date = proc_date.replace(tzinfo=timezone.utc)
            days_diff = (proc_date.date() - now.date()).days
            days_away = max(0, days_diff)

        # 1. Build grounded clinical knowledge library text
        all_content = session.exec(select(ClinicalContent)).all()
        library_lines = []
        for c in all_content:
            library_lines.append(f"- {c.title} ({c.type.capitalize()}): {c.description}\n  Clinical Rationale: {c.rationale}")
        grounded_library_text = "\n\n".join(library_lines)

        # 2. Build activity options and active recommendations
        available_options = []
        active_recommendations = []
        rec_statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == patient.id)
            .order_by(Recommendation.scheduled_date.asc())
        )
        rec_results = session.exec(rec_statement).all()

        if rec_results:
            for rec, c in rec_results:
                is_completed = (rec.status == "completed")
                if not is_completed:
                    active_recommendations.append({
                        "id": rec.id,
                        "title": c.title,
                        "type": c.type,
                        "duration": rec.duration_minutes,
                    })

                available_options.append({
                    "id": f"content-{c.id}",
                    "recommendationId": rec.id,
                    "title": c.title,
                    "subtitle": c.description,
                    "durationMinutes": rec.duration_minutes,
                    "durationLabel": f"{rec.duration_minutes} minutes",
                    "intensity": "Low" if c.type in ["mindfulness", "nutrition"] else "Medium",
                    "imageUri": c.image_url,
                    "tag": c.type.capitalize(),
                    "isCompleted": is_completed,
                })

        # Add surprise option card
        available_options.append({
            "id": "content-surprise",
            "title": "Surprise Me! 🎁",
            "subtitle": "Let's See What You Get",
            "imageUri": "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?auto=format&fit=crop&w=300&q=80",
            "isSpecial": True,
            "isCompleted": False,
        })

        # 3. Load persistent multi-turn conversation history
        from services.conversation_service import conversation_service
        raw_history = conversation_service.get_messages(session, conversation.id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in raw_history[:-1] if msg.content
        ]

        # Execute through compiled LangGraph
        initial_state: CoachState = {
            "patient_id": patient.id,
            "patient_name": patient.name or "Sarah",
            "procedure_name": patient.procedure or "Knee Surgery",
            "days_away": days_away,
            "user_message": user_message,
            "conversation_history": conversation_history,
            "grounded_library_text": grounded_library_text,
            "available_options": available_options,
            "active_recommendations": active_recommendations,
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "completed_task": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }

        result_state: CoachState = self.graph.invoke(initial_state)

        # If task completion intent was identified, execute database mutation
        completed_task_info = None
        if result_state.get("is_task_completion") and not result_state.get("is_safety_alert"):
            act_name = result_state.get("completed_activity_name")
            updated_rec = recommendation_service.mark_task_completed(
                session=session,
                patient_id=patient.id,
                activity_name=act_name,
            )
            if updated_rec:
                # Find matching content title
                content_obj = session.get(ClinicalContent, updated_rec.content_id)
                completed_task_info = {
                    "taskId": updated_rec.id,
                    "title": content_obj.title if content_obj else act_name,
                    "isCompleted": True,
                }
                print(f"💾 [Database Updated] Recommendation #{updated_rec.id} marked COMPLETED for patient {patient.id}")

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
        print(f"📤 [Coach Amy Response Ready] Clean text length: {len(final_clean_text)} chars | Completed Task: {completed_task_info}\n")

        # Record automated evaluation scores into Langfuse
        if langfuse_context:
            try:
                is_safe = not result_state.get("is_safety_alert", False)
                langfuse_context.score_current_trace(
                    name="safety_score",
                    value=1.0 if is_safe else 0.0,
                    comment="Safety triage check passed" if is_safe else f"Safety Alert: {result_state.get('safety_trigger')}",
                )
                langfuse_context.score_current_trace(
                    name="clinical_grounding",
                    value=1.0 if grounded_library_text else 0.5,
                )
                langfuse_context.update_current_observation(
                    output={
                        "response_text": final_clean_text,
                        "is_safety_alert": result_state.get("is_safety_alert", False),
                        "completed_task": completed_task_info,
                        "quick_replies": result_state.get("quick_replies", []),
                    }
                )
                langfuse_context.flush()
            except Exception:
                pass

        return {
            "text": final_clean_text,
            "is_safety_alert": result_state.get("is_safety_alert", False),
            "risk_level": result_state.get("risk_level"),
            "options": result_state.get("suggested_options"),
            "quick_replies": result_state.get("quick_replies", []),
            "completed_task": completed_task_info,
        }


amy_service = AmyCoachService()
coach_service = amy_service  # Alias for compatibility
