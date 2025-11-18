"""
Configuration management for Meta MCP Server
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "default_timeout_seconds": 30,
    "default_max_memory_mb": 512,
    "max_concurrent_servers": 10,
    "default_python_command": "python3",
    "allowed_commands": [
        "python",
        "python3",
        "python3.9",
        "python3.10", 
        "python3.11",
        "python3.12",
        "python3.13",
        "python3.14",
        "node",
        "npm",
        "npx"
    ],
    "temp_directory": None,
    "log_level": "INFO"
}


class Config:
    """Configuration management for Meta MCP Server"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._apply_environment_overrides()
        self._setup_logging()
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file"""
        config = DEFAULT_CONFIG.copy()
        
        # If no path specified, check default locations
        if not config_path:
            possible_paths = [
                Path("meta_mcp_config.json"),
                Path.home() / ".config" / "meta-mcp" / "config.json",
                Path("/etc/meta-mcp/config.json"),
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        # Load from file if found
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return config
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides"""
        env_mappings = {
            "MCP_TIMEOUT_SECONDS": ("default_timeout_seconds", int),
            "MCP_MAX_SERVERS": ("max_concurrent_servers", int),
            "MCP_MAX_MEMORY_MB": ("default_max_memory_mb", int),
            "MCP_LOG_LEVEL": ("log_level", str),
            "MCP_TEMP_DIR": ("temp_directory", str),
        }
        
        for env_var, (config_key, type_func) in env_mappings.items():
            if env_var in os.environ:
                try:
                    self.config[config_key] = type_func(os.environ[env_var])
                    logger.info(f"Applied environment override: {env_var}")
                except ValueError as e:
                    logger.warning(f"Invalid value for {env_var}: {e}")
    
    def _setup_logging(self):
        """Configure logging based on config"""
        log_level = getattr(logging, self.config.get("log_level", "INFO").upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @property
    def timeout_seconds(self) -> int:
        return self.config["default_timeout_seconds"]
    
    @property
    def max_memory_mb(self) -> int:
        return self.config["default_max_memory_mb"]
    
    @property
    def max_concurrent_servers(self) -> int:
        return self.config["max_concurrent_servers"]
    
    @property
    def python_command(self) -> str:
        return self.config["default_python_command"]
    
    @property
    def allowed_commands(self) -> List[str]:
        return self.config["allowed_commands"]
    
    @property
    def temp_directory(self) -> Optional[str]:
        return self.config["temp_directory"]


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or create the global config instance"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
