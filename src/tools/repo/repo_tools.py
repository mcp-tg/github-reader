from fastmcp import FastMCP
from .repo_reader import register_repo_reader_tools


def register_repo_tools(server: FastMCP) -> None:
    """Register all repository tools."""
    register_repo_reader_tools(server)
