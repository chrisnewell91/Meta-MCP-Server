# Meta-MCP Server: Dynamic MCP Server Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Version 2.0** | [Changelog](CHANGELOG.md) | [Quick Start](QUICK_START_V2.md) | [Examples](examples_v2.py)

A powerful Model Context Protocol (MCP) server that can dynamically create and manage child MCP servers to accomplish complex tasks locally. This meta-server acts as an orchestrator, spawning specialized servers on-demand and coordinating their execution.

## 🆕 What's New in v2.0

- 🔒 **Enhanced Security**: Command whitelisting, path sanitization, resource limits
- ⚡ **Performance Boost**: Server pooling for 100x faster reuse
- 📊 **Health Monitoring**: Real-time server health checks and metrics
- 📜 **Event Tracking**: Complete audit trail of all server operations
- ⚙️ **Configuration Management**: External config files and environment variables
- 🛡️ **Cross-Platform**: Now fully compatible with Windows, macOS, and Linux

**[See full changelog →](CHANGELOG.md)**

## Features

### Core Features
- **Dynamic Server Spawning**: Create child MCP servers on-the-fly from templates or existing scripts
- **Process Isolation**: Each child server runs in its own isolated process
- **Lifecycle Management**: Full control over server creation, execution, and termination
- **Multi-Server Orchestration**: Coordinate complex workflows across multiple specialized servers
- **Template System**: Built-in templates for common server types (5 templates included)
- **Async Architecture**: Built on asyncio for efficient concurrent server management
- **Resource Cleanup**: Automatic cleanup of server processes and resources

### v2.0 Enhancements
- **Server Pooling**: Reuse servers for 100x performance improvement
- **Security Hardening**: Command validation, path sanitization, resource limits
- **Health Monitoring**: Track server uptime, idle time, and resource usage
- **Event System**: Pub/sub event bus with comprehensive audit trail
- **Configuration**: JSON config files and environment variable support
- **Resource Limits**: Timeout protection, max servers, memory limits

## Architecture

```
┌─────────────────────────────────────┐
│      AI Client (Claude/ChatGPT)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       Meta-MCP Server               │
│    (Orchestrator & Manager)         │
│                                     │
│  Tools (11 total):                  │
│  • create_server()                  │
│  • execute_on_server()              │
│  • orchestrate_task()               │
│  • list_servers()                   │
│  • stop_server()                    │
│  • health_check() [NEW]             │
│  • get_or_create_pooled_server()    │
│  • get_event_history() [NEW]        │
└────┬──────────┬──────────┬──────────┘
     │          │          │
     ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│Calculator│ │  Web    │ │  Data   │
│ Server   │ │ Scraper │ │Processor│
└─────────┘ └─────────┘ └─────────┘
   Child       Child       Child
   Servers     Servers     Servers
```

## Installation

### Prerequisites

- Python 3.9 or higher
- MCP Python SDK

### Setup

1. Install the MCP SDK:
```bash
pip install mcp
```

2. Clone or download the Meta-MCP server:
```bash
# Download the meta_mcp_server.py file
```

3. Configure your AI client (Claude Desktop, etc.):

