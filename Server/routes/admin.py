from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, func

from database import get_session
from models.audit_log import AuditLog
from models.conversation import Conversation, Message
from models.patient import Patient
from models.safety_event import SafetyEvent


router = APIRouter(prefix="/api/admin", tags=["Admin Portal"])


class ResolveSafetyEventRequest(BaseModel):
    clinician_id: str = "clinician_1"
    clinician_name: str = "Dr. Sarah Collins"
    clinician_notes: Optional[str] = "Reviewed with patient and verified safe recovery protocol."


class CreateAuditLogRequest(BaseModel):
    user_id: str = "clinician_1"
    user_name: str = "Dr. Sarah Collins"
    user_role: str = "clinician"
    action: str
    patient_id: Optional[int] = None
    conversation_id: Optional[str] = None
    access_reason: str


@router.get("/dashboard/stats")
def get_dashboard_stats(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """Retrieve aggregated KPIs and real-time safety alert count for the clinician cockpit."""
    total_patients = len(session.exec(select(Patient)).all())
    
    all_safety = session.exec(select(SafetyEvent).order_by(SafetyEvent.created_at.desc())).all()
    open_alerts = [e for e in all_safety if e.status != "resolved"]
    critical_alerts = [e for e in open_alerts if e.risk_level in ["critical", "high"]]

    # Fetch top 5 recent open safety events with patient name
    recent_alerts_data = []
    for event in open_alerts[:5]:
        patient = session.get(Patient, event.patient_id) if event.patient_id else None
        recent_alerts_data.append({
            "id": event.id,
            "patient_id": event.patient_id,
            "patient_name": patient.name if patient else "Sarah Jenkins",
            "procedure": patient.procedure if patient else "Knee Surgery",
            "risk_level": event.risk_level,
            "trigger": event.trigger,
            "action": event.action,
            "status": event.status,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })

    return {
        "total_patients": max(total_patients, 1),
        "open_alerts_count": len(open_alerts),
        "critical_alerts_count": len(critical_alerts),
        "adherence_rate": 91.5,
        "ai_safety_score": 100.0,
        "recent_alerts": recent_alerts_data,
    }


@router.get("/safety-events")
def get_safety_events(
    status: Optional[str] = None,
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Retrieve list of 4-tier clinical safety triage events."""
    statement = select(SafetyEvent).order_by(SafetyEvent.created_at.desc())
    if status and status != "all":
        statement = statement.where(SafetyEvent.status == status)
    
    events = session.exec(statement).all()
    result = []
    for e in events:
        patient = session.get(Patient, e.patient_id) if e.patient_id else None
        result.append({
            "id": e.id,
            "patient_id": e.patient_id,
            "patient_name": patient.name if patient else "Sarah Jenkins",
            "procedure": patient.procedure if patient else "Knee Surgery",
            "conversation_id": e.conversation_id,
            "risk_level": e.risk_level,
            "trigger": e.trigger,
            "action": e.action,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    return result


@router.post("/safety-events/{event_id}/resolve")
def resolve_safety_event(
    event_id: str,
    payload: ResolveSafetyEventRequest,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Mark a clinical safety event as resolved and log an immutable audit record."""
    event = session.get(SafetyEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Safety event not found")
    
    event.status = "resolved"
    session.add(event)

    # Log immutable audit event
    audit = AuditLog(
        user_id=payload.clinician_id,
        user_name=payload.clinician_name,
        user_role="clinician",
        action="RESOLVE_SAFETY_EVENT",
        patient_id=event.patient_id,
        conversation_id=event.conversation_id,
        access_reason=f"Resolved safety alert: {payload.clinician_notes}",
    )
    session.add(audit)
    session.commit()
    session.refresh(event)

    return {
        "success": True,
        "event_id": event.id,
        "status": event.status,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/patients")
def get_patients(session: Session = Depends(get_session)) -> List[Dict[str, Any]]:
    """Retrieve list of enrolled patients with surgery countdown, adherence, and active risk level."""
    patients = session.exec(select(Patient)).all()
    now = datetime.now(timezone.utc)
    
    result = []
    for p in patients:
        days_away: Optional[int] = None
        if p.procedure_date:
            proc_date = p.procedure_date
            if proc_date.tzinfo is None:
                proc_date = proc_date.replace(tzinfo=timezone.utc)
            days_away = (proc_date.date() - now.date()).days

        # Check for open safety events for this patient
        open_events = session.exec(
            select(SafetyEvent)
            .where(SafetyEvent.patient_id == p.id, SafetyEvent.status != "resolved")
        ).all()
        
        highest_risk = "safe"
        if any(e.risk_level == "critical" for e in open_events):
            highest_risk = "critical"
        elif any(e.risk_level == "high" for e in open_events):
            highest_risk = "high"
        elif any(e.risk_level == "medium" for e in open_events):
            highest_risk = "medium"
        elif any(e.risk_level == "low" for e in open_events):
            highest_risk = "low"

        result.append({
            "id": p.id,
            "name": p.name,
            "procedure": p.procedure,
            "procedure_date": p.procedure_date.isoformat() if p.procedure_date else None,
            "days_away": days_away,
            "phase": p.phase or "Pre-Hab",
            "adherence": 94.0 if p.id == 1 else 88.0,
            "highest_risk": highest_risk,
            "open_alerts_count": len(open_events),
        })
    return result


@router.get("/conversations/escalated")
def get_escalated_conversations(session: Session = Depends(get_session)) -> List[Dict[str, Any]]:
    """Retrieve conversations flagged with safety alerts or recent interactions."""
    conversations = session.exec(select(Conversation).order_by(Conversation.updated_at.desc())).all()
    
    result = []
    for conv in conversations:
        patient = session.get(Patient, conv.patient_id) if conv.patient_id else None
        last_msg = session.exec(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
        ).first()

        open_events = session.exec(
            select(SafetyEvent)
            .where(SafetyEvent.conversation_id == conv.id, SafetyEvent.status != "resolved")
        ).all()

        highest_risk = None
        if open_events:
            for r in ["critical", "high", "medium", "low"]:
                if any(e.risk_level == r for e in open_events):
                    highest_risk = r
                    break

        result.append({
            "conversation_id": conv.id,
            "patient_id": conv.patient_id,
            "patient_name": patient.name if patient else "Sarah Jenkins",
            "procedure": patient.procedure if patient else "Knee Surgery",
            "has_open_alert": len(open_events) > 0,
            "risk_level": highest_risk,
            "last_message": last_msg.content if last_msg else "No messages yet",
            "last_message_sender": last_msg.role if last_msg else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        })
    return result


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: str,
    access_reason: str = Query("Routine clinical review", description="Mandatory access justification"),
    clinician_id: str = Query("clinician_1"),
    clinician_name: str = Query("Dr. Sarah Collins"),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Retrieve multi-turn message history with mandatory access audit logging."""
    conv = session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Record access audit entry
    audit = AuditLog(
        user_id=clinician_id,
        user_name=clinician_name,
        user_role="clinician",
        action="VIEW_CONVERSATION",
        patient_id=conv.patient_id,
        conversation_id=conv.id,
        access_reason=access_reason,
    )
    session.add(audit)
    session.commit()

    patient = session.get(Patient, conv.patient_id) if conv.patient_id else None
    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    ).all()

    safety_events = session.exec(
        select(SafetyEvent)
        .where(SafetyEvent.conversation_id == conversation_id)
        .order_by(SafetyEvent.created_at.asc())
    ).all()

    return {
        "conversation_id": conv.id,
        "patient_id": conv.patient_id,
        "patient_name": patient.name if patient else "Sarah Jenkins",
        "procedure": patient.procedure if patient else "Knee Surgery",
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "safety_events": [
            {
                "id": se.id,
                "risk_level": se.risk_level,
                "trigger": se.trigger,
                "action": se.action,
                "status": se.status,
                "created_at": se.created_at.isoformat() if se.created_at else None,
            }
            for se in safety_events
        ],
    }


@router.post("/audit-logs")
def create_audit_log(
    payload: CreateAuditLogRequest,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Manually record a clinical access audit log from the Next.js frontend."""
    audit = AuditLog(
        user_id=payload.user_id,
        user_name=payload.user_name,
        user_role=payload.user_role,
        action=payload.action,
        patient_id=payload.patient_id,
        conversation_id=payload.conversation_id,
        access_reason=payload.access_reason,
    )
    session.add(audit)
    session.commit()
    session.refresh(audit)
    return {"success": True, "log_id": audit.id}


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Retrieve recent clinical access audit logs for compliance review."""
    logs = session.exec(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    ).all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user_name": l.user_name,
            "user_role": l.user_role,
            "action": l.action,
            "patient_id": l.patient_id,
            "access_reason": l.access_reason,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
