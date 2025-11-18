"""
Example Client for Meta-MCP Server

This demonstrates how to interact with the Meta-MCP Server
from a Python script (outside of Claude/ChatGPT).
"""

import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MetaMCPClient:
    """Client for interacting with Meta-MCP Server"""

    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session = None
        self.exit_stack = None

    async def connect(self):
        """Establish connection to Meta-MCP Server"""
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script_path]
        )

        self.exit_stack = AsyncExitStack()
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )

        await self.session.initialize()
        print("Connected to Meta-MCP Server")

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the Meta-MCP Server"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        result = await self.session.call_tool(tool_name, arguments)
        return result

    async def disconnect(self):
        """Close connection and cleanup"""
        if self.exit_stack:
            await self.exit_stack.aclose()
        print("Disconnected from Meta-MCP Server")


async def example_workflow():
    """Example workflow using Meta-MCP Server"""

    # Initialize client
    client = MetaMCPClient("./meta_mcp_server.py")
    await client.connect()

    try:
        # Example 1: Create a calculator server
        print("\n=== Creating Calculator Server ===")
        result = await client.call_tool("create_server", {
            "name": "my-calculator",
            "server_type": "python",
            "template": "basic_calculator"
        })
        print(f"Create result: {result}")

        # Extract server ID
        server_id = None
        for content in result.content:
            if hasattr(content, 'text'):
                data = json.loads(content.text)
                server_id = data.get('server_id')
                break

        if not server_id:
            print("Failed to get server ID")
            return

        print(f"Server ID: {server_id}")

        # Example 2: Get server capabilities
        print("\n=== Getting Server Capabilities ===")
        result = await client.call_tool("get_server_capabilities", {
            "server_id": server_id
        })
        print(f"Capabilities: {result}")

        # Example 3: Execute a calculation
        print("\n=== Executing Calculation ===")
        result = await client.call_tool("execute_on_server", {
            "server_id": server_id,
            "tool_name": "add",
            "arguments": {"a": 15, "b": 27}
        })
        print(f"Calculation result: {result}")

        # Example 4: List all servers
        print("\n=== Listing All Servers ===")
        result = await client.call_tool("list_servers", {})
        print(f"Active servers: {result}")

        # Example 5: Orchestrate complex task
        print("\n=== Orchestrating Multi-Server Task ===")
        result = await client.call_tool("orchestrate_task", {
            "task_description": "Process data with multiple tools",
            "required_capabilities": ["data_analysis", "calculator"]
        })
        print(f"Orchestration result: {result}")

        # Example 6: Cleanup - stop all servers
        print("\n=== Cleaning Up ===")
        result = await client.call_tool("stop_all_servers", {})
        print(f"Cleanup result: {result}")

    finally:
        await client.disconnect()


async def example_file_operations():
    """Example showing file operations workflow"""

    client = MetaMCPClient("./meta_mcp_server.py")
    await client.connect()

    try:
        # Create file handler server
        print("\n=== File Operations Workflow ===")
        result = await client.call_tool("create_server", {
            "name": "file-handler",
            "server_type": "python",
            "template": "file_handler_template"
        })

        # Extract server ID
        server_id = None
        for content in result.content:
            if hasattr(content, 'text'):
                data = json.loads(content.text)
                server_id = data.get('server_id')
                break

        if server_id:
            # Write a test file
            print("Writing test file...")
            await client.call_tool("execute_on_server", {
                "server_id": server_id,
                "tool_name": "write_file",
                "arguments": {
                    "path": "/tmp/test.txt",
                    "content": "Hello from Meta-MCP!"
                }
            })

            # Read the file back
            print("Reading test file...")
            result = await client.call_tool("execute_on_server", {
                "server_id": server_id,
                "tool_name": "read_file",
                "arguments": {"path": "/tmp/test.txt"}
            })
            print(f"File contents: {result}")

            # List directory
            print("Listing directory...")
            result = await client.call_tool("execute_on_server", {
                "server_id": server_id,
                "tool_name": "list_files",
                "arguments": {"directory": "/tmp"}
            })
            print(f"Directory listing: {result}")

            # Cleanup
            await client.call_tool("stop_server", {"server_id": server_id})

    finally:
        await client.disconnect()


async def example_data_processing():
    """Example showing data processing workflow"""

    client = MetaMCPClient("./meta_mcp_server.py")
    await client.connect()

    try:
        # Create data processor server
        print("\n=== Data Processing Workflow ===")
        result = await client.call_tool("create_server", {
            "name": "data-processor",
            "server_type": "python",
            "template": "data_processor"
        })

        # Extract server ID
        server_id = None
        for content in result.content:
            if hasattr(content, 'text'):
                data = json.loads(content.text)
                server_id = data.get('server_id')
                break

        if server_id:
            # Parse JSON data
            sample_data = json.dumps([
                {"id": 1, "category": "A", "value": 100},
                {"id": 2, "category": "B", "value": 200},
                {"id": 3, "category": "A", "value": 150}
            ])

            print("Parsing JSON data...")
            result = await client.call_tool("execute_on_server", {
                "server_id": server_id,
                "tool_name": "parse_json",
                "arguments": {"json_string": sample_data}
            })
            print(f"Parsed data: {result}")

            # Filter data
            print("Filtering data...")
            result = await client.call_tool("execute_on_server", {
                "server_id": server_id,
                "tool_name": "filter_data",
                "arguments": {
                    "data": json.loads(sample_data),
                    "key": "category",
                    "value": "A"
                }
            })
            print(f"Filtered data: {result}")

            # Summarize data
            print("Summarizing data...")
            result = await client.call_tool("execute_on_server", {
                "server_id": server_id,
                "tool_name": "summarize_data",
                "arguments": {"data": json.loads(sample_data)}
            })
            print(f"Summary: {result}")

            # Cleanup
            await client.call_tool("stop_server", {"server_id": server_id})

    finally:
        await client.disconnect()


def main():
    """Main entry point"""
    print("Meta-MCP Server Example Client")
    print("=" * 60)

    # Choose which example to run
    print("\nSelect example to run:")
    print("1. Basic workflow (calculator)")
    print("2. File operations")
    print("3. Data processing")
    print("4. All examples")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        asyncio.run(example_workflow())
    elif choice == "2":
        asyncio.run(example_file_operations())
    elif choice == "3":
        asyncio.run(example_data_processing())
    elif choice == "4":
        asyncio.run(example_workflow())
        asyncio.run(example_file_operations())
        asyncio.run(example_data_processing())
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
