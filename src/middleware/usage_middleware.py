import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from mcp import types as mt

from ..utils.logging import get_logger
from ..utils.storage import save_to_database, load_from_database


logger = get_logger(__name__)


class GitHubUsageTrackingMiddleware(Middleware):
    """Middleware to track API usage and execution time."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next,
    ) -> ToolResult:
        """
        Track tool usage, execution time, and save statistics.

        Args:
            context: Middleware context containing tool information
            call_next: Next middleware in chain

        Returns:
            Tool result from next middleware
        """
        # Generate request_id for correlation
        request_id = str(uuid.uuid4())

        tool_name = context.source.name if hasattr(context.source, 'name') else str(context.source)
        start_time = time.time()

        logger.info(
            f"Starting tool execution: {tool_name}",
            extra={
                "request_id": request_id,
                "extra_fields": {"tool_name": tool_name}
            }
        )

        # Store request_id in context for downstream use
        if hasattr(context, 'request_id'):
            context.request_id = request_id

        try:
            # Call the next middleware/tool
            result = await call_next(context)

            # Calculate execution time
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000

            # Track successful execution
            self._track_usage(tool_name, execution_time, success=True, request_id=request_id)

            logger.info(
                f"Tool {tool_name} completed in {execution_time:.2f}s",
                extra={
                    "request_id": request_id,
                    "execution_time_ms": execution_time_ms,
                    "extra_fields": {
                        "tool_name": tool_name,
                        "success": True
                    }
                }
            )

            return result

        except Exception as e:
            # Calculate execution time even on error
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000

            # Track failed execution
            self._track_usage(tool_name, execution_time, success=False, error=str(e), request_id=request_id)

            logger.error(
                f"Tool {tool_name} failed after {execution_time:.2f}s: {str(e)}",
                extra={
                    "request_id": request_id,
                    "execution_time_ms": execution_time_ms,
                    "extra_fields": {
                        "tool_name": tool_name,
                        "success": False,
                        "error": str(e)
                    }
                },
                exc_info=True
            )

            # Re-raise the exception
            raise

    def _track_usage(
        self,
        tool_name: str,
        execution_time: float,
        success: bool,
        error: str = None,
        request_id: str = None
    ) -> None:
        """
        Save usage statistics to database.

        Args:
            tool_name: Name of the tool executed
            execution_time: Time taken to execute in seconds
            success: Whether execution was successful
            error: Error message if execution failed
            request_id: Request ID for correlation
        """
        try:
            # Load existing usage data
            schema = f"middleware/usage/{tool_name}"
            existing_data = load_from_database(schema)

            # Get existing stats or create new
            stats = existing_data.get("data", {
                "tool_name": tool_name,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "last_called": None,
                "errors": []
            })

            # Update stats
            stats["total_calls"] += 1
            stats["total_execution_time"] += execution_time

            if success:
                stats["successful_calls"] += 1
            else:
                stats["failed_calls"] += 1
                if error:
                    stats["errors"].append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "error": error
                    })
                    # Keep only last 10 errors
                    stats["errors"] = stats["errors"][-10:]

            # Calculate average
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_calls"]
            stats["last_called"] = datetime.now(timezone.utc).isoformat()

            # Save updated stats
            save_to_database(schema, stats)

            logger.debug(
                f"Usage stats saved for {tool_name}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {"tool_name": tool_name}
                }
            )

        except Exception as e:
            # Don't fail the tool call if tracking fails
            logger.error(
                f"Failed to track usage for {tool_name}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool_name": tool_name,
                        "error": str(e)
                    }
                },
                exc_info=True
            )
