# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **FastMCP server** that provides GitHub repository observation capabilities through the Model Context Protocol (MCP). Built with Python 3.10+, it exposes tools to read and explore public GitHub repositories without cloning them locally, using GitHub's GraphQL API.

## Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment using uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
```

### Running the Server
```bash
# Run server with stdio transport (for MCP clients)
.venv/bin/python main.py

# Run server with HTTP transport and MCP Inspector
./dev-inspector.sh

# Or manually with HTTP transport
MCP_TRANSPORT=http PORT=8000 .venv/bin/python main.py
```

### Testing
```bash
# Validate server initialization and configuration
.venv/bin/python test_server.py
```

## Architecture

### Entry Point
- [main.py](main.py) - Creates FastMCP server, registers middleware and tools, runs with stdio or HTTP transport

### Core Architecture Pattern
The codebase follows a **registration-based pattern** where components are registered to the FastMCP server instance:

1. **Middleware Registration** ([src/middleware/register_middleware.py](src/middleware/register_middleware.py))
   - Order matters: Auth -> Usage Tracking
   - `GitHubAuthMiddleware` validates GitHub token configuration
   - `GitHubUsageTrackingMiddleware` tracks execution time and saves statistics to database

2. **Tool Registration** ([src/tools/repo/repo_tools.py](src/tools/repo/repo_tools.py))
   - Registers all repo tools from [repo_reader.py](src/tools/repo/repo_reader.py)
   - Six tools: `get_repository_info`, `get_directory_contents`, `get_file_content`, `get_branches`, `get_readme`, `get_commits`

### Key Components

**Utils** ([src/utils/](src/utils/))
- [config.py](src/utils/config.py) - `GitHubConfig` singleton with API credentials and timeout settings
- [github_client.py](src/utils/github_client.py) - `execute_query()` async function that makes GraphQL requests to GitHub API
- [storage.py](src/utils/storage.py) - JSON-based database under `database/` directory for usage tracking
- [logging.py](src/utils/logging.py) - Structured JSON logging

**Middleware** ([src/middleware/](src/middleware/))
- Authentication middleware checks `config.is_configured()` before tool execution
- Usage tracking middleware wraps tool calls with timing and saves statistics to `database/middleware/usage/{tool_name}/`

**Repository Tools** ([src/tools/repo/repo_reader.py](src/tools/repo/repo_reader.py))
- All tools are async functions decorated with `@server.tool()`
- Use FastMCP `Context` for logging via `ctx.info()` and `ctx.error()`
- Call `github_client.execute_query()` and handle `GitHubAPIError` exceptions
- Return standardized dicts with `success`, owner/repo info, and relevant data

### Data Flow
```
Client Request -> FastMCP Server -> Auth Middleware -> Usage Middleware (start timer)
  -> Tool Handler -> github_client.execute_query() -> GitHub GraphQL API
  -> Response -> Usage Middleware (save stats) -> Client Response
```

## Available Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `get_repository_info` | Repo metadata (stars, forks, language, topics) | `owner`, `repo` |
| `get_directory_contents` | List files/folders at a path | `owner`, `repo`, `path`, `branch` |
| `get_file_content` | Read a specific file | `owner`, `repo`, `path`, `branch` |
| `get_branches` | List branches with last commit | `owner`, `repo`, `limit` |
| `get_readme` | Fetch README content | `owner`, `repo`, `branch` |
| `get_commits` | Recent commit history | `owner`, `repo`, `branch`, `limit` |

## Configuration

- Required: `GITHUB_TOKEN` in `.env` (Personal Access Token from https://github.com/settings/tokens)
- Optional: `MCP_TRANSPORT` (stdio|http), `PORT` (default: 8000), `GITHUB_TIMEOUT` (default: 60s)
- GitHub settings in [src/utils/config.py](src/utils/config.py):
  - Base URL: `https://api.github.com/graphql`
  - Timeout: 60 seconds (configurable)

## Important Notes

- **ALWAYS ask the user for permission before making any code changes.** Do not edit, write, or modify files without explicit approval.
- The server uses `database/` directory for JSON-based storage (middleware usage tracking)
- Logs are written to stdout in JSON format
- The MCP Inspector ([dev-inspector.sh](dev-inspector.sh)) runs both server and inspector
- All tools use GitHub's GraphQL API for efficient data fetching
- Tools automatically detect default branch when not specified
