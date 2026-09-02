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
    # pyrefly: ignore [missing-import]
    from langchain_openai import ChatOpenAI
    GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model=GPT_MODEL, api_key=OPENAI_API_KEY, temperature=0.4, timeout=15)
except Exception:
    llm = None

# try:
#     from langchain_ollama import ChatOllama
#     OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")
#     OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
#     llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.4, timeout=10)
# except Exception:
#     llm = None


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
1. Explain the patient's approved daily recommendations and the physiological 
"Why" using ONLY the clinical library and rationales provided in context.
2. Provide warm encouragement, empathy, and positive reinforcement.
3. Celebrate completed tasks and progress milestones with enthusiasm.
4. Support emotional adherence: When patients feel sad, down, unmotivated, or overwhelmed, provide genuine human empathy, validate their feelings without judgment, remove guilt, and offer gentle restorative options (like 4-7-8 breathing or rest).
5. Keep responses concise, supportive, and easy to read on mobile.

STRICT CLINICAL BOUNDARIES (DO NOT VIOLATE):
1. NEVER invent unapproved exercises, diets, medications, or alternative treatments.
2. NEVER alter prescribed durations or repetitions.
3. NEVER diagnose medical conditions or say "You have a tear/infection".
4. NEVER tell a patient to push through pain, dizziness, or abnormal symptoms.
5. If the user asks for unapproved medical advice, politely explain that you can 
only guide approved routines and advise them to consult their clinician.

SAFETY PROTOCOL:
If the user mentions dizziness, sharp pain, fever, chest pain, or bleeding:
- Instruct them to stop the activity immediately and rest.
- Direct severe emergencies to 999 or NHS 111.
"""


def clean_plain_text(text: str) -> str:
    """
    Sanitize text to remove markdown formatting symbols (**, *, ###, __, ——)
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
    # Remove markdown horizontal rules and long dividers: ---, ___, ——, ───
    text = re.sub(r'^\s*[-_—─]{2,}\s*$', '', text, flags=re.MULTILINE)
    # Remove leading dashes/bullet points/em-dashes from list items
    text = re.sub(r'^\s*[-•—–]\s+', '', text, flags=re.MULTILINE)
    # Clean multiple consecutive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_quick_replies(
    raw_text: str,
    active_recommendations: Optional[List[Dict[str, Any]]] = None,
    is_emotional_support: bool = False,
) -> tuple[str, List[str]]:
    """
    Extract dynamic quick replies from the LLM output and return the cleaned text and reply list.
    Falls back dynamically to the patient's real assigned database tasks instead of hardcoded keywords.
    """
    quick_replies = []
    text = raw_text

    # 1. Flexible regex to extract whatever dynamic options the LLM returned
    match = re.search(r'(?:QUICK_REPLIES|SUGGESTED_QUESTIONS|OPTIONS):\s*(.+)$', raw_text, re.MULTILINE | re.IGNORECASE)
    if match:
        replies_str = match.group(1)
        raw_options = replies_str.split('|') if '|' in replies_str else replies_str.split(',')
        for opt in raw_options:
            cleaned = clean_plain_text(opt.strip("[] \t\n\r\"'"))
            if cleaned and len(cleaned) <= 45:
                quick_replies.append(cleaned)
        text = raw_text[:match.start()].strip()

    # 2. Emotional support fallback
    if not quick_replies and is_emotional_support:
        quick_replies = [
            "I'll take a rest day 🧘",
            "Guide me in 4-7-8 breathing 🌬️",
            "Tell me about my progress 🌟",
            "Thank you Amy 💙"
        ]

    # 3. Database-Driven Fallback: Grounded in patient's actual pending tasks from SQLite
    if not quick_replies and active_recommendations:
        pending_titles = [rec.get("title", "") for rec in active_recommendations if rec.get("title")]
        if pending_titles:
            first_task = pending_titles[0]
            quick_replies = [
                f"How do I do {first_task}?",
                f"Why is {first_task} helpful?",
                "What's my next task? 📋",
                "I'm feeling a bit tired 🥱"
            ]

    # 4. Universal graceful conversational fallback
    if not quick_replies:
        quick_replies = ["What's my next task? 📋", "Why is this recommended? 💡", "Sounds good! 👍"]

    return clean_plain_text(text), quick_replies[:4]


