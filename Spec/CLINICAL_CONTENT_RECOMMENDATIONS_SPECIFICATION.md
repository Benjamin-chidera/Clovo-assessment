# Clovo Platform — Clinical Content Library & Recommendation Data Model Specification

## 1. Overview & Architectural Motivation

In clinical recovery and digital wellness systems, content must be clearly decoupled into two distinct domains:
1. **Clinical Content ("The What")**: Curated, evidence-based medical and wellness routines (exercises, nutrition protocols, mindfulness exercises, surgery prep guides). These are immutable reference templates with visual media (`image_url`), iconography (`icon_name`), clinical rationale, and target surgery stages.
2. **Patient Recommendations ("The How Much & When")**: Patient-specific, personalized prescriptions linking a patient to a clinical content item with individualized dosages (duration, repetitions, scheduled date, progress status, and coach notes).

---

## 2. Entity-Relationship Model (SQLModel)

```
┌────────────────────────────────────────┐
│             Patient                    │
│ ├── id: int (PK)                       │
│ ├── name: str                          │
│ └── surgery_date: date                 │
└───────────────────┬────────────────────┘
                    │ 1
                    │
                    │ has many
                    │
                    │ N
┌───────────────────▼────────────────────┐       N:1        ┌────────────────────────────────────────┐
│          Recommendation                ├─────────────────►│           ClinicalContent              │
│ ├── id: int (PK)                       │                  │ ├── id: int (PK)                       │
│ ├── patient_id: int (FK -> Patient)    │                  │ ├── type: str (exercise/nutrition/...) │
│ ├── content_id: int (FK -> Content)    │                  │ ├── title: str                         │
│ ├── duration_minutes: int              │                  │ ├── description: str                   │
│ ├── repetitions: Optional[int]         │                  │ ├── rationale: str                     │
│ ├── scheduled_date: date               │                  │ ├── image_url: Optional[str]           │
│ ├── status: str (active/completed/...) │                  │ ├── icon_name: Optional[str]           │
│ └── notes: Optional[str]               │                  │ └── target_stage: str                  │
└────────────────────────────────────────┘                  └────────────────────────────────────────┘
```

---

## 3. SQLModel Schema Definitions

### 3.1 Clinical Content Model (`Server/models/clinical_content.py`)
Represents evidence-based recovery routines in the clinical library with rich media support.

```python
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.recommendation import Recommendation


class ClinicalContent(SQLModel, table=True):
    __tablename__ = "clinical_content"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(index=True, description="Content category: exercise, nutrition, mindfulness")
    title: str = Field(index=True, description="Readable title")
    description: str = Field(description="Step-by-step instructions or guidance")
    rationale: str = Field(description="Clinical reason and recovery benefit")
    target_stage: str = Field(index=True, description="Applicable stage: pre-op-21, pre-op-14, pre-op-all, post-op")
    image_url: Optional[str] = Field(default=None, description="Visual thumbnail/photography URL for cards and preview")
    icon_name: Optional[str] = Field(default=None, description="Ionicons / Vector icon symbol (e.g. fitness, water, moon)")

    # Relationship back to personalized recommendations
    recommendations: List["Recommendation"] = Relationship(back_populates="content")
```

### 3.2 Refactored Recommendation Model (`Server/models/recommendation.py`)
Represents a personalized prescription assigned to a patient.

```python
from typing import Optional, TYPE_CHECKING
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.patient import Patient
    from models.clinical_content import ClinicalContent


class Recommendation(SQLModel, table=True):
    __tablename__ = "recommendations"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Links to Patient (Who)
    patient_id: int = Field(foreign_key="patients.id", index=True)

    # Links to Clinical Content (The "What")
    content_id: int = Field(foreign_key="clinical_content.id", index=True)

    # Personalization (The "How Much")
    duration_minutes: int = Field(default=10, description="Prescribed duration in minutes")
    repetitions: Optional[int] = Field(default=None, description="Prescribed repetitions if applicable")

    # Scheduling (The "When")
    scheduled_date: date = Field(default_factory=date.today, index=True)

    # State & Lifecycle
    status: str = Field(default="active", index=True, description="active, completed, skipped")

    # Optional specific notes for this patient
    notes: Optional[str] = Field(default=None, description="Custom clinical or coach notes")

    # SQLModel Relationships
    patient: Optional["Patient"] = Relationship(back_populates="recommendations")
    content: Optional["ClinicalContent"] = Relationship(back_populates="recommendations")
```

---

## 4. Default Clinical Content Library with Imagery

The following evidence-based clinical routines are pre-seeded in the database:

