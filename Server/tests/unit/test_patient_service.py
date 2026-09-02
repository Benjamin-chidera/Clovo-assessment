import pytest
from datetime import date, timedelta
from sqlmodel import Session, select
from models.patient import Patient
from models.recommendation import Recommendation
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