from services.response_validator import response_validator

# =========================================================================
# 1. State Definition (TypedDict)
# =========================================================================
class CoachState(TypedDict):
    session: Any
    patient_id: int
    patient_name: str
    procedure_name: str
    days_away: Optional[int]
    user_message: str
    conversation_history: List[Dict[str, str]]
    grounded_library_text: str
    daily_tasks_summary: str
    available_options: List[Dict[str, Any]]
    active_recommendations: List[Dict[str, Any]]
    # Safety triage fields
    is_safety_alert: bool
    safety_category: Optional[str]
    risk_level: Optional[str]
    safety_trigger: Optional[str]
    safety_action: Optional[str]
    # Task completion / unmarking / options intent fields
    is_task_completion: bool
    completed_activity_name: Optional[str]
    is_task_unmark: bool
    unmarked_activity_name: Optional[str]
    should_show_options: bool
    completed_task_info: Optional[Any]
    # Adherence & Milestone fields
    adherence_context: Optional[str]
    milestones_summary: Optional[str]
    # Output & Validation fields
    response_text: str
    suggested_options: Optional[List[Dict[str, Any]]]
    quick_replies: List[str]
    validation_passed: bool
    validation_flags: List[str]





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


import json

# Prompt template for LLM-based intent classification
INTENT_CLASSIFICATION_PROMPT = """You are a clinical intent classifier for a patient recovery app.

Given the patient's message and the list of their assigned activities, classify the intent as ONE of:
- "completion": The patient is confirming they completed an activity (e.g. "I did my quad sets", "finished!", "done", "I'm done with that also", "did that too")
- "unmark": The patient is saying they did NOT do an activity, or wants to undo/reset it (e.g. "I haven't done it", "I didn't complete that", "undo", "reset my tasks")
- "view_plan": The patient explicitly wants to see, browse, or explore their schedule, tasks, plan, or recovery activity cards (e.g. "What's my plan for today?", "show me my tasks", "show options", "what routines do I have?", "what should I do now?", "what am I working on today?")
- "general": Any other general question, technique explanation, greeting, emotional support/motivation, or comment

Also extract which activity they are referring to. Use EXACTLY one of these values:
{activity_names}
- Use "all" if they refer to all/every/none of their tasks (e.g. "I haven't done any of them", "completed everything")
- If the patient refers to "that", "it", or does not repeat the activity name (e.g. "I'm done with that also", "finished that too", "done!"), resolve it to the specific activity discussed in the Recent conversation context.
- Use null ONLY if no activity can be inferred or the intent is "view_plan" or "general".

Recent conversation context (last coach message):
{last_coach_message}

Patient message: "{user_message}"

Respond with ONLY valid JSON, no other text:
{{"intent": "completion" | "unmark" | "view_plan" | "general", "activity": "<exact activity name>" | "all" | null}}"""


