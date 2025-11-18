"""
Data models and types for Meta MCP Server
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack
from mcp import ClientSession  # type: ignore[import]

logger = logging.getLogger(__name__)


class ChildServerProcess:
    """Manages a child MCP server process lifecycle"""

    def __init__(self, server_id: str, config: Dict[str, Any]):
        self.server_id = server_id
        self.config = config
        self.process = None
        self.session: Optional[ClientSession] = None
        self.stdio = None
        self.write = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self.created_at = datetime.now()
        self.status = "initialized"

    async def start(self):
        """Start the child server process"""
        from mcp import StdioServerParameters  # type: ignore[import]
        from mcp.client.stdio import stdio_client  # type: ignore[import]
        
        try:
            logger.info(f"Starting server {self.server_id}")

            # Create server parameters based on config
            server_params = StdioServerParameters(
                command=self.config.get("command", "python"),
                args=self.config.get("args", []),
                env=self.config.get("env")
            )

            # Use asyncio context stack for resource management
            self.exit_stack = AsyncExitStack()

            # Establish stdio transport
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport

            # Create client session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            # Initialize the connection
            await self.session.initialize()

            self.status = "running"
            logger.info(f"Server {self.server_id} started successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to start server {self.server_id}: {e}")
            self.status = "error"
            raise

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Execute a tool on the child server"""
        if not self.session:
            raise RuntimeError(f"Server {self.server_id} not running")

        try:
            logger.info(
                f"Executing tool '{tool_name}' on server {self.server_id}"
            )
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed on {self.server_id}: {e}")
            raise

    async def list_tools(self) -> List[str]:
        """List available tools from the child server"""
        if not self.session:
            raise RuntimeError(f"Server {self.server_id} not running")

        try:
            response = await self.session.list_tools()
            return [tool.name for tool in response.tools]
        except Exception as e:
            logger.error(f"Failed to list tools on {self.server_id}: {e}")
            raise

    async def list_resources(self) -> List[str]:
        """List available resources from the child server"""
        if not self.session:
            raise RuntimeError(f"Server {self.server_id} not running")

        try:
            response = await self.session.list_resources()
            return [resource.uri for resource in response.resources]
        except Exception as e:
            logger.error(f"Failed to list resources on {self.server_id}: {e}")
            raise

    async def stop(self):
        """Stop the child server and cleanup resources"""
        try:
            logger.info(f"Stopping server {self.server_id}")

            if self.exit_stack:
                await self.exit_stack.aclose()

            self.status = "stopped"
            logger.info(f"Server {self.server_id} stopped")

        except Exception as e:
            logger.error(f"Error stopping server {self.server_id}: {e}")
            raise


# Type definitions
ServerConfig = Dict[str, Any]
ServerRegistry = Dict[str, Dict[str, Any]]
