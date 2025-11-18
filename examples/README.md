# Meta MCP Server Examples

This directory contains examples demonstrating various features of the Meta MCP Server.

## Examples

### 1. Hello World (`hello_world.py`)

The simplest possible example showing how to:
- Connect to Meta MCP Server
- Create a calculator server
- Execute a calculation
- Clean up resources

Run it:
```bash
python examples/hello_world.py
```

### 2. Claude Desktop Conversation (`claude_conversation_example.md`)

A real conversation example showing how Claude Desktop interacts with the Meta MCP Server to:
- Create multiple specialized servers
- Perform calculations
- Handle web scraping requests
- Clean up resources

### 3. Advanced Examples (`example_client.py`)

More comprehensive examples showing:
- Error handling
- Multiple server orchestration
- Custom server configurations
- Advanced tool usage

### 4. V2 Features Examples (`examples_v2.py`)

Demonstrates v2.0 features:
- Server pooling for performance
- Health monitoring
- Event tracking
- Configuration management

Run it:
```bash
python examples/examples_v2.py
```

## Getting Started

1. Install Meta MCP Server:
   ```bash
   pip install -e .
   ```

2. Run the hello world example:
   ```bash
   python examples/hello_world.py
   ```

3. For Claude Desktop integration, follow the setup in `claude_conversation_example.md`

## Tips

- Start with `hello_world.py` to understand the basics
- Read `claude_conversation_example.md` to see real-world usage
- Explore `examples_v2.py` for advanced features
- Check the test suite for more usage patterns
