from typing import List, Optional
from sqlmodel import Session, select
from models.recommendation import (
    Recommendation,
    TaskItemData,
    RecommendationCreate,
    RecommendationUpdate,
)


class RecommendationService:
    @staticmethod
    def get_by_patient(session: Session, patient_id: str) -> List[Recommendation]:
        statement = (
            select(Recommendation)
            .where(Recommendation.patient_id == patient_id)
            .order_by(Recommendation.created_at.asc())
        )
        return list(session.exec(statement).all())

    @staticmethod
    def get_by_id(session: Session, recommendation_id: str) -> Optional[Recommendation]:
        return session.get(Recommendation, recommendation_id)

    @staticmethod
    def get_tasks_for_user(session: Session, patient_id: Optional[str] = None) -> List[TaskItemData]:
        from services.patient_service import patient_service

        patient = patient_service.get_patient_by_id(session, patient_id) if patient_id else None
        if not patient:
            patient = patient_service.get_or_create_default_patient(session)

        recs = RecommendationService.get_by_patient(session, patient.id)

        def map_category(t: str) -> str:
            t_lower = t.lower()
            if "walk" in t_lower:
                return "walking"
            if "mind" in t_lower:
                return "mindset"
            if "nutr" in t_lower or "hydr" in t_lower:
                return "nutrition"
            return "recovery"

        def map_label(t: str) -> str:
            t_lower = t.lower()
            if "walk" in t_lower:
                return "Movement"
            if "mind" in t_lower:
                return "Mindset"
            if "nutr" in t_lower:
                return "Nutrition"
            return "Daily Prep"

        def map_duration(t: str) -> str:
            t_lower = t.lower()
            if "walk" in t_lower:
                return "15 mins"
            if "mind" in t_lower:
                return "10 mins"
            return "Daily"

        return [
            TaskItemData(
                id=r.id,
                title=r.title,
                category=map_category(r.type),
                duration=map_duration(r.type),
                is_completed=(r.status == "completed"),
                category_label=map_label(r.type),
                instruction=r.instruction,
                rationale=r.rationale,
            )
            for r in recs
        ]

    @staticmethod
    def create(session: Session, data: RecommendationCreate) -> Recommendation:
        rec = Recommendation(
            patient_id=data.patient_id,
            type=data.type,
            title=data.title,
            instruction=data.instruction,
            rationale=data.rationale,
            content_id=data.content_id,
            version=data.version,
            status=data.status,
        )
        if data.id:
            rec.id = data.id
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return rec

    @staticmethod
    def toggle_status(session: Session, recommendation_id: str) -> Optional[Recommendation]:
        rec = session.get(Recommendation, recommendation_id)
        if not rec:
            return None
        rec.status = "completed" if rec.status != "completed" else "pending"
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return rec

    @staticmethod
    def update(session: Session, recommendation_id: str, data: RecommendationUpdate) -> Optional[Recommendation]:
        rec = session.get(Recommendation, recommendation_id)
        if not rec:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rec, key, value)
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return rec


recommendation_service = RecommendationService()
