from datetime import datetime, timezone
from typing import List
from sqlmodel import Session, select
from models.conversation import Conversation, Message, MessageCreate
from models.safety_event import SafetyEvent
from services.safety_service import safety_service


class ConversationService:
    @staticmethod
    def get_or_create_conversation(session: Session, patient_id: str) -> Conversation:
        statement = (
            select(Conversation)
            .where(Conversation.patient_id == patient_id)
            .order_by(Conversation.created_at.desc())
        )
        conv = session.exec(statement).first()
        if not conv:
            conv = Conversation(patient_id=patient_id)
            session.add(conv)
            session.commit()
            session.refresh(conv)
        return conv

    @staticmethod
    def get_messages(session: Session, conversation_id: str) -> List[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(session.exec(statement).all())

    @staticmethod
    def add_message(session: Session, data: MessageCreate) -> Message:
        msg = Message(
            conversation_id=data.conversation_id,
            role=data.role,
            content=data.content,
        )
        session.add(msg)

        # Update conversation timestamp
        conv = session.get(Conversation, data.conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            session.add(conv)

        session.commit()
        session.refresh(msg)

        # Screen for clinical safety triggers
        safety_flag = safety_service.screen_content(msg.content)
        if safety_flag:
            trigger, risk_level, action = safety_flag
            safety_event = SafetyEvent(
                conversation_id=msg.conversation_id,
                message_id=msg.id,
                risk_level=risk_level,
                trigger=trigger,
                action=action,
                status="open",
            )
            session.add(safety_event)
            session.commit()

        return msg


conversation_service = ConversationService()
