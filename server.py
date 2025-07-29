#!/usr/bin/env python3
"""
Intigriti Researcher API MCP Server

A Model Context Protocol server for interacting with the Intigriti Researcher API.
Based on the official OpenAPI specification v1.0.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin

import httpx
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("intigriti-mcp-server")

class IntigritiAPIError(Exception):
    """Custom exception for Intigriti API errors"""
    pass

class IntigritiResearcherAPI:
    """Client for Intigriti Researcher API v1.0"""
    
    def __init__(self, base_url: str = "https://api.intigriti.com/external/researcher", api_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token or os.getenv("INTIGRITI_API_TOKEN")
        
        if not self.api_token:
            raise ValueError("API token is required. Set INTIGRITI_API_TOKEN environment variable or pass api_token parameter.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "IntigritiMCPServer/1.0"
        }
        
        # HTTP client with proper timeouts and retry logic
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the Intigriti API with error handling"""
        url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise IntigritiAPIError(f"Rate limited. Retry after {retry_after} seconds.")
            
            # Handle authentication errors
            if response.status_code == 401:
                raise IntigritiAPIError("Authentication failed. Check your API token.")
            
            # Handle other HTTP errors
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise IntigritiAPIError(f"API request failed: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise IntigritiAPIError(f"Network error: {e}")
    
    # API Methods based on OpenAPI spec
    async def get_programs(self, status_id: Optional[int] = None, type_id: Optional[int] = None, 
                          following: Optional[bool] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get all programs you have access to"""
        params = {"limit": min(limit, 500), "offset": offset}
        if status_id is not None:
            params["statusId"] = status_id
        if type_id is not None:
            params["typeId"] = type_id
        if following is not None:
            params["following"] = following
            
        return await self._make_request("GET", "v1/programs", params=params)
    
    async def get_program_details(self, program_id: str) -> Dict[str, Any]:
        """Get program details"""
        return await self._make_request("GET", f"v1/programs/{program_id}")
    
    async def get_program_activities(self, created_since: Optional[int] = None, following: Optional[bool] = None,
                                   limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get all program activities"""
        params = {"limit": min(limit, 500), "offset": offset}
        if created_since is not None:
            params["createdSince"] = created_since
        if following is not None:
            params["following"] = following
            
        return await self._make_request("GET", "v1/programs/activities", params=params)
    
    async def get_program_domains(self, program_id: str, version_id: str) -> Dict[str, Any]:
        """Get program domains"""
        return await self._make_request("GET", f"v1/programs/{program_id}/domains/{version_id}")
    
    async def get_program_rules_of_engagement(self, program_id: str, version_id: str) -> Dict[str, Any]:
        """Get program rules of engagement"""
        return await self._make_request("GET", f"v1/programs/{program_id}/rules-of-engagements/{version_id}")
    
    # Generic method for future endpoints
    async def call_endpoint(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Generic method to call any API endpoint - useful for beta API evolution"""
        return await self._make_request(method, endpoint, **kwargs)

# Initialize the MCP server
app = Server("intigriti-researcher")

# Global API client
api_client: Optional[IntigritiResearcherAPI] = None

@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools for the Intigriti Researcher API"""
    return [
        types.Tool(
            name="get_programs",
            description="Get all programs you have access to with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "status_id": {
                        "type": "integer", 
                        "description": "Filter by program status ID"
                    },
                    "type_id": {
                        "type": "integer",
                        "description": "Filter by program type ID"
                    },
                    "following": {
                        "type": "boolean",
                        "description": "Filter by programs you're following"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of programs per page (max 500)",
                        "default": 20,
                        "maximum": 500,
                        "minimum": 0
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset for pagination",
                        "default": 0,
                        "minimum": 0
                    }
                }
            }
        ),
        types.Tool(
            name="get_program_details",
            description="Get detailed information about a specific bug bounty program",
            inputSchema={
                "type": "object",
                "properties": {
                    "program_id": {
                        "type": "string",
                        "description": "The unique identifier (GUID) of the program"
                    }
                },
                "required": ["program_id"]
            }
        ),
        types.Tool(
            name="get_program_activities",
            description="Get all program activities with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "created_since": {
                        "type": "integer",
                        "description": "Unix timestamp to filter activities created since this time"
                    },
                    "following": {
                        "type": "boolean",
                        "description": "Filter by programs you're following"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of activities per page (max 500)",
                        "default": 20,
                        "maximum": 500,
                        "minimum": 0
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset for pagination",
                        "default": 0,
                        "minimum": 0
                    }
                }
            }
        ),
        types.Tool(
            name="get_program_domains",
            description="Get program domains/scope for a specific version",
            inputSchema={
                "type": "object",
                "properties": {
                    "program_id": {
                        "type": "string",
                        "description": "The unique identifier (GUID) of the program"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "The unique identifier (GUID) of the domains version"
                    }
                },
                "required": ["program_id", "version_id"]
            }
        ),
        types.Tool(
            name="get_program_rules_of_engagement",
            description="Get program rules of engagement for a specific version",
            inputSchema={
                "type": "object",
                "properties": {
                    "program_id": {
                        "type": "string",
                        "description": "The unique identifier (GUID) of the program"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "The unique identifier (GUID) of the rules version"
                    }
                },
                "required": ["program_id", "version_id"]
            }
        ),
        types.Tool(
            name="call_custom_endpoint",
            description="Call a custom API endpoint (useful for new beta endpoints)",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                    },
                    "endpoint": {
                        "type": "string",
                        "description": "API endpoint path (e.g., 'v1/programs/new-endpoint')"
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters as key-value pairs"
                    },
                    "json_data": {
                        "type": "object",
                        "description": "JSON body data for POST/PUT requests"
                    }
                },
                "required": ["method", "endpoint"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle tool calls"""
    global api_client
    
    if not api_client:
        try:
            api_client = IntigritiResearcherAPI()
        except ValueError as e:
            return [types.TextContent(type="text", text=f"Configuration error: {e}")]
    
    try:
        if name == "get_programs":
            result = await api_client.get_programs(
                status_id=arguments.get("status_id"),
                type_id=arguments.get("type_id"),
                following=arguments.get("following"),
                limit=arguments.get("limit", 20),
                offset=arguments.get("offset", 0)
            )
            
        elif name == "get_program_details":
            result = await api_client.get_program_details(arguments["program_id"])
            
        elif name == "get_program_activities":
            result = await api_client.get_program_activities(
                created_since=arguments.get("created_since"),
                following=arguments.get("following"),
                limit=arguments.get("limit", 20),
                offset=arguments.get("offset", 0)
            )
            
        elif name == "get_program_domains":
            result = await api_client.get_program_domains(
                program_id=arguments["program_id"],
                version_id=arguments["version_id"]
            )
            
        elif name == "get_program_rules_of_engagement":
            result = await api_client.get_program_rules_of_engagement(
                program_id=arguments["program_id"],
                version_id=arguments["version_id"]
            )
            
        elif name == "call_custom_endpoint":
            kwargs = {}
            if "params" in arguments:
                kwargs["params"] = arguments["params"]
            if "json_data" in arguments:
                kwargs["json"] = arguments["json_data"]
                
            result = await api_client.call_endpoint(
                method=arguments["method"],
                endpoint=arguments["endpoint"],
                **kwargs
            )
            
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        # Format the response
        import json
        formatted_result = json.dumps(result, indent=2, ensure_ascii=False)
        return [types.TextContent(type="text", text=formatted_result)]
        
    except IntigritiAPIError as e:
        return [types.TextContent(type="text", text=f"API error: {e}")]
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        return [types.TextContent(type="text", text=f"Error: {e}")]

@app.list_resources()
async def list_resources() -> List[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri=AnyUrl("intigriti://api/status"),
            name="API Status",
            description="Check API connectivity and authentication status",
            mimeType="text/plain"
        ),
        types.Resource(
            uri=AnyUrl("intigriti://api/endpoints"),
            name="Available Endpoints",
            description="List of all available API endpoints based on OpenAPI spec",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read a resource"""
    global api_client
    
    if not api_client:
        api_client = IntigritiResearcherAPI()
    
    if str(uri) == "intigriti://api/status":
        try:
            programs = await api_client.get_programs(limit=1)
            return f"✅ API Connected\nTotal programs accessible: {programs.get('maxCount', 'Unknown')}"
        except Exception as e:
            return f"❌ API Connection Failed\nError: {e}"
    
    elif str(uri) == "intigriti://api/endpoints":
        endpoints = {
            "programs": "GET /v1/programs - Get all programs you have access to",
            "program_details": "GET /v1/programs/{programId} - Get program details",
            "program_activities": "GET /v1/programs/activities - Get all program activities",
            "program_domains": "GET /v1/programs/{programId}/domains/{versionId} - Get program domains",
            "program_rules": "GET /v1/programs/{programId}/rules-of-engagements/{versionId} - Get rules of engagement"
        }
        import json
        return json.dumps(endpoints, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def cleanup():
    """Cleanup function"""
    global api_client
    if api_client:
        await api_client.close()

async def main():
    """Main entry point"""
    # Setup cleanup
    import signal
    
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(cleanup())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        await cleanup()

if __name__ == "__main__":
    asyncio.run(main())