#!/usr/bin/env python
import shlex
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import time
import uuid
import base64
import mimetypes
import tempfile
from typing import List, Optional, Any, Union

from dotenv import load_dotenv
from daytona_sdk import Daytona, DaytonaConfig, CreateWorkspaceParams, Workspace
from daytona_sdk.process import ExecuteResponse
from daytona_sdk.filesystem import FileSystem

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource


# Custom exception classes for better error handling
class DaytonaError(Exception):
    """Base exception class for all Daytona-related errors."""
    pass


class WorkspaceError(DaytonaError):
    """Exception raised for workspace-related errors."""
    pass


class WorkspaceInitializationError(WorkspaceError):
    """Exception raised when workspace initialization fails."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Exception raised when a workspace is not found."""
    pass


class WorkspaceQuotaExceededError(WorkspaceError):
    """Exception raised when CPU quota is exceeded."""
    pass


class FileSystemError(DaytonaError):
    """Exception raised for filesystem-related errors."""
    pass


class FileNotAccessibleError(FileSystemError):
    """Exception raised when a file cannot be accessed."""
    pass


class FileTooLargeError(FileSystemError):
    """Exception raised when a file is too large to process."""
    pass


class CommandExecutionError(DaytonaError):
    """Exception raised when a command execution fails."""
    pass


class ConfigurationError(DaytonaError):
    """Exception raised for configuration-related errors."""
    pass


class NetworkError(DaytonaError):
    """Exception raised for network-related errors."""
    pass

# Initialize mimetypes
mimetypes.init()

# Uncomment the following line only if api_client is necessary and correctly imported
# from daytona_sdk import api_client

# Configure logging
LOG_FILE = '/tmp/daytona-interpreter.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# File to track workspace ID across multiple processes
WORKSPACE_TRACKING_FILE = '/tmp/daytona-workspace.json'
WORKSPACE_LOCK_FILE = '/tmp/daytona-workspace.lock'

# Removed global flag approach for better inter-process coordination
# Now using file locking for the entire initialization process

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

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
        # console_handler = logging.StreamHandler(sys.stderr)
        # console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        logger.addHandler(file_handler)
        # logger.addHandler(console_handler)

    return logger


