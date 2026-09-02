"""REST API Endpoints for Mesh Peer Discovery, Gossip Synchronization, and Heartbeats."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.mesh import (
    GossipExchangeRequest,
    GossipExchangeResponse,
    PeerNodeRegisterRequest,
    PeerNodeResponse,
    PeerPingRequest,
)
from backend.app.services.mesh_service import MeshService

router = APIRouter()


@router.get(
    "/peers",
    response_model=List[PeerNodeResponse],
    status_code=status.HTTP_200_OK,
    summary="List Discovered Mesh Peers",
    description="Query active and discovered peer nodes across local mDNS and federated gossip meshes.",
)
async def list_mesh_peers(
    status_filter: Optional[str] = Query("ONLINE", description="Filter by status (ONLINE, UNREACHABLE)"),
    capability: Optional[str] = Query(None, description="Filter by capability tag"),
    limit: int = Query(50, ge=1, le=100, description="Max peers to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> List[PeerNodeResponse]:
    """Query discovered peers."""
    _, peers = await MeshService.list_peers(
        session=db,
        status_filter=status_filter,
        capability=capability,
        limit=limit,
        offset=offset,
    )
    return [MeshService.to_peer_response(p) for p in peers]


@router.post(
    "/announce",
    response_model=PeerNodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Announce Node to Mesh",
    description="Register or refresh a node's heartbeat, URL, and hosted agent capabilities.",
)
async def announce_peer_node(
    payload: PeerNodeRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> PeerNodeResponse:
    """Announce self."""
    peer = await MeshService.register_or_update_peer(session=db, request=payload)
    return MeshService.to_peer_response(peer)


@router.post(
    "/gossip",
    response_model=GossipExchangeResponse,
    status_code=status.HTTP_200_OK,
    summary="Federated Gossip Exchange",
    description="Receive peer lists from a remote node and return our active nodes for bidirectional synchronization.",
)
async def exchange_gossip_peers(
    payload: GossipExchangeRequest,
    db: AsyncSession = Depends(get_db),
) -> GossipExchangeResponse:
    """Exchange gossip nodes."""
    received, new_discovered, active_peers = await MeshService.process_gossip_exchange(
        session=db,
        payload=payload,
    )
    return GossipExchangeResponse(
        received_count=received,
        new_peers_discovered=new_discovered,
        active_peers=[MeshService.to_peer_response(p) for p in active_peers],
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/ping",
    response_model=PeerNodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Peer Heartbeat Ping",
    description="Send a heartbeat ping to record node latency and keep status ONLINE.",
)
async def ping_mesh_peer(
    payload: PeerPingRequest,
    db: AsyncSession = Depends(get_db),
) -> PeerNodeResponse:
    """Ping peer."""
    peer = await MeshService.ping_peer(
        session=db,
        node_id=payload.node_id,
        latency_ms=payload.latency_ms,
    )
    return MeshService.to_peer_response(peer)
