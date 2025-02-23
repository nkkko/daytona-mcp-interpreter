# Daytona MCP Python Interpreter

A Model Context Protocol server that provides Python code execution capabilities in ephemeral Daytona sandbox.

[![Watch the video](https://img.youtube.com/vi/26m2MjY8a5c/maxresdefault.jpg)](https://youtu.be/26m2MjY8a5c)

## Installation+

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create and activate virtual environment.

If by any case you have existing env, you should deactivate and remove the virtual environment:
```bash
deactivate
rm -rf .venv
```

Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate
```

(On Windows: `.venv\Scripts\activate`)

3. Install dependencies:
```bash
uv add "mcp[cli]" pydantic python-dotenv daytona-sdk
```

## Development

Run the server directly:
```bash
uv run src/daytona_mcp_interpreter/server.py
```

Or if uv is not found (not in path):
```
/Users/USER/.local/bin/uv run ~LOCATION/daytona-mcp-interpreter/src/daytona_mcp_interpreter/server.py
```

NOTE. You can run `which uv` to get the path to uv.

You can use MCP Inspector to test the server:
```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory . \
  run \
  src/daytona_mcp_interpreter/server.py
```

Tail log:
```
tail -f /tmp/daytona-interpreter.log
```

## JSON Config file

1. Configure in Claude Desktop, Windsurf, Cursor or other config file:

Claude Desktop on MacOS config is here: `~/Library/Application Support/Claude/claude_desktop_config.json`.

CONFIG:
```json
{
    "mcpServers": {
        "daytona-interpreter": {
            "command": "/Users/USER/.local/bin/uv",
            "args": [
                "--directory",
                "/Users/USER/dev/daytona-mcp-interpreter",
                "run",
                "src/daytona_mcp_interpreter/server.py"
            ],
            "env": {
                "PYTHONUNBUFFERED": "1",
                "MCP_DAYTONA_API_KEY": "api_key",
                "MCP_DAYTONA_API_URL": "api_server_url",
                "MCP_DAYTONA_TIMEOUT": "30.0",
                "MCP_VERIFY_SSL": "false",
                "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            }
        }
    }
}
```

On Windows edit `%APPDATA%\Claude\claude_desktop_config.json` and adjust path.

2. Restart Claude Desktop

3. The Python interpreter tool will be available in Claude Desktop

## Features

- Executes Python code in isolated workspaces
- Captures stdout, stderr, and exit codes
- Automatic workspace cleanup
- Secure execution environment
- Logging for debugging

<a href="https://glama.ai/mcp/servers/hj7jlxkxpk"><img width="380" height="200" src="https://glama.ai/mcp/servers/hj7jlxkxpk/badge" alt="Daytona Python Interpreter MCP server" /></a>
[![smithery badge](https://smithery.ai/badge/@nkkko/daytona-mcp)](https://smithery.ai/server/@nkkko/daytona-mcp)
