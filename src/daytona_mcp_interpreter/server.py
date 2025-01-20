import asyncio
import json
import logging
import os
from typing import Optional, List
from pathlib import Path
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import BaseModel, Field

# Configuration and Environment
class Config:
    """Server configuration and environment variables"""
    def __init__(self):
        env_path = Path('.env')
        load_dotenv(dotenv_path=env_path)

        # Required configuration
        self.api_key = self._get_env('MCP_DAYTONA_API_KEY', required=True)
        self.api_url = self._get_env('MCP_DAYTONA_API_URL', default='http://localhost:3986')
        self.timeout = float(self._get_env('MCP_DAYTONA_TIMEOUT', default='30.0'))
        self.verify_ssl = self._get_env('MCP_VERIFY_SSL', default='false').lower() == 'true'

        # Validate API URL
        if not self.api_url:
            raise ValueError("MCP_DAYTONA_API_URL is required")

    def _get_env(self, var_name: str, default: Optional[str] = None, required: bool = False) -> str:
        """Helper to get environment variables with validation"""
        value = os.getenv(var_name, default)
        if required and not value:
            raise ValueError(f"Required environment variable {var_name} is not set")
        return value

class DaytonaInterpreter:
    """MCP Server for interpreting Python code in Daytona workspaces"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.config = Config()
        self.server = Server("daytona-interpreter")
        self.workspace_id: Optional[str] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.setup_handlers()

    def _setup_logging(self) -> logging.Logger:
        """Configure and return logger"""
        logger = logging.getLogger("daytona-interpreter")
        logging.basicConfig(
            level=logging.DEBUG,  # Set to DEBUG for more verbose output
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/tmp/daytona-interpreter.log')
            ]
        )
        return logger

    async def initialize_client(self) -> None:
        """Initialize HTTP client with configuration"""
        if self.http_client:
            await self.http_client.aclose()

        # Ensure base URL is properly formatted
        base_url = self.config.api_url.rstrip('/')
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"

        self.http_client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            follow_redirects=True  # Add follow_redirects=True here
        )

        self.logger.debug(f"Initialized HTTP client with base URL: {base_url}")

    def setup_handlers(self) -> None:
        """Set up MCP protocol handlers"""
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="python_interpreter",
                    description="Execute Python code in a Daytona workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"}
                        },
                        "required": ["code"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent | ImageContent | EmbeddedResource]:
            if name != "python_interpreter":
                raise ValueError(f"Unknown tool: {name}")

            try:
                code = arguments.get("code")
                if not code:
                    raise ValueError("Code argument is required")

                await self.check_health()

                if not self.workspace_id:
                    self.workspace_id = await self.create_workspace()

                result = await self.execute_python_code(code)

                return [TextContent(type="text", text=result)]

            except Exception as e:
                self.logger.error(f"Error executing code: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "stdout": "",
                        "stderr": str(e),
                        "exit_code": 1
                    }, indent=2)
                )]
            finally:
                await self.cleanup_workspace()

    async def check_health(self) -> None:
        """Check if Daytona API is healthy"""
        if not self.http_client:
            await self.initialize_client()
        try:
            response = await self.http_client.get("/health/")
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Daytona API health check failed: {str(e)}")

    async def create_workspace(self) -> str:
        """Create a new Daytona workspace and return its ID"""
        workspace_name = f"python-{os.urandom(4).hex()}"

        create_data = {
            "name": workspace_name,
            "id": workspace_name,
            "projects": [{
                "name": "python",
                "envVars": {
                    "PYTHONUNBUFFERED": "1"  # Ensure Python output is not buffered
                },
                "image": "python:3.10-slim",
                "user": "root",
                "source": {
                    "repository": {
                        "url": "https://github.com/dbarnett/python-helloworld.git",  # We don't need a real repository URL
                        "branch": "main",  # This can likely be a placeholder as well
                        "id": "placeholder",  # Placeholder
                        "name": "placeholder",  # Placeholder
                        "owner": "placeholder",  # Placeholder
                        "sha": "0000000000000000000000000000000000000000",  # Placeholder (40 zeros for a dummy SHA)
                        "source": "local"  # Indicate a local, non-Git source
                    }
                }
            }],
            "target": "local"
        }
        try:
            response = await self.http_client.post("/workspace/", json=create_data)
            response.raise_for_status()
            workspace_id = response.json()["id"]

            # Wait for workspace to be ready
            await asyncio.sleep(2)

            # Test Python execution
            test_response = await self.http_client.post(
                f"/workspace/{workspace_id}/python/toolbox/process/execute",
                json={
                    "command": "python3",
                    "args": ["-c", "print('test')"],
                    "timeout": 5
                }
            )
            test_response.raise_for_status()
            self.logger.debug(f"Test execution response: {test_response.json()}")

            return workspace_id
        except Exception as e:
            self.logger.error(f"Failed to create workspace: {str(e)}")
            raise RuntimeError(f"Failed to create workspace: {str(e)}")

    async def execute_python_code(self, code: str) -> str:
        """Execute Python code in workspace and return results"""
        if not self.workspace_id:
            raise RuntimeError("Workspace not initialized")

        try:
            # Execute Python code directly
            execute_response = await self.http_client.post(
                f"/workspace/{self.workspace_id}/python/toolbox/process/execute",
                json={
                    "command": f"python -c '{code}'",  # Pass as a single command string
                    "timeout": int(self.config.timeout)
                }
            )
            execute_response.raise_for_status()

            # Get the raw response for debugging
            response_data = execute_response.json()
            self.logger.debug(f"Execute response: {response_data}")

            stdout = response_data.get("result", "")
            stderr = response_data.get("error", "")
            exit_code = response_data.get("code", 0)

            return json.dumps({
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "exit_code": exit_code
            }, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to execute code: {str(e)}")
            return json.dumps({
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1
            }, indent=2)

    async def cleanup_workspace(self) -> None:
        """Clean up the workspace"""
        if self.workspace_id:
            try:
                await self.http_client.delete(
                    f"/workspace/{self.workspace_id}",
                    params={"force": True}
                )
                self.logger.info(f"Cleaned up workspace: {self.workspace_id}")
            except Exception as e:
                self.logger.error(f"Error cleaning up workspace: {e}")
            finally:
                self.workspace_id = None

    async def cleanup(self) -> None:
        """Clean up all resources"""
        await self.cleanup_workspace()
        if self.http_client:
            await self.http_client.aclose()

    async def start(self) -> None:
        """Start the MCP server"""
        self.logger.info("Starting Daytona MCP interpreter server")
        await self.initialize_client()

        async with stdio_server() as streams:
            try:
                await self.server.run(
                    streams[0],
                    streams[1],
                    self.server.create_initialization_options()
                )
            finally:
                await self.cleanup()

def main() -> None:
    """Main entry point"""
    try:
        interpreter = DaytonaInterpreter()
        asyncio.run(interpreter.start())
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()