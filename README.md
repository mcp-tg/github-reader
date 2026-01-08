# GitHub Reader MCP Server

A **FastMCP server** that provides read-only access to GitHub repositories through the Model Context Protocol (MCP). Explore any public GitHub repository without cloning it locally—perfect for AI assistants, code review workflows, and development tooling.

## Why Use This?

- **No Local Clone Required**: Read files, browse directories, and explore repositories remotely
- **Efficient GraphQL API**: Single requests fetch exactly what's needed
- **AI-Ready**: Designed for integration with Claude, GPT, and other LLM-powered tools via MCP
- **Built-in Observability**: Usage tracking, structured logging, and request correlation

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- GitHub Personal Access Token ([create one here](https://github.com/settings/tokens))

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd github-reader

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .

# Configure your GitHub token
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
```

### Running the Server

```bash
# For MCP clients (Claude Desktop, etc.)
.venv/bin/python main.py

# For development with MCP Inspector
./dev-inspector.sh
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_repository_info` | Get repository metadata (stars, forks, language, topics, license) |
| `get_directory_contents` | List files and folders at any path |
| `get_file_content` | Read the contents of any file |
| `get_branches` | List repository branches with last commit info |
| `get_readme` | Fetch the README content |
| `get_commits` | Get recent commit history |

### Tool Examples

**Get repository info:**
```json
{
  "owner": "anthropics",
  "repo": "claude-code"
}
```

**Browse a directory:**
```json
{
  "owner": "anthropics",
  "repo": "claude-code",
  "path": "src/components",
  "branch": "main"
}
```

**Read a file:**
```json
{
  "owner": "anthropics",
  "repo": "claude-code",
  "path": "package.json"
}
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | *Required* |
| `GITHUB_TIMEOUT` | API request timeout (seconds) | `60` |
| `MCP_TRANSPORT` | Transport type: `stdio` or `http` | `stdio` |
| `PORT` | HTTP port (for http transport) | `8000` |

### Token Permissions

- **Public repositories**: `public_repo` scope
- **Private repositories**: `repo` scope

## MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "github-reader": {
      "command": "/path/to/github-reader/.venv/bin/python",
      "args": ["/path/to/github-reader/main.py"],
      "env": {
        "GITHUB_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Claude Code CLI

Add to your MCP settings:

```json
{
  "mcpServers": {
    "github-reader": {
      "command": "/path/to/github-reader/.venv/bin/python",
      "args": ["/path/to/github-reader/main.py"],
      "env": {
        "GITHUB_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Project Structure

```
github-reader/
├── main.py                    # Server entry point
├── src/
│   ├── middleware/            # Auth & usage tracking middleware
│   ├── tools/repo/            # MCP tool implementations
│   └── utils/                 # Config, GitHub client, logging, storage
├── database/                  # Usage statistics (auto-created)
├── pyproject.toml             # Dependencies
└── dev-inspector.sh           # Development script
```

## Architecture

```
Client Request
    ↓
FastMCP Server
    ↓
Auth Middleware (validates GITHUB_TOKEN)
    ↓
Usage Tracking Middleware (starts timer)
    ↓
Tool Handler
    ↓
GitHub GraphQL API
    ↓
Response with usage stats saved
```

**Key Design Decisions:**

- **GraphQL over REST**: More efficient queries, fetches only needed data
- **Middleware Chain**: Authentication runs before any API tool
- **Async Throughout**: Non-blocking I/O for better performance
- **JSON Storage**: Simple file-based usage tracking without external dependencies

## Development

### Running Tests

```bash
# Validate server configuration
.venv/bin/python test_server.py
```

### Using the MCP Inspector

```bash
# Runs server with HTTP transport + opens inspector UI
./dev-inspector.sh
```

The inspector provides a web UI to test tools interactively.

## Features

- **Auto Branch Detection**: Tools automatically use the default branch when not specified
- **Multiple README Formats**: Searches for README.md, README, readme.md, README.rst, etc.
- **Binary File Detection**: Identifies binary files and handles them appropriately
- **Structured Logging**: JSON-formatted logs with request ID correlation
- **Usage Statistics**: Tracks per-tool execution times and success rates

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.
