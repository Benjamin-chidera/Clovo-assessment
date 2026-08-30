from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(SQLModel, table=True):
    """
    Immutable compliance audit log recording clinician access to patient conversations and medical records.
    """
    __tablename__ = "audit_logs"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    user_id: str = Field(default="clinician_1", index=True)
    user_name: str = Field(default="Dr. Sarah Collins")
    user_role: str = Field(default="clinician", index=True)
    action: str = Field(index=True, description="e.g. VIEW_CONVERSATION, RESOLVE_SAFETY_EVENT, UNMASK_PII")
    patient_id: Optional[int] = Field(default=None, index=True)
    conversation_id: Optional[str] = Field(default=None, index=True)
    access_reason: str = Field(description="Clinical reason for accessing patient data")
    ip_address: Optional[str] = Field(default="127.0.0.1")
    created_at: datetime = Field(default_factory=get_utc_now, index=True)