@observe(name="intent_classification")
def intent_classification_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 3: Classify user intent using the LLM for robust understanding of
    task completion, unmarking/reset, plan viewing, and general conversation.
    Falls back to lightweight heuristics if the LLM is unavailable.
    """
    user_msg = state["user_message"]
    msg_lower = user_msg.lower().strip()
    active_recs = state.get("active_recommendations", [])
    history = state.get("conversation_history", [])

    # Explicit plan viewing phrases (used only as fallback when LLM is offline)
    explicit_plan_phrases = [
        "what's my plan", "whats my plan", "what is my plan", "my plan today",
        "show me my tasks", "show my tasks", "show tasks", "my tasks",
        "show options", "show my options", "show activities", "show my activities",
        "show routine", "show routines", "show my routine", "show my routines",
        "what should i do", "what am i working on", "view plan", "view tasks",
        "what's on my schedule", "whats on my schedule", "what is on my schedule",
        "show today's routine", "show todays routine", "surprise me"
    ]
    is_explicit_plan_request = any(p in msg_lower for p in explicit_plan_phrases)

    # Build known activity names from recommendations
    known_activities = [rec.get("title", "") for rec in active_recs if rec.get("title")]
    for opt in state.get("available_options", []):
        title = opt.get("title", "")
        if title and title not in known_activities and not opt.get("isSpecial"):
            known_activities.append(title)

    activity_names_str = "\n".join(f'- "{name}"' for name in known_activities) if known_activities else '- (no activities assigned)'

    last_coach_msg = ""
    if history:
        last_coach_msg = next(
            (m.get("content", "")[:200] for m in reversed(history) if m.get("role") in ["coach", "assistant"]),
            ""
        )

    if llm:
        try:
            prompt = INTENT_CLASSIFICATION_PROMPT.format(
                activity_names=activity_names_str,
                last_coach_message=last_coach_msg or "(none)",
                user_message=user_msg,
            )
            response = llm.invoke([
                SystemMessage(content="You are a precise JSON classifier. Output ONLY valid JSON."),
                HumanMessage(content=prompt),
            ])

            if response and response.content:
                raw = str(response.content).strip()
                if raw.startswith("```"):
                    raw = re.sub(r'^```(?:json)?\s*', '', raw)
                    raw = re.sub(r'\s*```$', '', raw)

                parsed = json.loads(raw)
                intent = parsed.get("intent", "general")
                activity = parsed.get("activity")

                # Fallback context inference if intent is completion/unmark but activity came back null
                if intent == "completion" and not activity:
                    for act in known_activities:
                        if act.lower() in last_coach_msg.lower():
                            activity = act
                            break
                    if not activity and active_recs:
                        activity = active_recs[0].get("title")

                if intent == "unmark" and not activity:
                    for act in known_activities:
                        if act.lower() in last_coach_msg.lower():
                            activity = act
                            break

                # Intelligently show cards ONLY when the intent is explicitly view_plan
                should_show = (intent == "view_plan")

                if intent == "completion" and activity:
                    print(f"🎯 [LangGraph: Intent/LLM] Task completion confirmed for activity='{activity}'")
                    return {
                        "is_task_completion": True,
                        "completed_activity_name": activity,
                        "is_task_unmark": False,
                        "unmarked_activity_name": None,
                        "should_show_options": should_show,
                    }
                elif intent == "unmark" and activity:
                    print(f"🔄 [LangGraph: Intent/LLM] Task unmark/reset detected for activity='{activity}'")
                    return {
                        "is_task_completion": False,
                        "completed_activity_name": None,
                        "is_task_unmark": True,
                        "unmarked_activity_name": activity,
                        "should_show_options": should_show,
                    }
                else:
                    print(f"💬 [LangGraph: Intent/LLM] General / Plan intent: {intent} (Show Cards: {should_show})")
                    return {
                        "is_task_completion": False,
                        "completed_activity_name": None,
                        "is_task_unmark": False,
                        "unmarked_activity_name": None,
                        "should_show_options": should_show,
                    }
        except Exception as e:
            print(f"⚠️ [LangGraph: Intent] LLM classification error ({e}), falling back to heuristics")

    # Fallback to heuristics when LLM is unavailable
    heuristic = _heuristic_intent_classification(user_msg, active_recs, history)
    heuristic["should_show_options"] = is_explicit_plan_request
    return heuristic


def _heuristic_intent_classification(
    user_msg: str,
    active_recs: List[Dict[str, Any]],
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Fallback pattern-matching classifier used only when the LLM is unavailable."""
    msg_lower = user_msg.lower().strip()

    negation_signals = ["haven't", "have not", "didn't", "did not", "not yet", "not done",
                        "couldn't", "could not", "unmark", "reset", "undo", "cancel"]
    is_unmark = any(p in msg_lower for p in negation_signals)

    completion_signals = ["done", "finished", "completed", "did my", "did the",
                          "just finished", "all done", "i did", "i completed"]
    is_completion = any(t in msg_lower for t in completion_signals) and not is_unmark

    matched = None
    if "quad" in msg_lower:
        matched = "Quad Sets"
    elif "leg" in msg_lower or "raise" in msg_lower:
        matched = "Straight Leg Raise"
    elif "snack" in msg_lower or "protein" in msg_lower:
        matched = "Protein Power Snack"
    elif "breath" in msg_lower:
        matched = "4-7-8 Breathing"
    elif any(w in msg_lower for w in ["all", "everything", "every", "none of", "any of"]):
        matched = "all"
    elif history:
        for m in reversed(history):
            if m.get("role") in ["coach", "assistant"]:
                c_content = m.get("content", "").lower()
                if "quad" in c_content:
                    matched = "Quad Sets"
                elif "leg" in c_content:
                    matched = "Straight Leg Raise"
                elif "snack" in c_content or "protein" in c_content:
                    matched = "Protein Power Snack"
                elif "breath" in c_content:
                    matched = "4-7-8 Breathing"
                break

    if is_unmark and matched:
        return {
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": True,
            "unmarked_activity_name": matched,
        }
    elif is_completion and matched:
        return {
            "is_task_completion": True,
            "completed_activity_name": matched,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
        }
    return {
        "is_task_completion": False,
        "completed_activity_name": None,
        "is_task_unmark": False,
        "unmarked_activity_name": None,
    }