class Config:
    """Server configuration class that loads environment variables for MCP Daytona setup"""
    def __init__(self):
        # Load environment variables from .env file
        try:
            load_dotenv()
            logger = logging.getLogger("daytona-interpreter")
            
            # Required API key for authentication
            self.api_key = os.getenv('MCP_DAYTONA_API_KEY')
            if not self.api_key:
                raise ConfigurationError("MCP_DAYTONA_API_KEY environment variable is required")
            else:
                logger.info("MCP_DAYTONA_API_KEY loaded successfully.")

            # Optional configuration with defaults
            self.server_url = os.getenv('MCP_DAYTONA_SERVER_URL', 'https://app.daytona.io/api')
            
            # Validate server URL format
            if not self.server_url.startswith(('http://', 'https://')):
                logger.warning(f"Invalid server URL format: {self.server_url}, adding https://")
                self.server_url = f"https://{self.server_url}"
            
            self.target = os.getenv('MCP_DAYTONA_TARGET', 'eu')
            
            # Validate and parse timeout
            timeout_str = os.getenv('MCP_DAYTONA_TIMEOUT', '180.0')
            try:
                self.timeout = float(timeout_str)
                if self.timeout <= 0:
                    logger.warning(f"Invalid timeout value: {self.timeout}, using default of 180.0")
                    self.timeout = 180.0
            except ValueError:
                logger.warning(f"Invalid timeout format: {timeout_str}, using default of 180.0")
                self.timeout = 180.0
                
            self.verify_ssl = os.getenv('MCP_VERIFY_SSL', 'false').lower() == 'true'

            # Optional debug logging
            self._log_config()
            
        except ConfigurationError:
            # Re-raise ConfigurationError exceptions
            raise
        except Exception as e:
            # Convert other exceptions to ConfigurationError with context
            logger.error(f"Configuration initialization error: {e}", exc_info=True)
            raise ConfigurationError(f"Failed to initialize configuration: {str(e)}") from e

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
        self.filesystem: Optional[FileSystem] = None  # FileSystem instance for the workspace

        # Initialize MCP server
        self.server = Server("daytona-interpreter")

        # Setup MCP handlers
        self.setup_handlers()

        # Setup empty resources list handler to prevent "Method not found" errors
        @self.server.list_resources()
        async def list_resources():
            return []

        # Setup empty prompts list handler to prevent "Method not found" errors
        @self.server.list_prompts()
        async def list_prompts():
            return []

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
            if 'requestId' in params and 'reason' in params:
                self.logger.info(f"Request {params['requestId']} was cancelled: {params['reason']}")

            # Handle shutdown if we get a cancel notification with a specific error message that
            # indicates connection is closing
            if 'reason' in params and 'connection' in str(params.get('reason', '')).lower():
                self.logger.info("Cancel notification indicates connection is closing, initiating cleanup")
                asyncio.create_task(self.cleanup_workspace())
            # Otherwise don't trigger workspace cleanup on individual request cancellations
            # as this is likely just timeout on individual requests, not session termination

        async def handle_shutdown(params: dict[str, Any]) -> None:
            """Handle shutdown notification."""
            self.logger.info("Received shutdown notification")
            # Perform cleanup but don't await it to prevent blocking
            asyncio.create_task(self.cleanup_workspace())

        async def handle_unknown_notification(method: str, params: dict[str, Any]) -> None:
            """Handle any unknown notifications gracefully."""
            # Don't log warnings for common notifications to reduce log noise
            if method not in ["notifications/cancelled"]:
                self.logger.warning(f"Received unknown notification method: {method} with params: {params}")

        # Register notification handlers with error handling wrapped around each handler
        handlers = {
            "$/cancelRequest": handle_cancel_request,
            "notifications/progress": handle_progress,
            "notifications/initialized": handle_initialized,
            "notifications/roots/list_changed": handle_roots_list_changed,
            "notifications/cancelled": handle_cancelled,
            "notifications/shutdown": handle_shutdown,
            "*": handle_unknown_notification  # Add a catch-all handler for any unknown notifications
        }

        # Wrap all handlers with error handling
        wrapped_handlers = {}
        for method, handler in handlers.items():
            async def wrapped_handler(params: dict[str, Any], method=method, original_handler=handler) -> None:
                try:
                    await original_handler(params)
                except Exception as e:
                    self.logger.error(f"Error in notification handler for {method}: {e}", exc_info=True)

            wrapped_handlers[method] = wrapped_handler

        self.server.notification_handlers.update(wrapped_handlers)

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
            1. shell_exec: Executes shell commands in workspace
            2. file_download: Downloads a file from the workspace
            3. file_upload: Uploads a file to the workspace
            4. git_clone: Clones a Git repository into the workspace
            5. web_preview: Generates a preview URL for web servers
            """
            return [
                Tool(
                    name="shell_exec",
                    description="Execute shell commands in the ephemeral Daytona Linux environment. Returns full stdout and stderr output with exit codes. Commands have workspace user permissions and can install packages, modify files, and interact with running services. Always use /tmp directory. Use verbose flags where available for better output.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to execute. Always use verbose where available."}
                        },
                        "required": ["command"]
                    }
                ),
                Tool(
                    name="file_download",
                    description="Download files from the Daytona workspace with smart handling for different file types and sizes. Supports text, binary, images, PDFs, and other formats with automatic content type detection. Results can be returned as text, base64-encoded data, or embedded resources.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file in the workspace"},
                            "max_size_mb": {"type": "number", "description": "Maximum file size in MB to download automatically (default: 5.0)"},
                            "download_option": {"type": "string", "description": "Option for handling large files: 'download_partial', 'convert_to_text', 'compress_file', or 'force_download'"},
                            "chunk_size_kb": {"type": "integer", "description": "Size of each chunk in KB when downloading partially (default: 100)"}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="git_clone",
                    description="Clone Git repositories into the Daytona workspace with customizable options. Supports branch/tag selection, shallow clones, Git LFS for large files, and SSH/HTTPS authentication. Cloned content persists during the session and can be accessed by other tools. Returns repository structure and metadata for easier navigation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {"type": "string", "description": "URL of the Git repository to clone"},
                            "target_path": {"type": "string", "description": "Target directory to clone into (default: repository name)"},
                            "branch": {"type": "string", "description": "Branch to checkout (default: repository default branch)"},
                            "depth": {"type": "integer", "description": "Depth of history to clone (default: 1 for shallow clone)"},
                            "lfs": {"type": "boolean", "description": "Whether to enable Git LFS (default: false)"}
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="file_upload",
                    description="Upload files to the Daytona workspace from text or base64-encoded binary content. Creates necessary parent directories automatically and verifies successful writes. Files persist during the session and have appropriate permissions for further tool operations. Supports overwrite controls and maintains original file formats.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path where the file should be created in the workspace"},
                            "content": {"type": "string", "description": "Content to write to the file (text or base64-encoded binary)"},
                            "encoding": {"type": "string", "description": "Encoding of the content: 'text' (default) or 'base64'"},
                            "overwrite": {"type": "boolean", "description": "Whether to overwrite the file if it already exists (default: true)"}
                        },
                        "required": ["file_path", "content"]
                    }
                ),
                Tool(
                    name="web_preview",
                    description="Generate accessible preview URLs for web applications running in the Daytona workspace. Creates a secure tunnel to expose local ports externally without configuration. Validates if a server is actually running on the specified port and provides diagnostic information for troubleshooting. Supports custom descriptions and metadata for better organization of multiple services.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {"type": "integer", "description": "The port number the server is running on"},
                            "description": {"type": "string", "description": "Optional description of the server (default: empty string)"},
                            "check_server": {"type": "boolean", "description": "Whether to check if a server is running on the port (default: true)"}
                        },
                        "required": ["port"]
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

            if name == "shell_exec":
                command = arguments.get("command")
                if not command:
                    raise ValueError("Command argument is required")
                try:
                    result = await self.execute_command(command)
                    return [TextContent(type="text", text=result)]
                except Exception as e:
                    self.logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
                    return [TextContent(type="text", text=f"Error executing tool: {e}")]

            elif name == "file_download":
                file_path = arguments.get("file_path")
                if not file_path:
                    raise ValueError("File path argument is required")

                # Extract optional parameters
                max_size_mb = arguments.get("max_size_mb", 5.0)
                download_option = arguments.get("download_option")
                chunk_size_kb = arguments.get("chunk_size_kb", 100)

                try:
                    # Add extra debug logging
                    self.logger.info(f"Using file_download with: path={file_path}, max_size={max_size_mb}MB, option={download_option}, chunk_size={chunk_size_kb}KB")

                    # Validate inputs before calling file_downloader
                    if max_size_mb is not None and not isinstance(max_size_mb, (int, float)):
                        try:
                            max_size_mb = float(max_size_mb)
                        except (ValueError, TypeError):
                            self.logger.warning(f"Invalid max_size_mb value: {max_size_mb}, using default of 5.0")
                            max_size_mb = 5.0
                            
                    if chunk_size_kb is not None and not isinstance(chunk_size_kb, (int, float)):
                        try:
                            chunk_size_kb = int(chunk_size_kb)
                        except (ValueError, TypeError):
                            self.logger.warning(f"Invalid chunk_size_kb value: {chunk_size_kb}, using default of 100")
                            chunk_size_kb = 100

                    # Call our improved file_downloader function
                    result = file_downloader(
                        path=file_path,
                        max_size_mb=max_size_mb,
                        download_option=download_option,
                        chunk_size_kb=chunk_size_kb
                    )

                    self.logger.info(f"Download result: success={result.get('success', False)}")

                    # Check if we got a download options response (for large files)
                    if result.get("file_too_large"):
                        options_text = (
                            f"File '{result.get('filename')}' is {result.get('file_size_mb')}MB which exceeds the "
                            f"{result.get('max_size_mb')}MB limit.\n\n"
                            "Available options:\n"
                            "- download_partial: Download first part of the file\n"
                            "- convert_to_text: Try to convert file to plain text\n"
                            "- compress_file: Compress the file before downloading\n"
                            "- force_download: Download the entire file anyway\n\n"
                            "To proceed, call file_download again with the desired option, for example:\n"
                            f"file_download(file_path='{file_path}', download_option='download_partial')"
                        )
                        return [TextContent(type="text", text=options_text)]

                    # For successful downloads, process the content
                    if result.get("success"):
                        # If partial download, convert_to_text, or compressed, add a message
                        if result.get("partial") or result.get("converted") or result.get("compressed"):
                            message = result.get("message", "")
                            content = result.get("content", b"")

                            # For binary content, determine content type
                            content_type = result.get("content_type", "application/octet-stream")

                            # For image content types, return as ImageContent
                            if content_type.startswith("image/"):
                                # Convert binary content to base64
                                base64_content = base64.b64encode(content).decode('utf-8')
                                return [
                                    ImageContent(type="image", data=base64_content, mimeType=content_type),
                                    TextContent(type="text", text=message)
                                ]
                            else:
                                # For text content
                                try:
                                    # Try to decode as text if it's a text type
                                    if content_type.startswith("text/"):
                                        text_content = content.decode('utf-8')
                                        return [TextContent(type="text", text=f"{message}\n\n{text_content}")]
                                    else:
                                        # Return as embedded resource for binary files
                                        base64_content = base64.b64encode(content).decode('utf-8')
                                        return [
                                            EmbeddedResource(
                                                type="resource",
                                                resource={
                                                    "uri": f"file://{file_path}",
                                                    "data": base64_content,
                                                    "mimeType": content_type
                                                }
                                            ),
                                            TextContent(type="text", text=message)
                                        ]
                                except UnicodeDecodeError:
                                    # If we can't decode as text, treat as binary
                                    base64_content = base64.b64encode(content).decode('utf-8')
                                    return [
                                        EmbeddedResource(
                                            type="resource",
                                            resource={
                                                "uri": f"file://{file_path}",
                                                "data": base64_content,
                                                "mimeType": content_type
                                            }
                                        ),
                                        TextContent(type="text", text=message)
                                    ]

                        # For standard downloads, use process_file_content
                        content = result.get("content", b"")
                        if content:
                            return await self.process_file_content(file_path, content)

                    # For errors, return the error message with specific error handling based on error type
                    if not result.get("success"):
                        error_msg = result.get('error', 'Unknown error')
                        error_type = result.get('error_type', 'UnknownError')
                        
                        # Format user-friendly error messages based on error type
                        if error_type == "FileNotAccessibleError":
                            friendly_msg = f"File not accessible: {error_msg}. Please check if the file exists and you have permission to access it."
                        elif error_type == "FileTooLargeError":
                            friendly_msg = f"File too large: {error_msg}. Try downloading with a specific option like 'download_partial'."
                        elif error_type == "WorkspaceQuotaExceededError":
                            friendly_msg = f"Resource limit exceeded: {error_msg}. Please try again later or contact support."
                        elif error_type == "NetworkError":
                            friendly_msg = f"Network error: {error_msg}. Please check your connection and try again."
                        elif error_type in ["FileSystemError", "WorkspaceError", "WorkspaceInitializationError"]:
                            friendly_msg = f"System error ({error_type}): {error_msg}. Please try again or contact support if the issue persists."
                        else:
                            friendly_msg = f"Error downloading file: {error_msg}"
                            
                        self.logger.error(f"Error type: {error_type}, Message: {error_msg}")
                        return [TextContent(type="text", text=friendly_msg)]

                    # Fallback for unexpected results
                    return [TextContent(type="text", text=f"Unexpected download result: {json.dumps(result, default=str)}")]
                except Exception as e:
                    self.logger.error(f"Error in file_downloader: {e}", exc_info=True)
                    
                    # Classify exception type for better error messages
                    if isinstance(e, FileNotAccessibleError):
                        error_msg = f"File not accessible: {str(e)}. Please check if the file exists and you have permission to access it."
                    elif isinstance(e, FileTooLargeError):
                        error_msg = f"File too large: {str(e)}. Try downloading with a specific option."
                    elif isinstance(e, FileSystemError):
                        error_msg = f"File system error: {str(e)}. Please try again."
                    elif isinstance(e, NetworkError):
                        error_msg = f"Network error: {str(e)}. Please check your connection and try again."
                    elif isinstance(e, WorkspaceError):
                        error_msg = f"Workspace error: {str(e)}. Please try again later."
                    else:
                        error_msg = f"Error downloading file: {str(e)}"
                        
                    # Return error as text
                    return [TextContent(type="text", text=error_msg)]


            elif name == "git_clone":
                repo_url = arguments.get("repo_url")
                if not repo_url:
                    raise ValueError("Repository URL is required")

                # Extract optional parameters
                target_path = arguments.get("target_path")
                branch = arguments.get("branch")
                depth = arguments.get("depth", 1)
                lfs = arguments.get("lfs", False)

                try:
                    # Add debug logging
                    self.logger.info(f"Using git_clone with: url={repo_url}, target={target_path}, branch={branch}, depth={depth}, lfs={lfs}")

                    # Call the git_clone function
                    result = git_repo_cloner(
                        repo_url=repo_url,
                        target_path=target_path,
                        branch=branch,
                        depth=depth,
                        lfs=lfs
                    )

                    # Handle errors
                    if not result.get("success", False):
                        error_msg = f"Error cloning repository: {result.get('error', 'Unknown error')}"
                        self.logger.error(error_msg)
                        return [TextContent(type="text", text=error_msg)]

                    # Format successful clone result
                    target_dir = result.get("target_directory", "repo")
                    total_files = result.get("total_files", 0)
                    files_sample = result.get("files_sample", [])
                    repo_info = result.get("repository_info", "")

                    # Build response
                    response_parts = [
                        f"Repository cloned successfully into '{target_dir}'",
                        f"Total files: {total_files}",
                        f"\nRepository information:\n{repo_info}"
                    ]

                    if files_sample:
                        sample_list = "\n".join(files_sample[:20])  # Show first 20 files
                        file_count_msg = ""
                        if len(files_sample) > 20:
                            file_count_msg = f"...and {len(files_sample) - 20} more files"
                        response_parts.append(f"\nSample files:\n{sample_list}\n{file_count_msg}")

                        if total_files > len(files_sample):
                            response_parts.append(f"\n(Showing {len(files_sample)} of {total_files} total files)")

                    return [TextContent(type="text", text="\n".join(response_parts))]
                except Exception as e:
                    self.logger.error(f"Error in git_repo_cloner: {e}", exc_info=True)
                    return [TextContent(type="text", text=f"Error cloning repository: {str(e)}")]

            elif name == "file_upload":
                file_path = arguments.get("file_path")
                content = arguments.get("content")
                encoding = arguments.get("encoding", "text")
                overwrite = arguments.get("overwrite", True)

                if not file_path:
                    raise ValueError("File path is required")
                if content is None:
                    raise ValueError("Content is required")

                try:
                    # Add debug logging
                    self.logger.info(f"Using file_upload with: path={file_path}, encoding={encoding}, overwrite={overwrite}")

                    # Call the file_uploader function
                    result = file_uploader(
                        file_path=file_path,
                        content=content,
                        encoding=encoding,
                        overwrite=overwrite
                    )

                    self.logger.info(f"Upload result: success={result.get('success', False)}")

                    if result.get("success"):
                        return [TextContent(type="text", text=result.get("message", "File uploaded successfully"))]
                    else:
                        return [TextContent(type="text", text=f"Error uploading file: {result.get('error', 'Unknown error')}")]
                except Exception as e:
                    self.logger.error(f"Error in file_upload: {e}", exc_info=True)
                    return [TextContent(type="text", text=f"Error uploading file: {str(e)}")]

            elif name == "web_preview":
                port = arguments.get("port")
                if port is None:
                    raise ValueError("Port number is required")

                # Validate port is a valid number
                try:
                    port = int(port)
                    if port < 1 or port > 65535:
                        raise ValueError(f"Invalid port number: {port}. Must be between 1 and 65535.")
                except ValueError as e:
                    return [TextContent(type="text", text=f"Invalid port: {e}")]

                # Extract optional parameters
                description = arguments.get("description", "")
                check_server = arguments.get("check_server", True)

                try:
                    # Call the web_preview function
                    self.logger.info(f"Using web_preview with port={port}")
                    result = preview_link_generator(
                        port=port,
                        description=description,
                        check_server=check_server
                    )

                    # Handle errors
                    if not result.get("success", False):
                        error_msg = f"Error generating preview link: {result.get('error', 'Unknown error')}"

                        # Add process info if available to help diagnose the issue
                        process_info = result.get("process_info", "")
                        if process_info and process_info != "No process found":
                            error_msg += f"\n\nProcess found on port {port}:\n{process_info}"

                        self.logger.error(error_msg)
                        return [TextContent(type="text", text=error_msg)]

                    # Format successful result
                    preview_url = result.get("preview_url", "")
                    accessible = result.get("accessible", None)
                    status_code = result.get("status_code", None)

                    # Create a response message with the preview URL
                    response_parts = []

                    # Add the description if provided
                    if description:
                        response_parts.append(f"# {description}")

                    # Add the preview URL (primary information)
                    response_parts.append(f"Preview URL: {preview_url}")

                    # Add accessibility status if checked
                    if check_server and accessible is not None:
                        if accessible:
                            response_parts.append(f"URL is accessible (status code: {status_code})")
                        else:
                            response_parts.append(f"Warning: URL is not accessible. The server may not be properly configured to accept external requests.")

                    # Add any additional notes
                    note = result.get("note", "")
                    if note:
                        response_parts.append(f"Note: {note}")

                    # Add useful information for debugging
                    response_parts.append(f"\nPort: {port}")
                    response_parts.append(f"Workspace ID: {result.get('workspace_id', '')}")

                    # Create clickable link using markdown
                    response_parts.append(f"\n[Click here to open preview]({preview_url})")

                    return [TextContent(type="text", text="\n".join(response_parts))]
                except Exception as e:
                    self.logger.error(f"Error in preview_link_generator: {e}", exc_info=True)
                    return [TextContent(type="text", text=f"Error generating preview link: {str(e)}")]

            else:
                self.logger.error(f"Unknown tool: {name}")
                raise ValueError(f"Unknown tool: {name}")

    async def initialize_workspace(self) -> None:
        """
        Initialize the Daytona workspace using the SDK.
        Creates a new workspace if it doesn't exist, or reuses an existing one.
        Uses a file-based lock to coordinate between processes.

        IMPORTANT: This method enforces a single workspace per session by using
        a tracking file to store and retrieve the active workspace ID.
        
        Raises:
            WorkspaceInitializationError: If workspace initialization fails
            WorkspaceQuotaExceededError: If CPU quota is exceeded
            WorkspaceNotFoundError: If a referenced workspace cannot be found
            NetworkError: If network-related errors occur
        """
        # First check if this instance already has a workspace
        if self.workspace:
            self.logger.info(f"Instance already has workspace ID: {self.workspace.id}")
            return

        # Use file lock for the ENTIRE initialization process to prevent race conditions
        # This is critical to prevent multiple processes from initializing at the same time
        try:
            # Try to get the lock with a timeout
            with FileLock(WORKSPACE_LOCK_FILE):
                self.logger.info(f"Acquired file lock for workspace initialization (process {os.getpid()})")

                # Check if another process has already initialized the workspace
                workspace_id, created_at = get_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                if workspace_id:
                    try:
                        self.logger.info(f"Found active workspace ID: {workspace_id} (process {os.getpid()})")
                        # Try to get the workspace from Daytona
                        try:
                            workspaces = self.daytona.list()
                        except Exception as list_err:
                            if "Unauthorized" in str(list_err) or "401" in str(list_err):
                                raise NetworkError("Authentication failed when listing workspaces. Please check your API key.")
                            elif "Connection" in str(list_err) or "Timeout" in str(list_err):
                                raise NetworkError(f"Network error when listing workspaces: {str(list_err)}")
                            else:
                                raise WorkspaceError(f"Failed to list workspaces: {str(list_err)}")
                                
                        for workspace in workspaces:
                            if workspace.id == workspace_id:
                                # Reuse the existing workspace
                                self.workspace = workspace
                                # Initialize filesystem for this workspace
                                try:
                                    # The API has changed in daytona-sdk 0.10.2
                                    # We need to create the FileSystem instance with proper parameters
                                    # In SDK 0.10.2, toolbox_api is available directly on the Daytona instance
                                    toolbox_api = self.daytona.toolbox_api

                                    # Create filesystem with the workspace instance and toolbox_api
                                    self.filesystem = FileSystem(instance=self.workspace, toolbox_api=toolbox_api)
                                    self.logger.info(f"Reusing existing workspace ID: {workspace_id}")
                                    return
                                except Exception as fs_err:
                                    self.logger.error(f"Failed to initialize filesystem for workspace {workspace_id}: {fs_err}")
                                    raise FileSystemError(f"Failed to initialize filesystem: {str(fs_err)}")

                        # If we get here, the workspace in the file wasn't found in Daytona
                        self.logger.warning(f"Workspace {workspace_id} not found in Daytona, clearing tracking")
                        # Use filesystem if available for this instance
                        clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                        raise WorkspaceNotFoundError(f"Workspace {workspace_id} not found in Daytona")
                    except (WorkspaceNotFoundError, FileSystemError, NetworkError, WorkspaceError) as specific_error:
                        # Clear tracking file to prevent future issues
                        clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                        raise
                    except Exception as e:
                        self.logger.warning(f"Error fetching workspace: {e}")
                        # Clear tracking file to prevent future issues
                        clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                        raise WorkspaceError(f"Error fetching workspace: {str(e)}")

                # If we get here, we need to create a new workspace
                if os.path.exists(WORKSPACE_TRACKING_FILE):
                    self.logger.info(f"Clearing stale workspace tracking file")
                    # Use filesystem if available for this instance
                    clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)

                # Only create a new workspace if we don't have a valid tracking file
                self.logger.info(f"Creating a new Daytona workspace (process {os.getpid()})")
                params = CreateWorkspaceParams(
                    language="python",
                    os_user="workspace"  # Fix: use os_user instead of user parameter
                    # Additional parameters can be defined here
                )

                # Check if we have any existing workspaces and terminate them if needed
                try:
                    # List existing workspaces to avoid creating too many
                    try:
                        workspaces = self.daytona.list()
                    except Exception as list_err:
                        if "Unauthorized" in str(list_err) or "401" in str(list_err):
                            raise NetworkError("Authentication failed when listing workspaces. Please check your API key.")
                        elif "Connection" in str(list_err) or "Timeout" in str(list_err):
                            raise NetworkError(f"Network error when listing workspaces: {str(list_err)}")
                        else:
                            self.logger.warning(f"Error listing workspaces: {list_err}")
                            # Continue without failing - we'll attempt creation anyway
                            workspaces = []
                    
                    if len(workspaces) > 0:
                        self.logger.info(f"Found {len(workspaces)} existing workspaces, removing oldest")
                        # Sort by creation time (oldest first) if available
                        try:
                            workspaces.sort(key=lambda ws: getattr(ws, 'created_at', 0))
                            # Remove oldest workspace
                            if workspaces:
                                oldest = workspaces[0]
                                self.logger.info(f"Removing oldest workspace: {oldest.id}")
                                self.daytona.remove(oldest)
                        except Exception as e:
                            self.logger.warning(f"Error sorting/removing workspaces: {e}")
                except Exception as e:
                    self.logger.warning(f"Error listing workspaces: {e}")

                # Add a retry mechanism for workspace creation
                max_retries = 3
                retry_count = 0
                retry_delay = 2.0
                last_error = None

                while retry_count < max_retries:
                    try:
                        self.workspace = self.daytona.create(params)
                        workspace_id = self.workspace.id
                        # Initialize filesystem for this workspace
                        try:
                            toolbox_api = self.daytona.toolbox_api
                            self.filesystem = FileSystem(instance=self.workspace, toolbox_api=toolbox_api)
                            self.logger.info(f"Created Workspace ID: {workspace_id}")

                            # Save workspace ID to tracking file for other processes to reuse
                            # This must happen BEFORE releasing the lock to prevent race conditions
                            set_active_workspace(workspace_id, self.filesystem)
                            self.logger.info(f"Registered workspace ID {workspace_id} in tracking file")
                            break
                        except Exception as fs_err:
                            self.logger.error(f"Failed to initialize filesystem for workspace {workspace_id}: {fs_err}")
                            # Try to clean up the workspace we just created
                            try:
                                self.daytona.remove(self.workspace)
                                self.logger.info(f"Cleaned up workspace {workspace_id} after filesystem initialization failed")
                            except Exception as cleanup_err:
                                self.logger.warning(f"Failed to clean up workspace after error: {cleanup_err}")
                            
                            raise FileSystemError(f"Failed to initialize filesystem: {str(fs_err)}")
                    except Exception as e:
                        last_error = e
                        error_str = str(e)
                        
                        # Handle quota exceeded errors
                        if "Total CPU quota exceeded" in error_str or "quota" in error_str.lower():
                            # Extract the quota information if available
                            quota_info = ""
                            try:
                                import re
                                match = re.search(r"Total CPU quota exceeded \((\d+) > (\d+)\)", error_str)
                                if match:
                                    current = match.group(1)
                                    limit = match.group(2)
                                    quota_info = f" (Current: {current}, Limit: {limit})"
                            except:
                                pass

                            self.logger.error(f"CPU quota exceeded error{quota_info}: {e}")
                            # Provide more user-friendly error message
                            error_message = (
                                f"Daytona CPU quota exceeded{quota_info}. Please delete unused workspaces "
                                "from your Daytona account or upgrade your plan to continue."
                            )
                            self.logger.error(error_message)
                            # Don't retry on quota errors
                            raise WorkspaceQuotaExceededError(error_message)
                        
                        # Handle network-related errors
                        elif "Connection" in error_str or "Timeout" in error_str:
                            self.logger.warning(f"Network error during workspace creation: {e}")
                            if retry_count >= max_retries - 1:
                                raise NetworkError(f"Network error during workspace creation: {str(e)}")
                        
                        # Handle authentication errors
                        elif "Unauthorized" in error_str or "401" in str(e):
                            raise NetworkError("Authentication failed when creating workspace. Please check your API key.")

                        retry_count += 1
                        if retry_count >= max_retries:
                            self.logger.error(f"Workspace creation failed after {max_retries} attempts")
                            raise WorkspaceInitializationError(f"Failed to create workspace after {max_retries} attempts: {str(last_error)}")
                            
                        self.logger.warning(f"Workspace creation attempt {retry_count} failed: {e}, retrying in {retry_delay}s")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                        
        except (WorkspaceInitializationError, WorkspaceQuotaExceededError, 
                WorkspaceNotFoundError, FileSystemError, NetworkError, WorkspaceError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            self.logger.error(f"Failed to create/find workspace: {e}", exc_info=True)
            raise WorkspaceInitializationError(f"Failed to create/find workspace: {str(e)}")

    async def execute_python_code(self, code: str) -> str:
        """
        Execute Python code in the Daytona workspace using the SDK.
        Returns the execution result as a JSON string.

        Uses a wrapped code approach with robust error handling, environment
        diagnostics, and improved temporary directory management. Results
        are clearly marked for easier parsing.
        """
        if not self.workspace:
            self.logger.error("Workspace is not initialized.")
            raise RuntimeError("Workspace is not initialized.")

        # Create wrapped code with all the requested enhancements
        wrapped_code = f"""