| ID | Type | Title | Description | Rationale | Target Stage | Image & Icon |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `exercise` | **Quad Sets** | Lie on your back with legs straight. Press the back of your knee down into the floor/mat. Hold for 5 seconds, then relax. Repeat 10 times. | Activates the quadriceps muscle without moving the joint, preventing muscle atrophy before surgery. | `pre-op-21` | `fitness` / [Stretching Photo](https://images.unsplash.com/photo-1544367567-0f2fcb009e0b) |
| **2** | `exercise` | **Straight Leg Raise** | Lie on your back. Bend your good knee, keep the surgical leg straight. Lift the straight leg to the height of the bent knee. Hold 3 seconds, lower slowly. Repeat 10 times. | Strengthens the hip flexors and quads, which are critical for walking after surgery. | `pre-op-14` | `body` / [Leg Routine Photo](https://images.unsplash.com/photo-1518611012118-696072aa579a) |
| **3** | `nutrition` | **Protein Power Snack** | Eat a serving of Greek yogurt, a hard-boiled egg, or a small handful of almonds as a mid-morning snack. | Protein provides the building blocks (amino acids) your body needs to repair tissue after surgery. | `pre-op-all` | `nutrition` / [Healthy Snack Photo](https://images.unsplash.com/photo-1490645935967-10de6ba17061) |
| **4** | `mindfulness` | **4-7-8 Breathing** | Inhale through your nose for 4 seconds. Hold your breath for 7 seconds. Exhale slowly through your mouth for 8 seconds. Repeat 4 times. | Activates the parasympathetic nervous system to lower heart rate and calm pre-surgery anxiety. | `pre-op-all` | `moon` / [Calm Meditation Photo](https://images.unsplash.com/photo-1506126613408-eca07ce68773) |

### Python Seed Data:
```python
DEFAULT_CONTENT_LIBRARY = [
    # Exercises
    {
        "id": 1,
        "type": "exercise",
        "title": "Quad Sets",
        "description": "Lie on your back with legs straight. Press the back of your knee down into the floor/mat. Hold for 5 seconds, then relax. Repeat 10 times.",
        "rationale": "Activates the quadriceps muscle without moving the joint, preventing muscle atrophy before surgery.",
        "target_stage": "pre-op-21",
        "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&q=80",
        "icon_name": "fitness-outline",
    },
    {
        "id": 2,
        "type": "exercise",
        "title": "Straight Leg Raise",
        "description": "Lie on your back. Bend your good knee, keep the surgical leg straight. Lift the straight leg to the height of the bent knee. Hold 3 seconds, lower slowly. Repeat 10 times.",
        "rationale": "Strengthens the hip flexors and quads, which are critical for walking after surgery.",
        "target_stage": "pre-op-14",
        "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=600&q=80",
        "icon_name": "body-outline",
    },
    # Nutrition
    {
        "id": 3,
        "type": "nutrition",
        "title": "Protein Power Snack",
        "description": "Eat a serving of Greek yogurt, a hard-boiled egg, or a small handful of almonds as a mid-morning snack.",
        "rationale": "Protein provides the building blocks (amino acids) your body needs to repair tissue after surgery.",
        "target_stage": "pre-op-all",
        "image_url": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=600&q=80",
        "icon_name": "nutrition-outline",
    },
    # Mindfulness
    {
        "id": 4,
        "type": "mindfulness",
        "title": "4-7-8 Breathing",
        "description": "Inhale through your nose for 4 seconds. Hold your breath for 7 seconds. Exhale slowly through your mouth for 8 seconds. Repeat 4 times.",
        "rationale": "Activates the parasympathetic nervous system to lower heart rate and calm pre-surgery anxiety.",
        "target_stage": "pre-op-all",
        "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=600&q=80",
        "icon_name": "moon-outline",
    },
]
```

---

## 5. DTOs & API Response Serialization

When recommendations are retrieved for client consumption (such as the mobile Home dashboard or Tasks screen), the joined `ClinicalContent` fields including media are flattened into clean API response schemas:

```python
class RecommendationRead(SQLModel):
    id: int
    patient_id: int
    content_id: int
    title: str
    type: str
    description: str
    rationale: str
    image_url: Optional[str] = None
    icon_name: Optional[str] = None
    duration_minutes: int
    repetitions: Optional[int] = None
    scheduled_date: date
    status: str
    notes: Optional[str] = None


class RecommendationCreate(SQLModel):
    patient_id: int
    content_id: int
    duration_minutes: int = 10
    repetitions: Optional[int] = None
    scheduled_date: Optional[date] = None
    status: str = "active"
    notes: Optional[str] = None


class RecommendationUpdate(SQLModel):
    status: Optional[str] = None
    duration_minutes: Optional[int] = None
    repetitions: Optional[int] = None
    notes: Optional[str] = None
```

---

## 6. Service Layer Operations (`Server/services/recommendation_service.py`)

### 6.1 Key Query Patterns
1. **Fetch Patient Recommendations with Content & Media Join**:
   ```python
   select(Recommendation, ClinicalContent).join(ClinicalContent, Recommendation.content_id == ClinicalContent.id).where(Recommendation.patient_id == patient_id)
   ```
2. **Toggle Recommendation Status**:
   - Status changes between `"active"` and `"completed"`.
   - Broadcasts real-time update through Socket.IO and invalidates Redis cache.
3. **Automated Stage-Based Recommendation Generation**:
   - Queries `ClinicalContent` by `target_stage` matching the patient's countdown (e.g. `pre-op-21`).
   - Automatically creates personalized `Recommendation` records for the patient with full image and icon references.

---

## 7. Implementation Checklist

- [ ] **Create Clinical Content Model (`Server/models/clinical_content.py`)**: Define `ClinicalContent` SQLModel table with `image_url` and `icon_name`.
- [ ] **Refactor Recommendation Model (`Server/models/recommendation.py`)**: Update `Recommendation` schema with `patient_id: int`, `content_id: int`, `duration_minutes: int`, `repetitions: Optional[int]`, `scheduled_date: date`, `status: str`, and `notes: Optional[str]`.
- [ ] **Export Models in `Server/models/__init__.py`**: Ensure all models (`ClinicalContent`, `Recommendation`, `Patient`) are exported.
- [ ] **Database Seeding (`Server/database.py`)**: Pre-seed the 4 default content library items with their high-resolution imagery and icons.
- [ ] **Update Service Layer (`Server/services/recommendation_service.py`)**: Refactor queries to join `ClinicalContent` and include media URLs in client DTOs.
- [ ] **Update Route Controllers (`Server/routes/recommendations.py` & `Server/routes/tasks.py`)**: Ensure API inputs/outputs match refactored types.
