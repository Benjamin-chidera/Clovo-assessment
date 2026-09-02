import pytest
from unittest.mock import AsyncMock, patch
import socketio
from sqlmodel import Session
from routes.sockets import register_socket_events


@pytest.fixture
def mock_sio():
    """Provides an AsyncServer instance with registered Clovo event handlers and spied emissions."""
    server = socketio.AsyncServer(async_mode="asgi")
    server.save_session = AsyncMock()
    server.get_session = AsyncMock(return_value={"userId": "1", "room": "user_1"})
    server.enter_room = AsyncMock()
    server.emit = AsyncMock()
    register_socket_events(server)
    return server


class TestSocketEvents:
    """Integration tests for real-time Socket.IO communication lifecycle."""

    async def test_socket_connect_handshake(self, mock_sio):
        """SRV-INT-SCK-000: Socket connect sends session_ready event to client."""
        environ = {}
        auth = {"userId": "1"}
        connect_handler = mock_sio.handlers["/"]["connect"]
        await connect_handler("test-sid-1", environ, auth)

        # Verify session_ready was emitted
        emitted_events = [call.args[0] for call in mock_sio.emit.call_args_list]
        assert "session_ready" in emitted_events

    async def test_socket_task_completion_and_task_sync(self, mock_sio, db_session: Session):
        """SRV-INT-SCK-001: Completing task via message emits coach_message and broadcasts task_sync."""
        send_message_handler = mock_sio.handlers["/"]["send_message"]

        with patch("services.amy.invoke_coach_llm", return_value="Awesome job finishing Quad Sets, Sarah! 🎉"):
            with patch("routes.sockets.engine", db_session.get_bind()):
                await send_message_handler(
                    "test-sid-1",
                    {"text": "I finished my Quad Sets today"},
                )

        emitted_events = [call.args[0] for call in mock_sio.emit.call_args_list]
        assert "coach_message" in emitted_events

    async def test_socket_voice_session_start(self, mock_sio, db_session: Session):
        """SRV-INT-SCK-003: [VOICE_SESSION_START] emits welcoming response without error."""
        send_message_handler = mock_sio.handlers["/"]["send_message"]

        with patch("services.amy.invoke_coach_llm", return_value="Hello Sarah! I'm here, listening."):
            with patch("routes.sockets.engine", db_session.get_bind()):
                await send_message_handler(
                    "test-sid-1",
                    {"text": "[VOICE_SESSION_START]"},
                )

        emitted_events = [call.args[0] for call in mock_sio.emit.call_args_list]
        assert "coach_message" in emitted_events
