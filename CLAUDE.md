# Daytona MCP Interpreter Development Guide

## Build Commands
- **Run server**: `uv run src/daytona_mcp_interpreter/server.py`
- **Test with MCP Inspector**: `npx @modelcontextprotocol/inspector uv --directory . run src/daytona_mcp_interpreter/server.py`
- **Install dependencies**: `uv add "mcp[cli]" pydantic python-dotenv "daytona-sdk>=0.10.5" httpx>=0.24.0`
- **View logs**: `tail -f /tmp/daytona-interpreter.log`
- **Clean build files**: `rm -rf dist/ build/ *.egg-info/`
- **Build package**: `uv pip install build && python -m build`

## Code Style
- **Imports**: Group in order: standard library, third-party, project modules; alphabetize within groups
- **Type annotations**: Comprehensive type hints for all parameters and return values
- **Naming**: Classes in PascalCase, functions/methods in snake_case, constants in UPPER_SNAKE_CASE
- **Documentation**: Triple-quoted docstrings for classes and functions using Google style
- **Error handling**: Use try/except with specific exceptions, log exceptions with context
- **Logging**: Use hierarchical logging with appropriate levels (debug, info, error)
- **Async pattern**: Use asyncio for asynchronous operations
- **Line length**: 88 characters (Black formatter default)

## Project Structure
- `src/daytona_mcp_interpreter/`: Main source directory
- Use class-based architecture with clear separation of concerns
- Environment variables for configuration stored in .env file

## Environment Variables
- `MCP_DAYTONA_API_KEY`: API key for authentication (required)
- `MCP_DAYTONA_SERVER_URL`: Server URL (default: https://app.daytona.io/api)
- `MCP_DAYTONA_TIMEOUT`: Request timeout in seconds (default: 180.0)
- `MCP_DAYTONA_TARGET`: Target region (default: eu)
- `MCP_VERIFY_SSL`: Enable SSL verification (default: false)