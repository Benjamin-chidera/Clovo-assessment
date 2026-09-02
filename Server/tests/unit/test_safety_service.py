import pytest
from services.safety_service import safety_service
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage


class TestSafetyServiceFastPath:
    """Unit tests for deterministic fast-path regex triage (sub-2ms execution)."""

    def test_suicide_critical_trigger(self):
        """SRV-UNIT-SAF-001: Explicit suicidal intent must trigger critical alert instantly."""
        messages = [
            "I want to kill myself",
            "I am feeling suicidal",
            "I want to end my life",
            "I want to die today",
        ]
        for msg in messages:
            result = safety_service._check_deterministic_fast_path(msg)
            assert result is not None, f"Failed to trigger fast-path for '{msg}'"
            assert result["category"] == "mental_health"
            assert result["risk_level"] == "critical"
            assert result["is_safety_alert"] is True

    def test_critical_medical_emergency_trigger(self):
        """SRV-UNIT-SAF-002: Critical medical emergencies (chest pain, cannot breathe, heavy bleeding) trigger fast-path."""
        messages = [
            "I have severe chest pain",
            "I can't breathe",
            "I have heavy bleeding from my wound",
            "I passed out on the floor",
        ]
        for msg in messages:
            result = safety_service._check_deterministic_fast_path(msg)
            assert result is not None, f"Failed to trigger fast-path for '{msg}'"
            assert result["category"] == "acute_medical"
            assert result["risk_level"] == "critical"
            assert result["is_safety_alert"] is True

    def test_heuristic_fallback_trauma_infection_and_pain(self):
        """SRV-UNIT-SAF-003: Heuristic fallback patterns detect head trauma, wound infection, and severe pain."""
        trauma_msg = "I hit my head on the floor"
        res_trauma = safety_service._check_heuristic_fallback(trauma_msg)
        assert res_trauma is not None
        assert res_trauma["is_safety_alert"] is True
        assert res_trauma["category"] == "acute_medical"
        assert res_trauma["risk_level"] == "high"

        infection_msg = "My knee is hot, swollen, and oozing pus"
        res_infection = safety_service._check_heuristic_fallback(infection_msg)
        assert res_infection is not None
        assert res_infection["is_safety_alert"] is True
        assert res_infection["category"] == "acute_medical"
        assert res_infection["risk_level"] == "high"

        pain_msg = "My pain is an 8 out of 10"
        res_pain = safety_service._check_heuristic_fallback(pain_msg)
        assert res_pain is not None
        assert res_pain["is_safety_alert"] is True
        assert res_pain["category"] == "severe_pain"
        assert res_pain["risk_level"] == "medium"


class TestSafetyServiceSemanticClassifier:
    """Unit tests for semantic safety triage classifier (prompt boundary verification)."""

    def test_emotional_sadness_is_safe(self):
        """SRV-UNIT-SAF-004: Normal sadness or low mood must classify as safe (prevents 999 false alarm)."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"is_safety_alert": false, "category": "safe", "risk_level": null, "trigger": null, "action": null}'
        )

        result = safety_service.screen_message_semantic(
            user_message="I feel really sad to do anything today.",
            llm_instance=mock_llm
        )
        assert result["is_safety_alert"] is False
        assert result["category"] == "safe"
        assert result["risk_level"] is None

    def test_low_motivation_and_fatigue_is_safe(self):
        """SRV-UNIT-SAF-005: Low energy, tiredness, and lack of motivation must classify as safe."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"is_safety_alert": false, "category": "safe", "risk_level": null, "trigger": null, "action": null}'
        )

        result = safety_service.screen_message_semantic(
            user_message="I have zero motivation and feel completely exhausted today.",
            llm_instance=mock_llm
        )
        assert result["is_safety_alert"] is False
        assert result["category"] == "safe"
        assert result["risk_level"] is None

    def test_clinical_decision_prescription_change(self):
        """SRV-UNIT-SAF-006: Patient asking Amy to alter medication triggers low-risk clinical notice."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"is_safety_alert": true, "category": "clinical_decision", "risk_level": "low", "trigger": "Medication change inquiry", "action": "Consult surgeon or pharmacist"}'
        )

        result = safety_service.screen_message_semantic(
            user_message="Should I double my blood thinner dose to twice a day?",
            llm_instance=mock_llm
        )
        assert result["is_safety_alert"] is True
        assert result["category"] == "clinical_decision"
        assert result["risk_level"] == "low"