import tempfile
import os
import base64
import json
import io
import sys
import platform
import shutil
import uuid
from pathlib import Path
import traceback

# Dictionary to collect execution results
result_dict = {{
    "stdout": "",
    "stderr": "",
    "exit_code": 0,
    "environment": {{}},
    "images": []
}}

# Setup output capture
original_stdout = sys.stdout
original_stderr = sys.stderr
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()
sys.stdout = stdout_capture
sys.stderr = stderr_capture

try:
    # Collect environment diagnostics
    result_dict["environment"] = {{
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "user": os.getenv("USER", "unknown"),
        "home": os.path.expanduser("~"),
        "cwd": os.getcwd(),
        "pid": os.getpid()
    }}

    # Print diagnostics to stdout
    print(f"Python {{platform.python_version()}} on {{platform.platform()}}")
    print(f"Process ID: {{os.getpid()}}")
    print(f"Working directory: {{os.getcwd()}}")

    # Multiple fallback options for temporary directory
    temp_dir = None
    temp_dirs_to_try = [
        os.path.expanduser("~/.daytona_tmp"),   # First try user home
        "/tmp/daytona_tmp",                     # Then try system /tmp
        os.getcwd(),                            # Then try current directory
        os.path.join(os.path.expanduser("~"), ".cache")  # Then try .cache
    ]

    # Try creating temp directory in each location
    for dir_path in temp_dirs_to_try:
        try:
            # Make sure parent directory exists with appropriate permissions
            parent = os.path.dirname(dir_path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, mode=0o777, exist_ok=True)

            # Create the directory if it doesn't exist
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, mode=0o777, exist_ok=True)

            # Set as tempdir and create a unique subdirectory
            tempfile.tempdir = dir_path
            temp_dir = tempfile.mkdtemp(prefix='daytona_execution_')
            print(f"Created temporary directory: {{temp_dir}}")
            break
        except Exception:
            error = traceback.format_exc()
            print(f"Failed to use {{dir_path}} as temp directory:")
            print(error)

    # If all fallbacks failed, use a uuid-based directory in the current path
    if not temp_dir:
        try:
            temp_dir = os.path.join(os.getcwd(), f"daytona_tmp_{{uuid.uuid4().hex}}")
            os.makedirs(temp_dir, exist_ok=True)
            print(f"Using last-resort temporary directory: {{temp_dir}}")
        except Exception:
            error = traceback.format_exc()
            print(f"Failed to create last-resort temp directory: {{error}}")
            # Continue with temp_dir=None, will use current directory

    # Store original working directory
    original_dir = os.getcwd()

    # Change to temp directory if it exists
    if temp_dir and os.path.exists(temp_dir):
        try:
            os.chdir(temp_dir)
            print(f"Changed to working directory: {{os.getcwd()}}")
        except Exception:
            print(f"Failed to change to {{temp_dir}}, using current directory")

    # Create globals and locals dictionaries for execution
    globals_dict = {{'__name__': '__main__'}}
    locals_dict = {{}}

    # Add common packages to globals to make them available
    try:
        # Standard library modules
        import datetime, math, random, re, collections, itertools
        globals_dict.update({{
            'datetime': datetime,
            'math': math,
            'random': random,
            're': re,
            'collections': collections,
            'itertools': itertools,
            'os': os,
            'sys': sys,
            'json': json,
            'Path': Path
        }})

        # Try importing common data science packages
        try:
            import numpy as np
            globals_dict['np'] = np
            print("NumPy successfully imported")
        except ImportError:
            print("Warning: numpy not available")

        try:
            import pandas as pd
            globals_dict['pd'] = pd
            print("Pandas successfully imported")
        except ImportError:
            print("Warning: pandas not available")

        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            globals_dict['plt'] = plt
            globals_dict['matplotlib'] = matplotlib
            print("Matplotlib successfully imported")
        except ImportError:
            print("Warning: matplotlib not available")
    except Exception:
        print("Warning: Error importing common packages")
        print(traceback.format_exc())

    # Execute the user code with exec() in the prepared environment
    try:
        print("\\n--- Executing Code ---")
        exec(r'''{code}''', globals_dict, locals_dict)
        print("--- Code execution completed successfully ---\\n")
    except Exception:
        traceback_str = traceback.format_exc()
        print(f"\\n--- Error executing code ---\\n{{traceback_str}}\\n--- End of error ---\\n")
        result_dict["exit_code"] = 1

    # Check for matplotlib figures
    if 'plt' in globals_dict and hasattr(globals_dict['plt'], 'get_fignums'):
        plt = globals_dict['plt']
        if plt.get_fignums():
            try:
                print("Saving unsaved matplotlib figures...")
                for fig_num in plt.get_fignums():
                    fig = plt.figure(fig_num)
                    img_path = f"figure_{{fig_num}}.png"
                    fig.savefig(img_path)
                    print(f"Saved figure {{fig_num}} to {{img_path}}")
                plt.close('all')
            except Exception:
                print("Error saving matplotlib figures:")
                print(traceback.format_exc())

    # Collect and encode any image files
    image_files = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
    if image_files:
        print(f"Found {{len(image_files)}} image files: {{image_files}}")
        for img_file in image_files:
            try:
                with open(img_file, 'rb') as f:
                    img_data = f.read()
                    if img_data:
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        mime_type = "image/png"
                        if img_file.endswith('.jpg') or img_file.endswith('.jpeg'):
                            mime_type = "image/jpeg"
                        elif img_file.endswith('.gif'):
                            mime_type = "image/gif"
                        elif img_file.endswith('.svg'):
                            mime_type = "image/svg+xml"

                        # Add to result
                        result_dict["images"].append({{
                            "data": img_base64,
                            "mime_type": mime_type,
                            "filename": img_file,
                            "size": len(img_data)
                        }})
                        print(f"Added {{img_file}} to results ({{len(img_data)}} bytes)")
            except Exception:
                print(f"Error processing image file {{img_file}}:")
                print(traceback.format_exc())

    # Restore stdout, stderr before final output
    sys.stdout = original_stdout
    sys.stderr = original_stderr

    # Get captured output
    result_dict["stdout"] = stdout_capture.getvalue()
    result_dict["stderr"] = stderr_capture.getvalue()

    # Cleanup temporary directory if it exists
    if temp_dir and os.path.exists(temp_dir):
        try:
            # Change back to original directory first
            if original_dir:
                os.chdir(original_dir)
            # Delete temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"Cleaned up temporary directory: {{temp_dir}}")
        except Exception:
            print(f"Failed to remove temporary directory {{temp_dir}}")

    # Print results with special marker for parsing
    result_json = json.dumps(result_dict, indent=2)
    print("RESULT_JSON:" + result_json)

except Exception:
    # Global exception handler for the entire wrapper
    sys.stdout = original_stdout
    sys.stderr = original_stderr

    error_trace = traceback.format_exc()
    print(f"Critical error in code execution wrapper:\\n{{error_trace}}")

    # Ensure we still return a valid JSON result
    result_dict = {{
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue() + "\\n" + error_trace,
        "exit_code": 2,
        "images": []
    }}

    # Print with marker for parsing
    result_json = json.dumps(result_dict, indent=2)
    print("RESULT_JSON:" + result_json)
