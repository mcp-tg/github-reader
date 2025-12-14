import aiohttp
import time
import uuid
from typing import Any, Dict, Optional
from .config import config
from .logging import get_logger


logger = get_logger(__name__)


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""
    pass


async def execute_query(
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a GraphQL query against GitHub API.

    Args:
        query: GraphQL query string
        variables: Query variables dictionary
        request_id: Optional request ID for tracking (generated if not provided)

    Returns:
        Dictionary containing the response data

    Raises:
        GitHubAPIError: If the API request fails
    """
    # Generate request_id if not provided
    if request_id is None:
        request_id = str(uuid.uuid4())

    start_time = time.time()

    # Build request payload
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    # Log API request
    logger.info(
        "GitHub API request started",
        extra={
            "request_id": request_id,
            "extra_fields": {
                "variables": variables
            }
        }
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.base_url,
                headers=config.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=config.timeout)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Check for GraphQL errors
                if "errors" in data:
                    errors = data["errors"]
                    error_messages = [e.get("message", "Unknown error") for e in errors]
                    error_msg = "; ".join(error_messages)

                    execution_time_ms = (time.time() - start_time) * 1000
                    logger.error(
                        f"GitHub GraphQL error: {error_msg}",
                        extra={
                            "request_id": request_id,
                            "execution_time_ms": execution_time_ms,
                            "extra_fields": {
                                "error_type": "GraphQLError",
                                "errors": errors
                            }
                        }
                    )
                    raise GitHubAPIError(error_msg)

                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000

                # Log successful response
                logger.info(
                    "GitHub API request successful",
                    extra={
                        "request_id": request_id,
                        "execution_time_ms": execution_time_ms,
                        "extra_fields": {}
                    }
                )

                return data.get("data", {})

    except aiohttp.ClientResponseError as e:
        execution_time_ms = (time.time() - start_time) * 1000
        error_msg = ""

        if e.status == 401:
            error_msg = "Invalid or expired GitHub token"
        elif e.status == 403:
            error_msg = "Rate limit exceeded or forbidden resource"
        elif e.status == 404:
            error_msg = "Resource not found"
        else:
            error_msg = f"API request failed: {e.status} {e.message}"

        logger.error(
            f"GitHub API error: {error_msg}",
            extra={
                "request_id": request_id,
                "execution_time_ms": execution_time_ms,
                "extra_fields": {
                    "status_code": e.status,
                    "error_type": "ClientResponseError"
                }
            },
            exc_info=True
        )
        raise GitHubAPIError(error_msg)

    except aiohttp.ClientError as e:
        execution_time_ms = (time.time() - start_time) * 1000
        error_msg = f"Network error: {str(e)}"

        logger.error(
            f"GitHub API network error: {error_msg}",
            extra={
                "request_id": request_id,
                "execution_time_ms": execution_time_ms,
                "extra_fields": {
                    "error_type": "ClientError"
                }
            },
            exc_info=True
        )
        raise GitHubAPIError(error_msg)

    except GitHubAPIError:
        # Re-raise GitHubAPIError without wrapping
        raise

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        error_msg = f"Unexpected error: {str(e)}"

        logger.error(
            f"GitHub API unexpected error: {error_msg}",
            extra={
                "request_id": request_id,
                "execution_time_ms": execution_time_ms,
                "extra_fields": {
                    "error_type": "UnexpectedError"
                }
            },
            exc_info=True
        )
        raise GitHubAPIError(error_msg)
