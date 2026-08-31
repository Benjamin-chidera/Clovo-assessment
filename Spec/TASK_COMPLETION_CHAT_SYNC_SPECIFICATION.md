# Clovo Platform — Conversational Task Verification & Real-Time Sync Specification

## 1. Overview & Architectural Goals

This specification defines the bidirectional task verification and synchronization system between the patient, **Coach Amy**, and the Clovo user interface.

Task completion is supported across three primary interaction channels:
1. **Conversational Natural Language (Prompted & Unprompted)**: The patient can confirm completion when Amy asks, or unpromptedly state that they finished a routine (e.g. *"I just finished my quad sets"*).
2. **Home Screen Manual Controls**: Tapping the daily checklist checkboxes in [`PendingTasksList.tsx`](file:///Users/benjaminchidera/Desktop/Clovo/Client/mobile/src/components/home/PendingTasksList.tsx).
3. **Chat Screen Activity Card Controls**: Tapping cards directly in [`RecoveryActivityCards.tsx`](file:///Users/benjaminchidera/Desktop/Clovo/Client/mobile/src/components/chat/RecoveryActivityCards.tsx).

All actions persist to the SQLite database and synchronize in real-time across both screens via Socket.IO.

---

## 2. End-to-End Workflow

```
                              ┌─────────────────────────────────────────┐
                              │ Patient Utterance (Prompted/Unprompted) │
                              │   "I just finished my quad sets!"       │
                              └────────────────────┬────────────────────┘
                                                   │
                                                   ▼
                              ┌─────────────────────────────────────────┐
                              │ Node 1: Fast Safety Triage Guard        │
                              │ (Checks for pain, dizziness, red flags) │
                              └────────────────────┬────────────────────┘
                                                   │
                                                   ▼
                              ┌─────────────────────────────────────────┐
                              │ Node 2: LLM Structured Intent Classifier│
                              │ Pydantic extraction:                    │
                              │ • intent: "task_completion"             │
                              │ • completed_activity: "Quad Sets"       │
                              │ • is_negated: false                     │
                              └────────────────────┬────────────────────┘
                                                   │
                   ┌───────────────────────────────┴───────────────────────────────┐
                   │                                                               │
     [intent == "task_completion" & !is_negated]                       [intent != "task_completion"]
                   │                                                               │
                   ▼                                                               ▼
    ┌─────────────────────────────────────────┐                     ┌─────────────────────────────┐
    │ Node 3: Task Mutation & Socket Sync     │                     │ Node 4: Grounded Coaching   │
    │ • Match "Quad Sets" in SQLite recs      │                     │ • Formulate Q&A / rationale │
    │ • Update status = "completed"           │                     │ • Empathetic motivation     │
    │ • Broadcast Socket.IO `task_sync`       │                     └──────────────┬──────────────┘
    │ • Invalidate Redis cache keys           │                                    │
    └──────────────────────┬──────────────────┘                                    │
                           │                                                       │
                           └───────────────────────┬───────────────────────────────┘
                                                   │
                                                   ▼
                              ┌─────────────────────────────────────────┐
                              │ Node 5: Amy Celebration & UI Highlighting│
                              │ • Amy: "Awesome job, Sarah! 🎉 I've     │
                              │   marked Quad Sets as completed."       │
                              │ • Chat Card: Emerald "✓ Completed" badge│
                              │ • Home Screen: Task checkbox ticked (✓) │
                              └─────────────────────────────────────────┘
```

---

## 3. LLM Structured Intent & Entity Classifier

To avoid the fragility of raw keyword matching (which fails on negations like *"I haven't done it yet"* or natural rephrasing like *"Knocked out the leg workout"*), LangGraph uses a **Pydantic Structured Output Model**:

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field


class UserIntentExtraction(BaseModel):
    intent: Literal["task_completion", "question_about_routine", "general_chat", "symptom_report"] = Field(
        description="Primary intent of the patient message"
    )
    completed_activity: Optional[str] = Field(
        default=None,
        description="Name or keywords of the activity completed, e.g., 'Quad Sets', 'Straight Leg Raise', 'Protein Power Snack', '4-7-8 Breathing', or 'all'"
    )
    is_negated: bool = Field(
        default=False,
        description="True if the patient states they DID NOT do it (e.g. 'I haven't done it yet', 'I couldn't do quad sets today')"
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
```

### 3.1 Decision Rules
1. If `intent == "task_completion"` AND `is_negated is False`:
   - Match `completed_activity` semantically to patient's active `Recommendation` records in SQLite.
   - If matched, set `status = "completed"`.
   - If user says *"Yes, I did"* in response to Amy asking about an activity, resolve `completed_activity` from the previous conversation turn.
2. If `intent == "task_completion"` AND `is_negated is True`:
   - Do NOT mark as complete.
   - Amy responds with gentle encouragement and guidance on how to start when ready.

---

## 4. Service Layer & Database Implementation

### 4.1 Recommendation Completion Method (`Server/services/recommendation_service.py`)
```python
@staticmethod
def mark_task_completed(
    session: Session,
    patient_id: int,
    task_id: Optional[int] = None,
    activity_name: Optional[str] = None
) -> Optional[Recommendation]:
    """
    Mark a recommendation as completed by ID or semantic activity name matching.
    """
    # 1. Match by integer ID
    if task_id:
        rec = session.get(Recommendation, task_id)
        if rec and rec.patient_id == patient_id:
            rec.status = "completed"
            session.add(rec)
            session.commit()
            session.refresh(rec)
            return rec

    # 2. Match by activity name / title in ClinicalContent
    if activity_name:
        statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(
                Recommendation.patient_id == patient_id,
                Recommendation.status == "active"
            )
        )
        results = session.exec(statement).all()

        act_lower = activity_name.lower()
        for rec, content in results:
            c_title = content.title.lower()
            c_type = content.type.lower()
            if (
                c_title in act_lower
                or act_lower in c_title
                or (c_type in act_lower and c_type != "exercise")
                or ("quad" in act_lower and "quad" in c_title)
                or ("leg" in act_lower and "leg" in c_title)
                or ("snack" in act_lower and "snack" in c_title)
                or ("breath" in act_lower and "breath" in c_title)
            ):
                rec.status = "completed"
                session.add(rec)
                session.commit()
                session.refresh(rec)
                return rec

    # 3. Fallback: Mark the oldest active recommendation
    statement = (
        select(Recommendation)
        .where(Recommendation.patient_id == patient_id, Recommendation.status == "active")
        .order_by(Recommendation.scheduled_date.asc())
    )
    rec = session.exec(statement).first()
    if rec:
        rec.status = "completed"
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return rec

    return None
```

---

## 5. UI Visual Highlighting Specification

### 5.1 Chat Activity Cards (`RecoveryActivityCards.tsx`)
When a card represents a completed task (`is_completed === true` or matched in `useTaskStore`):
- **Card Background & Border**: Soft emerald border (`border-emerald-300`) with subtle green background tint (`bg-emerald-50/25`).
- **Completion Pill Badge**: Top-right emerald pill badge:
  ```tsx
  <View className="bg-emerald-100 px-2.5 py-0.5 rounded-full flex-row items-center">
    <Ionicons name="checkmark-circle" size={13} color="#059669" style={{ marginRight: 3 }} />
    <Text className="text-[11px] font-bold text-emerald-700">Completed</Text>
  </View>
  ```
- **Tap State**: Remains viewable/tappable to review instructions and clinical rationale without re-submitting.

### 5.2 Home Screen Checklist (`PendingTasksList.tsx`)
- Immediate optimistic checkbox tick (`✓`) with haptic feedback.
- Progress counter updates in real-time (e.g. `2 of 3 completed`).

---

## 6. Real-Time Socket.IO Synchronization

When a task is marked completed (whether via Chat conversation, Home checkbox, or Card tap), the server emits:

```json
{
  "event": "task_sync",
  "data": {
    "taskId": 1,
    "title": "Quad Sets",
    "isCompleted": true,
    "patientId": 1
  }
}
```

- `useTaskStore`: Updates task list state instantly without refetching.
- `useChatStore`: Updates activity card state in chat bubbles.

---

## 7. Implementation Checklist

- [ ] **Structured Intent Classifier**: Implement LLM structured intent extraction in `Server/services/amy.py`.
- [ ] **Task Completion Service**: Add `mark_task_completed()` in `Server/services/recommendation_service.py`.
- [ ] **Socket.IO Event Broadcast**: Emit `task_sync` upon conversational task completion in `Server/routes/sockets.py`.
- [ ] **Visual Highlighting in Mobile UI**:
  - [ ] Add `isCompleted` detection and Emerald Green badges in `Client/mobile/src/components/chat/RecoveryActivityCards.tsx`.
  - [ ] Ensure `useTaskStore` and `useChatStore` synchronize on `task_sync`.