"""

        # Execute the wrapped code in the workspace
        try:
            # Log the code execution attempt
            self.logger.debug(f"Executing wrapped Python code with length: {len(wrapped_code)}")

            # Execute using the SDK
            response = self.workspace.process.code_run(wrapped_code)

            # Process the results
            raw_result = str(response.result).strip() if response.result else ""
            exit_code = response.exit_code if hasattr(response, 'exit_code') else -1

            # Log a truncated version of the output
            log_output = raw_result[:500] + "..." if len(raw_result) > 500 else raw_result
            self.logger.info(f"Code execution completed with exit code {exit_code}, output length: {len(raw_result)}")
            self.logger.debug(f"Execution Output (truncated):\n{log_output}")

            # Look for the RESULT_JSON marker in the output
            result_json = None
            marker = "RESULT_JSON:"
            marker_pos = raw_result.find(marker)

            if marker_pos >= 0:
                # Extract JSON after the marker
                json_str = raw_result[marker_pos + len(marker):].strip()
                try:
                    result_data = json.loads(json_str)
                    self.logger.info("Successfully parsed execution result JSON")

                    # Process images if present
                    if result_data.get("images"):
                        self.logger.info(f"Found {len(result_data['images'])} images in result")
                        # If only one image, include it in the main result
                        if len(result_data["images"]) == 1:
                            img = result_data["images"][0]
                            result_data["image"] = img["data"]
                            result_data["metadata"] = {
                                "filename": img["filename"],
                                "size": img["size"],
                                "type": img["mime_type"].split("/")[-1]
                            }

                    # Return the formatted result
                    return json.dumps(result_data, indent=2)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse result JSON, marker found but JSON invalid")
                    # Continue with fallback

            # Fallback: If no marker or invalid JSON, return the raw output
            self.logger.warning("No result marker found, returning raw output")
            return json.dumps({
                "stdout": raw_result,
                "stderr": "",
                "exit_code": exit_code
            }, indent=2)

        except Exception as exc:
            # Capture the error and return it in a structured format
            error_info = str(exc)
            self.logger.error(f"Error executing Python code: {error_info}")

            # Return a properly formatted error result
            return json.dumps({
                "stdout": "",
                "stderr": f"Error executing code: {error_info}",
                "exit_code": -1
            }, indent=2)

    async def execute_command(self, command: str) -> str:
        """
        Execute a shell command in the Daytona workspace using the SDK.
        Returns the execution result as a JSON string.
        
        Args:
            command: The shell command to execute
            
        Returns:
            JSON string containing stdout, stderr, and exit_code
            
        Raises:
            WorkspaceError: If workspace is not initialized
            CommandExecutionError: If command execution fails
            NetworkError: If connection issues occur during execution
        """
        if not self.workspace:
            self.logger.error("Workspace is not initialized.")
            raise WorkspaceError("Workspace is not initialized.")

        try:
            # Validate command input
            if not command or not isinstance(command, str):
                raise ValueError("Command must be a non-empty string")
                
            # For commands containing && or cd, execute them as a single shell command
            if '&&' in command or command.strip().startswith('cd '):
                # Wrap the entire command in /bin/sh -c
                command = f'/bin/sh -c {shlex.quote(command)}'
            else:
                # For simple commands, just use shlex.quote on arguments if needed
                command = command.strip()

            self.logger.debug(f"Executing command: {command}")

            try:
                # Execute shell command using the SDK
                response: ExecuteResponse = self.workspace.process.exec(command)
                self.logger.debug(f"ExecuteResponse received: {type(response)}")

                # Handle the response result
                result = str(response.result).strip() if response.result else ""
                exit_code = response.exit_code if hasattr(response, 'exit_code') else -1
                self.logger.info(f"Command completed with exit code: {exit_code}, output length: {len(result)}")

                # Truncate log output if too long
                log_output = result[:500] + "..." if len(result) > 500 else result
                self.logger.debug(f"Command Output (truncated):\n{log_output}")

                # Check for high exit code (error conditions)
                if exit_code > 0:
                    self.logger.warning(f"Command exited with non-zero status: {exit_code}")
                
                # Return the execution output as JSON
                return json.dumps({
                    "stdout": result,
                    "stderr": "",
                    "exit_code": exit_code
                }, indent=2)
            except Exception as e:
                error_str = str(e)
                self.logger.error(f"Error during command execution: {e}", exc_info=True)
                
                # Classify error types for better handling
                if "Connection" in error_str or "Timeout" in error_str:
                    raise NetworkError(f"Network error during command execution: {error_str}")
                elif "Unauthorized" in error_str or "401" in str(e):
                    raise NetworkError("Authentication failed during command execution. Please check your API key.")
                else:
                    raise CommandExecutionError(f"Command execution failed: {error_str}")
        except (NetworkError, CommandExecutionError, WorkspaceError, ValueError) as specific_error:
            # For specific error types, return formatted output with appropriate error info
            self.logger.error(f"Command execution error: {specific_error}")
            return json.dumps({
                "stdout": "",
                "stderr": str(specific_error),
                "exit_code": -1,
                "error_type": specific_error.__class__.__name__
            }, indent=2)
        except Exception as e:
            # For unexpected errors, wrap in CommandExecutionError but preserve original
            self.logger.error(f"Unexpected error executing command: {e}", exc_info=True)
            error = CommandExecutionError(f"Unexpected error: {str(e)}")
            return json.dumps({
                "stdout": "",
                "stderr": str(error),
                "exit_code": -1,
                "error_type": "CommandExecutionError"
            }, indent=2)

    async def cleanup_workspace(self) -> None:
        """
        Clean up the Daytona workspace by removing it using the SDK.
        Uses a file lock to coordinate between processes.
        
        This method handles workspace cleanup with error recovery and ensures
        proper coordination between multiple processes accessing the same workspace.
        """
        if not self.workspace:
            self.logger.debug("No workspace to clean up for this instance")
            return

        # Store workspace ID for logging
        workspace_id = self.workspace.id

        try:
            # Use file lock to ensure only one process cleans up
            with FileLock(WORKSPACE_LOCK_FILE):
                # Check if this instance's workspace is the active workspace
                active_id, _ = get_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                if active_id and active_id == workspace_id:
                    self.logger.info(f"Starting cleanup for workspace ID: {workspace_id}")
                    
                    # Attempt to remove the workspace with retry mechanism
                    max_retries = 2
                    retry_count = 0
                    retry_delay = 1.0
                    success = False
                    last_error = None
                    
                    while retry_count < max_retries and not success:
                        try:
                            # Remove the workspace
                            self.daytona.remove(self.workspace)
                            success = True
                            
                            # Clear tracking file so other processes know it's gone
                            clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                            
                            # Log success
                            self.logger.info(f"Successfully removed Workspace ID: {workspace_id}")
                        except Exception as e:
                            last_error = e
                            retry_count += 1
                            error_str = str(e)
                            
                            # Handle different error cases
                            if "not found" in error_str.lower() or "404" in error_str:
                                # Workspace already removed, just clear tracking
                                self.logger.info(f"Workspace {workspace_id} already removed, clearing tracking")
                                clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                                success = True
                                break
                            elif "Connection" in error_str or "Timeout" in error_str:
                                # Network errors might be temporary, retry
                                self.logger.warning(f"Network error during workspace removal: {e}, retrying...")
                            elif "Unauthorized" in error_str or "401" in str(e):
                                # Auth errors won't be fixed by retry
                                self.logger.error(f"Authentication error during workspace removal: {e}")
                                break
                            else:
                                self.logger.warning(f"Failed to remove workspace (attempt {retry_count}): {e}")
                            
                            if retry_count < max_retries:
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 1.5
                                
                    # If we've exhausted retries and still failed, log but don't raise
                    if not success and last_error:
                        self.logger.error(f"Failed to remove workspace after {max_retries} attempts: {last_error}")
                        
                        # Last-ditch effort: at least clear tracking file
                        try:
                            clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                            self.logger.info("Cleared workspace tracking file despite removal failure")
                        except Exception as tracking_error:
                            self.logger.error(f"Failed to clear tracking file: {tracking_error}")
                else:
                    self.logger.info(f"This process doesn't own the active workspace, skipping cleanup")
        except Exception as e:
            # Log lock acquisition errors but don't crash
            self.logger.error(f"Error during workspace cleanup lock acquisition: {e}", exc_info=True)
            
            # Try cleanup without lock as last resort
            try:
                self.logger.warning("Attempting cleanup without lock as fallback")
                self.daytona.remove(self.workspace)
                self.logger.info(f"Successfully removed Workspace ID: {workspace_id} without lock")
            except Exception as fallback_error:
                self.logger.error(f"Fallback cleanup also failed: {fallback_error}")
        finally:
            # Always clear this instance's references regardless of cleanup success
            self.workspace = None
            self.filesystem = None
            self.logger.debug("Cleared workspace and filesystem references")

    async def process_file_content(self, file_path: str, file_content: bytes) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
        """
        Process downloaded file content and return in appropriate format.
        """
        try:
            # If download succeeded, get the file extension
            ext = Path(file_path).suffix.lower()
            filename = Path(file_path).name

            # Log success for debugging
            self.logger.info(f"Processing file: {file_path}, size: {len(file_content)} bytes")

            # Special case: Check if this might be a JSON file containing a base64 image
            # This handles matplotlib plots saved as JSON with embedded base64 images
            if ext == '.json':
                try:
                    # Try to parse as JSON first
                    text_content = file_content.decode('utf-8')
                    json_data = json.loads(text_content)

                    # Look for a base64 image field (common pattern in matplotlib exports)
                    if isinstance(json_data, dict) and 'image' in json_data and isinstance(json_data['image'], str):
                        # This might be a matplotlib plot with embedded image
                        try:
                            # Verify it's valid base64
                            image_data = json_data['image']
                            # Try to decode a small part to validate it's base64
                            base64.b64decode(image_data[:20] + "=" * ((4 - len(image_data[:20]) % 4) % 4))

                            # If we get here, it seems to be a valid base64 string
                            self.logger.info(f"Detected JSON with embedded base64 image in {file_path}")

                            # Get metadata if available
                            metadata = json_data.get('metadata', {})
                            metadata_text = ""
                            if metadata:
                                try:
                                    # Format metadata nicely
                                    metadata_items = []
                                    if isinstance(metadata, dict):
                                        for key, value in metadata.items():
                                            if key != 'elements':  # Skip detailed elements array
                                                metadata_items.append(f"{key}: {value}")

                                        # Handle elements separately if present
                                        if 'elements' in metadata and isinstance(metadata['elements'], list):
                                            elements = metadata['elements']
                                            if elements:
                                                metadata_items.append(f"elements: [{len(elements)} items]")

                                    if metadata_items:
                                        metadata_text = "\n\nMetadata:\n" + "\n".join(metadata_items)
                                except Exception as e:
                                    self.logger.warning(f"Error formatting metadata: {e}")

                            # Return both the image and any metadata as text
                            mime_type = "image/png"  # Default for matplotlib
                            return [
                                ImageContent(type="image", data=image_data, mimeType=mime_type),
                                *([TextContent(type="text", text=metadata_text)] if metadata_text else [])
                            ]
                        except Exception as e:
                            self.logger.debug(f"Not a valid base64 image in JSON: {e}")
                            # Continue with normal JSON handling

                    # If not a special case, continue with normal text handling
                    return [TextContent(type="text", text=text_content)]
                except Exception as e:
                    self.logger.debug(f"Error parsing as JSON with image: {e}")
                    # Continue with regular file handling

            # Handle standard image files
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']
            if ext in image_extensions:
                try:
                    # Convert binary content to base64
                    base64_content = base64.b64encode(file_content).decode('utf-8')
                    # Determine MIME type based on extension
                    # Use mimetypes library to get the correct MIME type
                    mime_type = mimetypes.guess_type(file_path)[0]
                    if not mime_type:
                        # Fallback for common image types
                        mime_type = f"image/{ext[1:]}" if ext[1:] != 'svg' else "image/svg+xml"
                        if ext[1:] == 'jpg':
                            mime_type = "image/jpeg"

                    self.logger.info(f"Downloaded image file: {file_path} ({mime_type})")
                    result = [ImageContent(type="image", data=base64_content, mimeType=mime_type)]
                    # Check result is valid
                    self.logger.info(f"Created ImageContent successfully: {type(result[0])}")
                    return result
                except Exception as e:
                    self.logger.error(f"Error creating ImageContent: {e}", exc_info=True)
                    # Fallback to text description
                    return [TextContent(
                        type="text",
                        text=f"Image downloaded but could not be displayed. File: {file_path}, Size: {len(file_content)} bytes."
                    )]

            # Handle text files - try to decode as UTF-8
            try:
                # Try to decode as text
                text_content = file_content.decode('utf-8')
                self.logger.info(f"Downloaded text file: {file_path}")

                # For matplotlib plots that might be plain text with base64 content
                if len(text_content) > 1000 and 'base64' in text_content[:1000] and (
                    'matplotlib' in text_content[:1000] or 'plt' in text_content[:1000]):
                    try:
                        # Try to extract a base64 string
                        import re
                        match = re.search(r"base64,([A-Za-z0-9+/=]+)", text_content)
                        if match:
                            base64_content = match.group(1)
                            self.logger.info(f"Found embedded base64 content in text file: {file_path}")
                            return [
                                ImageContent(type="image", data=base64_content, mimeType="image/png"),
                                TextContent(type="text", text="Found embedded image in text content.")
                            ]
                    except Exception as e:
                        self.logger.debug(f"Error extracting base64 from text: {e}")
                        # Continue with normal text handling

                # Wrap the result in a try-except to avoid any unexpected errors
                try:
                    return [TextContent(type="text", text=text_content)]
                except Exception as e:
                    self.logger.error(f"Error creating TextContent: {e}", exc_info=True)
                    # Fallback to plain string with truncation
                    return [TextContent(type="text", text=f"File content (first 1000 chars): {text_content[:1000]}"+(len(text_content)>1000 and "..." or ""))]
            except UnicodeDecodeError:
                # If we can't decode as text, return as binary
                base64_content = base64.b64encode(file_content).decode('utf-8')
                # For binary files, try to return as an attachment with base64 data
                self.logger.info(f"Downloaded binary file: {file_path}")

                # For PDF and other document files
                document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
                if ext.lower() in document_extensions:
                    # Get the MIME type
                    mime_type = mimetypes.guess_type(file_path)[0]
                    if not mime_type:
                        # Default to application/octet-stream if cannot determine
                        mime_type = "application/octet-stream"

                    self.logger.info(f"Detected document file: {file_path} ({mime_type})")
                    try:
                        return [EmbeddedResource(
                            type="resource",
                            resource={
                                "uri": f"file://{file_path}",
                                "data": base64_content,
                                "mimeType": mime_type
                            }
                        )]
                    except Exception as e:
                        self.logger.error(f"Error creating EmbeddedResource: {e}", exc_info=True)
                        # Fallback to text
                        return [TextContent(
                            type="text",
                            text=f"Binary file downloaded but could not be embedded. File size: {len(file_content)} bytes."
                        )]

                # For other binary types, try to detect if it's an image based on content
                try:
                    # Check for common image headers
                    if (len(file_content) > 4 and
                        (file_content[:4] == b'\x89PNG' or  # PNG
                         file_content[:3] == b'\xff\xd8\xff' or  # JPEG
                         file_content[:4] == b'GIF8' or  # GIF
                         file_content[:2] == b'BM')):  # BMP

                        self.logger.info(f"Detected binary image file without correct extension: {file_path}")
                        # Guess mime type from headers
                        mime_type = "image/png"
                        if file_content[:3] == b'\xff\xd8\xff':
                            mime_type = "image/jpeg"
                        elif file_content[:4] == b'GIF8':
                            mime_type = "image/gif"
                        elif file_content[:2] == b'BM':
                            mime_type = "image/bmp"

                        return [ImageContent(type="image", data=base64_content, mimeType=mime_type)]
                except Exception as e:
                    self.logger.debug(f"Error detecting binary image: {e}")

                # If none of the special cases match, return generic binary message
                return [TextContent(
                    type="text",
                    text=f"Binary file downloaded but can't be displayed directly. File size: {len(file_content)} bytes."
                )]

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
            # Return error as text rather than raising an exception
            # to prevent the server from crashing
            return [TextContent(
                type="text",
                text=f"Error processing file: {str(e)}"
            )]

    async def download_file(self, file_path: str) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
        """
        Download a file from the Daytona workspace.
        Returns the file content either as text or as a base64 encoded image.
        Handles special cases like matplotlib plots stored as JSON with embedded base64 images.
        """
        if not self.workspace:
            self.logger.error("Workspace is not initialized.")
            raise RuntimeError("Workspace is not initialized.")

        try:
            # Need to check if the file exists first
            # Use the filesystem API to download the file content
            if not self.filesystem:
                self.logger.error("Filesystem is not initialized.")
                raise RuntimeError("Filesystem is not initialized.")

            # Check if file exists using a command instead of filesystem.exists()
            # which doesn't exist in the Daytona SDK
            try:
                response = self.workspace.process.exec(f"test -f {shlex.quote(file_path)} && echo 'exists' || echo 'not exists'")
                if "exists" not in str(response.result):
                    raise FileNotFoundError(f"File not found: {file_path}")
            except Exception as e:
                self.logger.warning(f"Error checking if file exists: {e}, will try to download anyway")

            file_content = self.filesystem.download_file(file_path)
            return await self.process_file_content(file_path, file_content)

        except Exception as e:
            self.logger.error(f"Error downloading file {file_path}: {e}", exc_info=True)
            # Return error as text rather than raising an exception
            # to prevent the server from crashing
            return [TextContent(
                type="text",
                text=f"Error downloading file: {str(e)}"
            )]

    async def cleanup(self) -> None:
        """
        Perform full cleanup of resources:
        1. Clean up workspace if it exists
        2. Close Daytona SDK client connection if necessary
        3. Ensure workspace tracking files are cleaned up
        """
        try:
            self.logger.info("Starting full cleanup procedure")
            await self.cleanup_workspace()

            # Attempt to clean up tracking files if we exit unexpectedly
            try:
                # Only attempt if we have an active workspace
                if self.workspace:
                    # Check if our workspace is the active one
                    active_id, _ = get_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                    if active_id == self.workspace.id:
                        # We own the tracking file, so clean it up
                        clear_active_workspace(self.filesystem if hasattr(self, 'filesystem') else None)
                        self.logger.info("Cleared workspace tracking file")
            except Exception as e:
                self.logger.warning(f"Error clearing workspace tracking: {e}")

            self.logger.info("Cleanup procedure completed")
            # Additional cleanup steps can be added here if the SDK requires
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)
            # Don't raise the exception to prevent crashes

    async def run(self) -> None:
        """
        Main server execution loop:
        1. Initialize workspace
        2. Run MCP server with stdio communication
        3. Handle cleanup on shutdown
        """
        try:
            # Before initializing a workspace, check if we have any existing ones and clean up
            # This helps prevent multiple sandbox issues
            try:
                # List and clean up existing workspaces
                workspaces = self.daytona.list()
                if len(workspaces) > 0:
                    self.logger.info(f"Found {len(workspaces)} existing workspaces at startup, cleaning up")
                    for workspace in workspaces:
                        try:
                            self.logger.info(f"Removing existing workspace: {workspace.id}")
                            self.daytona.remove(workspace)
                        except Exception as e:
                            self.logger.warning(f"Error removing workspace {workspace.id}: {e}")
            except Exception as e:
                self.logger.warning(f"Error listing/cleaning workspaces at startup: {e}")

            # Only initialize workspace once at the beginning of the run
            # and don't initialize workspace in each stdio_server context
            try:
                await self.initialize_workspace()
            except Exception as e:
                # Special handling for quota errors to make them more visible
                if "CPU quota exceeded" in str(e):
                    error_message = [
                        "\n\n======= DAYTONA ERROR =======",
                        "CPU quota exceeded on Daytona server. To resolve this issue:",
                        "1. Log into your Daytona account and delete unused workspaces",
                        "2. Or upgrade your Daytona plan for higher CPU quota"
                    ]

                    # Try automatic cleanup of old workspaces first
                    try:
                        error_message.append("\nAttempting automatic cleanup of workspaces older than 1 day...")
                        cleaned, errors, remaining = cleanup_stale_workspaces(self.daytona, max_age_days=1, logger=self.logger)

                        if cleaned > 0:
                            error_message.append(f"Successfully cleaned up {cleaned} old workspaces.")
                            error_message.append("Retrying workspace creation...")

                            # Try again to create the workspace
                            try:
                                await self.initialize_workspace()
                                error_message.append("Workspace created successfully after cleanup!")
                                error_message.append("============================\n")
                                print("\n".join(error_message), file=sys.stderr)
                                # If we reach here, we succeeded - continue with the run
                                self.logger.info("Workspace initialization succeeded after cleanup")
                                # Skip straight to server startup
                            except Exception as retry_error:
                                error_message.append(f"Retry failed after cleanup: {retry_error}")
                                # Continue with normal error flow
                        else:
                            error_message.append(f"No old workspaces found to clean up ({remaining} workspaces remain).")
                    except Exception as cleanup_error:
                        error_message.append(f"Automatic cleanup failed: {cleanup_error}")

                    # If we're still here, the initialization failed even after cleanup
                    # Try to list existing workspaces to help user identify what to clean up manually
                    try:
                        workspaces = self.daytona.list()
                        if workspaces:
                            error_message.append("\nExisting workspaces:")
                            for ws in workspaces:
                                created_info = ""
                                if hasattr(ws, 'created_at'):
                                    if isinstance(ws.created_at, (int, float)):
                                        # Convert timestamp to readable date
                                        from datetime import datetime
                                        created_info = datetime.fromtimestamp(ws.created_at).strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        created_info = str(ws.created_at)
                                error_message.append(f"- {ws.id} (created: {created_info or 'unknown'})")
                    except Exception as list_error:
                        self.logger.warning(f"Failed to list workspaces: {list_error}")
                        error_message.append("\nCould not list existing workspaces due to an error.")

                    error_message.append("============================\n")
                    full_message = "\n".join(error_message)
                    print(full_message, file=sys.stderr)  # Print to stderr for visibility
                    self.logger.error(full_message)

                    # Only re-raise if we don't have a workspace (meaning cleanup didn't work)
                    if not self.workspace:
                        raise
                else:
                    # For non-quota errors, always re-raise
                    raise

            # Now run the MCP server
            async with stdio_server() as streams:
                try:
                    # Add additional debug logging for server lifetime
                    self.logger.info("Starting MCP server with stdio communication")

                    # Create a keep-alive task that periodically logs to keep connection alive
                    async def keep_alive():
                        while True:
                            try:
                                await asyncio.sleep(30)  # Log every 30 seconds
                                self.logger.debug("Server keep-alive ping")
                            except asyncio.CancelledError:
                                self.logger.debug("Keep-alive task cancelled")
                                break

                    # Start the keep-alive task
                    keep_alive_task = asyncio.create_task(keep_alive())

                    try:
                        await self.server.run(
                            streams[0],
                            streams[1],
                            self.server.create_initialization_options()
                        )
                    finally:
                        # Make sure to cancel the keep-alive task
                        keep_alive_task.cancel()
                        # No need to await the cancelled task, it's causing BrokenResourceError
                        # when the underlying stream is already closed

                except BaseExceptionGroup as e:
                    # Handle ExceptionGroup (introduced in Python 3.11)
                    if any(isinstance(exc, asyncio.CancelledError) for exc in e.exceptions):
                        self.logger.info("Server was cancelled")
                    elif any(isinstance(exc, (BrokenPipeError, ConnectionResetError)) or hasattr(exc, '__class__') and 'BrokenResourceError' in exc.__class__.__name__ for exc in e.exceptions):
                        self.logger.info("Client disconnected unexpectedly")
                    elif any("notifications/cancelled" in str(exc) for exc in e.exceptions):
                        self.logger.info("Server received cancel notification, handling gracefully")
                    elif any("ValidationError" in str(exc) for exc in e.exceptions):
                        self.logger.info("Encountered validation error in notification handling, continuing")
                    else:
                        # Just log the error but don't re-raise it to prevent crashes
                        filtered_exceptions = [exc for exc in e.exceptions if not (
                            hasattr(exc, '__class__') and 'BrokenResourceError' in exc.__class__.__name__
                        )]
                        if filtered_exceptions:
                            self.logger.error(f"Server error during run: {e}", exc_info=True)
                        else:
                            self.logger.info("Server shutdown initiated due to connection close")
                except asyncio.CancelledError:
                    self.logger.info("Server task was cancelled")
                except BrokenPipeError:
                    self.logger.info("Client pipe was broken")
                except ConnectionResetError:
                    self.logger.info("Connection was reset by peer")
                except Exception as e:
                    # Check for anyio BrokenResourceError by name to avoid import dependencies
                    if hasattr(e, '__class__') and 'BrokenResourceError' in e.__class__.__name__:
                        self.logger.info("Client resource was broken or closed")
                    else:
                        self.logger.error(f"Unhandled exception in MCP server: {e}", exc_info=True)
                finally:
                    self.logger.info("MCP server shutdown initiated, starting cleanup")
                    await self.cleanup()
                    self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Server error during run: {e}", exc_info=True)
            await self.cleanup()
            # Don't re-raise the exception to prevent crashing the process
            # Just log it and exit gracefully

# Global variable to track interpreter instance within a process
_interpreter_instance = None

class FileLock:
    """Simple file-based lock for inter-process coordination."""
    def __init__(self, lock_file, timeout_seconds=10):
        self.lock_file = lock_file
        self.lock_fd = None
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger("daytona-interpreter")

    def acquire(self):
        """Acquire the lock. Returns True if successful, False otherwise."""
        start_time = time.time()

        # Keep trying until we get the lock or timeout
        while time.time() - start_time < self.timeout_seconds:
            try:
                # Create lock directory if it doesn't exist, with permissive permissions
                lock_dir = os.path.dirname(self.lock_file)
                try:
                    os.makedirs(lock_dir, mode=0o777, exist_ok=True)
                except Exception as e:
                    self.logger.warning(f"Failed to create lock directory with permissions: {e}")
                    # Try again without setting permissions
                    os.makedirs(lock_dir, exist_ok=True)

                # Open the lock file exclusively
                self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                # Write the current process ID
                os.write(self.lock_fd, str(os.getpid()).encode())
                return True
            except (OSError, IOError):
                # Another process already has the lock, wait a bit and retry
                self.logger.debug(f"Lock file {self.lock_file} is held by another process, waiting...")
                time.sleep(0.5)

                # Check if the lock file still exists - might have been released
                if not os.path.exists(self.lock_file):
                    self.logger.debug("Lock file no longer exists, will retry")
                    continue

                # Check if the lock is stale (older than 60 seconds)
                try:
                    lock_stat = os.stat(self.lock_file)
                    if time.time() - lock_stat.st_mtime > 60:
                        self.logger.warning(f"Found stale lock file (over 60s old), removing")
                        try:
                            os.unlink(self.lock_file)
                            continue  # retry immediately
                        except:
                            pass  # If we can't remove it, just wait and retry normally
                except:
                    pass  # If we can't stat the file, just wait and retry

        self.logger.warning(f"Failed to acquire lock after {self.timeout_seconds} seconds")
        return False

    def release(self):
        """Release the lock if held."""
        if self.lock_fd is not None:
            os.close(self.lock_fd)
            try:
                os.unlink(self.lock_file)
            except (OSError, IOError):
                pass  # Lock file already gone
            self.lock_fd = None

    def __enter__(self):
        # Only return self if lock was successfully acquired
        if not self.acquire():
            # Wait and retry a few times
            for _ in range(3):
                time.sleep(0.2)
                if self.acquire():
                    break
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def get_content_type(file_path: str) -> str:
    """Determine the content type of a file based on its extension."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    # Default content types for common extensions
    ext = os.path.splitext(file_path.lower())[1]
    content_types = {
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.json': 'application/json',
        '.py': 'text/x-python',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.zip': 'application/zip',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
    }

    return content_types.get(ext, 'application/octet-stream')

