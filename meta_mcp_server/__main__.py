"""
Entry point for running Meta MCP Server as a module

Usage:
    python -m meta_mcp_server
    python -m meta_mcp_server --config /path/to/config.json
"""
import argparse
import sys
from . import __version__
from .server import MetaMCPServer


def main():
    """Main entry point for the Meta MCP Server CLI"""
    parser = argparse.ArgumentParser(
        description="Meta MCP Server - Dynamic MCP Server Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  meta-mcp-server
  
  # Run with custom config file
  meta-mcp-server --config ~/.config/meta-mcp/config.json
  
  # Show version
  meta-mcp-server --version
"""
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"Meta MCP Server v{__version__}"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON format)",
        metavar="PATH"
    )
    
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio"],
        help="Transport method (default: stdio)"
    )
    
    args = parser.parse_args()
    
    try:
        # Create and run the server
        server = MetaMCPServer(config_path=args.config)
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\nShutting down Meta MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
