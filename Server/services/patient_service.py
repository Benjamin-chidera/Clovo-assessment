from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlmodel import Session, select
from models.patient import Patient, PatientHomeData, UserProfileData
from models.recommendation import Recommendation, PreparationItem


class PatientService:
    @staticmethod
    def get_patient_by_id(session: Session, patient_id: str) -> Optional[Patient]:
        return session.get(Patient, patient_id)

    @staticmethod
    def get_patient_by_name(session: Session, name: str) -> Optional[Patient]:
        statement = select(Patient).where(Patient.name == name)
        return session.exec(statement).first()

    @staticmethod
    def list_patients(session: Session) -> List[Patient]:
        statement = select(Patient).order_by(Patient.created_at.asc())
        return list(session.exec(statement).all())

    @staticmethod
    def get_or_create_default_patient(session: Session) -> Patient:
        """
        Retrieves or seeds the default patient (Sarah) with surgery scheduled 21 days away
        and today's preparation task list.
        """
        patient = PatientService.get_patient_by_name(session, "Sarah")
        if not patient:
            now = datetime.now(timezone.utc)
            procedure_date = now + timedelta(days=21)

            patient = Patient(
                id="patient-sarah",
                name="Sarah",
                email="sarah@clovo.app",
                avatar_uri="https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80",
                plan="Pre-Op Preparation",
                streak_count=5,
                age=38,
                pathway="Pre-Op Orthopedic",
                procedure="Knee Surgery",
                procedure_date=procedure_date,
                preferences="Prefers gentle morning routines and walking",
            )
            session.add(patient)
            session.commit()
            session.refresh(patient)

            # Seed Today's preparation tasks:
            # 1. ✓ 15 min walking (completed)
            # 2. ○ Mindfulness (pending)
            # 3. ○ Nutrition goal (pending)
            initial_preparations = [
                Recommendation(
                    id="prep-walk-1",
                    patient_id=patient.id,
                    type="walking",
                    title="15 min walking",
                    instruction="Maintain a steady, gentle pace for 15 minutes",
                    rationale="Build endurance and pre-op cardiovascular health",
                    status="completed",
                ),
                Recommendation(
                    id="prep-mind-2",
                    patient_id=patient.id,
                    type="mindfulness",
                    title="Mindfulness",
                    instruction="5 to 10 minutes of guided mindful breathing",
                    rationale="Reduce stress and optimize nervous system recovery",
                    status="pending",
                ),
                Recommendation(
                    id="prep-nutr-3",
                    patient_id=patient.id,
                    type="nutrition",
                    title="Nutrition goal",
                    instruction="Meet protein intake and maintain hydration target",
                    rationale="Supports cellular repair and tissue preparation",
                    status="pending",
                ),
            ]
            for prep in initial_preparations:
                session.add(prep)
            session.commit()

        return patient

    @staticmethod
    def get_user_profile(session: Session, patient_id: Optional[str] = None) -> UserProfileData:
        """
        Retrieves formatted user profile for the current/selected patient from the database.
        """
        patient: Optional[Patient] = None
        if patient_id:
            patient = PatientService.get_patient_by_id(session, patient_id)

        if not patient:
            patient = PatientService.get_or_create_default_patient(session)

        days_away = 21
        if patient.procedure_date:
            now = datetime.now(timezone.utc)
            proc_date = patient.procedure_date
            if proc_date.tzinfo is None:
                proc_date = proc_date.replace(tzinfo=timezone.utc)
            days_diff = (proc_date.date() - now.date()).days
            days_away = max(0, days_diff)

        current_hour = datetime.now().hour
        time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"

        return UserProfileData(
            id=patient.id,
            name=patient.name,
            email=patient.email or f"{patient.name.lower()}@clovo.app",
            avatar_uri=patient.avatar_uri,
            plan=patient.plan or "Pre-Op Preparation",
            streak_count=patient.streak_count if patient.streak_count is not None else 5,
            greeting=f"{time_greeting}, {patient.name}",
            surgery_title="Your surgery",
            days_away=days_away,
            procedure_name=patient.procedure or "Knee Surgery",
            procedure_date=patient.procedure_date,
        )

    @staticmethod
    def get_patient_home_data(session: Session, patient_id: Optional[str] = None) -> PatientHomeData:
        """
        Calculates and returns home page dashboard data:
        - Greeting: 'Good morning, Sarah'
        - Surgery Countdown: '21 days away'
        - Today's preparation items
        """
        patient: Optional[Patient] = None
        if patient_id:
            patient = PatientService.get_patient_by_id(session, patient_id)

        if not patient:
            patient = PatientService.get_or_create_default_patient(session)

        days_away = 21
        if patient.procedure_date:
            now = datetime.now(timezone.utc)
            proc_date = patient.procedure_date
            if proc_date.tzinfo is None: 
                proc_date = proc_date.replace(tzinfo=timezone.utc)
            days_diff = (proc_date.date() - now.date()).days
            days_away = max(0, days_diff)

        current_hour = datetime.now().hour
        time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
        greeting = f"{time_greeting}, {patient.name}"

        rec_statement = (
            select(Recommendation)
            .where(Recommendation.patient_id == patient.id)
            .order_by(Recommendation.created_at.asc())
        )
        recommendations = session.exec(rec_statement).all()

        preparations = [
            PreparationItem(
                id=rec.id,
                title=rec.title,
                is_completed=(rec.status == "completed"),
                type=rec.type,
                instruction=rec.instruction,
                rationale=rec.rationale,
            )
            for rec in recommendations
        ]

        return PatientHomeData(
            greeting=greeting,
            patient_name=patient.name,
            surgery_title="Your surgery",
            days_away=days_away,
            procedure_name=patient.procedure,
            procedure_date=patient.procedure_date,
            preparations=preparations,
        )


patient_service = PatientService()
