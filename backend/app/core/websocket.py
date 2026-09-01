"""WebSocket Connection Manager and Real-Time Event Bus."""

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Set
from fastapi import WebSocket


class EventBroadcaster:
    """Manages active WebSocket client connections and publishes real-time platform telemetry."""

    def __init__(self):
        # Maps topic -> set of WebSockets (e.g. "global", "task:tsk-123", "hive:hive-abc")
        self._topics: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, topic: str = "global"):
        """Accept WebSocket connection and subscribe to specified topic."""
        await websocket.accept()
        self._active_connections.add(websocket)
        self._topics[topic].add(websocket)

    def disconnect(self, websocket: WebSocket, topic: str = "global"):
        """Remove WebSocket connection from active rosters."""
        self._active_connections.discard(websocket)
        self._topics[topic].discard(websocket)
        # Also purge from any other topic subscriptions
        for t in list(self._topics.keys()):
            self._topics[t].discard(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any], topic: str = "global"):
        """Broadcast structured event to all subscribers of a topic and global listeners."""
        payload = {
            "event": event_type,
            "topic": topic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        message_str = json.dumps(payload)

        # Collect targets: topic subscribers + global listeners
        targets = set(self._topics.get(topic, set()))
        if topic != "global":
            targets.update(self._topics.get("global", set()))

        dead_connections: List[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(message_str)
            except Exception:
                dead_connections.append(ws)

        for ws in dead_connections:
            self.disconnect(ws, topic)

    @property
    def connection_count(self) -> int:
        return len(self._active_connections)


# Singleton event broadcaster instance
event_broadcaster = EventBroadcaster()