def preview_link_generator(port: int, description: str = "", check_server: bool = True):
    """
    Generate a preview link for a web server running inside the Daytona workspace.
    Used by the web_preview tool.

    Args:
        port: The port number the server is running on
        description: Optional description of the server
        check_server: Whether to check if the server is running (default: True)

    Returns:
        Dict containing preview link information
    """
    try:
        logger = logging.getLogger("daytona-interpreter")
        logger.info(f"Generating preview link for port {port}")

        # Initialize Daytona using the current interpreter's instance if possible
        global _interpreter_instance
        if _interpreter_instance and _interpreter_instance.workspace:
            logger.info("Using existing workspace from interpreter instance")
            workspace = _interpreter_instance.workspace
        else:
            logger.info("Creating new Daytona workspace")
            daytona = Daytona()
            workspace = daytona.create()

        # Check if the server is running on the specified port
        if check_server:
            logger.info(f"Checking if server is running on port {port}")
            check_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port} --max-time 2 || echo 'error'"
            check_result = workspace.process.exec(check_cmd)
            response = str(check_result.result).strip()

            # If we can't connect or get an error response
            if response == 'error' or response.startswith('0'):
                logger.warning(f"No server detected on port {port}")

                # Check what might be using the port
                ps_cmd = f"ps aux | grep ':{port}' | grep -v grep || echo 'No process found'"
                ps_result = workspace.process.exec(ps_cmd)
                process_info = str(ps_result.result).strip()

                return {
                    "success": False,
                    "error": f"No server detected on port {port}. Please make sure your server is running.",
                    "port": port,
                    "process_info": process_info
                }

        # Extract the necessary domain information from workspace metadata
        try:
            # Extract node domain from provider metadata (JSON)
            node_domain = json.loads(workspace.instance.info.provider_metadata)['nodeDomain']

            # Format the preview URL
            preview_url = f"http://{port}-{workspace.id}.{node_domain}"

            # Test that the URL is accessible via curl with timeout
            if check_server:
                # Test via port forwarding to make sure it's accessible
                check_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {preview_url} --max-time 3 || echo 'error'"
                check_result = workspace.process.exec(check_cmd)
                response = str(check_result.result).strip()

                accessible = response != 'error' and not response.startswith('0')
                status_code = response if response.isdigit() else None

                logger.info(f"Preview URL {preview_url} check result: {response}")
            else:
                accessible = None
                status_code = None

            # Return the formatted preview URL and metadata
            return {
                "success": True,
                "preview_url": preview_url,
                "port": port,
                "workspace_id": workspace.id,
                "node_domain": node_domain,
                "description": description,
                "accessible": accessible,
                "status_code": status_code
            }
        except Exception as e:
            logger.error(f"Error extracting domain information: {e}")

            # Try alternate method to get domain info
            try:
                # Extract from workspace info
                workspace_info = workspace.info()
                domains_info = str(workspace_info)

                # Look for domain pattern in the info
                import re
                domain_match = re.search(r'domain[\'"]?\s*:\s*[\'"]([^"\'\s]+)[\'"]', domains_info)
                if domain_match:
                    node_domain = domain_match.group(1)
                    preview_url = f"http://{port}-{workspace.id}.{node_domain}"

                    return {
                        "success": True,
                        "preview_url": preview_url,
                        "port": port,
                        "workspace_id": workspace.id,
                        "node_domain": node_domain,
                        "description": description,
                        "note": "Domain extracted using fallback method"
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback domain extraction failed: {fallback_error}")

            return {
                "success": False,
                "error": f"Failed to generate preview link: {str(e)}",
                "port": port
            }
    except Exception as e:
        logger.error(f"Error generating preview link: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "port": port
        }

def git_repo_cloner(repo_url: str, target_path: str = None, branch: str = None, depth: int = 1, lfs: bool = False):
    """
    Clone a Git repository into the Daytona workspace.
    Used by the git_clone tool.

    Args:
        repo_url: The URL of the Git repository to clone (https or ssh)
        target_path: Target directory to clone into (default: repository name)
        branch: Branch to checkout (default: repository default branch)
        depth: Depth of history to clone (default: 1 for shallow clone)
        lfs: Whether to enable Git LFS (default: False)

    Returns:
        Dict containing clone operation results and file list
    """
    try:
        logger = logging.getLogger("daytona-interpreter")
        logger.info(f"Cloning Git repository: {repo_url}")

        # Initialize Daytona using the current interpreter's instance if possible
        global _interpreter_instance
        if _interpreter_instance and _interpreter_instance.workspace:
            logger.info("Using existing workspace from interpreter instance")
            workspace = _interpreter_instance.workspace
        else:
            logger.info("Creating new Daytona workspace")
            daytona = Daytona()
            workspace = daytona.create()

        # Extract repo name from URL for default target path
        import re
        repo_name = re.search(r"([^/]+)(?:\.git)?$", repo_url)
        if repo_name:
            repo_name = repo_name.group(1)
        else:
            repo_name = "repo"

        # Use provided target path or default to repo name
        target_dir = target_path or repo_name

        # Prepare the git clone command
        clone_cmd = f"git clone"

        # Add depth parameter for shallow clone if specified
        if depth > 0:
            clone_cmd += f" --depth {depth}"

        # Add branch parameter if specified
        if branch:
            clone_cmd += f" --branch {branch}"

        # Add the repository URL
        clone_cmd += f" {shlex.quote(repo_url)}"

        # Add target directory if it's not the default
        if target_path:
            clone_cmd += f" {shlex.quote(target_path)}"

        # Execute the clone command
        logger.info(f"Executing git clone command: {clone_cmd}")
        clone_result = workspace.process.exec(clone_cmd, timeout=180)  # Longer timeout for large repos

        # Check if clone was successful
        if clone_result.exit_code != 0:
            logger.error(f"Git clone failed with exit code {clone_result.exit_code}")
            return {
                "success": False,
                "error": f"Git clone failed: {clone_result.result}",
                "exit_code": clone_result.exit_code
            }

        # If Git LFS is enabled, fetch LFS content
        if lfs:
            logger.info("Git LFS enabled, fetching LFS content")
            try:
                # Move into the cloned directory
                cd_cmd = f"cd {shlex.quote(target_dir)}"

                # Setup and pull LFS content
                lfs_cmd = f"{cd_cmd} && git lfs install && git lfs pull"
                lfs_result = workspace.process.exec(lfs_cmd, timeout=180)

                if lfs_result.exit_code != 0:
                    logger.warning(f"Git LFS pull had issues: {lfs_result.result}")
            except Exception as e:
                logger.warning(f"Error with Git LFS: {e}")

        # List files in the cloned repository
        try:
            ls_cmd = f"find {shlex.quote(target_dir)} -type f -not -path '*/\\.git/*' | sort | head -n 100"
            ls_result = workspace.process.exec(ls_cmd)
            file_list = str(ls_result.result).strip().split('\n')

            # Get repository info
            info_cmd = f"cd {shlex.quote(target_dir)} && git log -1 --pretty=format:'%h %an <%ae> %ad %s' && echo '' && git branch -v"
            info_result = workspace.process.exec(info_cmd)
            repo_info = str(info_result.result).strip()

            # Count total files
            count_cmd = f"find {shlex.quote(target_dir)} -type f -not -path '*/\\.git/*' | wc -l"
            count_result = workspace.process.exec(count_cmd)
            total_files = int(str(count_result.result).strip())

            return {
                "success": True,
                "repository": repo_url,
                "target_directory": target_dir,
                "branch": branch,
                "depth": depth,
                "files_sample": file_list[:100],  # Limit to first 100 files
                "total_files": total_files,
                "repository_info": repo_info,
                "message": f"Repository cloned successfully into {target_dir}"
            }
        except Exception as e:
            logger.error(f"Error listing repository files: {e}")
            return {
                "success": True,
                "repository": repo_url,
                "target_directory": target_dir,
                "error_listing_files": str(e),
                "message": f"Repository cloned successfully into {target_dir}, but error listing files"
            }

    except Exception as e:
        logger.error(f"Error cloning repository: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "repository": repo_url
        }


def file_uploader(file_path: str, content: str, encoding: str = "text", overwrite: bool = True):
    """
    Upload files to Daytona workspace.
    Used by the file_upload tool.

    Args:
        file_path: Path where the file should be created in the workspace
        content: Content to write to the file (text or base64-encoded binary)
        encoding: Encoding of the content: 'text' (default) or 'base64'
        overwrite: Whether to overwrite the file if it already exists (default: True)

    Returns:
        Dict containing upload status and any error messages
    """
    try:
        logger = logging.getLogger("daytona-interpreter")
        logger.info(f"Uploading file: {file_path}, encoding: {encoding}")

        # Get workspace from the tracking file
        try:
            # Initialize Daytona SDK
            config = Config()
            daytona = Daytona(
                config=DaytonaConfig(
                    api_key=config.api_key,
                    server_url=config.server_url,
                    target=config.target
                )
            )
            
            # First, try to use the FileSystem from an existing interpreter instance
            global _interpreter_instance
            if _interpreter_instance and _interpreter_instance.workspace and _interpreter_instance.filesystem:
                logger.info("Using existing workspace from interpreter instance")
                workspace = _interpreter_instance.workspace
            else:
                # Get workspace ID from tracking file
                workspace_id, _ = get_active_workspace()
                
                if not workspace_id:
                    return {
                        "success": False,
                        "error": "No workspace ID found in tracking file"
                    }
                
                # Get the current workspace using workspace ID
                all_workspaces = daytona.list()
                workspace = None
                for ws in all_workspaces:
                    if ws.id == workspace_id:
                        workspace = ws
                        break
        except Exception as e:
            logger.error(f"Error getting workspace: {e}")
            return {
                "success": False,
                "error": f"Failed to get workspace: {str(e)}"
            }
            
        if not workspace:
            return {
                "success": False,
                "error": "No workspace available"
            }

        # Get file system instance from workspace
        fs = workspace.fs

        # Check if file exists
        if not overwrite:
            try:
                # Try to check file info, which will raise an exception if file doesn't exist
                # Use get_file_info instead of stat (which doesn't exist in the FileSystem class)
                fs.get_file_info(file_path)
                return {
                    "success": False,
                    "error": f"File '{file_path}' already exists and overwrite=False"
                }
            except Exception:
                # File doesn't exist, which is good in this case
                pass

        # Prepare content based on encoding
        if encoding.lower() == "base64":
            try:
                # Decode base64 content
                binary_content = base64.b64decode(content)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Invalid base64 encoding: {str(e)}"
                }
        else:
            # Default is text encoding
            binary_content = content.encode('utf-8')

        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            try:
                # The SDK will create parent directories as needed, but we'll check first
                if not fs.dir_exists(parent_dir):
                    fs.create_folder(parent_dir)
            except Exception as e:
                logger.warning(f"Error checking/creating parent directory: {e}")
                # Continue anyway, as upload_file might handle this

        # Upload the file
        fs.upload_file(file_path, binary_content)

        # Get file size for information
        file_info = fs.get_file_info(file_path)
        file_size = file_info.size  # The size attribute in FileInfo class
        file_size_kb = file_size / 1024

        return {
            "success": True,
            "message": f"File uploaded successfully: {file_path} ({file_size_kb:.2f} KB)",
            "file_path": file_path,
            "file_size_bytes": file_size
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }

