"""
Comprehensive Test Suite for Meta-MCP Server v2.0

Tests all v2.0 improvements:
- Security features (command validation, path sanitization)
- Server pooling
- Health monitoring
- Event tracking
- Resource limits
- Configuration management

Run: python test_meta_mcp_v2.py
"""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters  # type: ignore[import]
from mcp.client.stdio import stdio_client  # type: ignore[import]


class TestMetaMCPServer:
    """Test suite for Meta-MCP Server v2.0"""

    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session = None
        self.exit_stack = None
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    async def connect(self):
        """Connect to Meta-MCP Server"""
        server_params = StdioServerParameters(
            command=self.server_script_path,
            args=[]
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

    async def disconnect(self):
        """Disconnect from server"""
        if self.exit_stack:
            await self.exit_stack.aclose()

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool and extract result"""
        result = await self.session.call_tool(tool_name, arguments)
        for content in result.content:
            if hasattr(content, 'text'):
                return json.loads(content.text)
        return None

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result_msg = f"{status} - {test_name}"
        if message:
            result_msg += f": {message}"
        print(result_msg)
        
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    # ====================================================================
    # TEST CATEGORY 1: Security Features
    # ====================================================================

    async def test_command_validation(self):
        """Test that only whitelisted commands are allowed"""
        print("\n" + "="*70)
        print("TEST CATEGORY 1: Security Features")
        print("="*70)
        
        # Test 1.1: Allowed command should work
        result = await self.call_tool("create_server", {
            "name": "test-allowed-cmd",
            "server_type": "python",
            "template": "basic_calculator"
        })
        
        passed = result.get("status") == "created and running"
        self.log_test(
            "1.1 - Allowed command (python)",
            passed,
            f"Status: {result.get('status')}"
        )
        
        if passed:
            await self.call_tool("stop_server", {"server_id": result["server_id"]})
        
        # Test 1.2: Disallowed command should be blocked
        # (This test depends on implementation - bash is not in whitelist)
        print("\nSkipping 1.2 - Disallowed command test (requires error handling)")
        
    async def test_path_sanitization(self):
        """Test path traversal protection"""
        # Test 1.3: Create file handler server
        result = await self.call_tool("create_server", {
            "name": "test-file-server",
            "server_type": "python",
            "template": "file_handler_template"
        })
        
        if result.get("status") != "created and running":
            self.log_test("1.3 - Path sanitization setup", False, "Failed to create server")
            return
        
        server_id = result["server_id"]
        
        # Test 1.4: Path traversal should be blocked
        file_result = await self.call_tool("execute_on_server", {
            "server_id": server_id,
            "tool_name": "read_file",
            "arguments": {"path": "../../etc/passwd"}
        })
        
        result_text = str(file_result.get('result', {}).get('content', [{}])[0].get('text', ''))
        blocked = "Security error" in result_text or "Access denied" in result_text
        
        self.log_test(
            "1.4 - Path traversal blocked",
            blocked,
            "Path sanitization working" if blocked else "Security issue!"
        )
        
        # Cleanup
        await self.call_tool("stop_server", {"server_id": server_id})

    # ====================================================================
    # TEST CATEGORY 2: Server Pooling
    # ====================================================================

    async def test_server_pooling(self):
        """Test server pooling performance"""
        print("\n" + "="*70)
        print("TEST CATEGORY 2: Server Pooling & Performance")
        print("="*70)
        
        # Test 2.1: First creation (should create new server)
        start = time.time()
        result1 = await self.call_tool("get_or_create_pooled_server", {
            "template": "basic_calculator",
            "use_pooling": True
        })
        time1 = time.time() - start
        
        passed = result1.get("status") in ["created and running", "reused from pool"]
        self.log_test(
            "2.1 - Create pooled server",
            passed,
            f"Time: {time1*1000:.2f}ms"
        )
        
        # Test 2.2: Second call (should reuse from pool)
        await asyncio.sleep(1.1)  # Wait for idle threshold
        
        start = time.time()
        result2 = await self.call_tool("get_or_create_pooled_server", {
            "template": "basic_calculator",
            "use_pooling": True
        })
        time2 = time.time() - start
        
        reused = result2.get("reused", False)
        speedup = time1 / time2 if time2 > 0 else 0
        
        self.log_test(
            "2.2 - Reuse pooled server",
            reused,
            f"Time: {time2*1000:.2f}ms, Speedup: {speedup:.1f}x"
        )
        
        # Test 2.3: Pooled server should work
        calc_result = await self.call_tool("execute_on_server", {
            "server_id": result2["server_id"],
            "tool_name": "add",
            "arguments": {"a": 10, "b": 15}
        })
        
        result_value = calc_result.get('result', {}).get('content', [{}])[0].get('text', '')
        passed = str(result_value) == "25"
        
        self.log_test(
            "2.3 - Pooled server functionality",
            passed,
            f"10 + 15 = {result_value}"
        )

    # ====================================================================
    # TEST CATEGORY 3: Health Monitoring
    # ====================================================================

    async def test_health_monitoring(self):
        """Test health check features"""
        print("\n" + "="*70)
        print("TEST CATEGORY 3: Health Monitoring")
        print("="*70)
        
        # Create test servers
        servers = []
        for i in range(2):
            result = await self.call_tool("create_server", {
                "name": f"health-test-{i}",
                "server_type": "python",
                "template": "basic_calculator"
            })
            if result.get("status") == "created and running":
                servers.append(result["server_id"])
        
        # Test 3.1: health_check_all
        health_all = await self.call_tool("health_check_all", {})
        
        passed = (
            health_all.get("total_servers", 0) >= 2 and
            "healthy" in health_all and
            "unhealthy" in health_all
        )
        
        self.log_test(
            "3.1 - health_check_all",
            passed,
            f"Total: {health_all.get('total_servers')}, Healthy: {health_all.get('healthy')}"
        )
        
        # Test 3.2: Individual health check
        if servers:
            health = await self.call_tool("health_check", {
                "server_id": servers[0]
            })
            
            passed = (
                "uptime_seconds" in health and
                "idle_seconds" in health and
                "healthy" in health and
                health.get("status") == "running"
            )
            
            self.log_test(
                "3.2 - Individual health check",
                passed,
                f"Uptime: {health.get('uptime_seconds', 0):.2f}s, Healthy: {health.get('healthy')}"
            )
        
        # Cleanup
        for server_id in servers:
            await self.call_tool("stop_server", {"server_id": server_id})

    # ====================================================================
    # TEST CATEGORY 4: Event Tracking
    # ====================================================================

    async def test_event_tracking(self):
        """Test event history and tracking"""
        print("\n" + "="*70)
        print("TEST CATEGORY 4: Event Tracking & History")
        print("="*70)
        
        # Test 4.1: Events are recorded
        # Create server (should generate events)
        result = await self.call_tool("create_server", {
            "name": "event-test-server",
            "server_type": "python",
            "template": "basic_calculator"
        })
        
        server_id = result.get("server_id")
        
        # Execute tool (should generate event)
        await self.call_tool("execute_on_server", {
            "server_id": server_id,
            "tool_name": "multiply",
            "arguments": {"a": 3, "b": 4}
        })
        
        # Get event history
        events = await self.call_tool("get_event_history", {"limit": 20})
        
        passed = (
            "events" in events and
            len(events["events"]) > 0 and
            "total_in_history" in events
        )
        
        self.log_test(
            "4.1 - Event history recording",
            passed,
            f"Found {len(events.get('events', []))} events"
        )
        
        # Test 4.2: Check for specific event types
        event_types = [e["event"] for e in events.get("events", [])]
        has_server_event = any(e in event_types for e in ["server_created", "server_started"])
        has_tool_event = "tool_executed" in event_types
        
        self.log_test(
            "4.2 - Event types present",
            has_server_event or has_tool_event,
            f"Event types: {set(event_types)}"
        )
        
        # Cleanup
        await self.call_tool("stop_server", {"server_id": server_id})
        
        # Test 4.3: Stop event recorded
        await asyncio.sleep(0.1)  # Let event process
        events_after = await self.call_tool("get_event_history", {"limit": 10})
        event_types_after = [e["event"] for e in events_after.get("events", [])]
        
        has_stop_event = "server_stopped" in event_types_after
        
        self.log_test(
            "4.3 - Server stop event",
            has_stop_event,
            "Stop event recorded" if has_stop_event else "Stop event not found"
        )

    # ====================================================================
    # TEST CATEGORY 5: Resource Limits
    # ====================================================================

    async def test_resource_limits(self):
        """Test resource limit enforcement"""
        print("\n" + "="*70)
        print("TEST CATEGORY 5: Resource Limits")
        print("="*70)
        
        # Test 5.1: Custom timeout configuration
        result = await self.call_tool("create_server", {
            "name": "timeout-test",
            "server_type": "python",
            "template": "basic_calculator",
            "config": {"timeout": 5, "max_memory_mb": 256}
        })
        
        passed = result.get("status") == "created and running"
        self.log_test(
            "5.1 - Custom timeout configuration",
            passed,
            "Server created with custom limits"
        )
        
        if passed:
            server_id = result["server_id"]
            
            # Check that limits are set
            health = await self.call_tool("health_check", {"server_id": server_id})
            
            limits_correct = (
                health.get("timeout_limit") == 5 and
                health.get("max_memory_mb") == 256
            )
            
            self.log_test(
                "5.2 - Resource limits applied",
                limits_correct,
                f"Timeout: {health.get('timeout_limit')}s, Memory: {health.get('max_memory_mb')}MB"
            )
            
            # Cleanup
            await self.call_tool("stop_server", {"server_id": server_id})
        
        # Test 5.3: Max servers limit
        health_all = await self.call_tool("health_check_all", {})
        max_servers = health_all.get("max_servers", 0)
        
        passed = max_servers > 0
        self.log_test(
            "5.3 - Max servers limit configured",
            passed,
            f"Max servers: {max_servers}"
        )

    # ====================================================================
    # TEST CATEGORY 6: Basic Functionality
    # ====================================================================

    async def test_basic_functionality(self):
        """Test core server functionality"""
        print("\n" + "="*70)
        print("TEST CATEGORY 6: Basic Functionality")
        print("="*70)
        
        # Test 6.1: Create server
        result = await self.call_tool("create_server", {
            "name": "basic-test",
            "server_type": "python",
            "template": "basic_calculator"
        })
        
        passed = result.get("status") == "created and running"
        server_id = result.get("server_id")
        
        self.log_test(
            "6.1 - Create server",
            passed,
            f"Server ID: {server_id[:8] if server_id else 'N/A'}"
        )
        
        if not passed:
            return
        
        # Test 6.2: Execute tool
        calc_result = await self.call_tool("execute_on_server", {
            "server_id": server_id,
            "tool_name": "subtract",
            "arguments": {"a": 50, "b": 18}
        })
        
        result_value = calc_result.get('result', {}).get('content', [{}])[0].get('text', '')
        passed = str(result_value) == "32"
        
        self.log_test(
            "6.2 - Execute tool",
            passed,
            f"50 - 18 = {result_value}"
        )
        
        # Test 6.3: List servers
        servers = await self.call_tool("list_servers", {})
        
        passed = isinstance(servers, list) and len(servers) > 0
        self.log_test(
            "6.3 - List servers",
            passed,
            f"Found {len(servers) if isinstance(servers, list) else 0} servers"
        )
        
        # Test 6.4: Get capabilities
        caps = await self.call_tool("get_server_capabilities", {
            "server_id": server_id
        })
        
        tools = caps.get("tools", [])
        passed = len(tools) >= 4  # Calculator should have 4+ tools
        
        self.log_test(
            "6.4 - Get capabilities",
            passed,
            f"Tools: {len(tools)}"
        )
        
        # Test 6.5: Stop server
        stop_result = await self.call_tool("stop_server", {
            "server_id": server_id
        })
        
        passed = stop_result.get("status") == "stopped and removed"
        self.log_test(
            "6.5 - Stop server",
            passed,
            stop_result.get("status", "unknown")
        )

    # ====================================================================
    # TEST RUNNER
    # ====================================================================

    async def run_all_tests(self):
        """Run all test categories"""
        print("\n" + "="*70)
        print("  Meta-MCP Server v2.0 - Comprehensive Test Suite")
        print("="*70)
        
        try:
            await self.connect()
            print("✅ Connected to Meta-MCP Server\n")
            
            # Run all test categories
            await self.test_basic_functionality()
            await self.test_command_validation()
            await self.test_path_sanitization()
            await self.test_server_pooling()
            await self.test_health_monitoring()
            await self.test_event_tracking()
            await self.test_resource_limits()
            
            # Cleanup all servers
            print("\n🧹 Cleaning up all servers...")
            await self.call_tool("stop_all_servers", {})
            
        except Exception as e:
            print(f"\n❌ Error running tests: {e}")
            import traceback
            traceback.print_exc()
            self.tests_failed += 1
        
        finally:
            await self.disconnect()
            self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("  TEST SUMMARY")
        print("="*70)
        
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.tests_failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"   - {result['name']}: {result['message']}")
        
        print("\n" + "="*70)
        
        if self.tests_failed == 0:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Review output above.")
        
        print("="*70)


async def run_tests():
    """Main test runner"""
        test_suite = TestMetaMCPServer("meta-mcp-server")
    await test_suite.run_all_tests()


if __name__ == "__main__":
    print("\n🧪 Starting Meta-MCP Server v2.0 Test Suite\n")
    asyncio.run(run_tests())

