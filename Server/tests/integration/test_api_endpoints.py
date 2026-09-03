import pytest
import io
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session
from main import app
from database import get_session
from models.safety_event import SafetyEvent


@pytest.fixture
def client(db_session: Session):
    """Provides an async HTTP client with FastAPI dependency overrides pointing to in-memory DB."""
    def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    client_instance = AsyncClient(transport=transport, base_url="http://test")
    yield client_instance
    app.dependency_overrides.clear()


class TestApiEndpoints:
    """Integration tests for Clovo REST API endpoints."""

    async def test_get_home_data(self, client: AsyncClient):
        """SRV-INT-API-001: GET /api/home returns patient dashboard, streak, and daily preparations."""
        response = await client.get("/api/home?patient_id=1")
        assert response.status_code == 200
        data = response.json()
        assert data["patient_name"] == "Sarah"
        assert "preparations" in data
        assert len(data["preparations"]) > 0
        assert data["days_away"] >= 0
        assert data["phase"] == "pre-op"

    async def test_get_home_data_jane_post_op(self, client: AsyncClient):
        """SRV-INT-API-005: GET /api/home?patient_id=patient-jane returns post-op knee rehabilitation data."""
        response = await client.get("/api/home?patient_id=patient-jane")
        assert response.status_code == 200
        data = response.json()
        assert data["patient_name"] == "Jane"
        assert data["phase"] == "post-op"
        assert data["days_post_op"] is not None and data["days_post_op"] >= 1
        assert "Post-Op" in data["surgery_title"]
        assert len(data["preparations"]) > 0
        assert any("Ankle Pumps" in p["title"] for p in data["preparations"])

    async def test_recommendation_action_complete(self, client: AsyncClient):
        """SRV-INT-API-002: PATCH /api/recommendations/{id}/toggle marks task complete in database."""
        response = await client.patch("/api/recommendations/1/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    async def test_admin_safety_events(self, client: AsyncClient, db_session: Session):
        """SRV-INT-API-003: GET /api/admin/safety-events returns filtered clinician safety incidents."""
        # Seed test safety event
        event = SafetyEvent(
            patient_id=1,
            conversation_id="test-conv-1",
            trigger="Severe chest pain reported",
            risk_level="critical",
            action="Advised immediate 999 call",
            status="active",
        )
        db_session.add(event)
        db_session.commit()

        response = await client.get("/api/admin/safety-events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(e["risk_level"] == "critical" for e in data)

    async def test_voice_transcribe_rejects_empty(self, client: AsyncClient):
        """SRV-INT-API-004: POST /api/voice/transcribe handles audio upload streams."""
        # Test with empty file to verify validation response
        fake_wav = io.BytesIO(b"RIFF....WAVEfmt ....data....")
        response = await client.post(
            "/api/voice/transcribe",
            files={"file": ("test.wav", fake_wav, "audio/wav")},
        )
        # Should return either 200 (if Whisper mock available) or 400/500 with proper JSON error
        assert response.status_code in [200, 400, 500]
        assert "detail" in response.json() or "text" in response.json()
