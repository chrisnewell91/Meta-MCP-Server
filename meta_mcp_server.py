"""
Meta MCP Server - A Dynamic MCP Server Orchestrator

This server can dynamically create and manage child MCP servers
to accomplish complex tasks locally.

Author: Your Name
License: MIT
"""

import json
import uuid
import logging
from typing import Any
from pathlib import Path
from datetime import datetime
from contextlib import AsyncExitStack

from mcp.server.fastmcp import FastMCP
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import ClientSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the meta-MCP server
mcp = FastMCP("Meta-MCP-Server")

# Global registry to track spawned servers
server_registry: dict[str, dict[str, Any]] = {}


class ChildServerProcess:
    """Manages a child MCP server process lifecycle"""

    def __init__(self, server_id: str, config: dict[str, Any]):
        self.server_id = server_id
        self.config = config
        self.process = None
        self.session: ClientSession | None = None
        self.stdio = None
        self.write = None
        self.exit_stack: AsyncExitStack | None = None
        self.created_at = datetime.now()
        self.status = "initialized"

    async def start(self):
        """Start the child server process"""
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
        self, tool_name: str, arguments: dict[str, Any]
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

    async def list_tools(self) -> list[str]:
        """List available tools from the child server"""
        if not self.session:
            raise RuntimeError(f"Server {self.server_id} not running")

        try:
            response = await self.session.list_tools()
            return [tool.name for tool in response.tools]
        except Exception as e:
            logger.error(f"Failed to list tools on {self.server_id}: {e}")
            raise

    async def list_resources(self) -> list[str]:
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


@mcp.tool()
async def create_server(
    name: str,
    server_type: str,
    script_path: str | None = None,
    template: str | None = None,
    config: dict[str, Any] | None = None
) -> dict[str, str]:
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
        temp_file = f"/tmp/mcp_server_{server_id}.py"
        _generate_from_template(template, temp_file)
        server_config["command"] = "python"
        server_config["args"] = [temp_file]
    else:
        raise ValueError("Must provide either script_path or template")

    # Create and start the child server
    child_server = ChildServerProcess(server_id, server_config)

    try:
        await child_server.start()

        # Register the server
        server_registry[server_id] = {
            "id": server_id,
            "name": name,
            "type": server_type,
            "config": server_config,
            "process": child_server,
            "created_at": child_server.created_at.isoformat(),
            "status": child_server.status
        }

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


