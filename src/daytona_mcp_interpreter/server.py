
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import List, Optional, Any
from pathlib import Path
import sys
import uuid

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Configure logging
LOG_FILE = '/tmp/daytona-interpreter.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class Config:
    """Server configuration class that loads environment variables for MCP Daytona setup"""
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Required API key for authentication
        self.api_key = os.getenv('MCP_DAYTONA_API_KEY')
        if not self.api_key:
            raise ValueError("MCP_DAYTONA_API_KEY environment variable is required")
        
        # Optional configuration with defaults
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
    """
    MCP Server implementation for executing Python code and shell commands in Daytona workspaces.
    Handles workspace creation, file operations, and command execution.
    """

    def __init__(self, logger: logging.Logger):
        # Initialize core components
        self.logger = logger
        self.config = Config()
        self.server = Server("daytona-interpreter")
        
        # State tracking
        self.workspace_id: Optional[str] = None  # Current workspace identifier
        self.project_id: Optional[str] = None    # Current project identifier
        self.http_client: Optional[httpx.AsyncClient] = None  # HTTP client for API calls
        
        self.setup_handlers()
        self.logger.info("Initialized DaytonaInterpreter")

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
        Defines available tools and their execution logic.
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
        async def call_tool(name: str, arguments: dict) -> List[TextContent | ImageContent | EmbeddedResource]:
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
                raise ValueError(f"Unknown tool: {name}")

    async def initialize_client(self) -> None:
        """
        Initialize HTTP client with proper configuration for API communication.
        Sets up authentication, timeout, and SSL verification settings.
        """
        if self.http_client:
            await self.http_client.aclose()
            
        base_url = self.config.api_url.rstrip('/')
        
        self.http_client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}"
                # Removed "Content-Type": "application/json"
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

    async def create_workspace_and_project(self) -> None:
        """
        Create a new Daytona workspace and project with unique identifiers.
        Sets up Python environment and initializes with a basic repository.
        """
        workspace_name = f"python-{uuid.uuid4().hex[:8]}"
        project_name = f"python-project-{uuid.uuid4().hex[:8]}"
        self.logger.info(f"Creating Workspace with name: {workspace_name}")
        self.logger.info(f"Creating Project with name: {project_name}")

        create_workspace_data = {
            "id": workspace_name,
            "name": workspace_name,
            "projects": [{
                "name": project_name,
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
                        "sha": "0000000000000000000000000000000000000000",
                        "source": "local"
                    }
                }
            }],
            "target": "local"  # Ensure target is specified
        }

        try:
            response = await self.http_client.post("/workspace", json=create_workspace_data)
            response.raise_for_status()
            workspace = response.json()
            
            # Log the entire workspace response
            # self.logger.debug(f"Workspace creation response: {json.dumps(workspace, indent=2)}")
            
            self.workspace_id = workspace.get("id")
            projects = workspace.get("projects", [])

            if projects:
                project_info = projects[0]
                # self.logger.debug(f"First project details: {json.dumps(project_info, indent=2)}")
                # Use 'id' if available and not a placeholder; otherwise, use 'name'
                if 'id' in project_info and project_info['id'] and project_info['id'] != "placeholder":
                    self.project_id = project_info['id']
                else:
                    self.project_id = project_info.get("name")
                    # self.logger.warning(f"'id' not found or is a placeholder for project '{project_name}'. Using 'name' as 'project_id'.")
            else:
                self.logger.error("No projects found in workspace creation response.")
                self.project_id = None

            if not self.project_id:
                # Attempt to fetch project details separately
                self.project_id = await self.fetch_project_details(self.workspace_id, project_name)
            
            self.logger.info(f"Created Workspace ID: {self.workspace_id}, Project ID: {self.project_id}")
        except Exception as e:
            self.logger.error(f"Failed to create workspace and project: {str(e)}")
            raise RuntimeError(f"Failed to create workspace and project: {str(e)}")

    async def fetch_project_details(self, workspace_id: str, project_name: str) -> Optional[str]:
        """
        Fetch the project details to retrieve the project ID using project name.
        """
        fetch_url = f"/workspace/{workspace_id}"
        self.logger.info(f"Fetching workspace details from {fetch_url}")

        try:
            response = await self.http_client.get(fetch_url)
            response.raise_for_status()
            workspace = response.json()
            projects = workspace.get("projects", [])
            
            for project in projects:
                if project.get("name") == project_name:
                    project_id = project.get("id") or project.get("name")
                    self.logger.info(f"Found Project ID for project '{project_name}': {project_id}")
                    return project_id
            
            self.logger.error(f"Project '{project_name}' not found in workspace '{workspace_id}'.")
            return None
        except Exception as e:
            self.logger.error(f"Failed to fetch project details: {str(e)}")
            return None

    async def create_directory(self, directory_path: str) -> None:
        """
        Create a directory in the workspace project.
        Handles path normalization and error cases including existing directories.
        """
        create_dir_url = f"/workspace/{self.workspace_id}/{self.project_id}/toolbox/files/folder"
        self.logger.info(f"Creating directory at {directory_path}")

        # Ensure directory_path does not start with a leading slash
        if directory_path.startswith('/'):
            directory_path = directory_path[1:]

        # Construct relative path within the project
        relative_path = f"{directory_path}"  # No leading slash

        params = {
            "path": relative_path,  # Pass as relative path
            "mode": 755             # Mode as integer
        }

        try:
            response = await self.http_client.post(
                create_dir_url,
                params=params,  # Pass 'path' and 'mode' as query parameters
                data=''         # Empty body
            )
            response.raise_for_status()
            self.logger.info(f"Successfully created directory: {directory_path}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:  # Directory already exists
                self.logger.info(f"Directory already exists: {directory_path}")
            else:
                # Log the response text for better understanding of the error
                self.logger.error(f"Failed to create directory {directory_path}: {e.response.text}")
                raise RuntimeError(f"Failed to create directory {directory_path}: {e.response.text}")
        except Exception as e:
            self.logger.error(f"Unexpected error while creating directory {directory_path}: {e}")
            raise RuntimeError(f"Unexpected error while creating directory {directory_path}: {e}")

    async def upload_file(self, file_path: Path, upload_path: str) -> None:
        """
        Upload a file to the workspace project using multipart form data.
        Handles file reading and upload error cases.
        """
        upload_url = f"/workspace/{self.workspace_id}/{self.project_id}/toolbox/files/upload"
        self.logger.info(f"Uploading file {file_path} to {upload_path}")

        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path.name, f, 'application/octet-stream')  # MIME type can be adjusted if needed
                }
                params = {'path': upload_path}  # Pass 'path' as query parameter

                response = await self.http_client.post(
                    upload_url,
                    params=params,  # Correct usage: query parameters
                    files=files      # Let httpx set 'Content-Type: multipart/form-data'
                )
                response.raise_for_status()
                self.logger.info(f"Successfully uploaded {file_path.name} to {upload_path}")
        except httpx.HTTPStatusError as e:
            # Log the response text to understand the 400 error
            self.logger.error(f"Failed to upload file {file_path.name}: {e.response.text}")
            raise RuntimeError(f"Failed to upload file {file_path.name}: {e.response.text}")
        except Exception as e:
            self.logger.error(f"Failed to upload file {file_path.name}: {str(e)}")
            raise RuntimeError(f"Failed to upload file {file_path.name}: {str(e)}")

    async def execute_python_code(self, code: str) -> str:
        """
        Execute Python code in the workspace by:
        1. Creating a temporary script file
        2. Uploading it to the workspace
        3. Executing it using python3
        4. Capturing and returning the execution results
        """
        if not self.workspace_id or not self.project_id:
            raise RuntimeError("Workspace ID or Project ID is not set.")

        # Step 1: Create a temporary Python file
        unique_filename = f"temp_script_{uuid.uuid4().hex[:8]}.py"
        temp_dir = Path("/tmp/daytona_scripts")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = temp_dir / unique_filename

        self.logger.debug(f"Creating temporary Python file at {temp_file_path}")

        try:
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            self.logger.info(f"Temporary Python file created: {temp_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to create temporary Python file: {e}")
            raise RuntimeError(f"Failed to create temporary Python file: {e}")

        # Step 2: Create necessary directories (e.g., 'scripts/')
        scripts_dir = "scripts"
        await self.create_directory(scripts_dir)  # Now creates 'scripts' relative to project root

        # Step 3: Upload the Python file to the workspace project
        upload_path = f"{scripts_dir}/{unique_filename}"  # Relative path without leading '/'
        await self.upload_file(temp_file_path, upload_path)

        # Step 4: Execute the Python script
        execute_url = f"/workspace/{self.workspace_id}/{self.project_id}/toolbox/process/execute"
        command = f"python3 {upload_path}"  # Use the correct relative path

        execute_payload = {
            "command": command,
            "timeout": int(self.config.timeout)
        }

        self.logger.debug(f"Executing command: {command}")

        try:
            response = await self.http_client.post(
                execute_url,
                json=execute_payload
            )
            response.raise_for_status()
            result = response.json()

            # Parse the execution result
            stdout = result.get("result", "").strip()
            stderr = result.get("error", "").strip()
            exit_code = result.get("code", 0)

            self.logger.info(f"Execution completed with exit code {exit_code}")
            if stdout:
                self.logger.info(f"stdout: {stdout}")
            if stderr:
                self.logger.warning(f"stderr: {stderr}")

            # Step 5: Return the execution output as JSON
            return json.dumps({
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }, indent=2)
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error during code execution: {e.response.text}")
            raise RuntimeError(f"HTTP error during code execution: {e.response.text}")
        except Exception as e:
            self.logger.error(f"Error during code execution: {e}")
            raise RuntimeError(f"Error during code execution: {e}")
        finally:
            # Removed the call to delete_file(upload_path)

            # Step 6: Cleanup - Delete the local temporary file
            try:
                if temp_file_path.exists():
                    temp_file_path.unlink()
                    self.logger.debug(f"Deleted local temporary file: {temp_file_path}")
            except Exception as e:
                self.logger.error(f"Failed to delete local temporary file: {temp_file_path}, Error: {e}")

    async def execute_command(self, command: str) -> str:
        """
        Execute a shell command in the workspace.
        Captures and returns command output, errors, and exit code.
        """
        if not self.workspace_id or not self.project_id:
            raise RuntimeError("Workspace ID or Project ID is not set.")

        execute_url = f"/workspace/{self.workspace_id}/{self.project_id}/toolbox/process/execute"
        execute_payload = {
            "command": command,
            "timeout": int(self.config.timeout)
        }

        self.logger.debug(f"Executing shell command: {command}")

        try:
            response = await self.http_client.post(
                execute_url,
                json=execute_payload
            )
            response.raise_for_status()
            result = response.json()

            # Parse the execution result
            stdout = result.get("result", "").strip()
            stderr = result.get("error", "").strip()
            exit_code = result.get("code", 0)

            self.logger.info(f"Command execution completed with exit code {exit_code}")
            if stdout:
                self.logger.info(f"stdout: {stdout}")
            if stderr:
                self.logger.warning(f"stderr: {stderr}")

            # Return the execution output as JSON
            return json.dumps({
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }, indent=2)
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error during command execution: {e.response.text}")
            raise RuntimeError(f"HTTP error during command execution: {e.response.text}")
        except Exception as e:
            self.logger.error(f"Error during command execution: {e}")
            raise RuntimeError(f"Error during command execution: {e}")

    async def cleanup_workspace(self) -> None:
        """
        Clean up the workspace by deleting it and resetting state.
        Called during normal shutdown or error conditions.
        """
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
                self.project_id = None

    async def cleanup(self) -> None:
        """
        Perform full cleanup of resources:
        1. Clean up workspace if it exists
        2. Close HTTP client connection
        """
        if self.workspace_id:
            await self.cleanup_workspace()
        if self.http_client:
            await self.http_client.aclose()

    async def run(self) -> None:
        """
        Main server execution loop:
        1. Initialize client connection
        2. Create workspace and project
        3. Run MCP server with stdio communication
        4. Handle cleanup on shutdown
        """
        try:
            await self.initialize_client()
            await self.create_workspace_and_project()
            
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
    """
    Application entry point:
    1. Set up logging
    2. Create and run interpreter instance
    3. Handle interrupts and cleanup
    """
    logger = setup_logging()
    logger.info("Starting Daytona MCP interpreter")
    
    interpreter = DaytonaInterpreter(logger)
    
    try:
        await interpreter.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt")
    except BaseException as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await interpreter.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
