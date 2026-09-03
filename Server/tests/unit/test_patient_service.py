import pytest
from datetime import date, timedelta
from sqlmodel import Session, select
from models.patient import Patient
from models.recommendation import Recommendation
from models.clinical_content import ClinicalContent
from services.patient_service import patient_service


class TestPatientService:
    """Unit tests for patient adherence auditing, streak calculation, and milestones."""

    def test_audit_daily_adherence_no_missed_tasks(self, db_session: Session):
        """SRV-UNIT-PAT-001: Patient with all tasks completed yesterday reports zero missed days."""
        yesterday = date.today() - timedelta(days=1)
        # Add a completed recommendation for yesterday
        rec_yesterday = Recommendation(
            patient_id=1,
            content_id=1,
            duration_minutes=10,
            scheduled_date=yesterday,
            status="completed",
        )
        db_session.add(rec_yesterday)
        db_session.commit()

        audit = patient_service.audit_daily_adherence_and_missed_tasks(db_session, 1)
        assert audit["has_missed_yesterday"] is False
        assert audit["consecutive_missed_days"] == 0
        assert audit["requires_clinician_alert"] is False

    def test_audit_consecutive_missed_days_alerts_clinician(self, db_session: Session):
        """SRV-UNIT-PAT-002: Patient missing tasks for 2+ consecutive days triggers care team alert."""
        day_1 = date.today() - timedelta(days=1)
        day_2 = date.today() - timedelta(days=2)

        # Seed missed recommendations for 2 consecutive past days
        r1 = Recommendation(patient_id=1, content_id=1, scheduled_date=day_1, status="active")
        r2 = Recommendation(patient_id=1, content_id=2, scheduled_date=day_2, status="missed")
        db_session.add(r1)
        db_session.add(r2)
        db_session.commit()

        audit = patient_service.audit_daily_adherence_and_missed_tasks(db_session, 1)
        assert audit["consecutive_missed_days"] >= 2
        assert audit["requires_clinician_alert"] is True

    def test_update_streak_on_task_completion(self, db_session: Session):
        """SRV-UNIT-PAT-003: Completing a task increments streak and updates lifetime completed count."""
        patient = db_session.get(Patient, 1)
        assert patient is not None
        initial_completed = patient.total_completed_tasks or 0

        # Mark recommendation #1 completed
        rec = db_session.exec(select(Recommendation).where(Recommendation.id == 1)).first()
        assert rec is not None
        rec.status = "completed"
        db_session.add(rec)
        db_session.commit()

        new_streak = patient_service.update_streak_on_task_completion(db_session, 1)
        assert new_streak >= 1

        db_session.refresh(patient)
        assert patient.total_completed_tasks >= initial_completed + 1
        assert patient.last_active_date == date.today()

    def test_get_patient_home_data_format(self, db_session: Session):
        """SRV-UNIT-PAT-004: get_patient_home_data formats preparations and surgery days away."""
        home_data = patient_service.get_patient_home_data(db_session, 1)
        assert home_data.patient_name == "Sarah"
        assert len(home_data.preparations) > 0
        assert home_data.days_away >= 0
        assert home_data.streak_count >= 0
        assert home_data.phase == "pre-op"

    def test_resolve_patient_multi_user(self, db_session: Session):
        """SRV-UNIT-PAT-005: resolve_patient correctly distinguishes Sarah (pre-op) and Jane (post-op)."""
        sarah_by_str = patient_service.resolve_patient(db_session, "patient-sarah")
        assert sarah_by_str.name == "Sarah"
        assert sarah_by_str.phase == "pre-op"

        jane_by_str = patient_service.resolve_patient(db_session, "patient-jane")
        assert jane_by_str.name == "Jane"
        assert jane_by_str.phase == "post-op"

        jane_by_name = patient_service.resolve_patient(db_session, "Jane")
        assert jane_by_name.id == jane_by_str.id

    def test_jane_post_op_home_and_profile_data(self, db_session: Session):
        """SRV-UNIT-PAT-006: Jane's profile and home data reflect Day 6 Post-Op knee rehabilitation."""
        jane = patient_service.get_or_create_post_op_patient(db_session)
        profile = patient_service.get_user_profile(db_session, jane.id)
        assert profile.name == "Jane"
        assert profile.phase == "post-op"
        assert profile.days_post_op is not None and profile.days_post_op >= 1
        assert "Post-Op" in profile.surgery_title

        home_data = patient_service.get_patient_home_data(db_session, "patient-jane")
        assert home_data.patient_name == "Jane"
        assert home_data.phase == "post-op"
        assert "Post-Op" in home_data.surgery_title
        # Verify Jane's preparations are post-op clinical content
        post_op_titles = [prep.title for prep in home_data.preparations]
        assert any("Ankle Pumps" in t for t in post_op_titles)
        assert any("Heel Slides" in t for t in post_op_titles)

    def test_mark_task_completed_recovers_missed_status(self, db_session: Session):
        """SRV-UNIT-PAT-007: Completing an activity that was marked 'missed' transitions it to 'completed'."""
        from services.recommendation_service import recommendation_service

        sarah = patient_service.get_or_create_default_patient(db_session)
        # Find recommendation for 4-7-8 Breathing and simulate past missed status
        rec_statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == sarah.id)
        )
        results = db_session.exec(rec_statement).all()
        target_rec = next((r for r, c in results if "breathing" in c.title.lower()), None)
        assert target_rec is not None

        target_rec.status = "missed"
        db_session.add(target_rec)
        db_session.commit()

        # Mark completed via recommendation_service
        updated = recommendation_service.mark_task_completed(
            db_session,
            patient_id=sarah.id,
            activity_name="4-7-8 Breathing",
        )
        assert updated is not None
        assert updated.status == "completed"
        assert updated.completed_at is not None

