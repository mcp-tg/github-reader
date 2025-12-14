#!/bin/bash

# Development script to run GitHub Reader MCP Server with MCP Inspector
# This script:
# 1. Creates virtual environment and installs dependencies
# 2. Validates configuration
# 3. Launches MCP Inspector with stdio transport

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Setup Python virtual environment
echo "Setting up Python environment..."
if [ ! -d ".venv" ]; then
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: No .env file found. Copying from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env file from .env.example"
        echo "Warning: Please edit .env and add your GITHUB_TOKEN"
    else
        echo "Error: .env.example not found"
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Validate GitHub token
if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "your_github_token_here" ]; then
    echo "Error: GITHUB_TOKEN not configured in .env"
    echo "Please edit .env and add your GitHub personal access token"
    exit 1
fi

# Create required directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p database/middleware/usage

echo ""
echo "Starting GitHub Reader MCP Server with Inspector (stdio transport)..."
echo ""

# Run MCP Inspector with stdio transport - it spawns the Python server
npx @modelcontextprotocol/inspector python main.py
