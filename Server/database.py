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
    {
        "id": 8,
        "type": "exercise",
        "title": "Ankle Pumps & Elevation",
        "description": "Lie comfortably with surgical leg elevated on pillows above heart level. Slowly pump your feet up and down 20 times per session.",
        "rationale": "Activates the calf muscle pump to stimulate venous return, reduce joint edema, and prevent Deep Vein Thrombosis (DVT) after knee replacement.",
        "target_stage": "post-op",
        "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&q=80",
        "icon_name": "fitness-outline",
    },
    {
        "id": 9,
        "type": "exercise",
        "title": "Heel Slides (Gentle Knee Flexion)",
        "description": "Lie on back with legs straight. Slowly slide your heel toward your buttocks, bending the knee to gentle tension. Hold for 5 seconds, then slowly straighten. Repeat 10 times.",
        "rationale": "Restores active knee flexion and stretches the healing extensor mechanism without overloading the implant.",
        "target_stage": "post-op",
        "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=600&q=80",
        "icon_name": "body-outline",
    },
    {
        "id": 10,
        "type": "recovery",
        "title": "Ice Pack & Elevation Protocol",
        "description": "Apply a cold pack wrapped in a thin towel directly over the knee for 20 minutes with the leg elevated above heart level.",
        "rationale": "Vasoconstriction reduces inflammatory swelling, eases surgical discomfort, and prevents joint stiffness after rehabilitation.",
        "target_stage": "post-op",
        "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=600&q=80",
        "icon_name": "snow-outline",
    },
    {
        "id": 11,
        "type": "walking",
        "title": "Crutch Walking & Weight-Bearing Steps",
        "description": "Take a gentle 5-10 minute walk indoors using your crutches or walker, placing approved partial-to-full weight on the surgical leg.",
        "rationale": "Early progressive weight-bearing stimulates bone remodeling around the knee prosthesis and rebuilds symmetrical gait confidence.",
        "target_stage": "post-op",
        "image_url": "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?auto=format&fit=crop&w=600&q=80",
        "icon_name": "walk-outline",
    },
    {
        "id": 12,
        "type": "nutrition",
        "title": "Tissue Healing & Hydration Fuel",
        "description": "Drink a large glass of water and consume a protein-rich meal with Vitamin C (e.g. eggs, Greek yogurt, or berries).",
        "rationale": "Adequate hydration and amino acids support wound collagen synthesis and accelerate surgical recovery.",
        "target_stage": "post-op",
        "image_url": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=600&q=80",
        "icon_name": "nutrition-outline",
    },
]


