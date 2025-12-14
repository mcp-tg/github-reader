from fastmcp import FastMCP
from src.middleware.register_middleware import register_all_middleware
from src.tools.repo.repo_tools import register_repo_tools
from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create MCP server
logger.info("Initializing GitHub Reader MCP Server")
mcp = FastMCP(name="GitHub Reader MCP Server")

# Register middleware first
logger.info("Registering middleware")
register_all_middleware(mcp)

# Register all repo tools
logger.info("Registering repo tools")
register_repo_tools(mcp)

if __name__ == "__main__":
    import os

    # Use HTTP transport for inspector, stdio for direct MCP clients
    transport = os.getenv("MCP_TRANSPORT", "http")

    logger.info(
        "Starting MCP server",
        extra={
            "extra_fields": {
                "transport": transport,
                "port": int(os.getenv("PORT", "8000")) if transport == "http" else None
            }
        }
    )

    try:
        if transport == "http":
            port = int(os.getenv("PORT", "8000"))
            logger.info(
                f"Server starting on HTTP transport at 0.0.0.0:{port}",
                extra={
                    "extra_fields": {
                        "transport": "http",
                        "host": "0.0.0.0",
                        "port": port
                    }
                }
            )
            mcp.run(
                transport="http",
                host="0.0.0.0",
                port=port
            )
        else:
            logger.info(
                "Server starting on stdio transport",
                extra={
                    "extra_fields": {
                        "transport": "stdio"
                    }
                }
            )
            mcp.run(transport="stdio")
    except Exception as e:
        logger.error(
            f"Server failed to start: {str(e)}",
            extra={
                "extra_fields": {
                    "transport": transport,
                    "error": str(e)
                }
            },
            exc_info=True
        )
        raise
    finally:
        logger.info("Server shutdown")
