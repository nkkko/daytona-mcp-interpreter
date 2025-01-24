
"""
MCP server for interpreting Python code in Daytona workspaces.
Handles workspace lifecycle and code execution.
"""

import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import List, Optional, Any
from pathlib import Path
import sys

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Configure logging
LOG_FILE = '/tmp/daytona-interpreter.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class Config:
    """Server configuration"""
    def __init__(self):
        load_dotenv()
        
        self.api_key = os.getenv('MCP_DAYTONA_API_KEY')
        if not self.api_key:
            raise ValueError("MCP_DAYTONA_API_KEY environment variable is required")
            
        self.api_url = os.getenv('MCP_DAYTONA_API_URL', 'http://localhost:3986')
        self.timeout = float(os.getenv('MCP_DAYTONA_TIMEOUT', '30.0'))
        self.verify_ssl = os.getenv('MCP_VERIFY_SSL', 'false').lower() == 'true'

def setup_logging() -> logging.Logger:
    """Configure logging with file and console output"""
    logger = logging.getLogger("daytona-interpreter")
    logger.setLevel(logging.DEBUG)
    
    if not logger.hasHandlers():
        # File handler
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

class DaytonaInterpreter:
    """MCP Server for interpreting Python code in Daytona workspaces"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.config = Config()
        self.server = Server("daytona-interpreter")
        self.workspace_id: Optional[str] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        
        self.setup_handlers()
        self.logger.info("Initialized DaytonaInterpreter")

    def setup_notification_handlers(self):
        """Set up handlers for various notifications"""

        async def handle_cancel_request(params: dict[str, Any]) -> None:
            self.logger.info("Received cancellation request")
            await self.cleanup_workspace()

        async def handle_progress(params: dict[str, Any]) -> None:
            if 'progressToken' in params and 'progress' in params:
                self.logger.debug(f"Progress update: {params}")

        async def handle_initialized(params: dict[str, Any]) -> None:
            self.logger.debug("Received initialized notification")

        async def handle_roots_list_changed(params: dict[str, Any]) -> None:
            self.logger.debug("Received roots list changed notification")

        async def handle_cancelled(params: dict[str, Any]) -> None:
            self.logger.info(f"Received cancelled notification: {params}")
            await self.cleanup_workspace()

        async def handle_unknown_notification(method: str, params: dict[str, Any]) -> None:
            """Handle any unknown notifications gracefully."""
            self.logger.warning(f"Received unknown notification method: {method} with params: {params}")

        # Register notification handlers
        self.server.notification_handlers.update({
            "$/cancelRequest": handle_cancel_request,
            "notifications/progress": handle_progress,
            "notifications/initialized": handle_initialized,
            "notifications/roots/list_changed": handle_roots_list_changed,
            "cancelled": handle_cancelled  # Added handler for 'cancelled' method
        })

        # Note: If the MCP framework supports wildcards or a catch-all handler, implement it here
        # Otherwise, ensure all expected notification methods are handled above

    def setup_handlers(self):
        """Set up server request handlers"""
        self.setup_notification_handlers() 

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [Tool(
                name="python_interpreter",
                description="Execute Python code in a Daytona workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"}
                    },
                    "required": ["code"]
                }
            )]

        @self.server.call_tool() 
        async def call_tool(name: str, arguments: dict) -> List[TextContent | ImageContent | EmbeddedResource]:
            if name != "python_interpreter":
                raise ValueError(f"Unknown tool: {name}")

            code = arguments.get("code")
            if not code:
                raise ValueError("Code argument is required")

            try:
                result = await self.execute_python_code(code)
                return [TextContent(type="text", text=result)]
            except Exception as e:
                self.logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error executing tool: {e}")]
            # Removed cleanup_workspace from here

    async def initialize_client(self) -> None:
        """Initialize HTTP client"""
        if self.http_client:
            await self.http_client.aclose()
            
        base_url = self.config.api_url.rstrip('/')
        
        self.http_client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            follow_redirects=True  # Enable redirect following
        )
        
        # Test connection
        try:
            response = await self.http_client.get("/health")
            response.raise_for_status()
            self.logger.info("Successfully connected to MCP API")
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP API: {e}", exc_info=True)
            raise

    async def create_workspace(self) -> str:
        """Create a new Daytona workspace and return its ID"""
        workspace_name = f"python-{os.urandom(4).hex()}"
        create_data = {
            "name": workspace_name,
            "id": workspace_name,
            "projects": [{
                "name": "python",
                "envVars": {"PYTHONUNBUFFERED": "1"},
                "image": "python:3.10-slim",
                "user": "root",
                "source": {
                    "repository": {
                        "url": "https://github.com/dbarnett/python-helloworld.git",
                        "branch": "main",
                        "id": "placeholder",
                        "name": "placeholder", 
                        "owner": "placeholder",
                        "sha": "0" * 40,
                        "source": "local"
                    }
                }
            }],
            "target": "local"  # Ensure target is specified
        }

        try:
            response = await self.http_client.post("/workspace", json=create_data)
            response.raise_for_status()
            workspace_id = response.json()["id"]

            await asyncio.sleep(2)  # Keep the original delay

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
        """Execute code in workspace"""
        try:
            response = await self.http_client.post(
                f"/workspace/{self.workspace_id}/python/toolbox/process/execute",
                json={
                    "command": f"python3 -c '{code}'",
                    "timeout": int(self.config.timeout)
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return json.dumps({
                "stdout": result.get("result", "").strip(),
                "stderr": result.get("error", "").strip(),
                "exit_code": result.get("code", 0)
            }, indent=2)
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error during code execution: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error during code execution: {e}")
            raise

    async def cleanup_workspace(self) -> None:
        """Clean up workspace"""
        if self.workspace_id:
            try:
                await self.http_client.delete(
                    f"/workspace/{self.workspace_id}",
                    params={"force": True}
                )
                self.logger.info(f"Cleaned up workspace: {self.workspace_id}")
            except Exception as e:
                self.logger.error(f"Failed to clean up workspace: {str(e)}")
            finally:
                self.workspace_id = None

    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.workspace_id:
            await self.cleanup_workspace()
        if self.http_client:
            await self.http_client.aclose()

    async def run(self) -> None:
        """Run the server"""
        try:
            await self.initialize_client()
            self.workspace_id = await self.create_workspace()
            
            async with stdio_server() as streams:
                try:
                    await self.server.run(
                        streams[0],
                        streams[1],
                        self.server.create_initialization_options()
                    )
                except BaseExceptionGroup as e:
                    if any(isinstance(exc, asyncio.CancelledError) for exc in e.exceptions):
                        self.logger.info("Server cancelled")
                    else:
                        self.logger.error(f"Unhandled exception in TaskGroup: {e}", exc_info=True)
                except Exception as e:
                    self.logger.error(f"Unexpected exception: {e}", exc_info=True)
                finally:
                    await self.cleanup()
        except Exception as e:
            self.logger.error(f"Server error: {e}", exc_info=True)
            raise

async def main():
    """Main entry point"""
    logger = setup_logging()
    logger.info("Starting Daytona MCP interpreter")
    
    interpreter = DaytonaInterpreter(logger)
    
    try:
        await interpreter.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt")
    except BaseException as e:  # Changed exception type to catch all, including BaseExceptionGroup
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await interpreter.cleanup()

if __name__ == "__main__":
    asyncio.run(main())