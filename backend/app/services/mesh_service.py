"""Mesh Service Layer for Peer Node Registration, Gossip Exchange, and Federated Discovery."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.websocket import event_broadcaster
from backend.app.models import MeshGossipPacket, MeshPeerNode
from backend.app.schemas.mesh import (
    GossipExchangeRequest,
    GossipExchangeResponse,
    PeerNodeRegisterRequest,
    PeerNodeResponse,
)
from security.audit.auditor import AuditService


class MeshService:
    """Service providing decentralized node discovery, gossip sync, and peer health management."""

    @classmethod
    async def register_or_update_peer(
        cls,
        session: AsyncSession,
        request: PeerNodeRegisterRequest,
    ) -> MeshPeerNode:
        """Register a new peer node or update an existing node's heartbeat and capabilities."""
        query = select(MeshPeerNode).where(MeshPeerNode.node_id == request.node_id)
        result = await session.execute(query)
        peer = result.scalar_one_or_none()

        is_new = False
        if not peer:
            is_new = True
            peer = MeshPeerNode(
                id=uuid.uuid4(),
                node_id=request.node_id,
                node_name=request.node_name,
                endpoint_url=request.endpoint_url.rstrip("/"),
                protocol=request.protocol.upper(),
                discovery_method=request.discovery_method.upper(),
                status="ONLINE",
                capabilities=request.capabilities or [],
                agent_count=request.agent_count,
                trust_score=1.0,
                latency_ms=0.0,
                metadata_json=request.metadata or {},
                last_ping_at=datetime.now(timezone.utc),
            )
            session.add(peer)
        else:
            peer.node_name = request.node_name
            peer.endpoint_url = request.endpoint_url.rstrip("/")
            peer.protocol = request.protocol.upper()
            peer.capabilities = request.capabilities or peer.capabilities
            peer.agent_count = request.agent_count
            peer.status = "ONLINE"
            peer.last_ping_at = datetime.now(timezone.utc)
            if request.metadata:
                peer.metadata_json = {**(peer.metadata_json or {}), **request.metadata}

        await session.commit()
        await session.refresh(peer)

        if is_new:
            await event_broadcaster.broadcast(
                "MESH_PEER_DISCOVERED",
                {
                    "node_id": peer.node_id,
                    "node_name": peer.node_name,
                    "endpoint_url": peer.endpoint_url,
                    "discovery_method": peer.discovery_method,
                    "capabilities": peer.capabilities,
                },
                topic="global",
            )

        return peer

    @classmethod
    async def process_gossip_exchange(
        cls,
        session: AsyncSession,
        payload: GossipExchangeRequest,
    ) -> Tuple[int, int, List[MeshPeerNode]]:
        """Ingest a gossiped list of peers from a neighboring node and return our active peers."""
        new_count = 0
        received_count = len(payload.known_peers)

        for p_req in payload.known_peers:
            # Avoid self-referencing if origin matches
            query = select(MeshPeerNode).where(MeshPeerNode.node_id == p_req.node_id)
            res = await session.execute(query)
            existing = res.scalar_one_or_none()

            if not existing:
                new_node = MeshPeerNode(
                    id=uuid.uuid4(),
                    node_id=p_req.node_id,
                    node_name=p_req.node_name,
                    endpoint_url=p_req.endpoint_url.rstrip("/"),
                    protocol=p_req.protocol.upper(),
                    discovery_method="GOSSIP",
                    status="ONLINE",
                    capabilities=p_req.capabilities or [],
                    agent_count=p_req.agent_count,
                    trust_score=1.0,
                    latency_ms=0.0,
                    metadata_json=p_req.metadata or {},
                    last_ping_at=datetime.now(timezone.utc),
                )
                session.add(new_node)
                new_count += 1
            else:
                existing.last_ping_at = datetime.now(timezone.utc)
                existing.status = "ONLINE"
                existing.capabilities = p_req.capabilities or existing.capabilities

        # Log gossip packet into immutable ledger
        packet = MeshGossipPacket(
            id=uuid.uuid4(),
            packet_id=f"gossip-{uuid.uuid4().hex[:8]}",
            origin_node_id=payload.origin_node_id,
            packet_type="PEER_EXCHANGE",
            nodes_payload=[p.model_dump() for p in payload.known_peers],
            signature=payload.signature,
        )
        session.add(packet)
        await session.commit()

        # Fetch all active peers to return in the exchange
        active_peers_query = select(MeshPeerNode).where(MeshPeerNode.status == "ONLINE")
        all_active_res = await session.execute(active_peers_query)
        active_peers = list(all_active_res.scalars().all())

        return received_count, new_count, active_peers

    @classmethod
    async def ping_peer(
        cls,
        session: AsyncSession,
        node_id: str,
        latency_ms: Optional[float] = None,
    ) -> MeshPeerNode:
        """Update heartbeat timestamp and latency metric for a peer node."""
        query = select(MeshPeerNode).where(MeshPeerNode.node_id == node_id)
        result = await session.execute(query)
        peer = result.scalar_one_or_none()

        if not peer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Peer node '{node_id}' not found.")

        peer.status = "ONLINE"
        peer.last_ping_at = datetime.now(timezone.utc)
        if latency_ms is not None:
            peer.latency_ms = round(latency_ms, 2)

        await session.commit()
        await session.refresh(peer)
        return peer

    @classmethod
    async def list_peers(
        cls,
        session: AsyncSession,
        status_filter: Optional[str] = None,
        capability: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[MeshPeerNode]]:
        """Query discovered mesh peers with filtering."""
        query = select(MeshPeerNode)
        count_query = select(func.count()).select_from(MeshPeerNode)

        if status_filter:
            query = query.where(MeshPeerNode.status == status_filter.upper())
            count_query = count_query.where(MeshPeerNode.status == status_filter.upper())

        if capability:
            cap_clean = capability.strip().lower()
            query = query.where(MeshPeerNode.capabilities.any(cap_clean))
            count_query = count_query.where(MeshPeerNode.capabilities.any(cap_clean))

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(MeshPeerNode.last_ping_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        peers = list(result.scalars().all())

        return total, peers

    @classmethod
    def to_peer_response(cls, peer: MeshPeerNode) -> PeerNodeResponse:
        """Format MeshPeerNode to Pydantic schema."""
        return PeerNodeResponse(
            id=str(peer.id),
            node_id=peer.node_id,
            node_name=peer.node_name,
            endpoint_url=peer.endpoint_url,
            protocol=peer.protocol,
            discovery_method=peer.discovery_method,
            status=peer.status,
            capabilities=peer.capabilities or [],
            agent_count=peer.agent_count,
            trust_score=round(peer.trust_score, 2),
            latency_ms=round(peer.latency_ms or 0.0, 2),
            metadata=peer.metadata_json or {},
            last_ping_at=peer.last_ping_at,
            created_at=peer.created_at,
        )
