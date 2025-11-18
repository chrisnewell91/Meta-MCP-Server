"""
Server templates for Meta MCP Server
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# Server template definitions
TEMPLATES: Dict[str, str] = {
    "basic_calculator": """from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers\"\"\"
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a\"\"\"
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers\"\"\"
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    \"\"\"Divide a by b\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

    "web_scraper_template": """from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("Web Scraper Server")

@mcp.tool()
def fetch_url(url: str) -> str:
    \"\"\"Fetch content from a URL (simulated)\"\"\"
    # In production, use requests library
    return f"Simulated content from {url}"

@mcp.tool()
def extract_data(html: str, selector: str) -> dict:
    \"\"\"Extract data from HTML using selector (simulated)\"\"\"
    return {
        "selector": selector,
        "data": ["item1", "item2", "item3"],
        "count": 3
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

    "file_handler_template": """from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("File Handler Server")

@mcp.tool()
def read_file(path: str) -> str:
    \"\"\"Read file contents\"\"\"
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    \"\"\"Write content to file\"\"\"
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully written to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def list_files(directory: str = ".") -> list:
    \"\"\"List files in directory\"\"\"
    try:
        return os.listdir(directory)
    except Exception as e:
        return [f"Error: {str(e)}"]

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

    "data_processor": """from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("Data Processor Server")

@mcp.tool()
def parse_json(json_string: str) -> dict:
    \"\"\"Parse JSON string into dictionary\"\"\"
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        return {"error": str(e)}

@mcp.tool()
def filter_data(data: list, key: str, value: str) -> list:
    \"\"\"Filter list of dictionaries by key-value pair\"\"\"
    if not isinstance(data, list):
        return []
    return [
        item for item in data
        if isinstance(item, dict) and item.get(key) == value
    ]

@mcp.tool()
def summarize_data(data: list) -> dict:
    \"\"\"Generate summary statistics for data\"\"\"
    return {
        "count": len(data),
        "type": str(type(data).__name__),
        "sample": data[:3] if len(data) > 0 else []
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",

    "api_integration": """from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("API Integration Server")

@mcp.tool()
def make_request(url: str, method: str = "GET") -> dict:
    \"\"\"Make HTTP request (simulated)\"\"\"
    return {
        "url": url,
        "method": method,
        "status_code": 200,
        "message": "Simulated API response"
    }

@mcp.tool()
def parse_response(response_json: str) -> dict:
    \"\"\"Parse API response JSON\"\"\"
    try:
        data = json.loads(response_json)
        return {"valid": True, "data": data}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
"""
}


# Capability to template mapping
CAPABILITY_TEMPLATES = {
    "web_scraping": "web_scraper_template",
    "data_analysis": "data_processor",
    "file_operations": "file_handler_template",
    "api_client": "api_integration",
    "calculator": "basic_calculator"
}


def generate_from_template(template: str, output_path: str) -> None:
    """Generate a server script from a template"""
    template_code = TEMPLATES.get(template, TEMPLATES["basic_calculator"])
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(template_code)
    
    logger.info(
        f"Generated server from template '{template}' at {output_path}"
    )


def get_template_for_capability(capability: str) -> str:
    """Get the template name for a given capability"""
    return CAPABILITY_TEMPLATES.get(capability, "basic_calculator")
