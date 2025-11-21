"""
Server pooling functionality for Meta MCP Server

Note: These features are documented but not yet implemented in v2.0
TODO: Implement server pooling for performance optimization
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServerPool:
    """Manages a pool of reusable servers"""
    
    def __init__(self):
        self.pool: Dict[str, List[Dict[str, Any]]] = {}
        self.server_metadata: Dict[str, Dict[str, Any]] = {}
        self.idle_threshold_seconds = 1.0

    async def get_or_create_server(
        self,
        template: str,
        use_pooling: bool = True,
        create_server: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None,
        stop_callback: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Get an existing idle server from pool or create new one
        
        Args:
            template: The server template to use
            use_pooling: Whether to use pooling
            
        Returns:
            Server information dict
        """
        await self.cleanup_idle_servers(stop_callback=stop_callback)

        if not use_pooling:
            logger.info("Server pooling disabled; creating a fresh server")
            if not create_server:
                return {
                    "status": "error",
                    "error": "Pooling disabled and no create_server callback provided",
                    "reused": False
                }
            creation_result = await create_server()
            self._register_server_metadata(creation_result, template)
            return {**creation_result, "reused": False}

        now = datetime.utcnow()
        idle_servers = self.pool.get(template, [])

        while idle_servers:
            candidate = idle_servers.pop(0)
            if self._is_idle(candidate, now):
                server_id = candidate["server_id"]
                logger.info(
                    "Reusing idle server %s for template %s", server_id, template
                )
                self._touch_server(server_id, now)
                return {
                    "server_id": server_id,
                    "status": "reused from pool",
                    "reused": True
                }

        if not create_server:
            return {
                "status": "error",
                "error": "No idle server available and no create_server callback provided",
                "reused": False
            }

        creation_result = await create_server()
        self._register_server_metadata(creation_result, template)
        logger.info("Created new server %s for template %s", creation_result.get("server_id"), template)
        return {**creation_result, "reused": False}

    def mark_server_idle(self, server_id: str) -> None:
        """Mark a server as idle and available for reuse"""
        if server_id not in self.server_metadata:
            logger.debug("Server %s not tracked for pooling; skipping idle mark", server_id)
            return

        template = self.server_metadata[server_id]["template"]
        now = datetime.utcnow()
        self.server_metadata[server_id]["last_used"] = now

        pool_list = self.pool.setdefault(template, [])
        pool_list[:] = [s for s in pool_list if s["server_id"] != server_id]
        pool_list.append({"server_id": server_id, "last_used": now})
        logger.info("Marked server %s as idle for template %s", server_id, template)

    async def cleanup_idle_servers(
        self,
        stop_callback: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> int:
        """Clean up servers that have been idle too long"""
        now = datetime.utcnow()
        removed = 0

        for template, servers in list(self.pool.items()):
            active_servers = []
            for server in servers:
                if self._is_expired(server, now):
                    server_id = server["server_id"]
                    logger.info(
                        "Cleaning up idle server %s for template %s", server_id, template
                    )
                    self.server_metadata.pop(server_id, None)
                    removed += 1
                    if stop_callback:
                        await stop_callback(server_id)
                else:
                    active_servers.append(server)
            if active_servers:
                self.pool[template] = active_servers
            else:
                self.pool.pop(template, None)

        return removed

    def remove_server(self, server_id: str) -> None:
        """Remove a server from pool tracking"""
        self.server_metadata.pop(server_id, None)
        for template, servers in list(self.pool.items()):
            filtered = [s for s in servers if s["server_id"] != server_id]
            if filtered:
                self.pool[template] = filtered
            else:
                self.pool.pop(template, None)

    def register_server(self, server_id: str, template: Optional[str]) -> None:
        """Register a server for pooling with its template"""
        if not template:
            return
        self._register_server_metadata({"server_id": server_id}, template)

    def _register_server_metadata(self, server_info: Dict[str, Any], template: str) -> None:
        server_id = server_info.get("server_id")
        if not server_id:
            return
        self.server_metadata[server_id] = {
            "template": template,
            "last_used": datetime.utcnow(),
        }

    def _touch_server(self, server_id: str, when: datetime) -> None:
        if server_id in self.server_metadata:
            self.server_metadata[server_id]["last_used"] = when

    def _is_idle(self, server: Dict[str, Any], now: datetime) -> bool:
        return not self._is_expired(server, now)

    def _is_expired(self, server: Dict[str, Any], now: datetime) -> bool:
        last_used: datetime = server.get("last_used", now)
        return now - last_used > timedelta(seconds=self.idle_threshold_seconds)
