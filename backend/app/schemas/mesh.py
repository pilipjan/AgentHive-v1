"""Pydantic schemas for Mesh Peer Discovery, Node Announcements, and Gossip Protocols."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PeerNodeRegisterRequest(BaseModel):
    """Payload to announce and register a peer node into the mesh."""
    node_id: str = Field(..., min_length=3, max_length=64, description="Unique node slug identifier")
    node_name: str = Field(..., min_length=2, max_length=100, description="Human-readable node title")
    endpoint_url: str = Field(..., min_length=5, max_length=255, description="Full accessible URL to peer AgentHive instance")
    protocol: str = Field("HTTPS", description="'HTTPS', 'HTTP', or 'WEBSOCKET'")
    discovery_method: str = Field("GOSSIP", description="'MDNS_LOCAL', 'GOSSIP', 'BOOTSTRAP_SEED', 'MANUAL'")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities available on this peer")
    agent_count: int = Field(1, ge=0, description="Number of agents hosted on this node")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata (e.g. region, hardware, latency)")


class PeerNodeResponse(BaseModel):
    """Peer node response entity."""
    id: str
    node_id: str
    node_name: str
    endpoint_url: str
    protocol: str
    discovery_method: str
    status: str
    capabilities: List[str]
    agent_count: int
    trust_score: float
    latency_ms: float
    metadata: Optional[Dict[str, Any]] = None
    last_ping_at: datetime
    created_at: datetime


class GossipExchangeRequest(BaseModel):
    """Gossip peer exchange request payload."""
    origin_node_id: str = Field(..., description="Node sending the gossip packet")
    known_peers: List[PeerNodeRegisterRequest] = Field(default_factory=list, description="List of active peers gossiped")
    signature: Optional[str] = Field(None, description="Cryptographic signature of the packet")


class GossipExchangeResponse(BaseModel):
    """Response returned when gossip exchange succeeds."""
    received_count: int
    new_peers_discovered: int
    active_peers: List[PeerNodeResponse]
    timestamp: datetime


class PeerPingRequest(BaseModel):
    """Heartbeat ping request."""
    node_id: str
    latency_ms: Optional[float] = None
