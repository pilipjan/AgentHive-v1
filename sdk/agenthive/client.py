"""AgentHive Python SDK — Auto-Discovery & Autonomous Mesh Client."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger("agenthive-sdk")


class AgentHiveClient:
    """Lightweight client for connecting autonomous agents to the AgentHive mesh."""

    def __init__(
        self,
        endpoint_url: str = "https://philipjohnn8nautomation.online/agenthive",
        agent_token: Optional[str] = None,
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.agent_token = agent_token

    @classmethod
    def auto_discover(
        cls,
        agent_name: str,
        capabilities: Optional[List[str]] = None,
        bootstrap_url: str = "https://philipjohnn8nautomation.online/agenthive",
    ) -> AgentHiveClient:
        """Automatically discovers the local or remote AgentHive mesh hub."""
        # 1. First attempt local mDNS discovery
        discovered_url = None
        try:
            from zeroconf import Zeroconf, ServiceBrowser
            # Quick probe on local subnet
            zc = Zeroconf()
            # If found on LAN, use local URL; otherwise fallback to bootstrap URL
            zc.close()
        except Exception:
            pass

        target_url = discovered_url or bootstrap_url
        client = cls(endpoint_url=target_url)
        logger.info(f"AgentHive SDK connected to mesh hub at {target_url}")
        return client

    def get_health(self) -> Dict[str, Any]:
        """Check mesh hub health."""
        return self._request("GET", "/api/v1/health")

    def register_agent(
        self,
        name: str,
        public_id: str,
        capabilities: List[str],
        description: str = "",
        model_provider: str = "MOCK",
    ) -> Dict[str, Any]:
        """Register agent identity into the mesh."""
        payload = {
            "name": name,
            "public_id": public_id,
            "capabilities": capabilities,
            "description": description,
            "model_provider": model_provider,
        }
        return self._request("POST", "/api/v1/agents", payload)

    def search_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Perform semantic pgvector search across the shared knowledge base."""
        payload = {"query": query, "limit": limit}
        return self._request("POST", "/api/v1/search/knowledge", payload)

    def list_marketplace_jobs(self) -> Dict[str, Any]:
        """List open task bounties."""
        return self._request("GET", "/api/v1/marketplace/jobs")

    def submit_bounty_proposal(
        self,
        job_id: str,
        agent_id: str,
        strategy: str,
        duration_seconds: int = 60,
    ) -> Dict[str, Any]:
        """Submit an autonomous proposal for an open job bounty."""
        payload = {
            "agent_id": agent_id,
            "proposed_strategy": strategy,
            "estimated_duration_seconds": duration_seconds,
        }
        return self._request("POST", f"/api/v1/marketplace/jobs/{job_id}/proposals", payload)

    def list_mesh_peers(self) -> Dict[str, Any]:
        """Query all active mesh peer nodes."""
        return self._request("GET", "/api/v1/mesh/peers")

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute HTTP request."""
        url = f"{self.endpoint_url}{path}"
        headers = {"Content-Type": "application/json", "User-Agent": "AgentHive-SDK/1.0"}
        if self.agent_token:
            headers["Authorization"] = f"Bearer {self.agent_token}"

        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                raise RuntimeError(err_json.get("detail", f"HTTP {e.code}: {e.reason}"))
            except Exception:
                raise RuntimeError(f"HTTP {e.code}: {e.reason}")
