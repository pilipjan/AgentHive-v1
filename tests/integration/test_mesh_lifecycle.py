"""Integration tests for Autonomous Peer Discovery Mesh and Gossip Exchange."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mesh_peer_discovery_and_gossip_exchange_lifecycle(async_client: AsyncClient):
    """Verify peer node announcement, listing, gossip synchronization, and heartbeats."""
    uid = uuid.uuid4().hex[:6]
    local_node_id = f"node-tokyo-{uid}"
    remote_node_id = f"node-london-{uid}"

    # 1. Announce Local Node to Mesh
    announce_res = await async_client.post("/api/v1/mesh/announce", json={
        "node_id": local_node_id,
        "node_name": "Tokyo AI Edge Node",
        "endpoint_url": "https://tokyo.agenthive.network",
        "protocol": "HTTPS",
        "discovery_method": "MDNS_LOCAL",
        "capabilities": ["vision", "arm64", "robotics"],
        "agent_count": 3,
        "metadata": {"region": "ap-northeast-1", "device": "jetson-orin"},
    })
    assert announce_res.status_code == 200
    local_peer = announce_res.json()
    assert local_peer["node_id"] == local_node_id
    assert local_peer["status"] == "ONLINE"
    assert "arm64" in local_peer["capabilities"]

    # 2. Query Discovered Mesh Peers
    list_res = await async_client.get("/api/v1/mesh/peers")
    assert list_res.status_code == 200
    peers_data = list_res.json()
    assert len(peers_data) >= 1
    assert any(p["node_id"] == local_node_id for p in peers_data)

    # 3. Filter Peers by capability
    cap_res = await async_client.get("/api/v1/mesh/peers?capability=arm64")
    assert cap_res.status_code == 200
    cap_peers = cap_res.json()
    assert len(cap_peers) >= 1
    assert any(p["node_id"] == local_node_id for p in cap_peers)

    # 4. Exchange Gossip Packets with Remote Node
    gossip_res = await async_client.post("/api/v1/mesh/gossip", json={
        "origin_node_id": remote_node_id,
        "known_peers": [
            {
                "node_id": remote_node_id,
                "node_name": "London Research Node",
                "endpoint_url": "https://london.agenthive.network",
                "protocol": "HTTPS",
                "discovery_method": "GOSSIP",
                "capabilities": ["nlp", "translation", "rag"],
                "agent_count": 5,
                "metadata": {"region": "eu-west-2"},
            }
        ],
    })
    assert gossip_res.status_code == 200
    gossip_data = gossip_res.json()
    assert gossip_data["received_count"] == 1
    assert gossip_data["new_peers_discovered"] >= 1
    assert any(p["node_id"] == remote_node_id for p in gossip_data["active_peers"])

    # 5. Send Peer Ping Heartbeat
    ping_res = await async_client.post("/api/v1/mesh/ping", json={
        "node_id": local_node_id,
        "latency_ms": 14.5,
    })
    assert ping_res.status_code == 200
    ping_data = ping_res.json()
    assert ping_data["node_id"] == local_node_id
    assert ping_data["latency_ms"] == 14.5