@mcp.tool()
async def execute_on_server(
    server_id: str,
    tool_name: str,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Execute a tool on a specific child server.

    Args:
        server_id: ID of the server to execute on
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool

    Returns:
        Result from the tool execution
    """
    if server_id not in server_registry:
        return {"error": f"Server {server_id} not found"}

    child_server = server_registry[server_id]["process"]

    try:
        result = await child_server.execute_tool(tool_name, arguments)
        return {
            "server_id": server_id,
            "tool": tool_name,
            "result": result,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Execution error on {server_id}: {e}")
        return {
            "server_id": server_id,
            "tool": tool_name,
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def list_servers() -> list[dict[str, Any]]:
    """
    List all active child servers.

    Returns:
        List of server information dictionaries
    """
    servers = []
    for server_id, info in server_registry.items():
        servers.append({
            "server_id": server_id,
            "name": info["name"],
            "type": info["type"],
            "status": info["process"].status,
            "created_at": info["created_at"]
        })
    return servers


@mcp.tool()
async def get_server_capabilities(server_id: str) -> dict[str, Any]:
    """
    Get capabilities (tools and resources) of a specific server.

    Args:
        server_id: ID of the server to query

    Returns:
        Dictionary with tools and resources lists
    """
    if server_id not in server_registry:
        return {"error": f"Server {server_id} not found"}

    child_server = server_registry[server_id]["process"]

    try:
        tools = await child_server.list_tools()
        resources = await child_server.list_resources()

        return {
            "server_id": server_id,
            "name": server_registry[server_id]["name"],
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


@mcp.tool()
async def stop_server(server_id: str) -> dict[str, str]:
    """
    Stop and remove a child server.

    Args:
        server_id: ID of the server to stop

    Returns:
        Status message
    """
    if server_id not in server_registry:
        return {"error": f"Server {server_id} not found"}

    child_server = server_registry[server_id]["process"]

    try:
        await child_server.stop()
        del server_registry[server_id]

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


@mcp.tool()
async def orchestrate_task(
    task_description: str,
    required_capabilities: list[str]
) -> dict[str, Any]:
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
        # Map capabilities to server templates
        capability_templates = {
            "web_scraping": "web_scraper_template",
            "data_analysis": "data_processor",
            "file_operations": "file_handler_template",
            "api_client": "api_integration",
            "calculator": "basic_calculator"
        }

        logger.info(f"Orchestrating task {task_id}: {task_description}")

        # Spawn required servers
        for capability in required_capabilities:
            if capability in capability_templates:
                result = await create_server(
                    name=f"{capability}_server_{task_id[:8]}",
                    server_type="python",
                    template=capability_templates[capability]
                )
                if result.get("status") == "created and running":
                    spawned_servers.append(result["server_id"])

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
                await stop_server(server_id)
            except Exception:
                pass

        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
async def stop_all_servers() -> dict[str, Any]:
    """
    Stop all running child servers. Useful for cleanup.

    Returns:
        Summary of stopped servers
    """
    stopped = []
    errors = []

    for server_id in list(server_registry.keys()):
        try:
            result = await stop_server(server_id)
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


def _generate_from_template(template: str, output_path: str):
    """Generate a server script from a template"""

    templates = {
        "basic_calculator": """from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers\"\"\"
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a\"\"\"
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers\"\"\"
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    \"\"\"Divide a by b\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

        "web_scraper_template": """from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("Web Scraper Server")

@mcp.tool()
def fetch_url(url: str) -> str:
    \"\"\"Fetch content from a URL (simulated)\"\"\"
    # In production, use requests library
    return f"Simulated content from {url}"

@mcp.tool()
def extract_data(html: str, selector: str) -> dict:
    \"\"\"Extract data from HTML using selector (simulated)\"\"\"
    return {
        "selector": selector,
        "data": ["item1", "item2", "item3"],
        "count": 3
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

        "file_handler_template": """from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("File Handler Server")

@mcp.tool()
def read_file(path: str) -> str:
    \"\"\"Read file contents\"\"\"
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    \"\"\"Write content to file\"\"\"
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully written to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def list_files(directory: str = ".") -> list:
    \"\"\"List files in directory\"\"\"
    try:
        return os.listdir(directory)
    except Exception as e:
        return [f"Error: {str(e)}"]

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

        "data_processor": """from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("Data Processor Server")

@mcp.tool()
def parse_json(json_string: str) -> dict:
    \"\"\"Parse JSON string into dictionary\"\"\"
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        return {"error": str(e)}

@mcp.tool()
def filter_data(data: list, key: str, value: str) -> list:
    \"\"\"Filter list of dictionaries by key-value pair\"\"\"
    if not isinstance(data, list):
        return []
    return [
        item for item in data
        if isinstance(item, dict) and item.get(key) == value
    ]

@mcp.tool()
def summarize_data(data: list) -> dict:
    \"\"\"Generate summary statistics for data\"\"\"
    return {
        "count": len(data),
        "type": str(type(data).__name__),
        "sample": data[:3] if len(data) > 0 else []
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

        "api_integration": """from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("API Integration Server")

@mcp.tool()
def make_request(url: str, method: str = "GET") -> dict:
    \"\"\"Make HTTP request (simulated)\"\"\"
    return {
        "url": url,
        "method": method,
        "status_code": 200,
        "message": "Simulated API response"
    }

@mcp.tool()
def parse_response(response_json: str) -> dict:
    \"\"\"Parse API response JSON\"\"\"
    try:
        data = json.loads(response_json)
        return {"valid": True, "data": data}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
"""
    }

    template_code = templates.get(template, templates["basic_calculator"])

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(template_code)

    logger.info(
        f"Generated server from template '{template}' at {output_path}"
    )


# Run the meta-server
if __name__ == "__main__":
    logger.info("Starting Meta-MCP Server")
    mcp.run(transport="stdio")