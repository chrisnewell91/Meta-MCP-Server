"""
Core Meta MCP Server implementation
"""
from __future__ import annotations
import json
import uuid
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from .models import ChildServerProcess, ServerRegistry
from .config import get_config
from .templates import generate_from_template, get_template_for_capability
from .security import validate_command
from .pooling import ServerPool
from .health import HealthMonitor

logger = logging.getLogger(__name__)


class MetaMCPServer:
    """Meta MCP Server that orchestrates child MCP servers"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config(config_path)
        self.mcp = FastMCP("Meta-MCP-Server")
        self.server_registry: ServerRegistry = {}
        self.server_pool = ServerPool()
        self.health_monitor = HealthMonitor()
        
        # Register all tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all MCP tools"""
        self.mcp.tool()(self.create_server)
        self.mcp.tool()(self.execute_on_server)
        self.mcp.tool()(self.list_servers)
        self.mcp.tool()(self.get_server_capabilities)
        self.mcp.tool()(self.stop_server)
        self.mcp.tool()(self.orchestrate_task)
        self.mcp.tool()(self.stop_all_servers)
        
        # V2.0 tools (stubs for now)
        self.mcp.tool()(self.get_or_create_pooled_server)
        self.mcp.tool()(self.health_check)
        self.mcp.tool()(self.health_check_all)
        self.mcp.tool()(self.get_event_history)
    
    async def create_server(
        self,
        name: str,
        server_type: str,
        script_path: Optional[str] = None,
        template: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Create and spawn a new child MCP server.

        Args:
            name: Human-readable name for the server
            server_type: Type of server (python, typescript, custom)
            script_path: Path to existing server script
            template: Template to use for server generation
                (basic_calculator, web_scraper_template, etc.)
            config: Additional configuration (env vars, args)

        Returns:
            Dictionary with server_id and status
        """
        server_id = str(uuid.uuid4())

        # Build server configuration
        server_config = config or {}

        if script_path:
            # Use existing script
            server_config["command"] = (
                "python" if server_type == "python" else "node"
            )
            server_config["args"] = [script_path]
        elif template:
            # Generate from template
            temp_dir = self.config.temp_directory or "/tmp"
            temp_file = f"{temp_dir}/mcp_server_{server_id}.py"
            generate_from_template(template, temp_file)
            server_config["command"] = "python"
            server_config["args"] = [temp_file]
        else:
            raise ValueError("Must provide either script_path or template")

        # Validate command
        if not validate_command(server_config["command"], self.config.allowed_commands):
            return {
                "server_id": server_id,
                "status": "error",
                "error": f"Command '{server_config['command']}' not allowed"
            }

        # Create and start the child server
        child_server = ChildServerProcess(server_id, server_config)

        try:
            await child_server.start()

            # Register the server
            self.server_registry[server_id] = {
                "id": server_id,
                "name": name,
                "type": server_type,
                "config": server_config,
                "process": child_server,
                "created_at": child_server.created_at.isoformat(),
                "status": child_server.status,
                "template": template
            }

            self.server_pool.register_server(server_id, template)

            # Record event
            self.health_monitor.record_event(
                "server_created", 
                server_id, 
                {"name": name, "type": server_type}
            )

            logger.info(f"Server '{name}' (ID: {server_id}) created successfully")

            return {
                "server_id": server_id,
                "name": name,
                "status": "created and running",
                "message": f"Server {name} created successfully"
            }

        except Exception as e:
            logger.error(f"Failed to create server '{name}': {e}")
            return {
                "server_id": server_id,
                "status": "error",
                "error": str(e)
            }

    async def execute_on_server(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool on a specific child server.

        Args:
            server_id: ID of the server to execute on
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool

        Returns:
            Result from the tool execution
        """
        if server_id not in self.server_registry:
            return {"error": f"Server {server_id} not found"}

        child_server = self.server_registry[server_id]["process"]

        response: Dict[str, Any]
        try:
            result = await child_server.execute_tool(tool_name, arguments)

            # Record event
            self.health_monitor.record_event(
                "tool_executed",
                server_id,
                {"tool": tool_name, "success": True}
            )

            response = {
                "server_id": server_id,
                "tool": tool_name,
                "result": result,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Execution error on {server_id}: {e}")

            # Record failure event
            self.health_monitor.record_event(
                "tool_executed",
                server_id,
                {"tool": tool_name, "success": False, "error": str(e)}
            )

            response = {
                "server_id": server_id,
                "tool": tool_name,
                "error": str(e),
                "status": "error"
            }
        finally:
            if server_id in self.server_registry:
                self.server_pool.mark_server_idle(server_id)
                await self.server_pool.cleanup_idle_servers(
                    stop_callback=self._stop_server_for_pool
                )

        return response

    async def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all active child servers.

        Returns:
            List of server information dictionaries
        """
        servers = []
        for server_id, info in self.server_registry.items():
            servers.append({
                "server_id": server_id,
                "name": info["name"],
                "type": info["type"],
                "status": info["process"].status,
                "created_at": info["created_at"]
            })
        return servers

    async def get_server_capabilities(self, server_id: str) -> Dict[str, Any]:
        """
        Get capabilities (tools and resources) of a specific server.

        Args:
            server_id: ID of the server to query

        Returns:
            Dictionary with tools and resources lists
        """
        if server_id not in self.server_registry:
            return {"error": f"Server {server_id} not found"}

        child_server = self.server_registry[server_id]["process"]

        try:
            tools = await child_server.list_tools()
            resources = await child_server.list_resources()

            return {
                "server_id": server_id,
                "name": self.server_registry[server_id]["name"],
                "tools": tools,
                "resources": resources,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to get capabilities for {server_id}: {e}")
            return {
                "server_id": server_id,
                "error": str(e),
                "status": "error"
            }

    async def stop_server(self, server_id: str) -> Dict[str, str]:
        """
        Stop and remove a child server.

        Args:
            server_id: ID of the server to stop

        Returns:
            Status message
        """
        if server_id not in self.server_registry:
            return {"error": f"Server {server_id} not found"}

        child_server = self.server_registry[server_id]["process"]

        try:
            await child_server.stop()
            del self.server_registry[server_id]
            self.server_pool.remove_server(server_id)
            
            # Record event
            self.health_monitor.record_event(
                "server_stopped",
                server_id,
                {}
            )

            logger.info(f"Server {server_id} stopped and removed")

            return {
                "server_id": server_id,
                "status": "stopped and removed",
                "message": f"Server {server_id} stopped successfully"
            }
        except Exception as e:
            logger.error(f"Error stopping {server_id}: {e}")
            return {
                "server_id": server_id,
                "status": "error",
                "error": str(e)
            }

    async def orchestrate_task(
        self,
        task_description: str,
        required_capabilities: List[str]
    ) -> Dict[str, Any]:
        """
        Orchestrate a complex task by spawning required servers and
        coordinating execution.

        Args:
            task_description: Description of the task to accomplish
            required_capabilities: List of capabilities needed
                (e.g., "web_scraping", "data_analysis")

        Returns:
            Task execution result with spawned server IDs
        """
        task_id = str(uuid.uuid4())
        spawned_servers = []

        try:
            logger.info(f"Orchestrating task {task_id}: {task_description}")

            # Spawn required servers
            for capability in required_capabilities:
                template = get_template_for_capability(capability)
                result = await self.create_server(
                    name=f"{capability}_server_{task_id[:8]}",
                    server_type="python",
                    template=template
                )
                if result.get("status") == "created and running":
                    spawned_servers.append(result["server_id"])

            for server_id in spawned_servers:
                self.server_pool.mark_server_idle(server_id)

            await self.server_pool.cleanup_idle_servers(
                stop_callback=self._stop_server_for_pool
            )

            return {
                "task_id": task_id,
                "description": task_description,
                "spawned_servers": spawned_servers,
                "capabilities": required_capabilities,
                "status": "servers_ready",
                "message": (
                    "Task orchestration initialized. "
                    "Execute subtasks on spawned servers."
                )
            }

        except Exception as e:
            logger.error(f"Task orchestration failed: {e}")

            # Cleanup on error
            for server_id in spawned_servers:
                try:
                    await self.stop_server(server_id)
                except Exception:
                    pass

            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    async def stop_all_servers(self) -> Dict[str, Any]:
        """
        Stop all running child servers. Useful for cleanup.

        Returns:
            Summary of stopped servers
        """
        stopped = []
        errors = []

        for server_id in list(self.server_registry.keys()):
            try:
                result = await self.stop_server(server_id)
                if result.get("status") == "stopped and removed":
                    stopped.append(server_id)
                else:
                    errors.append({
                        "server_id": server_id,
                        "error": result.get("error")
                    })
            except Exception as e:
                errors.append({"server_id": server_id, "error": str(e)})

        return {
            "stopped": stopped,
            "errors": errors,
            "total_stopped": len(stopped),
            "total_errors": len(errors)
        }
    
    # V2.0 Tool Stubs (not yet implemented)
    
    async def get_or_create_pooled_server(
        self,
        template: str,
        use_pooling: bool = True
    ) -> Dict[str, Any]:
        """
        Get or create a pooled server for better performance

        Note: This feature is documented but not yet implemented
        """
        async def _create_server_from_template() -> Dict[str, Any]:
            return await self.create_server(
                name=f"pooled_{template}_{uuid.uuid4().hex[:8]}",
                server_type="python",
                template=template,
            )

        result = await self.server_pool.get_or_create_server(
            template=template,
            use_pooling=use_pooling,
            create_server=_create_server_from_template,
            stop_callback=self._stop_server_for_pool,
        )
        return result
    
    async def health_check(self, server_id: str) -> Dict[str, Any]:
        """
        Check health of a specific server
        
        Note: This feature is documented but not yet implemented
        """
        return await self.health_monitor.check_server_health(server_id)
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Check health of all servers
        
        Note: This feature is documented but not yet implemented  
        """
        result = await self.health_monitor.check_all_servers()
        result["max_servers"] = self.config.max_concurrent_servers
        return result
    
    async def get_event_history(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get recent event history
        
        Note: This feature is documented but not yet implemented
        """
        return self.health_monitor.get_event_history(limit)
    
    def run(self, transport: str = "stdio"):
        """Run the Meta MCP Server"""
        logger.info("Starting Meta-MCP Server")
        self.mcp.run(transport=transport)

    async def _stop_server_for_pool(self, server_id: str) -> None:
        """Stop a server during pool cleanup"""
        if server_id in self.server_registry:
            await self.stop_server(server_id)
        else:
            self.server_pool.remove_server(server_id)
