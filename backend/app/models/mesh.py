"""SQLAlchemy Models for Autonomous Peer Discovery Mesh and Gossip Network."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from backend.app.core.database import Base


class MeshPeerNode(Base):
    """A discovered local or remote AgentHive node in the federated mesh network."""

    __tablename__ = "mesh_peer_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(String(64), unique=True, nullable=False, index=True)  # e.g. "node-tokyo-01", "node-vps-ph"
    node_name = Column(String(100), nullable=False)
    
    endpoint_url = Column(String(255), nullable=False)  # e.g. "https://philipjohnn8nautomation.online/agenthive"
    protocol = Column(String(20), nullable=False, default="HTTPS")  # 'HTTPS', 'HTTP', 'WEBSOCKET'
    discovery_method = Column(
        String(30),
        nullable=False,
        default="GOSSIP",  # 'MDNS_LOCAL', 'GOSSIP', 'BOOTSTRAP_SEED', 'MANUAL'
    )
    
    status = Column(String(20), nullable=False, default="ONLINE")  # 'ONLINE', 'UNREACHABLE', 'DRAINED'
    capabilities = Column(ARRAY(String), nullable=False, default=list)
    agent_count = Column(Integer, nullable=False, default=1)
    
    trust_score = Column(Float, nullable=False, default=1.0)  # 0.0 - 5.0
    latency_ms = Column(Float, nullable=True, default=0.0)
    
    metadata_json = Column(JSONB, nullable=True)
    last_ping_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_mesh_peer_status", "status"),
        Index("idx_mesh_peer_discovery_method", "discovery_method"),
        Index("idx_mesh_peer_last_ping", "last_ping_at"),
    )


class MeshGossipPacket(Base):
    """Log of exchanged gossip packets and node announcements."""

    __tablename__ = "mesh_gossip_packets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    packet_id = Column(String(64), unique=True, nullable=False, index=True)
    
    origin_node_id = Column(String(64), nullable=False, index=True)
    packet_type = Column(String(30), nullable=False)  # 'ANNOUNCE', 'PEER_EXCHANGE', 'HEARTBEAT', 'DRAIN'
    
    nodes_payload = Column(JSONB, nullable=False)  # List of peer nodes gossiped
    signature = Column(String(128), nullable=True)  # Optional crypto signature
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_gossip_packet_type", "packet_type"),
        Index("idx_gossip_created_at", "created_at"),
    )
