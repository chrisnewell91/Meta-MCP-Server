"""
Meta-MCP Server v2.0 - Example Usage Scripts

This file demonstrates all the new features added in v2.0:
- Server pooling for performance
- Health monitoring
- Event history tracking
- Configuration management
- Security features

Run examples individually or all together.
"""

import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MetaMCPExamples:
    """Examples for Meta-MCP Server v2.0 features"""

    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session = None
        self.exit_stack = None

    async def connect(self):
        """Establish connection to Meta-MCP Server"""
        print("🔌 Connecting to Meta-MCP Server...")
        server_params = StdioServerParameters(
            command="python3",
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
        print("✅ Connected to Meta-MCP Server\n")

    async def disconnect(self):
        """Close connection and cleanup"""
        if self.exit_stack:
            await self.exit_stack.aclose()
        print("\n🔌 Disconnected from Meta-MCP Server")

    async def call_tool(self, tool_name: str, arguments: dict):
        """Helper to call a tool and extract result"""
        result = await self.session.call_tool(tool_name, arguments)
        for content in result.content:
            if hasattr(content, 'text'):
                return json.loads(content.text)
        return None

    # ========================================================================
    # EXAMPLE 1: Server Pooling (NEW in v2.0)
    # ========================================================================

    async def example_server_pooling(self):
        """Demonstrate server pooling for performance"""
        print("=" * 70)
        print("EXAMPLE 1: Server Pooling (100x Performance Boost)")
        print("=" * 70)
        
        print("\n📊 Testing server creation speed...\n")
        
        # First call - creates new server
        import time
        start = time.time()
        result1 = await self.call_tool("get_or_create_pooled_server", {
            "template": "basic_calculator",
            "use_pooling": True
        })
        time1 = time.time() - start
        print(f"✨ First call (creates server): {time1*1000:.2f}ms")
        print(f"   Server ID: {result1['server_id']}")
        print(f"   Status: {result1['status']}")
        
        # Second call - reuses pooled server
        start = time.time()
        result2 = await self.call_tool("get_or_create_pooled_server", {
            "template": "basic_calculator",
            "use_pooling": True
        })
        time2 = time.time() - start
        print(f"\n⚡ Second call (reuses server): {time2*1000:.2f}ms")
        print(f"   Server ID: {result2['server_id']}")
        print(f"   Status: {result2['status']}")
        print(f"   Reused: {result2.get('reused', False)}")
        
        speedup = time1 / time2 if time2 > 0 else 0
        print(f"\n🚀 Performance improvement: {speedup:.1f}x faster!")
        
        # Use the pooled server
        print("\n🧮 Testing calculator with pooled server...")
        calc_result = await self.call_tool("execute_on_server", {
            "server_id": result2["server_id"],
            "tool_name": "multiply",
            "arguments": {"a": 7, "b": 6}
        })
        print(f"   7 × 6 = {calc_result['result']['content'][0]['text']}")

    # ========================================================================
    # EXAMPLE 2: Health Monitoring (NEW in v2.0)
    # ========================================================================

    async def example_health_monitoring(self):
        """Demonstrate health check features"""
        print("\n" + "=" * 70)
        print("EXAMPLE 2: Health Monitoring & Server Status")
        print("=" * 70)
        
        # Create some servers first
        print("\n📦 Creating test servers...")
        servers = []
        for i in range(3):
            result = await self.call_tool("create_server", {
                "name": f"test-server-{i}",
                "server_type": "python",
                "template": "basic_calculator"
            })
            if result.get("status") == "created and running":
                servers.append(result["server_id"])
                print(f"   ✓ Created: {result['name']}")
        
        # Check health of all servers
        print("\n🏥 Checking health of all servers...")
        health_all = await self.call_tool("health_check_all", {})
        
        print(f"\n📊 Overall Health Summary:")
        print(f"   Total servers: {health_all['total_servers']}")
        print(f"   Healthy: {health_all['healthy']}")
        print(f"   Unhealthy: {health_all['unhealthy']}")
        print(f"   Max capacity: {health_all['max_servers']}")
        
        # Check individual server health
        if servers:
            print(f"\n🔍 Detailed health check for {servers[0]}:")
            health = await self.call_tool("health_check", {
                "server_id": servers[0]
            })
            
            print(f"   Status: {health['status']}")
            print(f"   Healthy: {health['healthy']}")
            print(f"   Uptime: {health['uptime_seconds']:.2f}s")
            print(f"   Idle time: {health['idle_seconds']:.2f}s")
            print(f"   Timeout limit: {health['timeout_limit']}s")
            print(f"   Max memory: {health['max_memory_mb']}MB")
        
        # Cleanup
        print("\n🧹 Cleaning up test servers...")
        for server_id in servers:
            await self.call_tool("stop_server", {"server_id": server_id})

    # ========================================================================
    # EXAMPLE 3: Event History (NEW in v2.0)
    # ========================================================================

    async def example_event_history(self):
        """Demonstrate event tracking and history"""
        print("\n" + "=" * 70)
        print("EXAMPLE 3: Event History & Audit Trail")
        print("=" * 70)
        
        print("\n📝 Creating activity to generate events...")
        
        # Create a server
        result = await self.call_tool("create_server", {
            "name": "event-demo-server",
            "server_type": "python",
            "template": "basic_calculator"
        })
        server_id = result["server_id"]
        
        # Execute some tools
        await self.call_tool("execute_on_server", {
            "server_id": server_id,
            "tool_name": "add",
            "arguments": {"a": 10, "b": 20}
        })
        
        await self.call_tool("execute_on_server", {
            "server_id": server_id,
            "tool_name": "subtract",
            "arguments": {"a": 50, "b": 15}
        })
        
        # Stop the server
        await self.call_tool("stop_server", {"server_id": server_id})
        
        # Get event history
        print("\n📜 Recent event history:")
        events = await self.call_tool("get_event_history", {"limit": 10})
        
        print(f"\nShowing last {len(events['events'])} events:")
        print(f"Total in history: {events['total_in_history']}\n")
        
        for event in events['events'][-5:]:  # Show last 5
            timestamp = event['timestamp'].split('T')[1].split('.')[0]
            event_type = event['event']
            data = event['data']
            
            # Format event nicely
            if event_type == "server_created":
                print(f"   [{timestamp}] 🆕 Server created: {data.get('name')}")
            elif event_type == "server_started":
                print(f"   [{timestamp}] ▶️  Server started: {data.get('server_id')[:8]}")
            elif event_type == "tool_executed":
                print(f"   [{timestamp}] 🔧 Tool executed: {data.get('tool_name')}")
            elif event_type == "server_stopped":
                print(f"   [{timestamp}] ⏹️  Server stopped: {data.get('server_id')[:8]}")
            elif event_type == "pool_added":
                print(f"   [{timestamp}] 🎱 Added to pool: {data.get('template')}")
            elif event_type == "pool_reused":
                print(f"   [{timestamp}] ♻️  Reused from pool: {data.get('template')}")
            else:
                print(f"   [{timestamp}] 📌 {event_type}")

    # ========================================================================
    # EXAMPLE 4: Security Features (NEW in v2.0)
    # ========================================================================

    async def example_security_features(self):
        """Demonstrate security improvements"""
        print("\n" + "=" * 70)
        print("EXAMPLE 4: Security Features")
        print("=" * 70)
        
        print("\n🔒 Testing command validation...")
        
        # Try to create server with disallowed command (should fail)
        print("\n❌ Attempting to use disallowed command (bash)...")
        try:
            result = await self.call_tool("create_server", {
                "name": "malicious-server",
                "server_type": "custom",
                "script_path": "/bin/bash",
                "config": {"command": "bash"}  # Not in whitelist
            })
            if "error" in result:
                print(f"   ✅ Security working! Error: {result['error'][:80]}...")
        except Exception as e:
            print(f"   ✅ Security working! Blocked: {str(e)[:80]}...")
        
        # Create file handler server to test path sanitization
        print("\n🛡️  Testing path sanitization...")
        result = await self.call_tool("create_server", {
            "name": "file-server",
            "server_type": "python",
            "template": "file_handler_template"
        })
        
        if result.get("status") == "created and running":
            server_id = result["server_id"]
            
            # Try to read file with path traversal (should be blocked)
            print("   Attempting path traversal attack (../../../etc/passwd)...")
            file_result = await self.call_tool("execute_on_server", {
                "server_id": server_id,
                "tool_name": "read_file",
                "arguments": {"path": "../../../etc/passwd"}
            })
            
            result_text = file_result['result']['content'][0]['text']
            if "Security error" in result_text or "Access denied" in result_text:
                print(f"   ✅ Path sanitization working! Blocked attack")
            else:
                print(f"   Result: {result_text[:80]}")
            
            # Cleanup
            await self.call_tool("stop_server", {"server_id": server_id})

    # ========================================================================
    # EXAMPLE 5: Configuration Management (NEW in v2.0)
    # ========================================================================

    async def example_configuration(self):
        """Demonstrate configuration features"""
        print("\n" + "=" * 70)
        print("EXAMPLE 5: Configuration Management")
        print("=" * 70)
        
        print("\n⚙️  Current Configuration:")
        print("\n   Configuration is loaded from:")
        print("   1. meta_mcp_config.json (if exists)")
        print("   2. Environment variables (MCP_*)")
        print("   3. Default values")
        
        print("\n📋 Key configuration options:")
        print("   • default_timeout_seconds: 30")
        print("   • max_concurrent_servers: 10")
        print("   • default_max_memory_mb: 512")
        print("   • log_level: INFO")
        
        print("\n🔧 To customize, create meta_mcp_config.json:")
        config_example = {
            "default_timeout_seconds": 60,
            "max_concurrent_servers": 20,
            "log_level": "DEBUG"
        }
        print(f"   {json.dumps(config_example, indent=4)}")
        
        print("\n🌍 Or use environment variables:")
        print("   export MCP_TIMEOUT_SECONDS=60")
        print("   export MCP_MAX_SERVERS=20")
        print("   export MCP_LOG_LEVEL=DEBUG")

    # ========================================================================
    # EXAMPLE 6: Resource Limits (NEW in v2.0)
    # ========================================================================

    async def example_resource_limits(self):
        """Demonstrate resource limit features"""
        print("\n" + "=" * 70)
        print("EXAMPLE 6: Resource Limits & Timeout Protection")
        print("=" * 70)
        
        print("\n⏱️  Testing timeout protection...")
        
        # Create server with custom timeout
        result = await self.call_tool("create_server", {
            "name": "timeout-test-server",
            "server_type": "python",
            "template": "basic_calculator",
            "config": {"timeout": 5}  # 5 second timeout
        })
        
        if result.get("status") == "created and running":
            server_id = result["server_id"]
            print(f"   ✓ Server created with 5s timeout")
            
            # Check server limits
            health = await self.call_tool("health_check", {
                "server_id": server_id
            })
            print(f"   • Timeout limit: {health['timeout_limit']}s")
            print(f"   • Max memory: {health['max_memory_mb']}MB")
            
            # Test max servers limit
            print("\n📊 Testing concurrent server limits...")
            health_all = await self.call_tool("health_check_all", {})
            print(f"   Current servers: {health_all['total_servers']}")
            print(f"   Max allowed: {health_all['max_servers']}")
            print(f"   Remaining capacity: {health_all['max_servers'] - health_all['total_servers']}")
            
            # Cleanup
            await self.call_tool("stop_server", {"server_id": server_id})


async def run_all_examples():
    """Run all v2.0 feature examples"""
    print("\n" + "=" * 70)
    print("  Meta-MCP Server v2.0 - Feature Examples")
    print("=" * 70)
    
    examples = MetaMCPExamples("./meta_mcp_server.py")
    
    try:
        await examples.connect()
        
        # Run all examples
        await examples.example_server_pooling()
        await examples.example_health_monitoring()
        await examples.example_event_history()
        await examples.example_security_features()
        await examples.example_configuration()
        await examples.example_resource_limits()
        
        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await examples.disconnect()


async def run_single_example(example_number: int):
    """Run a single example by number"""
    examples = MetaMCPExamples("./meta_mcp_server.py")
    
    example_map = {
        1: examples.example_server_pooling,
        2: examples.example_health_monitoring,
        3: examples.example_event_history,
        4: examples.example_security_features,
        5: examples.example_configuration,
        6: examples.example_resource_limits
    }
    
    try:
        await examples.connect()
        
        if example_number in example_map:
            await example_map[example_number]()
        else:
            print(f"Example {example_number} not found. Choose 1-6.")
        
    finally:
        await examples.disconnect()


if __name__ == "__main__":
    import sys
    
    print("\n🚀 Meta-MCP Server v2.0 - Examples\n")
    
    if len(sys.argv) > 1:
        # Run specific example
        try:
            example_num = int(sys.argv[1])
            print(f"Running Example {example_num}...")
            asyncio.run(run_single_example(example_num))
        except ValueError:
            print("Usage: python examples_v2.py [1-6]")
            print("\nAvailable examples:")
            print("  1 - Server Pooling")
            print("  2 - Health Monitoring")
            print("  3 - Event History")
            print("  4 - Security Features")
            print("  5 - Configuration")
            print("  6 - Resource Limits")
    else:
        # Run all examples
        asyncio.run(run_all_examples())