@observe(name="recommendation_action")
def recommendation_action_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 4: Execute deterministic recommendation state mutations inside the graph
    for task completions or unmarking.
    Updates the live checklist and active recommendations in CoachState before coaching generation.
    """
    session = state.get("session")
    patient_id = state["patient_id"]
    is_completion = state.get("is_task_completion", False)
    is_unmark = state.get("is_task_unmark", False)
    completed_task_info = None

    if not session or state.get("is_safety_alert"):
        return {"completed_task_info": None}

    # 1. Handle Task Completion
    if is_completion:
        act_name = state.get("completed_activity_name")
        updated_rec = recommendation_service.mark_task_completed(
            session=session,
            patient_id=patient_id,
            activity_name=act_name,
        )
        if updated_rec:
            content_obj = session.get(ClinicalContent, updated_rec.content_id)
            completed_task_info = {
                "taskId": updated_rec.id,
                "title": content_obj.title if content_obj else act_name,
                "isCompleted": True,
            }
            print(f"💾 [LangGraph RecommendationAction] Recommendation #{updated_rec.id} marked COMPLETED for patient {patient_id}")


    # 2. Handle Task Unmark / Reset
    elif is_unmark:
        act_name = state.get("unmarked_activity_name")
        result = recommendation_service.mark_task_active(
            session=session,
            patient_id=patient_id,
            activity_name=act_name,
        )
        reset_recs = result if isinstance(result, list) else ([result] if result else [])
        if reset_recs:
            completed_task_info = [
                {
                    "taskId": rec.id,
                    "title": (session.get(ClinicalContent, rec.content_id).title
                              if session.get(ClinicalContent, rec.content_id) else act_name),
                    "isCompleted": False,
                }
                for rec in reset_recs
            ]
            for rec in reset_recs:
                print(f"🔄 [LangGraph TaskAction] Recommendation #{rec.id} RESET to ACTIVE for patient {patient_id}")

    # 3. Refresh live task statuses in state if mutation occurred
    updates: Dict[str, Any] = {"completed_task_info": completed_task_info}
    if completed_task_info:
        rec_statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == patient_id)
            .order_by(Recommendation.scheduled_date.asc())
        )
        rec_results = session.exec(rec_statement).all()
        task_status_lines = []
        active_recs = []
        for rec, c in rec_results:
            is_comp = (rec.status == "completed")
            status_lbl = "COMPLETED ✅" if is_comp else "PENDING ⏳"
            task_status_lines.append(f"- {c.title}: {status_lbl} ({rec.duration_minutes} mins)")
            if not is_comp:
                active_recs.append({
                    "id": rec.id,
                    "title": c.title,
                    "type": c.type,
                    "duration": rec.duration_minutes,
                })
        updates["daily_tasks_summary"] = "\n".join(task_status_lines)
        updates["active_recommendations"] = active_recs

    return updates


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
    Node 5: Generate grounded, empathetic coaching response using SQLite knowledge library.
    Unified prompt assembly with full multi-turn conversation history across all intents.
    """
    name = state["patient_name"]
    procedure = state["procedure_name"]
    days = state["days_away"]
    user_msg = state["user_message"]
    clinical_library = state.get("grounded_library_text", "")
    daily_tasks = state.get("daily_tasks_summary", "")
    db_options = state.get("available_options", [])
    active_recs = state.get("active_recommendations", [])
    history = state.get("conversation_history", [])

    is_completion = state.get("is_task_completion", False)
    completed_task_name = state.get("completed_activity_name")
    is_unmark = state.get("is_task_unmark", False)
    unmarked_activity = state.get("unmarked_activity_name")
    should_show_options = state.get("should_show_options", False)

    time_context = f"in {days} days" if days is not None else "in your recovery journey"

    # Detect low mood, sadness, fatigue, or low motivation
    low_mood_signals = [
        "sad", "feeling sad", "really sad", "down", "feeling down", "unmotivated",
        "no motivation", "don't feel like", "dont feel like", "lazy", "feel lazy",
        "discouraged", "hard day", "crying", "feel like crying", "overwhelmed",
        "exhausted", "giving up", "too hard", "struggling today", "cant do this",
        "cannot do this", "not feeling it", "hopeless", "blue"
    ]
    is_emotional_support = any(sig in user_msg.lower() for sig in low_mood_signals)

    # 1. Assemble dynamic instruction based on intent
    if is_completion and completed_task_name:
        event_instruction = (
            f"EVENT: The patient has confirmed completing their routine: '{completed_task_name}'.\n"
            f"INSTRUCTIONS: Enthusiastically celebrate their achievement in 2-3 warm, clear sentences. "
            f"Explain how completing {completed_task_name} helps their surgical recovery, and ask how they're feeling or suggest their next step."
        )
    elif is_unmark and unmarked_activity:
        event_instruction = (
            f"EVENT: The patient stated they have NOT completed or wish to reset their routine: '{unmarked_activity}'.\n"
            f"INSTRUCTIONS: Reassure {name} warmly in 2-3 sentences that it is completely fine to take their time or reset a task. "
            f"Confirm that you've reset {unmarked_activity} on their checklist to pending. "
            f"Gently explain why {unmarked_activity} is helpful when they feel ready, and ask how they'd like to proceed."
        )
    elif is_emotional_support:
        event_instruction = (
            f"EVENT: The patient expressed sadness, low energy, or low motivation ('{user_msg}').\n"
            f"INSTRUCTIONS: Respond as a deeply caring, empathetic, and human-like recovery coach in 2-3 warm sentences:\n"
            f"1. Warmly validate and normalize their feelings: reassure {name} that recovery is emotionally demanding with ups and downs, and feeling sad, tired, or unmotivated is completely natural and valid.\n"
            f"2. Remove all pressure or guilt: reassure them that resting and mental wellbeing are just as critical for surgical healing as physical exercises.\n"
            f"3. Offer a gentle, restorative option: suggest taking today as a guilt-free restorative rest day, or trying just 2 minutes of gentle 4-7-8 breathing if they want a soothing moment.\n"
            f"4. Reassure them: 'I'm right here with you, {name}. No pressure at all. 💙'"
        )
    elif should_show_options:
        event_instruction = (
            f"INSTRUCTIONS: The patient wants to see or explore today's recovery activities. "
            f"Introduce today's approved routines warmly in 2-3 sentences. Highlight what's pending vs completed, "
            f"and encourage them to pick what feels best for their energy level today."
        )
    else:
        event_instruction = (
            f"INSTRUCTIONS: Respond empathetically, encouragingly, and clinically grounded in 2-4 sentences. "
            f"Address their message directly, staying within approved clinical boundaries."
        )

    # 2. Primary LLM Generation with FULL Multi-Turn History
    adherence_ctx = state.get("adherence_context")
    milestone_ctx = state.get("milestones_summary")
    adherence_prompt_line = f"\nADHERENCE & STREAK CONTEXT:\n{adherence_ctx}\n" if adherence_ctx else ""
    milestone_prompt_line = f"\nPATIENT ACHIEVEMENTS & MILESTONES:\n{milestone_ctx}\n" if milestone_ctx else ""

    if llm:
        try:
            prompt_context = (
                f"Patient Profile: {name} (Preparing for {procedure} {time_context}).\n\n"
                f"Today's Assigned Daily Tasks & Real-Time Statuses (Updated Live):\n{daily_tasks}\n"
                f"{adherence_prompt_line}"
                f"{milestone_prompt_line}\n"
                f"Approved Clinical Content & Physiological Rationales (From Database):\n{clinical_library}\n\n"
                f"TASK AWARENESS & EVENT RULES:\n"
                f"1. Refer to the real-time task statuses above.\n"
                f"2. {event_instruction}"
            )
            prompt_messages: List[Any] = [
                SystemMessage(content=AMY_SYSTEM_PROMPT),
                HumanMessage(content=prompt_context),
            ]


            # Append multi-turn history for all conversational intents
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

            llm_text = invoke_coach_llm(prompt_messages, GPT_MODEL)
            if llm_text:
                reply_text, dynamic_replies = extract_quick_replies(llm_text, active_recs, is_emotional_support)
                return {
                    "response_text": reply_text,
                    "suggested_options": db_options if should_show_options else None,
                    "quick_replies": dynamic_replies,
                    "completed_task_info": state.get("completed_task_info"),
                }
        except Exception as e:
            print(f"⚠️ [LangChain LLM Unified Coaching Fallback] {e}")

    # 3. Deterministic Grounded Fallbacks (if LLM is unavailable or fails)
    if is_completion and completed_task_name:
        response_text = (
            f"Awesome job, {name}! 🎉 I've marked {completed_task_name} as completed in your daily recovery checklist. "
            f"Every bit of preparation strengthens your body and brings you one step closer to a smooth {procedure} recovery 💙. "
            "How are you feeling right now?"
        )
        quick_replies = ["Feeling good! 😊", "A bit tired but okay 👍", "What's my next task? 📋"]
    elif is_unmark and unmarked_activity:
        response_text = (
            f"No problem at all, {name}! 💙 I've reset {unmarked_activity} to pending on your daily checklist. "
            "Progress isn't about rushing; it's about listening to your body and staying consistent when you feel ready. "
            f"Whenever you feel up for doing your {unmarked_activity}, let me know and we can do it together! 🌟"
        )
        quick_replies = ["Let's do it now! 💪", "Show other options 📋", "I'll do it later 👍"]
    elif is_emotional_support:
        response_text = (
            f"I hear you, {name}, and I want you to know it is completely okay to feel sad and have days where your energy is low 💙. "
            "Recovery is an emotional journey, and listening to your feelings and resting is just as important for your healing as physical exercises. "
            "Would you like to take today as a restful recovery day, or perhaps try 2 minutes of gentle 4-7-8 breathing together? No pressure at all, I'm right here with you."
        )
        quick_replies = ["I'll take a rest day 🧘", "Guide me in 4-7-8 breathing 🌬️", "Tell me about my progress 🌟", "Thank you Amy 💙"]
    elif should_show_options:
        response_text = (
            f"Here are your approved daily recovery activities for today, {name}! 🌟 "
            "Pick what feels best for your energy level right now—we can take it one step at a time. 💙"
        )
        quick_replies = ["Let's start! 💪", "Tell me more about Quad Sets", "Surprise me! 🎁"]
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
        "suggested_options": db_options if should_show_options else None,
        "quick_replies": quick_replies,
        "completed_task_info": state.get("completed_task_info"),
    }


