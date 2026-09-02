"""Unit tests for Mesh discovery data structures, gossip parsing, and SDK client initialization."""

import pytest
from sdk.agenthive import AgentHiveClient
from backend.app.mesh.local_discovery import LocalMeshDiscovery


def test_sdk_client_initialization():
    """Verify AgentHive Python SDK initializes with default parameters."""
    client = AgentHiveClient(endpoint_url="https://philipjohnn8nautomation.online/agenthive")
    assert client.endpoint_url == "https://philipjohnn8nautomation.online/agenthive"
    assert client.agent_token is None


def test_local_mesh_discovery_initialization():
    """Verify mDNS Zeroconf broadcaster properties."""
    discovery = LocalMeshDiscovery(
        node_id="node-test-01",
        node_name="Test Node",
        port=8000,
        capabilities=["python", "fastapi"],
    )
    assert discovery.node_id == "node-test-01"
    assert discovery.port == 8000
    assert "fastapi" in discovery.capabilities