def file_downloader(path: str, max_size_mb: float = 5.0, download_option: str = None, chunk_size_kb: int = 100):
    """
    Download files from Daytona workspace with advanced handling for large files.
    Used by the file_download tool.

    Args:
        path: Path to the file in the Daytona workspace
        max_size_mb: Maximum file size in MB to download automatically
        download_option: Option to handle large files: 'download_partial', 'convert_to_text', 'compress_file', or None
        chunk_size_kb: Size of each chunk in KB when downloading partially

    Returns:
        Dict containing file content and metadata or download options
        
    Raises:
        FileNotAccessibleError: When the file cannot be accessed
        FileTooLargeError: When file exceeds size limits without download option
        FileSystemError: For filesystem-related errors
        NetworkError: For network-related errors
    """
    logger = logging.getLogger("daytona-interpreter")
    logger.info(f"Downloading file: {path}, max_size: {max_size_mb}MB, option: {download_option}")
    
    workspace = None
    filesystem = None
    needs_cleanup = False
    daytona = None
    
    try:
        # Validate inputs
        if not path:
            raise ValueError("File path is required")
        if max_size_mb <= 0:
            logger.warning(f"Invalid max_size_mb value: {max_size_mb}, using default of 5.0")
            max_size_mb = 5.0
        if chunk_size_kb <= 0:
            logger.warning(f"Invalid chunk_size_kb value: {chunk_size_kb}, using default of 100")
            chunk_size_kb = 100
        if download_option and download_option not in ["download_partial", "convert_to_text", "compress_file", "force_download"]:
            logger.warning(f"Unrecognized download option: {download_option}")
            
        # Initialize Daytona using the current interpreter's instance if possible
        global _interpreter_instance
        if _interpreter_instance and _interpreter_instance.workspace and _interpreter_instance.filesystem:
            logger.info("Using existing workspace from interpreter instance")
            workspace = _interpreter_instance.workspace
            filesystem = _interpreter_instance.filesystem
            needs_cleanup = False
        else:
            try:
                logger.info("Creating new Daytona workspace")
                daytona = Daytona()
                try:
                    workspace = daytona.create()
                    filesystem = workspace.fs
                    needs_cleanup = True
                except Exception as create_err:
                    error_str = str(create_err)
                    if "Total CPU quota exceeded" in error_str or "quota" in error_str.lower():
                        raise WorkspaceQuotaExceededError(f"CPU quota exceeded when creating workspace for file download: {error_str}")
                    elif "Connection" in error_str or "Timeout" in error_str:
                        raise NetworkError(f"Network error when creating workspace for file download: {error_str}")
                    elif "Unauthorized" in error_str or "401" in str(create_err):
                        raise NetworkError("Authentication failed when creating workspace for file download")
                    else:
                        raise WorkspaceInitializationError(f"Failed to create workspace for file download: {error_str}")
            except (WorkspaceQuotaExceededError, NetworkError, WorkspaceInitializationError) as specific_error:
                # Re-raise specific exceptions 
                logger.error(f"Error creating workspace: {specific_error}")
                return {
                    "success": False,
                    "error": str(specific_error),
                    "error_type": specific_error.__class__.__name__,
                    "file_path": path
                }

        # First check if file exists and get file info using Daytona FileSystem
        try:
            # Use filesystem.get_file_info to check if file exists and get size information
            try:
                file_info = filesystem.get_file_info(path)
                logger.info(f"File exists: {path}")
            except Exception as fs_err:
                if "not found" in str(fs_err).lower() or "not exist" in str(fs_err).lower():
                    raise FileNotAccessibleError(f"File not found: {path}")
                elif "permission" in str(fs_err).lower():
                    raise FileNotAccessibleError(f"Permission denied accessing file: {path}")
                else:
                    logger.warning(f"Error accessing file with FileSystem API: {fs_err}")
                    raise FileSystemError(f"Error accessing file with FileSystem API: {fs_err}")
            
            # Get additional information with process.exec for backward compatibility
            try:
                # Get mime type
                mime_cmd = f"file --mime-type -b {shlex.quote(path)}"
                mime_result = workspace.process.exec(mime_cmd)
                mime_type = str(mime_result.result).strip()
                
                # Set complete file info
                file_info = {
                    "name": os.path.basename(path),
                    "size": file_info.size,  # Use size from FileSystem's get_file_info
                    "mime_type": mime_type
                }
                logger.debug(f"Enhanced file info with MIME type: {mime_type}")
            except Exception as e:
                # If getting additional info fails, create minimal file_info dict
                logger.warning(f"Error getting additional file info: {e}")
                file_info = {
                    "name": os.path.basename(path),
                    "size": file_info.size
                }
            
            logger.info(f"File info: {file_info}")
            
        except (FileNotAccessibleError, FileSystemError) as specific_error:
            # First try with process.exec as fallback
            logger.warning(f"Using process.exec fallback for file check: {specific_error}")
            
            try:
                # Check if file exists
                response = workspace.process.exec(f"test -f {shlex.quote(path)} && echo 'exists' || echo 'not exists'")
                if "exists" not in str(response.result):
                    if needs_cleanup and daytona and workspace:
                        try:
                            daytona.remove(workspace)
                        except Exception as cleanup_err:
                            logger.warning(f"Error cleaning up workspace: {cleanup_err}")
                    
                    raise FileNotAccessibleError(f"File not found: {path}")
                    
                # Get file size using stat command
                try:
                    size_cmd = f"stat -f %z {shlex.quote(path)}"
                    size_result = workspace.process.exec(size_cmd)
                    file_size = int(str(size_result.result).strip())
                except Exception:
                    # Try Linux stat format as fallback
                    try:
                        size_cmd = f"stat -c %s {shlex.quote(path)}"
                        size_result = workspace.process.exec(size_cmd)
                        file_size = int(str(size_result.result).strip())
                    except Exception as stat_err:
                        logger.error(f"Failed to get file size: {stat_err}")
                        raise FileSystemError(f"Failed to get file size: {stat_err}")
                
                # Get mime type
                try:
                    mime_cmd = f"file --mime-type -b {shlex.quote(path)}"
                    mime_result = workspace.process.exec(mime_cmd)
                    mime_type = str(mime_result.result).strip()
                except Exception:
                    # Default mime type based on extension
                    mime_type = get_content_type(path)
                
                file_info = {
                    "name": os.path.basename(path),
                    "size": file_size,
                    "mime_type": mime_type
                }
                logger.info(f"File info (via exec): {file_info}")
            except (FileNotAccessibleError, FileSystemError) as exec_error:
                # Cleanup on error
                if needs_cleanup and daytona and workspace:
                    try:
                        daytona.remove(workspace)
                    except Exception as cleanup_err:
                        logger.warning(f"Error cleaning up workspace: {cleanup_err}")
                        
                # Re-raise with more context
                return {
                    "success": False,
                    "error": str(exec_error),
                    "error_type": exec_error.__class__.__name__,
                    "file_path": path
                }
            except Exception as e:
                logger.error(f"File does not exist or cannot be accessed: {e}")
                
                # Cleanup on error
                if needs_cleanup and daytona and workspace:
                    try:
                        daytona.remove(workspace)
                    except Exception as cleanup_err:
                        logger.warning(f"Error cleaning up workspace: {cleanup_err}")
                
                return {
                    "success": False,
                    "error": f"File not found or inaccessible: {path}",
                    "error_type": "FileNotAccessibleError",
                    "file_path": path
                }

        # Calculate size in MB
        size_mb = file_info["size"] / (1024 * 1024) if isinstance(file_info, dict) else file_info.size / (1024 * 1024)
        logger.info(f"File size: {size_mb:.2f}MB")

        # If file is too large and no download option is specified, offer options
        if size_mb > max_size_mb and download_option is None:
            options = {
                "success": True,
                "file_too_large": True,
                "file_size_mb": round(size_mb, 2),
                "max_size_mb": max_size_mb,
                "file_path": path,
                "filename": os.path.basename(path),
                "content_type": get_content_type(path),
                "options": [
                    "download_partial",
                    "convert_to_text",
                    "compress_file",
                    "force_download"
                ],
                "message": f"File is {round(size_mb, 2)}MB which exceeds the {max_size_mb}MB limit. Choose an option to proceed."
            }

            # Clean up if needed
            if needs_cleanup and daytona and workspace:
                try:
                    daytona.remove(workspace)
                    logger.info("Cleaned up temporary workspace")
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")

            return options

        # Process according to download option for large files
        if size_mb > max_size_mb and download_option:
            if download_option == "download_partial":
                # Download first chunk of the file using combined approach
                chunk_size_bytes = chunk_size_kb * 1024
                
                try:
                    # Try to get a chunk using filesystem API if available
                    # Since FileSystem doesn't have a direct partial download method,
                    # we'll use process.exec to create a temporary file with the chunk
                    temp_chunk_path = f"/tmp/chunk_{uuid.uuid4()}.tmp"
                    
                    try:
                        # Create the chunk
                        workspace.process.exec(f"head -c {chunk_size_bytes} {shlex.quote(path)} > {temp_chunk_path}")
                        
                        # Use filesystem to download the chunk
                        content = filesystem.download_file(temp_chunk_path)
                        
                        # Remove temp file
                        workspace.process.exec(f"rm {temp_chunk_path}")
                    except Exception as e:
                        logger.warning(f"Error using filesystem for partial download: {e}, falling back to process.exec")
                        # Fallback to direct base64 encoding
                        head_cmd = f"head -c {chunk_size_bytes} {shlex.quote(path)} | base64"
                        head_result = workspace.process.exec(head_cmd)
                        
                        # Decode base64 content
                        content_b64 = str(head_result.result).strip()
                        content = base64.b64decode(content_b64)

                    # Clean up if needed
                    if needs_cleanup and daytona and workspace:
                        try:
                            daytona.remove(workspace)
                        except Exception as cleanup_err:
                            logger.warning(f"Error cleaning up workspace: {cleanup_err}")

                    return {
                        "success": True,
                        "filename": os.path.basename(path),
                        "content_type": get_content_type(path),
                        "size": file_info["size"] if isinstance(file_info, dict) else file_info.size,
                        "content": content,
                        "partial": True,
                        "downloaded_bytes": len(content),
                        "total_bytes": file_info["size"] if isinstance(file_info, dict) else file_info.size,
                        "message": f"Downloaded first {chunk_size_kb}KB of file."
                    }
                except Exception as partial_err:
                    logger.error(f"Error downloading partial file: {partial_err}")
                    
                    # Cleanup on error
                    if needs_cleanup and daytona and workspace:
                        try:
                            daytona.remove(workspace)
                        except Exception as cleanup_err:
                            logger.warning(f"Error cleaning up workspace: {cleanup_err}")
                    
                    return {
                        "success": False,
                        "error": f"Error downloading partial file: {str(partial_err)}",
                        "error_type": "FileSystemError" if isinstance(partial_err, FileSystemError) else "DownloadError",
                        "file_path": path
                    }

            elif download_option == "convert_to_text":
                # Try to convert file to text (works best for PDFs, code files, etc.)
                try:
                    # Check file type and use appropriate conversion method
                    if path.lower().endswith('.pdf'):
                        # Try to extract text from PDF
                        text_cmd = f"pdftotext {shlex.quote(path)} - 2>/dev/null || echo 'PDF text extraction failed'"
                        text_result = workspace.process.exec(text_cmd)
                        content = str(text_result.result).encode('utf-8')
                    else:
                        # For other files, try to extract as text
                        text_cmd = f"cat {shlex.quote(path)} | head -c 100000"
                        text_result = workspace.process.exec(text_cmd)
                        content = str(text_result.result).encode('utf-8')

                    # Clean up if needed
                    if needs_cleanup and daytona and workspace:
                        try:
                            daytona.remove(workspace)
                        except Exception as cleanup_err:
                            logger.warning(f"Error cleaning up workspace: {cleanup_err}")

                    return {
                        "success": True,
                        "filename": os.path.basename(path),
                        "content_type": "text/plain",
                        "size": len(content),
                        "content": content,
                        "converted": True,
                        "original_size": file_info["size"] if isinstance(file_info, dict) else file_info.size,
                        "message": "File was converted to text format."
                    }
                except Exception as convert_err:
                    logger.error(f"Error converting to text: {convert_err}")
                    
                    # Cleanup on error
                    if needs_cleanup and daytona and workspace:
                        try:
                            daytona.remove(workspace)
                        except Exception as cleanup_err:
                            logger.warning(f"Error cleaning up workspace: {cleanup_err}")
                    
                    return {
                        "success": False,
                        "error": f"Error converting file to text: {str(convert_err)}",
                        "error_type": "FileSystemError" if isinstance(convert_err, FileSystemError) else "ConversionError",
                        "file_path": path
                    }

            elif download_option == "compress_file":
                # Compress the file before downloading
                try:
                    temp_path = f"/tmp/compressed_{uuid.uuid4().hex}.gz"
                    compress_cmd = f"gzip -c {shlex.quote(path)} > {temp_path}"
                    workspace.process.exec(compress_cmd)

                    # Get compressed file size
                    try:
                        size_cmd = f"stat -f %z {temp_path}"
                        size_result = workspace.process.exec(size_cmd)
                        compressed_size = int(str(size_result.result).strip())
                    except Exception:
                        # Try Linux stat format as fallback
                        size_cmd = f"stat -c %s {temp_path}"
                        size_result = workspace.process.exec(size_cmd)
                        compressed_size = int(str(size_result.result).strip())

                    # Download the compressed file
                    if hasattr(filesystem, 'download_file'):
                        content = filesystem.download_file(temp_path)
                    else:
                        # Fallback to base64 encoding
                        cat_cmd = f"cat {temp_path} | base64"
                        cat_result = workspace.process.exec(cat_cmd)
                        content = base64.b64decode(str(cat_result.result).strip())

                    # Clean up temporary file
                    try:
                        workspace.process.exec(f"rm {temp_path}")
                    except Exception as rm_err:
                        logger.warning(f"Error removing temporary file: {rm_err}")

                    # Clean up workspace if needed
                    if needs_cleanup and daytona and workspace:
                        try:
                            daytona.remove(workspace)
                        except Exception as cleanup_err:
                            logger.warning(f"Error cleaning up workspace: {cleanup_err}")

                    return {
                        "success": True,
                        "filename": f"{os.path.basename(path)}.gz",
                        "content_type": "application/gzip",
                        "size": compressed_size,
                        "content": content,
                        "compressed": True,
                        "original_size": file_info["size"] if isinstance(file_info, dict) else file_info.size,
                        "compression_ratio": round(compressed_size / (file_info["size"] if isinstance(file_info, dict) else file_info.size), 2),
                        "message": f"File was compressed before download. Original: {size_mb:.2f}MB, Compressed: {compressed_size/(1024*1024):.2f}MB"
                    }
                except Exception as compress_err:
                    logger.error(f"Error compressing file: {compress_err}")
                    
                    # Cleanup on error
                    if needs_cleanup and daytona and workspace:
                        try:
                            daytona.remove(workspace)
                        except Exception as cleanup_err:
                            logger.warning(f"Error cleaning up workspace: {cleanup_err}")
                    
                    return {
                        "success": False,
                        "error": f"Error compressing file: {str(compress_err)}",
                        "error_type": "FileSystemError" if isinstance(compress_err, FileSystemError) else "CompressionError",
                        "file_path": path
                    }

            elif download_option == "force_download":
                # Force download despite size
                logger.info(f"Forcing download of large file: {path}")
                # Fall through to regular download
            else:
                return {
                    "success": False,
                    "error": f"Unknown download option: {download_option}",
                    "options": ["download_partial", "convert_to_text", "compress_file", "force_download"],
                    "error_type": "InvalidOptionError"
                }

        # Download the file normally
        try:
            # Download using Daytona FileSystem API
            content = filesystem.download_file(path)

            logger.info(f"Successfully downloaded file: {path}, size: {len(content)} bytes")

            # Clean up if needed
            if needs_cleanup and daytona and workspace:
                try:
                    daytona.remove(workspace)
                    logger.info("Cleaned up temporary workspace")
                except Exception as cleanup_err:
                    logger.warning(f"Error cleaning up workspace: {cleanup_err}")

            # Return metadata along with content
            return {
                "success": True,
                "filename": os.path.basename(path),
                "content_type": get_content_type(path),
                "size": len(content),
                "content": content,
                "message": f"Successfully downloaded file ({len(content)/1024:.1f}KB)"
            }
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            
            # Cleanup on error
            if needs_cleanup and daytona and workspace:
                try:
                    daytona.remove(workspace)
                except Exception as cleanup_err:
                    logger.warning(f"Error cleaning up workspace: {cleanup_err}")
            
            error_type = "FileSystemError"
            if "permission" in str(e).lower():
                error_type = "FileNotAccessibleError"
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                error_type = "NetworkError"
            
            return {
                "success": False,
                "error": f"Error downloading file: {str(e)}",
                "error_type": error_type,
                "file_path": path
            }

    except Exception as e:
        logger.error(f"File download failed: {e}", exc_info=True)
        
        # Cleanup on error
        if needs_cleanup and daytona and workspace:
            try:
                daytona.remove(workspace)
            except Exception as cleanup_err:
                logger.warning(f"Error cleaning up workspace during exception handling: {cleanup_err}")
        
        error_type = "UnknownError"
        if isinstance(e, FileNotAccessibleError):
            error_type = "FileNotAccessibleError"
        elif isinstance(e, FileTooLargeError):
            error_type = "FileTooLargeError"
        elif isinstance(e, FileSystemError):
            error_type = "FileSystemError"
        elif isinstance(e, NetworkError):
            error_type = "NetworkError"
        elif isinstance(e, WorkspaceError):
            error_type = "WorkspaceError"
        
        return {
            "success": False,
            "error": str(e),
            "error_type": error_type,
            "file_path": path
        }