DEFAULT_MILESTONES = [
    {
        "id": 1,
        "code": "first_step",
        "title": "First Step",
        "description": "Completed your very first pre-op preparation activity",
        "category": "adherence",
        "icon_name": "footsteps",
        "color": "#4F46E5",
        "bg_gradient_start": "#E0E7FF",
        "bg_gradient_end": "#C7D2FE",
        "criteria_type": "completed_tasks",
        "criteria_threshold": 1,
    },
    {
        "id": 2,
        "code": "quad_master",
        "title": "Quad Master",
        "description": "Strengthened knee quads with targeted isometric sets",
        "category": "exercise",
        "icon_name": "fitness",
        "color": "#4F46E5",
        "bg_gradient_start": "#E0E7FF",
        "bg_gradient_end": "#C7D2FE",
        "criteria_type": "specific_exercise",
        "criteria_threshold": 1,
    },
    {
        "id": 3,
        "code": "mindful_zen",
        "title": "Mindfulness Zen",
        "description": "Lowered pre-op cortisol with 4-7-8 breathing practice",
        "category": "mindfulness",
        "icon_name": "flower",
        "color": "#10B981",
        "bg_gradient_start": "#D1FAE5",
        "bg_gradient_end": "#A7F3D0",
        "criteria_type": "specific_exercise",
        "criteria_threshold": 1,
    },
    {
        "id": 4,
        "code": "protein_champ",
        "title": "Nutrition Champion",
        "description": "Fueled body with surgery-prep protein snack",
        "category": "nutrition",
        "icon_name": "nutrition",
        "color": "#F59E0B",
        "bg_gradient_start": "#FEF3C7",
        "bg_gradient_end": "#FDE68A",
        "criteria_type": "specific_exercise",
        "criteria_threshold": 1,
    },
    {
        "id": 5,
        "code": "streak_3",
        "title": "3-Day Streak",
        "description": "Maintained 3 consecutive days of pre-op routine",
        "category": "adherence",
        "icon_name": "flame",
        "color": "#EF4444",
        "bg_gradient_start": "#FEE2E2",
        "bg_gradient_end": "#FECACA",
        "criteria_type": "streak_days",
        "criteria_threshold": 3,
    },
    {
        "id": 6,
        "code": "streak_5",
        "title": "5-Day Streak",
        "description": "Achieved a 5-day consistency streak before surgery",
        "category": "adherence",
        "icon_name": "walk",
        "color": "#EC4899",
        "bg_gradient_start": "#FCE7F3",
        "bg_gradient_end": "#FBCFE8",
        "criteria_type": "streak_days",
        "criteria_threshold": 5,
    },
    {
        "id": 7,
        "code": "recovery_ready",
        "title": "Core & Mobility",
        "description": "Demonstrated consistent daily mobility and core readiness",
        "category": "exercise",
        "icon_name": "barbell",
        "color": "#10B981",
        "bg_gradient_start": "#D1FAE5",
        "bg_gradient_end": "#A7F3D0",
        "criteria_type": "completed_tasks",
        "criteria_threshold": 5,
    },
    {
        "id": 8,
        "code": "circulation_hero",
        "title": "Circulation Champion",
        "description": "Maintained post-op venous circulation and reduced joint swelling with ankle pumps",
        "category": "exercise",
        "icon_name": "water",
        "color": "#0284C7",
        "bg_gradient_start": "#E0F2FE",
        "bg_gradient_end": "#BAE6FD",
        "criteria_type": "specific_exercise",
        "criteria_threshold": 1,
    },
    {
        "id": 9,
        "code": "flexion_pioneer",
        "title": "Flexion Pioneer",
        "description": "Restored early post-op knee mobility with gentle heel slides",
        "category": "exercise",
        "icon_name": "fitness",
        "color": "#10B981",
        "bg_gradient_start": "#D1FAE5",
        "bg_gradient_end": "#A7F3D0",
        "criteria_type": "specific_exercise",
        "criteria_threshold": 1,
    },
    {
        "id": 10,
        "code": "postop_walker",
        "title": "First Post-Op Steps",
        "description": "Completed first assisted walking and weight-bearing session with crutches",
        "category": "adherence",
        "icon_name": "walk",
        "color": "#F59E0B",
        "bg_gradient_start": "#FEF3C7",
        "bg_gradient_end": "#FDE68A",
        "criteria_type": "completed_tasks",
        "criteria_threshold": 2,
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
            for key, val in item.items():
                setattr(existing, key, val)
            session.add(existing)
    session.commit()


def seed_milestones(session: Session) -> None:
    """Seed default milestone definitions catalog."""
    from models.milestone import Milestone

    for item in DEFAULT_MILESTONES:
        existing = session.get(Milestone, item["id"])
        if not existing:
            milestone = Milestone(**item)
            session.add(milestone)
        else:
            for key, val in item.items():
                setattr(existing, key, val)
            session.add(existing)
    session.commit()


def migrate_db_columns() -> None:
    """Safely migrate any newly added SQLite columns if they don't exist yet."""
    import sqlite3

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Check patients table columns
        cursor.execute("PRAGMA table_info(patients)")
        patient_cols = [row[1] for row in cursor.fetchall()]
        if "last_active_date" not in patient_cols:
            cursor.execute("ALTER TABLE patients ADD COLUMN last_active_date DATE")
        if "total_completed_tasks" not in patient_cols:
            cursor.execute("ALTER TABLE patients ADD COLUMN total_completed_tasks INTEGER DEFAULT 0")

        # Check recommendations table columns
        cursor.execute("PRAGMA table_info(recommendations)")
        rec_cols = [row[1] for row in cursor.fetchall()]
        if "completed_at" not in rec_cols:
            cursor.execute("ALTER TABLE recommendations ADD COLUMN completed_at TIMESTAMP")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ [Database Migration Note]: {e}")


def create_db_and_tables() -> None:
    """
    Create SQLite database and all registered SQLModel tables, then seed default data if needed.
    """
    import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    migrate_db_columns()

    with Session(engine) as session:
        # 1. Seed clinical content library
        seed_clinical_content(session)

        # 2. Seed milestone catalog
        seed_milestones(session)

        # 3. Seed initial patient (Sarah) and personalized recommendations
        from services.patient_service import patient_service

        patient_service.get_or_create_default_patient(session)




def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and safely closes it upon completion.
    """
    with Session(engine) as session:
        yield session
