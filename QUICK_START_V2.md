# Quick Start Guide - Meta-MCP Server v2.0

## What's New in v2.0?

🔒 **Security**: Command whitelisting, path sanitization, resource limits
⚡ **Performance**: Server pooling for 100x faster reuse
📊 **Monitoring**: Health checks and event history
⚙️ **Configuration**: External config files and environment variables

## Installation

```bash
# Install dependencies
pip install mcp

# No changes needed to existing installations
```

## Quick Examples

### 1. Basic Usage (Same as Before)

```python
# Create a calculator server
result = await create_server(
    name="calculator",
    server_type="python",
    template="basic_calculator"
)

# Execute a tool
result = await execute_on_server(
    server_id=server_id,
    tool_name="add",
    arguments={"a": 5, "b": 3}
)
```

### 2. Using Server Pooling (NEW - Recommended)

```python
# First call: creates server (~200ms)
result = await get_or_create_pooled_server(
    template="basic_calculator"
)

# Second call: reuses existing (~2ms) ⚡
result = await get_or_create_pooled_server(
    template="basic_calculator"
)

# Execute on pooled server
result = await execute_on_server(
    server_id=result["server_id"],
    tool_name="multiply",
    arguments={"a": 7, "b": 6}
)
```

### 3. Health Monitoring (NEW)

```python
# Check all servers
health = await health_check_all()
print(f"Healthy servers: {health['healthy']}/{health['total_servers']}")

# Check specific server
health = await health_check(server_id="abc-123")
print(f"Uptime: {health['uptime_seconds']}s")
print(f"Idle: {health['idle_seconds']}s")
```

### 4. Event History (NEW)

```python
# Get recent events
events = await get_event_history(limit=10)

for event in events['events']:
    print(f"{event['timestamp']}: {event['event']} - {event['data']}")

# Example output:
# 2025-11-18T10:30:15: server_created - {'server_id': 'abc-123', 'name': 'calc'}
# 2025-11-18T10:30:16: tool_executed - {'server_id': 'abc-123', 'tool_name': 'add'}
# 2025-11-18T10:30:17: pool_added - {'server_id': 'abc-123', 'template': 'basic_calculator'}
```

## Configuration

### Option 1: Configuration File (Recommended)

Create `meta_mcp_config.json`:

```json
{
  "default_timeout_seconds": 60,
  "default_max_memory_mb": 1024,
  "max_concurrent_servers": 20,
  "log_level": "INFO",
  "allowed_commands": [
    "python",
    "python3",
    "node"
  ]
}
```

### Option 2: Environment Variables

```bash
export MCP_TIMEOUT_SECONDS=60
export MCP_MAX_SERVERS=20
export MCP_MAX_MEMORY_MB=1024
export MCP_LOG_LEVEL=DEBUG
export MCP_CONFIG_FILE="/path/to/config.json"
```

## Security Best Practices

1. **Use Configuration File**: Limit allowed commands
   ```json
   {
     "allowed_commands": ["python3"]  // Only Python 3
   }
   ```

2. **Set Resource Limits**: Prevent resource exhaustion
   ```json
   {
     "default_timeout_seconds": 30,
     "max_concurrent_servers": 5
   }
   ```

3. **File Operations**: Use base_dir parameter
   ```python
   # Restrict to specific directory
   result = await execute_on_server(
       server_id=file_server_id,
       tool_name="read_file",
       arguments={
           "path": "data.txt",
           "base_dir": "/path/to/safe/directory"
       }
   )
   ```

## Performance Tips

### 1. Use Server Pooling

```python
# ❌ Slow: Creates new server every time
for i in range(10):
    server = await create_server(name=f"calc{i}", template="basic_calculator")
    # ... use server ...
    await stop_server(server["server_id"])

# ✅ Fast: Reuses same server
pooled = await get_or_create_pooled_server(template="basic_calculator")
for i in range(10):
    # ... use pooled server (100x faster) ...
```

### 2. Monitor Server Health

```python
# Check if servers are idle
health = await health_check_all()
for server in health['servers']:
    if server['idle_seconds'] > 300:  # 5 minutes
        print(f"Server {server['server_id']} is idle, consider stopping")
        await stop_server(server['server_id'])
```

### 3. Use Event History for Debugging

```python
# Find timeouts
events = await get_event_history(limit=100)
timeouts = [e for e in events['events'] if e['event'] == 'tool_timeout']
print(f"Found {len(timeouts)} timeouts")
```

## Troubleshooting

### Problem: "Command not allowed" error

**Solution**: Add command to allowed list in config file

```json
{
  "allowed_commands": ["python", "python3", "node", "npm"]
}
```

### Problem: "Maximum number of servers reached"

**Solution**: Increase limit or stop unused servers

```bash
export MCP_MAX_SERVERS=20
```

Or stop servers:
```python
await stop_all_servers()
```

### Problem: "Tool execution timed out"

**Solution**: Increase timeout

```json
{
  "default_timeout_seconds": 120
}
```

Or pass timeout in config:
```python
await create_server(
    name="slow-server",
    template="my_template",
    config={"timeout": 120}
)
```

### Problem: Path access denied

**Solution**: Check base_dir parameter

```python
# File must be within base_dir
await execute_on_server(
    server_id=server_id,
    tool_name="read_file",
    arguments={
        "path": "file.txt",  # Will be joined with base_dir
        "base_dir": "/safe/directory"
    }
)
```

## Tool Reference

### Core Tools (Unchanged)

1. `create_server(name, server_type, script_path?, template?, config?)`
2. `execute_on_server(server_id, tool_name, arguments)`
3. `list_servers()`
4. `get_server_capabilities(server_id)`
5. `stop_server(server_id)`
6. `stop_all_servers()`
7. `orchestrate_task(task_description, required_capabilities)`

### New Tools in v2.0

8. `health_check(server_id)` - Check server health status
9. `health_check_all()` - Check all servers
10. `get_or_create_pooled_server(template, use_pooling?)` - Pooled server management
11. `get_event_history(limit?)` - Retrieve event logs

## Migration Checklist

- [ ] Update `requirements.txt` (if modified)
- [ ] Create `meta_mcp_config.json` (optional but recommended)
- [ ] Replace `create_server()` with `get_or_create_pooled_server()` for repeated templates
- [ ] Add health monitoring to your workflows
- [ ] Review security settings (allowed commands, resource limits)
- [ ] Test with your existing MCP client

## Next Steps

1. Read the full [CHANGELOG.md](CHANGELOG.md) for detailed improvements
2. Review [README.md](README.md) for complete documentation
3. Check [meta_mcp_config.json](meta_mcp_config.json) for configuration options
4. Run [example_client.py](example_client.py) to see examples

## Support

For issues or questions:
- Check the [README.md](README.md) troubleshooting section
- Review [CHANGELOG.md](CHANGELOG.md) for known limitations
- Check event history for debugging: `get_event_history()`

---

**Happy orchestrating! 🚀**