Add to your MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "meta-mcp-orchestrator": {
      "command": "python",
      "args": ["/path/to/meta_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

4. Restart your AI client

## Usage

### Available Tools

#### 1. create_server
Create and spawn a new child MCP server.

```python
{
  "name": "my-calculator",
  "server_type": "python",
  "template": "basic_calculator"
}
```

**Templates Available:**
- `basic_calculator` - Mathematical operations
- `web_scraper_template` - Web scraping tools
- `file_handler_template` - File system operations
- `data_processor` - Data manipulation and analysis
- `api_integration` - HTTP API client tools

#### 2. execute_on_server
Execute a tool on a specific child server.

```python
{
  "server_id": "<server-id-from-create>",
  "tool_name": "add",
  "arguments": {"a": 5, "b": 3}
}
```

#### 3. orchestrate_task
Automatically spawn multiple servers for complex workflows.

```python
{
  "task_description": "Scrape data and perform analysis",
  "required_capabilities": ["web_scraping", "data_analysis"]
}
```

#### 4. list_servers
Get information about all active child servers.

```python
{}  # No arguments required
```

#### 5. get_server_capabilities
Query available tools and resources on a server.

```python
{
  "server_id": "<server-id>"
}
```

#### 6. stop_server
Stop and remove a child server.

```python
{
  "server_id": "<server-id>"
}
```

#### 7. stop_all_servers
Stop all running child servers (cleanup).

```python
{}  # No arguments required
```

### 🆕 New Tools in v2.0

#### 8. get_or_create_pooled_server
Get an existing server from the pool or create a new one (100x faster for reuse).

```python
{
  "template": "basic_calculator",
  "use_pooling": true  # optional, defaults to true
}
```

#### 9. health_check
Check health status of a specific child server.

```python
{
  "server_id": "<server-id>"
}
```

**Returns**: Status, uptime, idle time, resource limits, timestamps

#### 10. health_check_all
Check health status of all child servers.

```python
{}  # No arguments required
```

**Returns**: Overall health summary with healthy/unhealthy counts

#### 11. get_event_history
Retrieve recent server lifecycle events.

```python
{
  "limit": 20  # optional, defaults to 20, max 100
}
```

**Returns**: Event history with timestamps, event types, and data

## Example Workflows

### Example 1: Simple Calculator Task

```
User: "I need to calculate 15 + 27"

AI Client → Meta-MCP:
  create_server(name="calc", template="basic_calculator")

Meta-MCP Response:
  {server_id: "abc-123", status: "running"}

AI Client → Meta-MCP:
  execute_on_server(server_id="abc-123", tool_name="add", 
                   arguments={a: 15, b: 27})

Meta-MCP Response:
  {result: 42, status: "success"}

AI Client → Meta-MCP:
  stop_server(server_id="abc-123")
```

### Example 2: Complex Multi-Server Workflow

```
User: "Fetch data from API and analyze it"

AI Client → Meta-MCP:
  orchestrate_task(
    task_description="Fetch and analyze API data",
    required_capabilities=["api_client", "data_analysis"]
  )

Meta-MCP:
  - Spawns API Integration Server
  - Spawns Data Processor Server
  - Returns server IDs

AI Client:
  1. execute_on_server(api_server, "make_request", {...})
  2. execute_on_server(data_server, "parse_json", {...})
  3. execute_on_server(data_server, "summarize_data", {...})
  4. stop_server(api_server)
  5. stop_server(data_server)
```

## Custom Server Templates

You can add your own templates by modifying the `_generate_from_template()` function:

```python
templates = {
    "my_custom_server": """
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Custom Server")

@mcp.tool()
def my_tool(param: str) -> str:
    return f"Processing {param}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
"""
}
```

## Advanced Configuration

### 🆕 Configuration File (v2.0)

Create `meta_mcp_config.json` for persistent configuration:

```json
{
  "default_timeout_seconds": 60,
  "default_max_memory_mb": 1024,
  "max_concurrent_servers": 20,
  "log_level": "INFO",
  "allowed_commands": ["python", "python3", "node"],
  "temp_directory": null
}
```

### Environment Variables

v2.0 adds comprehensive environment variable support:

- `MCP_CONFIG_FILE`: Path to config JSON file (default: `meta_mcp_config.json`)
- `MCP_TIMEOUT_SECONDS`: Default tool execution timeout (default: 30)
- `MCP_MAX_SERVERS`: Maximum concurrent child servers (default: 10)
- `MCP_MAX_MEMORY_MB`: Max memory per server in MB (default: 512)
- `MCP_LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `MCP_TEMP_DIR`: Directory for temporary server scripts

**Priority**: Config file > Environment variables > Defaults

### Using External Scripts

Instead of templates, you can spawn servers from existing scripts:

```python
{
  "name": "my-custom-server",
  "server_type": "python",
  "script_path": "/path/to/my_server.py",
  "config": {
    "timeout": 120,  # Custom timeout for this server
    "max_memory_mb": 1024
  }
}
```

## 🔒 Security Considerations (Enhanced in v2.0)

### Built-in Security Features

1. **Command Whitelisting**: Only approved commands can be executed
   - Default whitelist: `python`, `python3`, `node`, `npm`, `npx`
   - Configurable via `allowed_commands` in config file
   - Prevents arbitrary command execution

2. **Path Sanitization**: Prevents directory traversal attacks
   - All file operations validate paths
   - Restricts access to base directory
   - Blocks `../` path escape attempts

3. **Resource Limits**: Prevents resource exhaustion
   - Execution timeouts (default: 30s)
   - Maximum concurrent servers (default: 10)
   - Memory limits per server (configurable)

4. **Process Isolation**: Each child server runs in a separate process
   - Independent memory space
   - Isolated execution environment

5. **Input Validation**: All inputs validated before execution
   - Type checking on tool arguments
   - Command validation before subprocess creation

6. **Cross-Platform Temp Files**: Secure temporary file handling
   - Uses system-appropriate temp directories
   - Automatic cleanup of generated servers

### Security Best Practices

- **Restrict Commands**: Minimize the `allowed_commands` list
- **Set Resource Limits**: Configure appropriate timeouts and server limits
- **Monitor Events**: Use `get_event_history()` for audit trails
- **Health Checks**: Regular monitoring with `health_check_all()`

## Troubleshooting

### Server won't start
- Check that Python is in your PATH
- Verify the MCP SDK is installed: `pip install mcp`
- Check log output for specific errors
- Verify config file syntax if using `meta_mcp_config.json`

### Tool execution fails
- Verify the server is running with `list_servers` or `health_check_all`
- Check tool availability with `get_server_capabilities`
- Review event history: `get_event_history(limit=50)`
- Check for timeout issues in server health status

### 🆕 Command not allowed error (v2.0)
- Add the command to `allowed_commands` in `meta_mcp_config.json`
- Or set via environment: `MCP_ALLOWED_COMMANDS="python,python3,node"`

### 🆕 Path access denied (v2.0)
- Verify file is within allowed base directory
- Use `base_dir` parameter in file operations
- Check event history for security violations

### 🆕 Maximum servers reached (v2.0)
- Stop unused servers: `stop_all_servers()`
- Check server health: `health_check_all()`
- Increase limit in config: `"max_concurrent_servers": 20`
- Use server pooling to reuse servers

### Memory or performance issues
- Use server pooling: `get_or_create_pooled_server()`
- Monitor server health regularly
- Stop idle servers (check `idle_seconds` in health check)
- Review event history for timeout patterns

## Project Files

### Core Files
- `meta_mcp_server.py` - Main server implementation (1100+ lines)
- `requirements.txt` - Python dependencies
- `README.md` - This file

### Configuration
- `meta_mcp_config.json` - Configuration file (optional)
- `Config_Tools.json` - Claude Desktop configuration example

### Documentation (v2.0)
- `CHANGELOG.md` - Detailed v2.0 improvements and changes
- `QUICK_START_V2.md` - Quick start guide for v2.0 features
- `Program_Summary.txt` - Original project summary

### Examples & Tests (v2.0)
- `examples_v2.py` - Comprehensive examples of v2.0 features
- `test_meta_mcp_v2.py` - Test suite for v2.0 functionality
- `example_client.py` - Original example client

## Architecture Details

### Component Overview

**Core Components:**
1. **Meta-MCP Server**: Main orchestrator that manages child servers
2. **ChildServerProcess**: Class managing individual child server lifecycle
3. **Server Registry**: In-memory registry tracking all active servers
4. **Template System**: Pre-built server templates for common tasks

**🆕 v2.0 Components:**
5. **EventBus**: Pub/sub event system for lifecycle tracking
6. **MetaServerConfig**: Configuration management with file/env support
7. **Server Pools**: Server pooling system for performance
8. **Security Layer**: Command validation and path sanitization

### Communication Flow

1. AI client sends request to Meta-MCP
2. Meta-MCP validates command and checks resource limits
3. Meta-MCP spawns required child servers (or reuses from pool)
4. Child servers initialize and register capabilities
5. Meta-MCP routes tool execution to appropriate child (with timeout)
6. Child executes tool and returns result
7. Events are logged to event history
8. Meta-MCP aggregates results and responds to client
9. Servers can be pooled for reuse or terminated after completion

## Contributing

Contributions are welcome! v2.0 has addressed many areas, but there's still room for improvement:

### Implemented in v2.0 ✅
- ~~Enhanced error handling~~
- ~~Resource usage monitoring~~
- ~~Advanced orchestration patterns~~
- ~~Security improvements~~

### Future Enhancements
- Memory monitoring with psutil
- CPU usage tracking  
- Persistent event storage
- Additional server templates
- Server persistence options
- Web UI for monitoring
- Metrics export (Prometheus format)

See [CHANGELOG.md](CHANGELOG.md) for known limitations and future plans.

## Quick Links

📚 **Documentation**
- [Full Changelog](CHANGELOG.md) - What's new in v2.0
- [Quick Start Guide](QUICK_START_V2.md) - Get started with v2.0
- [Examples](examples_v2.py) - Run examples: `python examples_v2.py`
- [Tests](test_meta_mcp_v2.py) - Run tests: `python test_meta_mcp_v2.py`

⚙️ **Configuration**
- [Config Template](meta_mcp_config.json) - Configuration options
- [Claude Config](Config_Tools.json) - Claude Desktop setup

## Performance

- Server creation: ~100-300ms
- Server reuse (pooled): ~1-5ms (**100x faster**)
- Tool execution: Depends on tool
- Health check: ~1ms per server
- Event tracking: <1ms overhead

## Version History

- **v2.0** (November 2025): Security, performance, monitoring, events
- **v1.0** (Initial): Basic server orchestration and management

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built using the Model Context Protocol (MCP) by Anthropic and the broader MCP community.

**v2.0 Improvements**: Enhanced security, server pooling, health monitoring, event tracking, configuration management, and cross-platform compatibility.
