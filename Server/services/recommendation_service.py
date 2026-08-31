from typing import List, Optional
from sqlmodel import Session, select
from models.recommendation import (
    Recommendation,
    TaskItemData,
    RecommendationRead,
)
from models.clinical_content import ClinicalContent


class RecommendationService:
    @staticmethod
    def get_by_patient(session: Session, patient_id: int) -> List[RecommendationRead]:
        """
        Fetch all recommendations for a patient joined with their ClinicalContent details.
        """
        statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == patient_id)
            .order_by(Recommendation.scheduled_date.asc())
        )
        results = session.exec(statement).all()

        return [
            RecommendationRead(
                id=rec.id,
                patient_id=rec.patient_id,
                content_id=rec.content_id,
                title=content.title,
                type=content.type,
                description=content.description,
                rationale=content.rationale,
                image_url=content.image_url,
                icon_name=content.icon_name,
                duration_minutes=rec.duration_minutes,
                repetitions=rec.repetitions,
                scheduled_date=rec.scheduled_date,
                status=rec.status,
                notes=rec.notes,
            )
            for rec, content in results
        ]

    @staticmethod
    def get_by_id(session: Session, recommendation_id: int) -> Optional[Recommendation]:
        """Fetch raw Recommendation entity by integer ID."""
        return session.get(Recommendation, recommendation_id)

    @staticmethod
    def get_tasks_for_user(session: Session, patient_id: Optional[int] = None) -> List[TaskItemData]:
        """
        Return formatted task checklist for a patient for mobile tasks display.
        """
        from services.patient_service import patient_service

        patient = patient_service.get_patient_by_id(session, patient_id) if patient_id else None
        if not patient:
            patient = patient_service.get_or_create_default_patient(session)

        statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == patient.id)
            .order_by(Recommendation.scheduled_date.asc())
        )
        results = session.exec(statement).all()

        def map_category(t: str) -> str:
            t_lower = t.lower()
            if "exercise" in t_lower or "walk" in t_lower:
                return "recovery"
            if "mind" in t_lower:
                return "mindset"
            if "nutr" in t_lower or "hydr" in t_lower:
                return "nutrition"
            return "recovery"

        def map_label(t: str) -> str:
            t_lower = t.lower()
            if "exercise" in t_lower:
                return "Movement"
            if "mind" in t_lower:
                return "Mindset"
            if "nutr" in t_lower:
                return "Nutrition"
            return "Recovery Prep"

        return [
            TaskItemData(
                id=rec.id,
                title=content.title,
                category=map_category(content.type),
                duration=f"{rec.duration_minutes} mins" if rec.duration_minutes else "10 mins",
                is_completed=(rec.status == "completed"),
                category_label=map_label(content.type),
                instruction=content.description,
                rationale=content.rationale,
                image_url=content.image_url,
                icon_name=content.icon_name,
                repetitions=rec.repetitions,
                notes=rec.notes,
            )
            for rec, content in results
        ]

    @staticmethod
    def create(session: Session, recommendation: Recommendation) -> Recommendation:
        """Create and persist a new personalized recommendation."""
        session.add(recommendation)
        session.commit()
        session.refresh(recommendation)
        return recommendation

    @staticmethod
    def toggle_status(session: Session, recommendation_id: int) -> Optional[Recommendation]:
        """Toggle recommendation status between 'active' and 'completed'."""
        rec = session.get(Recommendation, recommendation_id)
        if not rec:
            return None
        rec.status = "completed" if rec.status != "completed" else "active"
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return rec

    @staticmethod
    def mark_task_completed(
        session: Session,
        patient_id: int,
        task_id: Optional[int] = None,
        activity_name: Optional[str] = None,
    ) -> Optional[Recommendation]:
        """
        Mark a recommendation as completed by ID or semantic activity name matching.
        """
        # 1. Match by explicit integer ID
        if task_id:
            rec = session.get(Recommendation, task_id)
            if rec and rec.patient_id == patient_id:
                rec.status = "completed"
                session.add(rec)
                session.commit()
                session.refresh(rec)
                return rec

        # 2. Match by activity name / keywords in ClinicalContent
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

            act_lower = activity_name.lower().strip()
            for rec, content in results:
                c_title = content.title.lower()
                c_type = content.type.lower()
                if (
                    c_title in act_lower
                    or act_lower in c_title
                    or ("quad" in act_lower and "quad" in c_title)
                    or ("leg" in act_lower and "leg" in c_title)
                    or ("raise" in act_lower and "raise" in c_title)
                    or ("snack" in act_lower and "snack" in c_title)
                    or ("protein" in act_lower and "protein" in c_title)
                    or ("breath" in act_lower and "breath" in c_title)
                    or ("stretch" in act_lower and "stretch" in c_title)
                    or ("walk" in act_lower and "walk" in c_title)
                    or ("all" in act_lower or "everything" in act_lower)
                ):
                    rec.status = "completed"
                    session.add(rec)
                    session.commit()
                    session.refresh(rec)
                    return rec

        # 3. Fallback: Mark the first active recommendation for this patient
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


recommendation_service = RecommendationService()
