from datetime import datetime, timezone, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from sqlmodel import Session, select
from models.patient import Patient, PatientHomeData, UserProfileData
from models.recommendation import Recommendation, PreparationItem
from models.clinical_content import ClinicalContent
from models.milestone import Milestone, PatientMilestone, MilestoneDTO


class PatientService:
    @staticmethod
    def get_patient_by_id(session: Session, patient_id: int) -> Optional[Patient]:
        return session.get(Patient, patient_id)

    @staticmethod
    def get_patient_by_name(session: Session, name: str) -> Optional[Patient]:
        statement = select(Patient).where(Patient.name == name)
        return session.exec(statement).first()

    @staticmethod
    def list_patients(session: Session) -> List[Patient]:
        statement = select(Patient).order_by(Patient.id.asc())
        return list(session.exec(statement).all())

    @staticmethod
    def get_or_create_default_patient(session: Session) -> Patient:
        """
        Retrieves or seeds the default patient (Sarah) with surgery scheduled 21 days away,
        clean 0-streak baseline, and pending personalized recommendations.
        """
        patient = PatientService.get_patient_by_name(session, "Sarah")
        if not patient:
            now = datetime.now(timezone.utc)
            procedure_date = now + timedelta(days=21)

            patient = Patient(
                name="Sarah",
                email="sarah@clovo.app",
                avatar_uri="https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80",
                plan="Pre-Op Preparation",
                streak_count=0,
                last_active_date=None,
                total_completed_tasks=0,
                age=38,
                pathway="Pre-Op Orthopedic",
                procedure="Knee Surgery",
                procedure_date=procedure_date,
                preferences="Prefers gentle morning routines and walking",
            )
            session.add(patient)
            session.commit()
            session.refresh(patient)

            # Seed initial recommendations (all starting active/pending)
            initial_recommendations = [
                Recommendation(
                    patient_id=patient.id,
                    content_id=1,
                    duration_minutes=10,
                    repetitions=10,
                    scheduled_date=date.today(),
                    status="active",
                    completed_at=None,
                    notes="Recommended in the morning",
                ),
                Recommendation(
                    patient_id=patient.id,
                    content_id=4,
                    duration_minutes=5,
                    repetitions=4,
                    scheduled_date=date.today(),
                    status="active",
                    completed_at=None,
                    notes="Recommended before bedtime",
                ),
                Recommendation(
                    patient_id=patient.id,
                    content_id=3,
                    duration_minutes=10,
                    repetitions=None,
                    scheduled_date=date.today(),
                    status="active",
                    completed_at=None,
                    notes="Mid-morning protein snack",
                ),
            ]
            for rec in initial_recommendations:
                session.add(rec)
            session.commit()

        # Unlock milestones strictly earned by real completed tasks and streak
        PatientService.check_and_unlock_milestones(session, patient.id)

        return patient

    @staticmethod
    def get_or_create_post_op_patient(session: Session) -> Patient:
        """
        Retrieves or seeds the post-op patient (Jane) who recently completed knee replacement surgery
        (6 days ago) and is actively participating in rehabilitation.
        """
        patient = PatientService.get_patient_by_name(session, "Jane")
        if not patient:
            now = datetime.now(timezone.utc)
            procedure_date = now - timedelta(days=6)

            patient = Patient(
                name="Jane",
                email="jane@clovo.app",
                avatar_uri="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
                plan="Post-Op Rehabilitation",
                phase="post-op",
                streak_count=4,
                last_active_date=date.today(),
                total_completed_tasks=5,
                age=42,
                pathway="Post-Op Orthopedic Rehab",
                procedure="Knee Replacement",
                procedure_date=procedure_date,
                preferences="Focusing on knee swelling reduction, range of motion flexion, and crutch walking",
            )
            session.add(patient)
            session.commit()
            session.refresh(patient)

            # Seed post-op recommendations
            initial_recommendations = [
                Recommendation(
                    patient_id=patient.id,
                    content_id=8,
                    duration_minutes=10,
                    repetitions=20,
                    scheduled_date=date.today(),
                    status="active",
                    completed_at=None,
                    notes="Recommended 3x daily with leg elevated",
                ),
                Recommendation(
                    patient_id=patient.id,
                    content_id=9,
                    duration_minutes=10,
                    repetitions=10,
                    scheduled_date=date.today(),
                    status="active",
                    completed_at=None,
                    notes="Gentle range-of-motion to comfortable tension",
                ),
                Recommendation(
                    patient_id=patient.id,
                    content_id=10,
                    duration_minutes=20,
                    repetitions=None,
                    scheduled_date=date.today(),
                    status="active",
                    completed_at=None,
                    notes="Apply cold pack after walking or exercises",
                ),
                Recommendation(
                    patient_id=patient.id,
                    content_id=11,
                    duration_minutes=10,
                    repetitions=None,
                    scheduled_date=date.today(),
                    status="active",
                    completed_at=None,
                    notes="Gentle walking with crutches on flat surface",
                ),
            ]
            for rec in initial_recommendations:
                session.add(rec)
            session.commit()

            # Unlock initial circulation hero milestone for Jane
            pm = PatientMilestone(
                patient_id=patient.id,
                milestone_id=8,
                unlocked_at=datetime.now(timezone.utc),
            )
            session.add(pm)
            session.commit()

        # Unlock milestones strictly earned by real completed tasks and streak
        PatientService.check_and_unlock_milestones(session, patient.id)

        return patient

    @staticmethod
    def seed_default_patients(session: Session) -> Tuple[Patient, Patient]:
        """Ensures both Sarah (pre-op) and Jane (post-op) exist in the database."""
        sarah = PatientService.get_or_create_default_patient(session)
        jane = PatientService.get_or_create_post_op_patient(session)
        return sarah, jane

    @staticmethod
    def resolve_patient(session: Session, identifier: Any = None) -> Patient:
        """
        Resolves a patient from any identifier (ID integer, string ID, name, or token).
        Supports:
          - 1, '1', 'patient-sarah', 'sarah' -> Sarah (Pre-Op)
          - 2, '2', 'patient-jane', 'jane' -> Jane (Post-Op)
        """
        if identifier is None:
            return PatientService.get_or_create_default_patient(session)

        id_str = str(identifier).strip().lower()

        if "jane" in id_str or id_str == "2":
            jane = PatientService.get_patient_by_name(session, "Jane")
            if not jane:
                jane = PatientService.get_or_create_post_op_patient(session)
            return jane

        if id_str.isdigit():
            pid = int(id_str)
            p = session.get(Patient, pid)
            if p:
                return p

        sarah = PatientService.get_patient_by_name(session, "Sarah")
        if not sarah:
            sarah = PatientService.get_or_create_default_patient(session)
        return sarah



    @staticmethod
    def get_patient_milestones(session: Session, patient_id: int) -> Tuple[List[MilestoneDTO], int]:
        """
        Retrieves unlocked milestones for a patient and computes additional badge count.
        """
        statement = (
            select(Milestone, PatientMilestone)
            .join(PatientMilestone, Milestone.id == PatientMilestone.milestone_id)
            .where(PatientMilestone.patient_id == patient_id)
            .order_by(PatientMilestone.unlocked_at.desc())
        )
        results = session.exec(statement).all()

        seen_milestone_ids = set()
        milestones_dto: List[MilestoneDTO] = []
        for m, pm in results:
            if m.id in seen_milestone_ids:
                continue
            seen_milestone_ids.add(m.id)
            milestones_dto.append(
                MilestoneDTO(
                    id=str(m.id),
                    code=m.code,
                    title=m.title,
                    description=m.description,
                    icon_name=m.icon_name,
                    color=m.color,
                    bg_gradient=[m.bg_gradient_start, m.bg_gradient_end],
                    unlocked_at=pm.unlocked_at.isoformat() if pm.unlocked_at else None,
                )
            )

        additional_count = max(0, len(milestones_dto) - 3)
        return milestones_dto, additional_count

    @staticmethod
    def audit_daily_adherence_and_missed_tasks(session: Session, patient_id: int) -> Dict[str, Any]:
        """
        Audits scheduled tasks vs completion. Marks past uncompleted tasks as 'missed'
        and returns missed task summary for Amy's empathetic coaching prompts and clinician reporting.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Find any past recommendations that were left as 'active'
        past_active_statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(
                Recommendation.patient_id == patient_id,
                Recommendation.scheduled_date < today,
                Recommendation.status == "active",
            )
        )
        past_active = session.exec(past_active_statement).all()

        missed_yesterday_titles: List[str] = []
        for rec, content in past_active:
            rec.status = "missed"
            session.add(rec)
            if rec.scheduled_date == yesterday:
                missed_yesterday_titles.append(content.title)
        
        if past_active:
            session.commit()

        # Count consecutive missed days
        consecutive_missed = 0
        current_check_date = yesterday
        while consecutive_missed < 7:
            day_recs = session.exec(
                select(Recommendation).where(
                    Recommendation.patient_id == patient_id,
                    Recommendation.scheduled_date == current_check_date,
                )
            ).all()

            if not day_recs:
                break

            all_day_missed = all(r.status in ["missed", "skipped"] for r in day_recs)
            if all_day_missed:
                consecutive_missed += 1
                current_check_date -= timedelta(days=1)
            else:
                break

        return {
            "has_missed_yesterday": len(missed_yesterday_titles) > 0,
            "missed_yesterday_titles": missed_yesterday_titles,
            "consecutive_missed_days": consecutive_missed,
            "requires_clinician_alert": consecutive_missed >= 2,
        }

    @staticmethod
    def check_and_unlock_milestones(session: Session, patient_id: int) -> List[str]:
        """
        Evaluates patient progress and unlocks newly achieved milestones.
        Returns list of newly unlocked milestone titles.
        """
        patient = session.get(Patient, patient_id)
        if not patient:
            return []

        all_milestones = session.exec(select(Milestone)).all()
        existing_pms = session.exec(
            select(PatientMilestone).where(PatientMilestone.patient_id == patient_id)
        ).all()
        unlocked_milestone_ids = {pm.milestone_id for pm in existing_pms}

        # Query completed recommendation content IDs
        completed_recs = session.exec(
            select(Recommendation).where(
                Recommendation.patient_id == patient_id,
                Recommendation.status == "completed",
            )
        ).all()
        completed_content_ids = {r.content_id for r in completed_recs}
        total_completed = max(len(completed_recs), patient.total_completed_tasks or 0)

        newly_unlocked_titles: List[str] = []
        now = datetime.now(timezone.utc)

        for m in all_milestones:
            if m.id in unlocked_milestone_ids:
                continue

            unlocked = False
            if m.criteria_type == "streak_days" and (patient.streak_count or 0) >= m.criteria_threshold:
                unlocked = True
            elif m.criteria_type == "completed_tasks" and total_completed >= m.criteria_threshold:
                unlocked = True
            elif m.criteria_type == "specific_exercise":
                if m.code == "quad_master" and (1 in completed_content_ids or total_completed >= 1):
                    unlocked = True
                elif m.code == "mindful_zen" and 4 in completed_content_ids:
                    unlocked = True
                elif m.code == "protein_champ" and 3 in completed_content_ids:
                    unlocked = True

            if unlocked:
                pm = PatientMilestone(patient_id=patient_id, milestone_id=m.id, unlocked_at=now)
                session.add(pm)
                newly_unlocked_titles.append(m.title)

        if newly_unlocked_titles:
            session.commit()

        return newly_unlocked_titles


    @staticmethod
    def update_streak_on_task_completion(session: Session, patient_id: int) -> int:
        """
        Recalculates streak count and lifetime completed tasks when a task is completed.
        """
        patient = session.get(Patient, patient_id)
        if not patient:
            return 5

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Update total completed tasks
        completed_count = session.exec(
            select(Recommendation).where(
                Recommendation.patient_id == patient_id,
                Recommendation.status == "completed",
            )
        ).all()
        patient.total_completed_tasks = len(completed_count)

        # Calculate streak logic
        if patient.last_active_date is None or (patient.streak_count or 0) == 0:
            patient.streak_count = 1
            patient.last_active_date = today
        elif patient.last_active_date == yesterday:
            patient.streak_count += 1
            patient.last_active_date = today
        elif patient.last_active_date < yesterday:
            # Missed a day -> reset to 1
            patient.streak_count = 1
            patient.last_active_date = today
        # If last_active_date == today and streak_count > 0, streak is already maintained for today

        session.add(patient)
        session.commit()
        session.refresh(patient)


        # Check for newly unlocked milestones
        PatientService.check_and_unlock_milestones(session, patient_id)

        return patient.streak_count

    @staticmethod
    def get_user_profile(session: Session, patient_id: Optional[int] = None) -> UserProfileData:
        """
        Retrieves formatted user profile for the current/selected patient from the database.
        """
        patient = PatientService.resolve_patient(session, patient_id)

        # Audit adherence on profile fetch
        PatientService.audit_daily_adherence_and_missed_tasks(session, patient.id)

        is_post_op = (patient.phase == "post-op") or (patient.plan and "post-op" in patient.plan.lower())
        days_away = 0
        days_post_op: Optional[int] = None
        surgery_title = "Your surgery"

        if patient.procedure_date:
            now = datetime.now(timezone.utc)
            proc_date = patient.procedure_date
            if proc_date.tzinfo is None:
                proc_date = proc_date.replace(tzinfo=timezone.utc)
            
            if is_post_op:
                days_diff = (now.date() - proc_date.date()).days
                days_post_op = max(1, days_diff)
                surgery_title = f"Day {days_post_op} Post-Op"
            else:
                days_diff = (proc_date.date() - now.date()).days
                days_away = max(0, days_diff)
                surgery_title = "Your surgery"
        elif is_post_op:
            surgery_title = "Recovery Day"
            days_post_op = 6

        current_hour = datetime.now().hour
        time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"

        milestones_dto, additional_count = PatientService.get_patient_milestones(session, patient.id)

        return UserProfileData(
            id=patient.id,
            name=patient.name,
            email=patient.email or f"{patient.name.lower()}@clovo.app",
            avatar_uri=patient.avatar_uri,
            plan=patient.plan or ("Post-Op Rehabilitation" if is_post_op else "Pre-Op Preparation"),
            phase="post-op" if is_post_op else "pre-op",
            streak_count=patient.streak_count if patient.streak_count is not None else 4,
            greeting=f"{time_greeting}, {patient.name}",
            surgery_title=surgery_title,
            days_away=days_away,
            days_post_op=days_post_op,
            procedure_name=patient.procedure or ("Knee Replacement" if is_post_op else "Knee Surgery"),
            procedure_date=patient.procedure_date,
            milestones=milestones_dto,
            additional_milestones_count=additional_count,
            total_completed_tasks=patient.total_completed_tasks or len(milestones_dto),
        )

    @staticmethod
    def get_patient_home_data(session: Session, patient_id: Any = None) -> PatientHomeData:
        """
        Calculates and returns home page dashboard data with joined clinical content details,
        unlocked milestone badges, and live adherence metrics.
        """
        patient = PatientService.resolve_patient(session, patient_id)

        # Audit adherence on home fetch
        PatientService.audit_daily_adherence_and_missed_tasks(session, patient.id)

        is_post_op = (patient.phase == "post-op") or (patient.plan and "post-op" in patient.plan.lower())
        days_away = 0
        days_post_op: Optional[int] = None
        surgery_title = "Your surgery"

        if patient.procedure_date:
            now = datetime.now(timezone.utc)
            proc_date = patient.procedure_date
            if proc_date.tzinfo is None:
                proc_date = proc_date.replace(tzinfo=timezone.utc)

            if is_post_op:
                days_diff = (now.date() - proc_date.date()).days
                days_post_op = max(1, days_diff)
                surgery_title = f"Day {days_post_op} Post-Op"
            else:
                days_diff = (proc_date.date() - now.date()).days
                days_away = max(0, days_diff)
                surgery_title = "Your surgery"
        elif is_post_op:
            surgery_title = "Recovery Day"
            days_post_op = 6

        current_hour = datetime.now().hour
        time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
        greeting = f"{time_greeting}, {patient.name}"

        # Join Recommendation with ClinicalContent
        rec_statement = (
            select(Recommendation, ClinicalContent)
            .join(ClinicalContent, Recommendation.content_id == ClinicalContent.id)
            .where(Recommendation.patient_id == patient.id)
            .order_by(Recommendation.scheduled_date.asc())
        )
        results = session.exec(rec_statement).all()

        preparations = [
            PreparationItem(
                id=rec.id,
                title=content.title,
                is_completed=(rec.status == "completed"),
                type=content.type,
                instruction=content.description,
                rationale=content.rationale,
                image_url=content.image_url,
                icon_name=content.icon_name,
                duration_minutes=rec.duration_minutes,
                repetitions=rec.repetitions,
                notes=rec.notes,
            )
            for rec, content in results
        ]

        milestones_dto, additional_count = PatientService.get_patient_milestones(session, patient.id)

        return PatientHomeData(
            greeting=greeting,
            patient_name=patient.name,
            surgery_title=surgery_title,
            days_away=days_away,
            days_post_op=days_post_op,
            phase="post-op" if is_post_op else "pre-op",
            procedure_name=patient.procedure or ("Knee Replacement" if is_post_op else "Knee Surgery"),
            procedure_date=patient.procedure_date,
            streak_count=patient.streak_count if patient.streak_count is not None else 4,
            milestones=milestones_dto,
            additional_milestones_count=additional_count,
            total_completed_tasks=patient.total_completed_tasks or len(milestones_dto),
            preparations=preparations,
        )


patient_service = PatientService()