@observe(name="response_validation")
def response_validation_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 6: Post-LLM Clinical Response Validator & Output Guardrail (SaMD / Class IIa).
    Audits generated response against regulatory clinical rules before patient delivery.
    """
    raw_response = state.get("response_text", "")
    patient_name = state.get("patient_name", "Sarah")
    procedure = state.get("procedure_name", "Knee Surgery")

    # Run clinical validation
    val_result = response_validator.validate(
        text=raw_response,
        patient_name=patient_name,
        procedure=procedure,
    )

    if not val_result.is_valid:
        print(f"🚨 [LangGraph ResponseValidator] BLOCKED! Flags: {val_result.flags}")
        updates: Dict[str, Any] = {
            "response_text": val_result.sanitized_text,
            "validation_passed": False,
            "validation_flags": val_result.flags,
        }
        if val_result.suggested_quick_replies:
            updates["quick_replies"] = val_result.suggested_quick_replies
        return updates

    return {
        "response_text": val_result.sanitized_text,
        "validation_passed": True,
        "validation_flags": val_result.flags,
    }


# =========================================================================
# 3. Graph Assembly
# =========================================================================
def route_safety(state: CoachState) -> str:
    """Conditional routing based on safety alert detection."""
    return "safety_escalation" if state.get("is_safety_alert") else "intent_classification"


def build_coach_graph():
    """Build and compile the LangGraph pipeline with in-graph recommendation actions & response validation."""
    graph = StateGraph(CoachState)

    # Add Nodes
    graph.add_node("safety_triage", safety_triage_node)
    graph.add_node("safety_escalation", safety_escalation_node)
    graph.add_node("intent_classification", intent_classification_node)
    graph.add_node("recommendation_action", recommendation_action_node)
    graph.add_node("coaching", coaching_node)
    graph.add_node("response_validation", response_validation_node)

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
    graph.add_edge("intent_classification", "recommendation_action")
    graph.add_edge("recommendation_action", "coaching")
    graph.add_edge("coaching", "response_validation")
    graph.add_edge("response_validation", END)
    graph.add_edge("safety_escalation", END)

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
                    name=f"Amy Coaching: {patient.name or 'Sarah'}",
                    session_id=f"conv-{conversation.id}",
                    user_id=f"patient-{patient.id}",
                    tags=["amy_coach", patient.procedure or "wellness", f"plan_{patient.plan or 'Pre-Op'}"],
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
            except Exception as e:
                print(f"⚠️ [Langfuse Trace Update Error]: {e}")

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
        task_status_lines = []
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
                status_label = "COMPLETED ✅" if is_completed else "PENDING ⏳"
                task_status_lines.append(f"- {c.title}: {status_label} ({rec.duration_minutes} mins)")

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

        daily_tasks_summary = "\n".join(task_status_lines) if task_status_lines else "No tasks assigned for today."

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
        from services.patient_service import patient_service

        # Audit adherence (flag missed tasks and count streak)
        adherence_info = patient_service.audit_daily_adherence_and_missed_tasks(session, patient.id)
        milestones_list, add_count = patient_service.get_patient_milestones(session, patient.id)

        adherence_context_str = (
            f"- Current Streak: {patient.streak_count} days 🔥\n"
            f"- Total Completed Tasks: {patient.total_completed_tasks or len(milestones_list)}\n"
        )
        if adherence_info.get("has_missed_yesterday"):
            missed_str = ", ".join(adherence_info.get("missed_yesterday_titles", []))
            adherence_context_str += (
                f"- NOTE: Patient missed {missed_str} yesterday. "
                "If relevant or asked, offer gentle encouragement (no guilt/shame), explain the clinical rationale, and encourage a fresh start today.\n"
            )

        milestones_context_str = ", ".join([m.title for m in milestones_list[:5]]) if milestones_list else "Starting recovery journey"

        raw_history = conversation_service.get_messages(session, conversation.id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in raw_history[:-1] if msg.content
        ]

        # Execute through compiled LangGraph
        initial_state: CoachState = {
            "session": session,
            "patient_id": patient.id,
            "patient_name": patient.name or "Sarah",
            "procedure_name": patient.procedure or "Knee Surgery",
            "days_away": days_away,
            "user_message": user_message,
            "conversation_history": conversation_history,
            "grounded_library_text": grounded_library_text,
            "daily_tasks_summary": daily_tasks_summary,
            "available_options": available_options,
            "active_recommendations": active_recommendations,
            "adherence_context": adherence_context_str,
            "milestones_summary": milestones_context_str,
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }

        result_state: CoachState = self.graph.invoke(initial_state)

        completed_task_info = result_state.get("completed_task_info")

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
        elif adherence_info.get("requires_clinician_alert"):
            # Record low-risk adherence alert for care team cockpit
            safety_service.record_event(
                session=session,
                conversation_id=conversation.id,
                patient_id=patient.id,
                trigger=f"Pre-Op Adherence Alert: {adherence_info.get('consecutive_missed_days')} consecutive days missed",
                risk_level="low",
                action="Notify clinical care team / nurse for follow-up check-in",
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
