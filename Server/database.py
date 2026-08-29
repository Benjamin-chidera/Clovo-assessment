"""
Database configuration, session management, and content library seeding using SQLModel and SQLite.
"""

from pathlib import Path
from typing import Generator
from sqlmodel import Session, SQLModel, create_engine, select

# Database file path resolution (saved in Server directory as clovo.db)
BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "clovo.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Engine creation with SQLite thread safety setting
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

DEFAULT_CONTENT_LIBRARY = [
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
    {
        "id": 5,
        "type": "exercise",
        "title": "Gentle Stretching – Release Tension",
        "description": "Slow, low-intensity seated stretches for hamstrings, calves, and shoulders. Hold each stretch for 20 seconds.",
        "rationale": "Improves blood circulation and alleviates muscular tightness without loading the surgical joint.",
        "target_stage": "pre-op-all",
        "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&q=80",
        "icon_name": "body-outline",
    },
    {
        "id": 6,
        "type": "exercise",
        "title": "Recovery Walk – Shake Off Soreness",
        "description": "Gentle 15-30 minute flat surface walking at an easy, relaxed pace.",
        "rationale": "Promotes cardiovascular health and builds pre-operative stamina.",
        "target_stage": "pre-op-all",
        "image_url": "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?auto=format&fit=crop&w=600&q=80",
        "icon_name": "walk-outline",
    },
    {
        "id": 7,
        "type": "mindfulness",
        "title": "Yoga for Beginners – Recovery Basics",
        "description": "Gentle restorative yoga postures focusing on deep breathing and relaxation.",
        "rationale": "Reduces cortisol levels and prepares the body for restorative rest.",
        "target_stage": "pre-op-all",
        "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=600&q=80",
        "icon_name": "flower-outline",
    },
]


def seed_clinical_content(session: Session) -> None:
    """Seed default clinical content library if not already populated."""
    from models.clinical_content import ClinicalContent

    for item in DEFAULT_CONTENT_LIBRARY:
        existing = session.get(ClinicalContent, item["id"])
        if not existing:
            content = ClinicalContent(**item)
            session.add(content)
        else:
            # Update existing with complete metadata
            for key, val in item.items():
                setattr(existing, key, val)
            session.add(existing)
    session.commit()


def create_db_and_tables() -> None:
    """
    Create SQLite database and all registered SQLModel tables, then seed default data if needed.
    """
    import models  # noqa: F401

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 1. Seed clinical content library
        seed_clinical_content(session)

        # 2. Seed initial patient (Sarah) and personalized recommendations
        from services.patient_service import patient_service

        patient_service.get_or_create_default_patient(session)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and safely closes it upon completion.
    """
    with Session(engine) as session:
        yield session
