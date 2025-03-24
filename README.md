# Daytona MCP Interpreter

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
uv add "mcp[cli]" pydantic python-dotenv "daytona-sdk>=0.10.2"
```

> Note: This project requires daytona-sdk version 0.10.2 or higher. Earlier versions have incompatible FileSystem API.

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
- Handles file downloads with smart options for large files
- Automatic workspace cleanup
- Secure execution environment
- Logging for debugging

## Tools
### Shell Exec

Executes shell commands in the Daytona workspace.

```bash
# Example: List files
ls -la

# Example: Install a package
pip install pandas
```

### File Download

Downloads files from the Daytona workspace with smart handling for large files.

**Basic Usage:**
```
file_download(file_path="/path/to/file.txt")
```

**Advanced Usage:**
```
# Set custom file size limit
file_download(file_path="/path/to/large_file.csv", max_size_mb=10.0)

# Download partial content for large files
file_download(file_path="/path/to/large_file.csv", download_option="download_partial", chunk_size_kb=200)

# Convert large file to text
file_download(file_path="/path/to/large_file.pdf", download_option="convert_to_text")

# Compress file before downloading
file_download(file_path="/path/to/large_file.bin", download_option="compress_file")

# Force download despite size
file_download(file_path="/path/to/large_file.zip", download_option="force_download")
```

### File Upload

Uploads files to the Daytona workspace. Supports both text and binary files.

**Basic Usage:**
```
# Upload a text file
file_upload(file_path="/workspace/example.txt", content="Hello, World!")
```

**Advanced Usage:**
```
# Upload a text file with specific path
file_upload(
    file_path="/workspace/data/config.json",
    content='{"setting": "value", "enabled": true}'
)

# Upload a binary file using base64 encoding
import base64
with open("local_image.png", "rb") as f:
    base64_content = base64.b64encode(f.read()).decode('utf-8')

file_upload(
    file_path="/workspace/images/uploaded.png",
    content=base64_content,
    encoding="base64"
)

# Upload without overwriting existing files
file_upload(
    file_path="/workspace/important.txt",
    content="New content",
    overwrite=False
)
```

### Matplotlib Plot Generator

Generates optimized matplotlib plots with controlled format and resolution settings.

**Basic Usage:**
```python
matplotlib_plot_generator(code="""
import numpy as np

# Generate data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# Create plot
import matplotlib.pyplot as plt
plt.figure(figsize=(8, 5))
plt.plot(x, y1, 'b-', label='Sine')
plt.plot(x, y2, 'r--', label='Cosine')
plt.title('Sine and Cosine Functions')
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.legend()
plt.grid(True)
""")
```

**Advanced Usage:**
```python
# Generate high-resolution PNG plot 
matplotlib_plot_generator(
    code="import matplotlib.pyplot as plt; plt.plot([1, 2, 3, 4]); plt.title('Simple Line Plot')",
    format="png",
    dpi=150
)

# Generate SVG for better quality in documents
matplotlib_plot_generator(
    code="import matplotlib.pyplot as plt; plt.bar(['A', 'B', 'C'], [3, 7, 2]); plt.title('Simple Bar Chart')",
    format="svg"
)
```

### Git Clone

Clones a Git repository into the Daytona workspace for analysis and code execution.

**Basic Usage:**
```
git_clone(repo_url="https://github.com/username/repository.git")
```

**Advanced Usage:**
```
# Clone a specific branch
git_clone(
    repo_url="https://github.com/username/repository.git",
    branch="develop"
)

# Clone to a specific directory with full history
git_clone(
    repo_url="https://github.com/username/repository.git",
    target_path="my_project",
    depth=0  # 0 means full history
)

# Clone with Git LFS support for repositories with large files
git_clone(
    repo_url="https://github.com/username/large-files-repo.git",
    lfs=True
)
```

### Web Preview

Generates a preview URL for web servers running inside the Daytona workspace.

**Basic Usage:**
```
# Generate a preview link for a web server running on port 3000
web_preview(port=3000)
```

**Advanced Usage:**
```
# Generate a preview link with a descriptive name
web_preview(
    port=8080,
    description="React Development Server"
)

# Generate a link without checking if server is running
web_preview(
    port=5000,
    check_server=False
)
```

**Example:**
```bash
# First run a simple web server using Python via the shell
shell_exec(command="python -m http.server 8000 &")

# Then generate a preview link for the server
web_preview(port=8000, description="Python HTTP Server")
```
<a href="https://glama.ai/mcp/servers/hj7jlxkxpk"><img width="380" height="200" src="https://glama.ai/mcp/servers/hj7jlxkxpk/badge" alt="Daytona Python Interpreter MCP server" /></a>
[![smithery badge](https://smithery.ai/badge/@nkkko/daytona-mcp)](https://smithery.ai/server/@nkkko/daytona-mcp)
