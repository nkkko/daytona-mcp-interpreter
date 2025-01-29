import shlex
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import uuid
from typing import List, Optional, Any, Union

from dotenv import load_dotenv
from daytona_sdk import Daytona, DaytonaConfig, CreateWorkspaceParams
from daytona_sdk.workspace import Workspace
from daytona_sdk.process import ExecuteResponse
from daytona_sdk.filesystem import FileSystem

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Uncomment the following line only if api_client is necessary and correctly imported
# from daytona_sdk import api_client

# Configure logging
LOG_FILE = '/tmp/daytona-interpreter.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


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


class Config:
    """Server configuration class that loads environment variables for MCP Daytona setup"""
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Required API key for authentication
        self.api_key = os.getenv('MCP_DAYTONA_API_KEY')
        if not self.api_key:
            raise ValueError("MCP_DAYTONA_API_KEY environment variable is required")
        else:
            logging.getLogger("daytona-interpreter").info("MCP_DAYTONA_API_KEY loaded successfully.")
        
        # Optional configuration with defaults
        self.server_url = os.getenv('MCP_DAYTONA_SERVER_URL', 'https://daytona.work/api')  # Renamed
        self.target = os.getenv('MCP_DAYTONA_TARGET', 'local')
        self.timeout = float(os.getenv('MCP_DAYTONA_TIMEOUT', '180.0'))
        self.verify_ssl = os.getenv('MCP_VERIFY_SSL', 'false').lower() == 'true'

        # Optional debug logging
        self._log_config()

    def _log_config(self) -> None:
        """Logs the current configuration settings excluding sensitive information."""
        logger = logging.getLogger("daytona-interpreter")
        logger.debug("Configuration Loaded:")
        logger.debug(f"  Server URL: {self.server_url}")
        logger.debug(f"  Target: {self.target}")
        logger.debug(f"  Timeout: {self.timeout}")
        logger.debug(f"  Verify SSL: {self.verify_ssl}")


