import uuid
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp import types as mt

from ..utils.config import config
from ..utils.logging import get_logger


logger = get_logger(__name__)


class GitHubAuthMiddleware(Middleware):
    """Middleware to validate GitHub API authentication."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next,
    ) -> ToolResult:
        """
        Check if tool requires API authentication and validate API key.

        Args:
            context: Middleware context containing tool information
            call_next: Next middleware in chain

        Returns:
            Tool result from next middleware

        Raises:
            ToolError: If API key is missing for tools with "api" tag
        """
        # Get or generate request_id for tracking
        request_id = getattr(context, 'request_id', str(uuid.uuid4()))

        # Get the tool being called
        tool_name = context.source.name if hasattr(context.source, 'name') else str(context.source)

        logger.debug(
            f"Auth middleware checking tool: {tool_name}",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "tool_name": tool_name,
                    "has_api_key": config.is_configured()
                }
            }
        )

        # Check if the tool has "api" tag by getting tool metadata from FastMCP context
        # Tools with "api" tag require authentication
        fastmcp_ctx = context.fastmcp_context

        # Get tool from server's registered tools
        if hasattr(fastmcp_ctx, 'server'):
            tool = fastmcp_ctx.server.get_tool(tool_name)

            # Check if tool has "api" tag
            if tool and hasattr(tool, 'tags') and "api" in tool.tags:
                if not config.is_configured():
                    logger.error(
                        f"GitHub token not configured for tool: {tool_name}",
                        extra={
                            "request_id": request_id,
                            "extra_fields": {
                                "tool_name": tool_name,
                                "requires_auth": True
                            }
                        }
                    )
                    raise ToolError("GitHub token not configured. Please set GITHUB_TOKEN in your .env file.")

                logger.info(
                    f"Authentication validated for tool: {tool_name}",
                    extra={
                        "request_id": request_id,
                        "extra_fields": {
                            "tool_name": tool_name,
                            "auth_status": "valid"
                        }
                    }
                )

        # Continue to next middleware
        return await call_next(context)
