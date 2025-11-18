#!/usr/bin/env python3
"""
Meta MCP Server - Hello World Example

This minimal example demonstrates how to:
1. Connect to the Meta MCP Server
2. Create a child calculator server
3. Execute a simple calculation
4. Clean up resources

Run this example:
    python examples/hello_world.py

Before running, ensure you have:
1. Installed meta-mcp-server: pip install -e .
2. Started the Meta MCP Server: meta-mcp-server
"""
from __future__ import annotations

import asyncio
import json
from mcp import ClientSession, StdioServerParameters  # type: ignore[import]
from mcp.client.stdio import stdio_client  # type: ignore[import]
from contextlib import AsyncExitStack


async def hello_meta_mcp():
    """Minimal example of using Meta MCP Server"""
    
    # 1. Connect to Meta MCP Server
    print("🚀 Connecting to Meta MCP Server...")
    
    server_params = StdioServerParameters(
        command="meta-mcp-server",
        args=[]
    )
    
    async with AsyncExitStack() as exit_stack:
        # Establish connection
        stdio_transport = await exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        
        session = await exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )
        
        await session.initialize()
        print("✅ Connected to Meta MCP Server!")
        
        # 2. Create a calculator server
        print("\n📦 Creating a calculator server...")
        
        result = await session.call_tool(
            "create_server",
            {
                "name": "my-calculator",
                "server_type": "python",
                "template": "basic_calculator"
            }
        )
        
        server_info = json.loads(result.content[0].text)
        server_id = server_info["server_id"]
        print(f"✅ Calculator server created! ID: {server_id[:8]}...")
        
        # 3. Perform a calculation
        print("\n🧮 Let's calculate 42 + 17...")
        
        calc_result = await session.call_tool(
            "execute_on_server",
            {
                "server_id": server_id,
                "tool_name": "add",
                "arguments": {"a": 42, "b": 17}
            }
        )
        
        result_data = json.loads(calc_result.content[0].text)
        answer = result_data["result"]["content"][0]["text"]
        print(f"✅ Answer: {answer}")
        
        # 4. List all servers (optional)
        print("\n📋 Current servers:")
        servers = await session.call_tool("list_servers", {})
        server_list = json.loads(servers.content[0].text)
        
        for server in server_list:
            print(f"   - {server['name']} ({server['status']})")
        
        # 5. Clean up
        print("\n🧹 Cleaning up...")
        cleanup_result = await session.call_tool(
            "stop_server",
            {"server_id": server_id}
        )
        
        cleanup_info = json.loads(cleanup_result.content[0].text)
        print(f"✅ {cleanup_info['message']}")
        
        print("\n🎉 Hello World example completed!")


def main():
    """Run the Hello World example"""
    print("=" * 50)
    print("Meta MCP Server - Hello World Example")
    print("=" * 50)
    
    try:
        asyncio.run(hello_meta_mcp())
    except KeyboardInterrupt:
        print("\n\n⚠️  Example interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nMake sure the Meta MCP Server is installed and available.")
        print("Install: pip install -e .")
        print("Or run directly: python -m meta_mcp_server")


if __name__ == "__main__":
    main()
