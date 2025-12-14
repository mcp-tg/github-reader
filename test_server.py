#!/usr/bin/env python3
"""
Test script to verify GitHub Reader MCP Server initialization.
This script validates:
1. All imports work correctly
2. No syntax errors
3. Server can be instantiated
4. Middleware and tools are registered
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from fastmcp import FastMCP
        print("  FastMCP imported")

        from src.middleware.register_middleware import register_all_middleware
        print("  register_all_middleware imported")

        from src.tools.repo.repo_tools import register_repo_tools
        print("  register_repo_tools imported")

        from src.utils.config import config
        print("  config imported")

        from src.utils.logging import get_logger
        print("  logging utilities imported")

        from src.utils.github_client import execute_query, GitHubAPIError
        print("  github_client imported")

        from src.utils.storage import save_to_database, load_from_database
        print("  storage utilities imported")

        from src.middleware.auth_middleware import GitHubAuthMiddleware
        print("  GitHubAuthMiddleware imported")

        from src.middleware.usage_middleware import GitHubUsageTrackingMiddleware
        print("  GitHubUsageTrackingMiddleware imported")

        from src.tools.repo.repo_reader import register_repo_reader_tools
        print("  register_repo_reader_tools imported")

        print("All imports successful!\n")
        return True

    except ImportError as e:
        print(f"  Import error: {e}")
        return False


def test_server_initialization():
    """Test that the server can be initialized."""
    print("Testing server initialization...")

    try:
        from fastmcp import FastMCP
        from src.middleware.register_middleware import register_all_middleware
        from src.tools.repo.repo_tools import register_repo_tools

        # Create server
        mcp = FastMCP(name="GitHub Reader MCP Server")
        print("  Server instance created")

        # Register middleware
        register_all_middleware(mcp)
        print("  Middleware registered")

        # Register tools
        register_repo_tools(mcp)
        print("  Tools registered")

        print("Server initialization successful!\n")
        return True

    except Exception as e:
        print(f"  Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration loading."""
    print("Testing configuration...")

    try:
        from src.utils.config import config

        print(f"  Base URL: {config.base_url}")
        print(f"  Timeout: {config.timeout}s")

        if config.is_configured():
            print("  GitHub token is configured")
        else:
            print("  GitHub token is NOT configured (this is OK for testing)")

        print("Configuration test successful!\n")
        return True

    except Exception as e:
        print(f"  Config error: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("Testing file structure...")

    required_files = [
        "main.py",
        "pyproject.toml",
        ".env.example",
        "src/__init__.py",
        "src/middleware/__init__.py",
        "src/middleware/register_middleware.py",
        "src/middleware/auth_middleware.py",
        "src/middleware/usage_middleware.py",
        "src/tools/__init__.py",
        "src/tools/repo/__init__.py",
        "src/tools/repo/repo_tools.py",
        "src/tools/repo/repo_reader.py",
        "src/utils/__init__.py",
        "src/utils/config.py",
        "src/utils/logging.py",
        "src/utils/github_client.py",
        "src/utils/storage.py",
    ]

    base_dir = os.path.dirname(__file__)
    all_exist = True

    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"  {file_path}")
        else:
            print(f"  MISSING: {file_path}")
            all_exist = False

    if all_exist:
        print("All required files present!\n")
    else:
        print("Some files are missing!\n")

    return all_exist


def main():
    """Run all tests."""
    print("=" * 60)
    print("GitHub Reader MCP Server - Validation Tests")
    print("=" * 60)
    print()

    results = {
        "File Structure": test_file_structure(),
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Server Initialization": test_server_initialization(),
    }

    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")

    print()

    if all(results.values()):
        print("All tests passed! Server is ready to run.")
        print("\nTo start the server:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your GITHUB_TOKEN to .env")
        print("  3. Run: python main.py")
        return 0
    else:
        print("Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
