"""
Meta MCP Server - A Dynamic MCP Server Orchestrator

A powerful meta-server that can dynamically create and manage child MCP servers
to accomplish complex tasks through process isolation and orchestration.
"""

__version__ = "2.0.0"
__author__ = "Chris Newell"
__license__ = "MIT"

from .server import MetaMCPServer

__all__ = ["MetaMCPServer", "__version__"]
