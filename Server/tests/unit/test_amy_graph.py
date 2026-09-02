import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, select
from models.recommendation import Recommendation
from services.amy import (
    CoachState,
    safety_triage_node,
    intent_classification_node,
    recommendation_action_node,
    coaching_node,
    extract_quick_replies,
)
from langchain_core.messages import AIMessage


class TestAmyGraphNodes:
    """Unit tests for LangGraph nodes in Amy's coaching pipeline."""

    def test_safety_triage_node_detects_emergency(self):
        """SRV-UNIT-GRF-001: Safety triage flags critical emergencies and sets alert state."""
        state: CoachState = {
            "session": None,
            "patient_id": 1,
            "patient_name": "Sarah",
            "procedure_name": "Total Knee Replacement",
            "days_away": 14,
            "user_message": "I want to kill myself",
            "conversation_history": [],
            "grounded_library_text": "",
            "daily_tasks_summary": "",
            "available_options": [],
            "active_recommendations": [],
            "adherence_context": "",
            "milestones_summary": "",
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }
        res = safety_triage_node(state)
        assert res["is_safety_alert"] is True
        assert res["risk_level"] == "critical"
        assert res["safety_category"] == "mental_health"

    def test_intent_classification_task_completion(self):
        """SRV-UNIT-GRF-002: Task completion intent recognized without displaying cards."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"intent": "completion", "activity": "Quad Sets"}'
        )

        state: CoachState = {
            "session": None,
            "patient_id": 1,
            "patient_name": "Sarah",
            "procedure_name": "Total Knee Replacement",
            "days_away": 14,
            "user_message": "I finished my Quad Sets today",
            "conversation_history": [],
            "grounded_library_text": "",
            "daily_tasks_summary": "",
            "available_options": [],
            "active_recommendations": [{"title": "Quad Sets", "id": 1}],
            "adherence_context": "",
            "milestones_summary": "",
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }
        with patch("services.amy.llm", mock_llm):
            res = intent_classification_node(state)
            assert res["is_task_completion"] is True
            assert res["completed_activity_name"] == "Quad Sets"
            assert res["should_show_options"] is False  # Zero card dump

    def test_intent_classification_unmarking(self):
        """SRV-UNIT-GRF-003: Task unmarking intent recognized without displaying cards."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"intent": "unmark", "activity": "Straight Leg Raise"}'
        )

        state: CoachState = {
            "session": None,
            "patient_id": 1,
            "patient_name": "Sarah",
            "procedure_name": "Total Knee Replacement",
            "days_away": 14,
            "user_message": "I haven't done straight leg raises yet",
            "conversation_history": [],
            "grounded_library_text": "",
            "daily_tasks_summary": "",
            "available_options": [],
            "active_recommendations": [{"title": "Straight Leg Raise", "id": 2}],
            "adherence_context": "",
            "milestones_summary": "",
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }
        with patch("services.amy.llm", mock_llm):
            res = intent_classification_node(state)
            assert res["is_task_unmark"] is True
            assert res["unmarked_activity_name"] == "Straight Leg Raise"
            assert res["should_show_options"] is False

    def test_intent_classification_explicit_view_plan(self):
        """SRV-UNIT-GRF-004: Explicit plan request triggers should_show_options=True."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"intent": "view_plan", "activity": null}'
        )

        state: CoachState = {
            "session": None,
            "patient_id": 1,
            "patient_name": "Sarah",
            "procedure_name": "Total Knee Replacement",
            "days_away": 14,
            "user_message": "What's my plan for today?",
            "conversation_history": [],
            "grounded_library_text": "",
            "daily_tasks_summary": "",
            "available_options": [],
            "active_recommendations": [],
            "adherence_context": "",
            "milestones_summary": "",
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }
        with patch("services.amy.llm", mock_llm):
            res = intent_classification_node(state)
            assert res["should_show_options"] is True

    def test_intent_classification_sadness_is_general_without_cards(self):
        """SRV-UNIT-GRF-005: Emotional low mood is classified as general intent without card dump."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"intent": "general", "activity": null}'
        )

        state: CoachState = {
            "session": None,
            "patient_id": 1,
            "patient_name": "Sarah",
            "procedure_name": "Total Knee Replacement",
            "days_away": 14,
            "user_message": "I feel really sad to do anything today.",
            "conversation_history": [],
            "grounded_library_text": "",
            "daily_tasks_summary": "",
            "available_options": [],
            "active_recommendations": [],
            "adherence_context": "",
            "milestones_summary": "",
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }
        with patch("services.amy.llm", mock_llm):
            res = intent_classification_node(state)
            assert res["should_show_options"] is False

    def test_recommendation_action_completion_mutation(self, db_session: Session):
        """SRV-UNIT-GRF-006: Recommendation action node updates SQLite task to is_completed=True."""
        state: CoachState = {
            "session": db_session,
            "patient_id": 1,
            "patient_name": "Sarah",
            "procedure_name": "Total Knee Replacement",
            "days_away": 14,
            "user_message": "I did my quad sets",
            "conversation_history": [],
            "grounded_library_text": "",
            "daily_tasks_summary": "",
            "available_options": [],
            "active_recommendations": [],
            "adherence_context": "",
            "milestones_summary": "",
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": True,
            "completed_activity_name": "Quad Sets",
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }
        res = recommendation_action_node(state)
        task_info = res["completed_task_info"]
        assert task_info is not None
        assert task_info["taskId"] == 1
        assert task_info["isCompleted"] is True

        # Verify in SQLite database
        rec = db_session.exec(select(Recommendation).where(Recommendation.id == 1)).first()
        assert rec is not None
        assert rec.status == "completed"
        assert rec.completed_at is not None

    def test_coaching_node_compassionate_fallback(self):
        """SRV-UNIT-GRF-008: Coaching node returns warm, guilt-free message when patient is feeling sad."""
        state: CoachState = {
            "session": None,
            "patient_id": 1,
            "patient_name": "Sarah",
            "procedure_name": "Total Knee Replacement",
            "days_away": 14,
            "user_message": "I feel really sad to do anything today.",
            "conversation_history": [],
            "grounded_library_text": "",
            "daily_tasks_summary": "",
            "available_options": [],
            "active_recommendations": [],
            "adherence_context": "",
            "milestones_summary": "",
            "is_safety_alert": False,
            "safety_category": None,
            "risk_level": None,
            "safety_trigger": None,
            "safety_action": None,
            "is_task_completion": False,
            "completed_activity_name": None,
            "is_task_unmark": False,
            "unmarked_activity_name": None,
            "should_show_options": False,
            "completed_task_info": None,
            "response_text": "",
            "suggested_options": None,
            "quick_replies": [],
        }
        with patch("services.amy.invoke_coach_llm", return_value=None):
            res = coaching_node(state)
            assert "sad" in res["response_text"].lower() or "rest" in res["response_text"].lower()
            assert "4-7-8 breathing" in res["response_text"].lower()
            assert len(res["quick_replies"]) > 0

    def test_extract_quick_replies_emotional_support(self):
        """SRV-UNIT-GRF-010: Quick replies for emotional support offer restorative choices."""
        text, replies = extract_quick_replies(
            raw_text="I hear you, Sarah. Take all the time you need.",
            active_recommendations=[],
            is_emotional_support=True
        )
        assert any("rest" in r.lower() for r in replies)
        assert any("4-7-8" in r for r in replies)