class DaytonaInterpreter:
    """
    MCP Server implementation for executing Python code and shell commands in Daytona workspaces 
    using the Daytona SDK. Handles workspace creation, file operations, and command execution.
    """

    def __init__(self, logger: logging.Logger, config: Config):
        # Initialize core components
        self.logger = logger
        self.config = config
        
        # Initialize Daytona SDK client
        self.daytona = Daytona(
            config=DaytonaConfig(
                api_key=self.config.api_key,
                server_url=self.config.server_url,
                target=self.config.target
            )
        )
        
        self.workspace: Optional[Workspace] = None  # Current workspace instance

        # Initialize MCP server
        self.server = Server("daytona-interpreter")
        
        # Setup MCP handlers
        self.setup_handlers()
        self.logger.info("Initialized DaytonaInterpreter with Daytona SDK and MCP Server")

    def setup_notification_handlers(self):
        """
        Configure handlers for various MCP protocol notifications.
        Each handler processes specific notification types and performs appropriate actions.
        """

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

    def setup_handlers(self):
        """
        Configure server request handlers for tool listing and execution.
        Defines available tools and their execution logic using the Daytona SDK.
        """
        self.setup_notification_handlers()

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """
            Define available tools:
            1. python_interpreter: Executes Python code in workspace
            2. command_executor: Executes shell commands in workspace
            """
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
                ),
                Tool(
                    name="command_executor",
                    description="Execute a single-line shell command in a Daytona workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to execute"}
                        },
                        "required": ["command"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
            """
            Handle tool execution requests from MCP.
            Uses Daytona SDK to execute Python code or shell commands within the workspace.
            """
            if not self.workspace:
                self.logger.error("Workspace is not initialized.")
                raise RuntimeError("Workspace is not initialized.")

            if name == "python_interpreter":
                code = arguments.get("code")
                if not code:
                    raise ValueError("Code argument is required")
                try:
                    result = await self.execute_python_code(code)
                    return [TextContent(type="text", text=result)]
                except Exception as e:
                    self.logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
                    return [TextContent(type="text", text=f"Error executing tool: {e}")]
            
            elif name == "command_executor":
                command = arguments.get("command")
                if not command:
                    raise ValueError("Command argument is required")
                try:
                    result = await self.execute_command(command)
                    return [TextContent(type="text", text=result)]
                except Exception as e:
                    self.logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
                    return [TextContent(type="text", text=f"Error executing tool: {e}")]
            
            else:
                self.logger.error(f"Unknown tool: {name}")
                raise ValueError(f"Unknown tool: {name}")

    async def initialize_workspace(self) -> None:
        """
        Initialize the Daytona workspace using the SDK.
        Creates a new workspace if it doesn't exist.
        """
        if not self.workspace:
            self.logger.info("Creating a new Daytona workspace")
            params = CreateWorkspaceParams(
                language="python"
                # image="jupyter/datascience-notebook"
                # Additional parameters can be defined here
            )
            try:
                self.workspace = self.daytona.create(params)
                self.logger.info(f"Created Workspace ID: {self.workspace.id}")
            except Exception as e:
                self.logger.error(f"Failed to create workspace: {e}", exc_info=True)
                raise
        else:
            self.logger.info("Workspace already exists")

    async def execute_python_code(self, code: str) -> str:
        """
        Execute Python code in the Daytona workspace using the SDK.
        Returns the execution result as a JSON string.
        """
        if not self.workspace:
            self.logger.error("Workspace is not initialized.")
            raise RuntimeError("Workspace is not initialized.")

        try:
            # Execute Python code using the SDK
            response: ExecuteResponse = self.workspace.process.code_run(code)
            self.logger.debug(f"ExecuteResponse: {response}")

            # Handle the response result
            result = str(response.result).strip() if response.result else ""
            self.logger.info(f"Execution Output:\n{result}")

            # Return the execution output as JSON
            return json.dumps({
                "stdout": result,
                "stderr": "",
                "exit_code": response.code
            }, indent=2)
        except Exception as e:
            self.logger.error(f"Error executing Python code: {e}", exc_info=True)
            return json.dumps({
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }, indent=2)

    async def execute_command(self, command: str) -> str:
        """
        Execute a shell command in the Daytona workspace using the SDK.
        Returns the execution result as a JSON string.
        """
        if not self.workspace:
            self.logger.error("Workspace is not initialized.")
            raise RuntimeError("Workspace is not initialized.")

        try:
            # For commands containing &&, execute them as a single shell command
            if '&&' in command:
                # Wrap the entire command in /bin/sh -c
                command = f'/bin/sh -c {shlex.quote(command)}'
            else:
                # For simple commands, just use shlex.quote on arguments if needed
                command = command.strip()

            self.logger.debug(f"Executing command: {command}")
            
            # Execute shell command using the SDK
            response: ExecuteResponse = self.workspace.process.exec(command)
            self.logger.debug(f"ExecuteResponse: {response}")

            # Handle the response result
            result = str(response.result).strip() if response.result else ""
            self.logger.info(f"Command Output:\n{result}")

            # Return the execution output as JSON
            return json.dumps({
                "stdout": result,
                "stderr": "",
                "exit_code": 0 if response.code is None else response.code
            }, indent=2)
        except Exception as e:
            self.logger.error(f"Error executing command: {e}", exc_info=True)
            return json.dumps({
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }, indent=2)

    async def cleanup_workspace(self) -> None:
        """
        Clean up the Daytona workspace by removing it using the SDK.
        """
        if self.workspace:
            try:
                self.daytona.remove(self.workspace)
                self.logger.info(f"Removed Workspace ID: {self.workspace.id}")
                self.workspace = None
            except Exception as e:
                self.logger.error(f"Failed to remove workspace: {e}", exc_info=True)

    async def cleanup(self) -> None:
        """
        Perform full cleanup of resources:
        1. Clean up workspace if it exists
        2. Close Daytona SDK client connection if necessary
        """
        await self.cleanup_workspace()
        # Additional cleanup steps can be added here if the SDK requires

    async def run(self) -> None:
        """
        Main server execution loop:
        1. Initialize workspace
        2. Run MCP server with stdio communication
        3. Handle cleanup on shutdown
        """
        try:
            await self.initialize_workspace()
            async with stdio_server() as streams:
                try:
                    await self.server.run(
                        streams[0],
                        streams[1],
                        self.server.create_initialization_options()
                    )
                except BaseExceptionGroup as e:
                    # Handle ExceptionGroup (introduced in Python 3.11)
                    if any(isinstance(exc, asyncio.CancelledError) for exc in e.exceptions):
                        self.logger.info("Server was cancelled")
                    else:
                        self.logger.error(f"Unhandled exception in TaskGroup: {e}", exc_info=True)
                except asyncio.CancelledError:
                    self.logger.info("Server task was cancelled")
                except Exception as e:
                    self.logger.error(f"Unhandled exception in MCP server: {e}", exc_info=True)
                finally:
                    await self.cleanup()
        except Exception as e:
            self.logger.error(f"Server error during run: {e}", exc_info=True)
            await self.cleanup()
            raise

async def main():
    """
    Application entry point:
    1. Set up logging
    2. Load configuration
    3. Create and run interpreter instance
    4. Handle interrupts and cleanup
    """
    logger = setup_logging()
    logger.info("Starting Daytona MCP interpreter")
    
    try:
        config = Config()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    interpreter = DaytonaInterpreter(logger, config)
    
    try:
        await interpreter.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await interpreter.cleanup()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await interpreter.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())