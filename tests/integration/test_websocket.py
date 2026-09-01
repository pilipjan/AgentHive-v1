"""Integration tests for WebSocket Live Event Streaming."""

import pytest
from backend.app.core.websocket import event_broadcaster
from backend.app.main import app
from starlette.testclient import TestClient


def test_websocket_global_events():
    """Test WebSocket connection handshake, ping-pong, and event broadcast."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/events") as websocket:
        # Check initial handshake response
        data = websocket.receive_json()
        assert data["event"] == "CONNECTED"
        assert data["topic"] == "global"

        # Test ping-pong heartbeat
        websocket.send_text("ping")
        resp = websocket.receive_text()
        assert resp == "pong"


def test_websocket_task_stream():
    """Test scoped task WebSocket stream."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/tasks/tsk-test-123") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "TASK_STREAM_CONNECTED"
        assert data["task_id"] == "tsk-test-123"
