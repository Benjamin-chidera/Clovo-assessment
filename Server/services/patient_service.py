from datetime import datetime, timezone, timedelta, date
from typing import List, Optional
from sqlmodel import Session, select
from models.patient import Patient, PatientHomeData, UserProfileData
from models.recommendation import Recommendation, PreparationItem
from models.clinical_content import ClinicalContent


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
        Retrieves or seeds the default patient (Sarah) with surgery scheduled 21 days away
        and personalized recommendations linked to the clinical content library.
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

            # Seed Today's recommendations linked to ClinicalContent:
            # 1. content_id=1: Quad Sets (completed)
            # 2. content_id=4: 4-7-8 Breathing (active)
            # 3. content_id=3: Protein Power Snack (active)
            initial_recommendations = [
                Recommendation(
                    patient_id=patient.id,
                    content_id=1,
                    duration_minutes=10,
                    repetitions=10,
                    scheduled_date=date.today(),
                    status="completed",
                    notes="Completed in the morning",
                ),
                Recommendation(
                    patient_id=patient.id,
                    content_id=4,
                    duration_minutes=5,
                    repetitions=4,
                    scheduled_date=date.today(),
                    status="active",
                    notes="Recommended before bedtime",
                ),
                Recommendation(
                    patient_id=patient.id,
                    content_id=3,
                    duration_minutes=10,
                    repetitions=None,
                    scheduled_date=date.today(),
                    status="active",
                    notes="Mid-morning protein snack",
                ),
            ]
            for rec in initial_recommendations:
                session.add(rec)
            session.commit()

        return patient

    @staticmethod
    def get_user_profile(session: Session, patient_id: Optional[int] = None) -> UserProfileData:
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
    def get_patient_home_data(session: Session, patient_id: Optional[int] = None) -> PatientHomeData:
        """
        Calculates and returns home page dashboard data with joined clinical content details.
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
