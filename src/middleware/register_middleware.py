from fastmcp import FastMCP

from .auth_middleware import GitHubAuthMiddleware
from .usage_middleware import GitHubUsageTrackingMiddleware
from ..utils.logging import get_logger


logger = get_logger(__name__)


def register_all_middleware(server: FastMCP) -> None:
    """
    Register all middleware in the correct order.

    Middleware order matters:
    1. GitHubAuthMiddleware - Validates authentication first
    2. GitHubUsageTrackingMiddleware - Tracks usage after auth

    Args:
        server: FastMCP server instance
    """
    logger.info("Registering middleware...")

    # Register authentication middleware first
    server.add_middleware(GitHubAuthMiddleware())
    logger.info("Registered GitHubAuthMiddleware")

    # Register usage tracking middleware second
    server.add_middleware(GitHubUsageTrackingMiddleware())
    logger.info("Registered GitHubUsageTrackingMiddleware")

    logger.info("All middleware registered successfully")
