"""Local mDNS / Zeroconf Mesh Auto-Discovery Engine."""

import asyncio
import logging
import socket
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("agenthive")

SERVICE_TYPE = "_agenthive._tcp.local."


class LocalMeshDiscovery:
    """Advertises and auto-discovers AgentHive instances on the local LAN / Docker subnet."""

    def __init__(
        self,
        node_id: str,
        node_name: str,
        port: int = 8000,
        capabilities: Optional[List[str]] = None,
        on_peer_discovered: Optional[Callable[[Dict], None]] = None,
    ):
        self.node_id = node_id
        self.node_name = node_name
        self.port = port
        self.capabilities = capabilities or ["general"]
        self.on_peer_discovered = on_peer_discovered
        self._zeroconf = None
        self._service_info = None

    def start_broadcast(self) -> bool:
        """Broadcast local AgentHive instance via mDNS Zeroconf."""
        try:
            from zeroconf import ServiceInfo, Zeroconf

            self._zeroconf = Zeroconf()
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            desc = {
                "node_id": self.node_id,
                "node_name": self.node_name,
                "capabilities": ",".join(self.capabilities),
            }

            self._service_info = ServiceInfo(
                type_=SERVICE_TYPE,
                name=f"{self.node_id}.{SERVICE_TYPE}",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties=desc,
                server=f"{hostname}.local.",
            )

            self._zeroconf.register_service(self._service_info)
            logger.info(f"mDNS Zeroconf mesh broadcasting as '{self.node_id}' on port {self.port}")
            return True
        except Exception as e:
            logger.warning(f"mDNS broadcast initialization skipped ({e}).")
            return False

    def stop_broadcast(self) -> None:
        """Unregister mDNS broadcast service."""
        if self._zeroconf and self._service_info:
            try:
                self._zeroconf.unregister_service(self._service_info)
                self._zeroconf.close()
                logger.info("mDNS Zeroconf mesh broadcast stopped.")
            except Exception:
                pass