def get_active_workspace(filesystem=None):
    """
    Get the active workspace ID from the tracking file.
    Returns a tuple of (workspace_id, creation_time) or (None, None).
    
    Args:
        filesystem: Optional Daytona FileSystem instance to use for file operations
    """
    logger = logging.getLogger("daytona-interpreter")
    
    # Try using Daytona FileSystem if available
    if filesystem:
        try:
            # Check if the file exists using Daytona
            response = filesystem.instance.process.exec(f"test -f {shlex.quote(WORKSPACE_TRACKING_FILE)} && echo 'exists'")
            if response.stdout.strip() == 'exists':
                # Use Daytona to read the file
                content = filesystem.download_file(WORKSPACE_TRACKING_FILE)
                if content:
                    data = json.loads(content.decode('utf-8'))
                    logger.debug(f"Read workspace tracking file using Daytona FileSystem")
                    return data.get('workspace_id'), data.get('created_at')
        except Exception as e:
            logger.warning(f"Failed to use Daytona FileSystem to read workspace tracking: {e}")
    
    # Fallback to standard file operations
    try:
        if os.path.exists(WORKSPACE_TRACKING_FILE):
            with open(WORKSPACE_TRACKING_FILE, 'r') as f:
                data = json.load(f)
                return data.get('workspace_id'), data.get('created_at')
    except Exception as e:
        logger.error(f"Failed to read workspace tracking file: {e}")
    
    return None, None

