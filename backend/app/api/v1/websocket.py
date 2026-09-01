"""Real-Time WebSocket Endpoints for Live Event Streaming."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.websocket import event_broadcaster

router = APIRouter()
logger = logging.getLogger("agenthive:websocket")


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """Global WebSocket stream for live agent chatter, firewall alerts, and task status updates."""
    await event_broadcaster.connect(websocket, topic="global")
    # Send initial connection handshake confirmation
    try:
        await websocket.send_json({
            "event": "CONNECTED",
            "message": "Connected to AgentHive Real-Time Event Bus",
            "topic": "global",
        })
        while True:
            # Keep connection open and accept ping/heartbeat from client
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_broadcaster.disconnect(websocket, topic="global")
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
        event_broadcaster.disconnect(websocket, topic="global")


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_stream(websocket: WebSocket, task_id: str):
    """Scoped WebSocket stream for a specific task lifecycle and subtask synthesis."""
    topic = f"task:{task_id}"
    await event_broadcaster.connect(websocket, topic=topic)
    try:
        await websocket.send_json({
            "event": "TASK_STREAM_CONNECTED",
            "task_id": task_id,
            "topic": topic,
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_broadcaster.disconnect(websocket, topic=topic)
    except Exception as e:
        logger.warning("Task WebSocket error: %s", e)
        event_broadcaster.disconnect(websocket, topic=topic)
