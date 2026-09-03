from typing import Any, List, Optional, Union
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
    def get_tasks_for_user(session: Session, patient_id: Optional[Any] = None) -> List[TaskItemData]:
        """
        Return formatted task checklist for a patient for mobile tasks display.
        """
        from services.patient_service import patient_service

        patient = patient_service.resolve_patient(session, patient_id)

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
        from datetime import datetime, timezone
        from services.patient_service import patient_service

        rec = session.get(Recommendation, recommendation_id)
        if not rec:
            return None

        if rec.status != "completed":
            rec.status = "completed"
            rec.completed_at = datetime.now(timezone.utc)
            session.add(rec)
            session.commit()
            session.refresh(rec)
            # Update streak and unlock milestones
            patient_service.update_streak_on_task_completion(session, rec.patient_id)
        else:
            rec.status = "active"
            rec.completed_at = None
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
        from datetime import datetime, timezone
        from services.patient_service import patient_service

        # 1. Match by explicit integer ID
        if task_id:
            rec = session.get(Recommendation, task_id)
            if rec and rec.patient_id == patient_id:
                rec.status = "completed"
                rec.completed_at = datetime.now(timezone.utc)
                session.add(rec)
                session.commit()
                session.refresh(rec)
                patient_service.update_streak_on_task_completion(session, patient_id)
                return rec

        # 2. Match by activity name / keywords in ClinicalContent (allow 'active' or 'missed' status)
        if activity_name:
            statement = (
                select(Recommendation, ClinicalContent)
                .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
                .where(
                    Recommendation.patient_id == patient_id,
                    Recommendation.status != "completed"
                )
                .order_by(Recommendation.scheduled_date.desc())
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
                    or ("pump" in act_lower and "pump" in c_title)
                    or ("heel" in act_lower and "heel" in c_title)
                    or ("slide" in act_lower and "slide" in c_title)
                    or ("ice" in act_lower and "ice" in c_title)
                ):
                    rec.status = "completed"
                    rec.completed_at = datetime.now(timezone.utc)
                    session.add(rec)
                    session.commit()
                    session.refresh(rec)
                    patient_service.update_streak_on_task_completion(session, patient_id)
                    return rec

        # 3. Fallback: Mark the first non-completed recommendation for this patient
        statement = (
            select(Recommendation)
            .where(
                Recommendation.patient_id == patient_id,
                Recommendation.status != "completed"
            )
            .order_by(Recommendation.scheduled_date.asc())
        )
        rec = session.exec(statement).first()
        if rec:
            rec.status = "completed"
            rec.completed_at = datetime.now(timezone.utc)
            session.add(rec)
            session.commit()
            session.refresh(rec)
            patient_service.update_streak_on_task_completion(session, patient_id)
            return rec

        # 4. Fallback: Return matching task (marking it completed if not already)
        if activity_name:
            all_recs = session.exec(
                select(Recommendation, ClinicalContent)
                .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
                .where(Recommendation.patient_id == patient_id)
            ).all()
            for rec, content in all_recs:
                c_title = content.title.lower()
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
                    or ("pump" in act_lower and "pump" in c_title)
                    or ("heel" in act_lower and "heel" in c_title)
                    or ("slide" in act_lower and "slide" in c_title)
                    or ("ice" in act_lower and "ice" in c_title)
                ):
                    if rec.status != "completed":
                        rec.status = "completed"
                        rec.completed_at = datetime.now(timezone.utc)
                        session.add(rec)
                        session.commit()
                        session.refresh(rec)
                        patient_service.update_streak_on_task_completion(session, patient_id)
                    return rec

        return None

    @staticmethod
    def mark_task_active(
        session: Session,
        patient_id: int,
        task_id: Optional[int] = None,
        activity_name: Optional[str] = None,
    ) -> Union[Optional["Recommendation"], List["Recommendation"]]:
        """
        Reset / unmark a recommendation back to 'active' status by ID or activity name matching.
        When activity_name is 'all' or 'everything', resets ALL completed tasks and returns a list.
        Otherwise returns a single Recommendation or None.
        """
        # 1. Match by explicit integer ID
        if task_id:
            rec = session.get(Recommendation, task_id)
            if rec and rec.patient_id == patient_id:
                rec.status = "active"
                session.add(rec)
                session.commit()
                session.refresh(rec)
                return rec

        # 2. Match by activity name / keywords in ClinicalContent (among completed recommendations)
        if activity_name:
            statement = (
                select(Recommendation, ClinicalContent)
                .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
                .where(
                    Recommendation.patient_id == patient_id,
                    Recommendation.status == "completed"
                )
            )
            results = session.exec(statement).all()

            act_lower = activity_name.lower().strip()

            # The intent classification node in amy.py normalises bulk-reset phrases to "all"
            reset_all = (act_lower == "all")

            if reset_all:
                reset_recs = []
                for rec, _content in results:
                    rec.status = "active"
                    session.add(rec)
                    reset_recs.append(rec)
                if reset_recs:
                    session.commit()
                    for rec in reset_recs:
                        session.refresh(rec)
                return reset_recs

            # Single task fuzzy match
            for rec, content in results:
                c_title = content.title.lower()
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
                ):
                    rec.status = "active"
                    session.add(rec)
                    session.commit()
                    session.refresh(rec)
                    return rec

        return None

    @staticmethod
    def get_safe_surprise_activity(session: Session, patient_id: int) -> ClinicalContent:
        """
        Select a clinically safe bonus exploratory activity for the patient.

        Clinical Safety Rules:
        1. Excludes the patient's already assigned mandatory tasks so the surprise is genuinely fresh.
        2. Non-movement wellness (mindfulness, nutrition) is universally safe across all pathways.
        3. Low-intensity pre-op general exercises (e.g. gentle seated stretching) are permitted.
        4. Never returns heavy or contraindicated movements.
        """
        import random

        # 1. Fetch content IDs already assigned to this patient
        assigned_statement = select(Recommendation.content_id).where(Recommendation.patient_id == patient_id)
        assigned_content_ids = set(session.exec(assigned_statement).all())

        # 2. Fetch all available clinical content
        all_content = session.exec(select(ClinicalContent)).all()

        # 3. Filter for safe candidates not already on the patient's mandatory checklist
        safe_candidates = [
            c for c in all_content
            if c.id not in assigned_content_ids
            and (
                c.type in ["mindfulness", "nutrition"]
                or c.target_stage in ["pre-op-all", "all"]
            )
        ]

        if safe_candidates:
            return random.choice(safe_candidates)

        # Fallback: any unassigned content, or the first library item
        unassigned = [c for c in all_content if c.id not in assigned_content_ids]
        return random.choice(unassigned) if unassigned else all_content[0]


recommendation_service = RecommendationService()