def set_active_workspace(workspace_id, filesystem=None):
    """
    Set the active workspace ID in the tracking file.
    Uses Daytona FileSystem if available, falls back to standard file operations.
    
    Args:
        workspace_id: ID of the workspace to set as active
        filesystem: Optional Daytona FileSystem instance to use for file operations
    """
    logger = logging.getLogger("daytona-interpreter")
    data = {
        'workspace_id': workspace_id,
        'created_at': int(time.time()),
        'pid': os.getpid()
    }
    
    # Use Daytona FileSystem if available
    if filesystem:
        try:
            # Convert to JSON string and encode as bytes
            content = json.dumps(data).encode('utf-8')
            
            # Create directory if needed (using process.exec)
            tracking_dir = os.path.dirname(WORKSPACE_TRACKING_FILE)
            filesystem.instance.process.exec(f"mkdir -p {shlex.quote(tracking_dir)}")
                    
            # Use filesystem to write the file
            filesystem.upload_file(WORKSPACE_TRACKING_FILE, content)
            logger.debug(f"Workspace tracking file updated using Daytona FileSystem")
            return
        except Exception as e:
            logger.warning(f"Failed to use Daytona FileSystem for workspace tracking: {e}")
    
    # Fallback to standard file operations
    try:
        # Create directory if needed
        tracking_dir = os.path.dirname(WORKSPACE_TRACKING_FILE)
        try:
            os.makedirs(tracking_dir, mode=0o777, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create tracking directory with permissions: {e}")
            # Try again without setting permissions
            os.makedirs(tracking_dir, exist_ok=True)

        with open(WORKSPACE_TRACKING_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to update workspace tracking file: {e}")

def clear_active_workspace(filesystem=None):
    """
    Clear the active workspace ID from the tracking file.
    Uses Daytona FileSystem if available, falls back to standard file operations.
    
    Args:
        filesystem: Optional Daytona FileSystem instance to use for file operations
    """
    logger = logging.getLogger("daytona-interpreter")
    
    # Try using Daytona FileSystem if available
    if filesystem:
        try:
            # Check if the file exists using Daytona process.exec
            response = filesystem.instance.process.exec(f"test -f {shlex.quote(WORKSPACE_TRACKING_FILE)} && echo 'exists'")
            if response.stdout.strip() == 'exists':
                # Use rm command with process.exec
                filesystem.instance.process.exec(f"rm {shlex.quote(WORKSPACE_TRACKING_FILE)}")
                logger.debug(f"Workspace tracking file removed using Daytona FileSystem")
                return
        except Exception as e:
            logger.warning(f"Failed to use Daytona FileSystem to clear workspace tracking: {e}")
    
    # Fallback to standard file operations
    try:
        if os.path.exists(WORKSPACE_TRACKING_FILE):
            os.unlink(WORKSPACE_TRACKING_FILE)
    except Exception as e:
        logger.error(f"Failed to remove workspace tracking file: {e}")

def cleanup_stale_workspaces(daytona_instance, max_age_days=1, logger=None):
    """
    Utility function to clean up workspaces older than the specified age.

    Args:
        daytona_instance: Initialized Daytona SDK instance
        max_age_days: Maximum age in days to keep workspaces (default: 1 day)
        logger: Logger instance for output messages

    Returns:
        tuple: (cleaned_count, error_count, remaining_count)
    """
    if logger is None:
        logger = logging.getLogger("daytona-interpreter")

    logger.info(f"Starting cleanup of workspaces older than {max_age_days} days")
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60

    cleaned_count = 0
    error_count = 0
    remaining_count = 0

    try:
        # Get list of all workspaces
        workspaces = daytona_instance.list()
        logger.info(f"Found {len(workspaces)} total workspaces")

        for workspace in workspaces:
            try:
                # Check if workspace has creation time info
                if hasattr(workspace, 'created_at'):
                    # Parse the timestamp (format depends on API)
                    try:
                        # Try parsing as Unix timestamp
                        if isinstance(workspace.created_at, (int, float)):
                            created_timestamp = workspace.created_at
                        # Try parsing as ISO string
                        elif isinstance(workspace.created_at, str):
                            from datetime import datetime
                            created_timestamp = datetime.fromisoformat(workspace.created_at.replace('Z', '+00:00')).timestamp()
                        else:
                            # Unknown format, skip this workspace
                            logger.warning(f"Unknown timestamp format for workspace {workspace.id}")
                            remaining_count += 1
                            continue

                        # Check if workspace is older than threshold
                        age_seconds = current_time - created_timestamp
                        if age_seconds > max_age_seconds:
                            logger.info(f"Removing old workspace {workspace.id} (age: {age_seconds/86400:.1f} days)")
                            daytona_instance.remove(workspace)
                            cleaned_count += 1
                        else:
                            logger.debug(f"Keeping workspace {workspace.id} (age: {age_seconds/86400:.1f} days)")
                            remaining_count += 1
                    except Exception as e:
                        logger.warning(f"Error parsing timestamp for workspace {workspace.id}: {e}")
                        remaining_count += 1
                else:
                    # If no creation time, just count it
                    logger.debug(f"Workspace {workspace.id} has no creation timestamp, skipping")
                    remaining_count += 1
            except Exception as e:
                logger.warning(f"Error processing workspace {workspace.id}: {e}")
                error_count += 1

        logger.info(f"Cleanup complete: {cleaned_count} removed, {error_count} errors, {remaining_count} remaining")
        return (cleaned_count, error_count, remaining_count)
    except Exception as e:
        logger.error(f"Error during workspace cleanup: {e}")
        return (cleaned_count, error_count + 1, remaining_count)

async def main():
    """
    Application entry point:
    1. Set up logging
    2. Load configuration
    3. Create and run interpreter instance
    4. Handle interrupts and cleanup

    IMPORTANT: This function ensures only one interpreter instance exists
    per process. It also coordinates workspace usage across multiple processes
    to ensure a single sandbox is used for the entire session.
    """
    global _interpreter_instance

    # Check if interpreter is already running in this process - prevents multiple instances
    if _interpreter_instance is not None:
        print("Server is already running in this process, reusing existing instance")
        return

    # Create tmp directory with proper permissions if it doesn't exist
    tmp_dir = '/tmp'
    try:
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir, mode=0o777, exist_ok=True)
            logger.info(f"Created {tmp_dir} directory with permissions 0o777")
        else:
            # Ensure appropriate permissions on existing directory
            current_mode = os.stat(tmp_dir).st_mode & 0o777
            if current_mode != 0o777:
                os.chmod(tmp_dir, 0o777)
                logger.info(f"Updated {tmp_dir} permissions to 0o777")
    except Exception as e:
        fallback_tmp = os.path.join(os.path.expanduser('~'), '.daytona_tmp')
        logger.warning(f"Failed to create/update /tmp: {e}. Using fallback directory: {fallback_tmp}")
        os.makedirs(fallback_tmp, exist_ok=True)

        # Update log and workspace file paths to use fallback directory
        global LOG_FILE, WORKSPACE_TRACKING_FILE, WORKSPACE_LOCK_FILE
        LOG_FILE = os.path.join(fallback_tmp, 'daytona-interpreter.log')
        WORKSPACE_TRACKING_FILE = os.path.join(fallback_tmp, 'daytona-workspace.json')
        WORKSPACE_LOCK_FILE = os.path.join(fallback_tmp, 'daytona-workspace.lock')

    logger = setup_logging()
    logger.info("Initializing server...")

    # Enable stderr logging for better debugging
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    # Log the server address
    logger.info(f"MCP Server is configured for {HOST}:{PORT}")

    # Create a variable for the interpreter outside the try block
    interpreter = None

    try:
        # Load configuration with retry mechanism
        max_config_retries = 3
        config_retry_count = 0
        config_retry_delay = 1.0

        while config_retry_count < max_config_retries:
            try:
                logger.debug(f"Loading configuration (attempt {config_retry_count + 1})")
                config = Config()
                logger.info("Configuration loaded successfully")
                break
            except Exception as e:
                config_retry_count += 1
                if config_retry_count >= max_config_retries:
                    logger.error(f"Failed to load configuration after {max_config_retries} attempts: {e}")
                    raise
                logger.warning(f"Configuration loading failed: {e}, retrying in {config_retry_delay}s")
                await asyncio.sleep(config_retry_delay)
                config_retry_delay *= 1.5

        # Create interpreter and store in global variable - this is the only instance for this process
        logger.debug("Creating interpreter instance")
        _interpreter_instance = DaytonaInterpreter(logger, config)
        logger.info("Server started and connected successfully")

        # Set up signal handlers for graceful shutdown
        def signal_handler():
            logger.info("Received termination signal")
            if _interpreter_instance:
                # No await here, just schedule the cleanup
                asyncio.create_task(_interpreter_instance.cleanup())

        # Run the server - this will handle workspace initialization/reuse
        await _interpreter_instance.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        if _interpreter_instance:
            await _interpreter_instance.cleanup()
            _interpreter_instance = None
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if _interpreter_instance:
            await _interpreter_instance.cleanup()
            _interpreter_instance = None
        # Don't exit with error code to allow the service to restart
        # sys.exit(1)
    finally:
        logger.info("Server shutdown complete")
        # Always ensure the interpreter is reset on shutdown
        _interpreter_instance = None


if __name__ == "__main__":
    asyncio.run(main())