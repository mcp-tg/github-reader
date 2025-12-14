import uuid
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

from ...utils import github_client
from ...utils.logging import get_logger


logger = get_logger(__name__)


def register_repo_reader_tools(server: FastMCP) -> None:
    """Register all repository reader tools."""

    @server.tool(name="get_repository_info", tags={"api", "github", "repo"})
    async def get_repository_info(
        ctx: Context,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Get basic repository metadata.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name

        Returns:
            Dictionary containing repository metadata including name, description,
            stars, forks, language, license, dates, and topics
        """
        request_id = str(uuid.uuid4())

        logger.info(
            "Starting get_repository_info tool",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "tool": "get_repository_info",
                    "owner": owner,
                    "repo": repo
                }
            }
        )

        await ctx.info(f"Fetching repository info for {owner}/{repo}")

        query = """
        query GetRepository($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            name
            description
            stargazerCount
            forkCount
            primaryLanguage { name }
            licenseInfo { name spdxId }
            createdAt
            updatedAt
            isPrivate
            defaultBranchRef { name }
            repositoryTopics(first: 10) {
              nodes { topic { name } }
            }
          }
        }
        """

        variables = {"owner": owner, "name": repo}

        try:
            result = await github_client.execute_query(
                query=query,
                variables=variables,
                request_id=request_id
            )

            repository = result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")

            # Extract and format response
            response = {
                "success": True,
                "owner": owner,
                "repo": repo,
                "name": repository.get("name"),
                "description": repository.get("description"),
                "stars": repository.get("stargazerCount", 0),
                "forks": repository.get("forkCount", 0),
                "language": repository.get("primaryLanguage", {}).get("name") if repository.get("primaryLanguage") else None,
                "license": repository.get("licenseInfo", {}).get("spdxId") if repository.get("licenseInfo") else None,
                "created_at": repository.get("createdAt"),
                "updated_at": repository.get("updatedAt"),
                "is_private": repository.get("isPrivate", False),
                "default_branch": repository.get("defaultBranchRef", {}).get("name") if repository.get("defaultBranchRef") else None,
                "topics": [node["topic"]["name"] for node in repository.get("repositoryTopics", {}).get("nodes", [])]
            }

            logger.info(
                "get_repository_info tool completed successfully",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_repository_info",
                        "stars": response["stars"],
                        "forks": response["forks"]
                    }
                }
            )

            await ctx.info(f"Repository info retrieved: {response['stars']} stars, {response['forks']} forks")

            return response

        except github_client.GitHubAPIError as e:
            logger.error(
                f"get_repository_info tool failed with GitHub API error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_repository_info",
                        "error_type": "GitHubAPIError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"GitHub API error: {str(e)}")
            raise ToolError(str(e))

        except Exception as e:
            logger.error(
                f"get_repository_info tool failed with unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_repository_info",
                        "error_type": "UnexpectedError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"Unexpected error: {str(e)}")
            raise ToolError(f"Failed to get repository info: {str(e)}")

    @server.tool(name="get_directory_contents", tags={"api", "github", "repo"})
    async def get_directory_contents(
        ctx: Context,
        owner: str,
        repo: str,
        path: str = "",
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files and directories at a given path in a repository.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            path: Directory path (default: "" for root)
            branch: Branch name (optional, defaults to default branch)

        Returns:
            Dictionary containing list of entries with name, type, and path
        """
        request_id = str(uuid.uuid4())

        logger.info(
            "Starting get_directory_contents tool",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "tool": "get_directory_contents",
                    "owner": owner,
                    "repo": repo,
                    "path": path,
                    "branch": branch
                }
            }
        )

        await ctx.info(f"Listing contents of {owner}/{repo}/{path or '(root)'}")

        # First, get default branch if not specified
        if not branch:
            branch_query = """
            query GetDefaultBranch($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                defaultBranchRef { name }
              }
            }
            """
            branch_result = await github_client.execute_query(
                query=branch_query,
                variables={"owner": owner, "name": repo},
                request_id=request_id
            )
            repository = branch_result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")
            branch = repository.get("defaultBranchRef", {}).get("name", "main")

        # Build expression for the path
        expression = f"{branch}:{path}" if path else f"{branch}:"

        query = """
        query GetDirectoryContents($owner: String!, $name: String!, $expression: String!) {
          repository(owner: $owner, name: $name) {
            object(expression: $expression) {
              ... on Tree {
                entries {
                  name
                  type
                  path
                }
              }
            }
          }
        }
        """

        variables = {"owner": owner, "name": repo, "expression": expression}

        try:
            result = await github_client.execute_query(
                query=query,
                variables=variables,
                request_id=request_id
            )

            repository = result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")

            obj = repository.get("object")
            if not obj:
                raise ToolError(f"Path '{path}' not found in {owner}/{repo} on branch {branch}")

            entries = obj.get("entries", [])

            # Format entries
            formatted_entries = []
            for entry in entries:
                formatted_entries.append({
                    "name": entry.get("name"),
                    "type": "directory" if entry.get("type") == "tree" else "file",
                    "path": entry.get("path")
                })

            response = {
                "success": True,
                "owner": owner,
                "repo": repo,
                "path": path or "/",
                "branch": branch,
                "entries": formatted_entries,
                "count": len(formatted_entries)
            }

            logger.info(
                "get_directory_contents tool completed successfully",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_directory_contents",
                        "entries_count": len(formatted_entries)
                    }
                }
            )

            await ctx.info(f"Found {len(formatted_entries)} entries")

            return response

        except github_client.GitHubAPIError as e:
            logger.error(
                f"get_directory_contents tool failed with GitHub API error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_directory_contents",
                        "error_type": "GitHubAPIError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"GitHub API error: {str(e)}")
            raise ToolError(str(e))

        except Exception as e:
            logger.error(
                f"get_directory_contents tool failed with unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_directory_contents",
                        "error_type": "UnexpectedError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"Unexpected error: {str(e)}")
            raise ToolError(f"Failed to get directory contents: {str(e)}")

    @server.tool(name="get_file_content", tags={"api", "github", "repo"})
    async def get_file_content(
        ctx: Context,
        owner: str,
        repo: str,
        path: str,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Read the content of a specific file in a repository.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            path: File path
            branch: Branch name (optional, defaults to default branch)

        Returns:
            Dictionary containing file content, size, and encoding info
        """
        request_id = str(uuid.uuid4())

        logger.info(
            "Starting get_file_content tool",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "tool": "get_file_content",
                    "owner": owner,
                    "repo": repo,
                    "path": path,
                    "branch": branch
                }
            }
        )

        await ctx.info(f"Reading file {owner}/{repo}/{path}")

        # First, get default branch if not specified
        if not branch:
            branch_query = """
            query GetDefaultBranch($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                defaultBranchRef { name }
              }
            }
            """
            branch_result = await github_client.execute_query(
                query=branch_query,
                variables={"owner": owner, "name": repo},
                request_id=request_id
            )
            repository = branch_result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")
            branch = repository.get("defaultBranchRef", {}).get("name", "main")

        expression = f"{branch}:{path}"

        query = """
        query GetFileContent($owner: String!, $name: String!, $expression: String!) {
          repository(owner: $owner, name: $name) {
            object(expression: $expression) {
              ... on Blob {
                text
                byteSize
                isBinary
              }
            }
          }
        }
        """

        variables = {"owner": owner, "name": repo, "expression": expression}

        try:
            result = await github_client.execute_query(
                query=query,
                variables=variables,
                request_id=request_id
            )

            repository = result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")

            obj = repository.get("object")
            if not obj:
                raise ToolError(f"File '{path}' not found in {owner}/{repo} on branch {branch}")

            is_binary = obj.get("isBinary", False)
            content = obj.get("text") if not is_binary else None

            response = {
                "success": True,
                "owner": owner,
                "repo": repo,
                "path": path,
                "branch": branch,
                "content": content,
                "size": obj.get("byteSize", 0),
                "is_binary": is_binary
            }

            if is_binary:
                response["message"] = "File is binary and cannot be displayed as text"

            logger.info(
                "get_file_content tool completed successfully",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_file_content",
                        "file_size": obj.get("byteSize", 0),
                        "is_binary": is_binary
                    }
                }
            )

            await ctx.info(f"File read: {obj.get('byteSize', 0)} bytes")

            return response

        except github_client.GitHubAPIError as e:
            logger.error(
                f"get_file_content tool failed with GitHub API error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_file_content",
                        "error_type": "GitHubAPIError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"GitHub API error: {str(e)}")
            raise ToolError(str(e))

        except Exception as e:
            logger.error(
                f"get_file_content tool failed with unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_file_content",
                        "error_type": "UnexpectedError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"Unexpected error: {str(e)}")
            raise ToolError(f"Failed to get file content: {str(e)}")

    @server.tool(name="get_branches", tags={"api", "github", "repo"})
    async def get_branches(
        ctx: Context,
        owner: str,
        repo: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List repository branches.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            limit: Number of branches to return (default: 20, max: 100)

        Returns:
            Dictionary containing list of branches with name and last commit info
        """
        request_id = str(uuid.uuid4())

        # Enforce limit
        limit = min(limit, 100)

        logger.info(
            "Starting get_branches tool",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "tool": "get_branches",
                    "owner": owner,
                    "repo": repo,
                    "limit": limit
                }
            }
        )

        await ctx.info(f"Listing branches for {owner}/{repo}")

        query = """
        query GetBranches($owner: String!, $name: String!, $limit: Int!) {
          repository(owner: $owner, name: $name) {
            refs(refPrefix: "refs/heads/", first: $limit) {
              nodes {
                name
                target {
                  ... on Commit {
                    oid
                    committedDate
                    messageHeadline
                  }
                }
              }
            }
          }
        }
        """

        variables = {"owner": owner, "name": repo, "limit": limit}

        try:
            result = await github_client.execute_query(
                query=query,
                variables=variables,
                request_id=request_id
            )

            repository = result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")

            refs = repository.get("refs", {}).get("nodes", [])

            # Format branches
            branches = []
            for ref in refs:
                target = ref.get("target", {})
                branches.append({
                    "name": ref.get("name"),
                    "last_commit": {
                        "sha": target.get("oid"),
                        "date": target.get("committedDate"),
                        "message": target.get("messageHeadline")
                    }
                })

            response = {
                "success": True,
                "owner": owner,
                "repo": repo,
                "branches": branches,
                "count": len(branches)
            }

            logger.info(
                "get_branches tool completed successfully",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_branches",
                        "branches_count": len(branches)
                    }
                }
            )

            await ctx.info(f"Found {len(branches)} branches")

            return response

        except github_client.GitHubAPIError as e:
            logger.error(
                f"get_branches tool failed with GitHub API error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_branches",
                        "error_type": "GitHubAPIError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"GitHub API error: {str(e)}")
            raise ToolError(str(e))

        except Exception as e:
            logger.error(
                f"get_branches tool failed with unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_branches",
                        "error_type": "UnexpectedError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"Unexpected error: {str(e)}")
            raise ToolError(f"Failed to get branches: {str(e)}")

    @server.tool(name="get_readme", tags={"api", "github", "repo"})
    async def get_readme(
        ctx: Context,
        owner: str,
        repo: str,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get repository README content.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            branch: Branch name (optional, defaults to default branch)

        Returns:
            Dictionary containing README content as text
        """
        request_id = str(uuid.uuid4())

        logger.info(
            "Starting get_readme tool",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "tool": "get_readme",
                    "owner": owner,
                    "repo": repo,
                    "branch": branch
                }
            }
        )

        await ctx.info(f"Fetching README for {owner}/{repo}")

        # First, get default branch if not specified
        if not branch:
            branch_query = """
            query GetDefaultBranch($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                defaultBranchRef { name }
              }
            }
            """
            branch_result = await github_client.execute_query(
                query=branch_query,
                variables={"owner": owner, "name": repo},
                request_id=request_id
            )
            repository = branch_result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")
            branch = repository.get("defaultBranchRef", {}).get("name", "main")

        # Try different README filenames
        readme_files = ["README.md", "README", "readme.md", "Readme.md", "README.rst", "README.txt"]

        query = """
        query GetReadme($owner: String!, $name: String!, $expression: String!) {
          repository(owner: $owner, name: $name) {
            object(expression: $expression) {
              ... on Blob {
                text
              }
            }
          }
        }
        """

        try:
            for readme_name in readme_files:
                expression = f"{branch}:{readme_name}"
                variables = {"owner": owner, "name": repo, "expression": expression}

                result = await github_client.execute_query(
                    query=query,
                    variables=variables,
                    request_id=request_id
                )

                repository = result.get("repository")
                if not repository:
                    raise ToolError(f"Repository {owner}/{repo} not found")

                obj = repository.get("object")
                if obj and obj.get("text"):
                    content = obj.get("text")

                    response = {
                        "success": True,
                        "owner": owner,
                        "repo": repo,
                        "branch": branch,
                        "filename": readme_name,
                        "content": content
                    }

                    logger.info(
                        "get_readme tool completed successfully",
                        extra={
                            "request_id": request_id,
                            "extra_fields": {
                                "tool": "get_readme",
                                "filename": readme_name,
                                "content_length": len(content)
                            }
                        }
                    )

                    await ctx.info(f"Found README: {readme_name}")

                    return response

            # No README found
            raise ToolError(f"No README file found in {owner}/{repo} on branch {branch}")

        except github_client.GitHubAPIError as e:
            logger.error(
                f"get_readme tool failed with GitHub API error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_readme",
                        "error_type": "GitHubAPIError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"GitHub API error: {str(e)}")
            raise ToolError(str(e))

        except Exception as e:
            logger.error(
                f"get_readme tool failed with unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_readme",
                        "error_type": "UnexpectedError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"Unexpected error: {str(e)}")
            raise ToolError(f"Failed to get README: {str(e)}")

    @server.tool(name="get_commits", tags={"api", "github", "repo"})
    async def get_commits(
        ctx: Context,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get recent commits on a branch.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            branch: Branch name (optional, defaults to default branch)
            limit: Number of commits to return (default: 10, max: 50)

        Returns:
            Dictionary containing list of commits with sha, message, author, date
        """
        request_id = str(uuid.uuid4())

        # Enforce limit
        limit = min(limit, 50)

        logger.info(
            "Starting get_commits tool",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "tool": "get_commits",
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "limit": limit
                }
            }
        )

        await ctx.info(f"Fetching commits for {owner}/{repo}")

        # First, get default branch if not specified
        if not branch:
            branch_query = """
            query GetDefaultBranch($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                defaultBranchRef { name }
              }
            }
            """
            branch_result = await github_client.execute_query(
                query=branch_query,
                variables={"owner": owner, "name": repo},
                request_id=request_id
            )
            repository = branch_result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")
            branch = repository.get("defaultBranchRef", {}).get("name", "main")

        query = """
        query GetCommits($owner: String!, $name: String!, $branch: String!, $limit: Int!) {
          repository(owner: $owner, name: $name) {
            ref(qualifiedName: $branch) {
              target {
                ... on Commit {
                  history(first: $limit) {
                    nodes {
                      oid
                      messageHeadline
                      message
                      author {
                        name
                        email
                        date
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        variables = {"owner": owner, "name": repo, "branch": branch, "limit": limit}

        try:
            result = await github_client.execute_query(
                query=query,
                variables=variables,
                request_id=request_id
            )

            repository = result.get("repository")
            if not repository:
                raise ToolError(f"Repository {owner}/{repo} not found")

            ref = repository.get("ref")
            if not ref:
                raise ToolError(f"Branch '{branch}' not found in {owner}/{repo}")

            history = ref.get("target", {}).get("history", {}).get("nodes", [])

            # Format commits
            commits = []
            for commit in history:
                author = commit.get("author", {})
                commits.append({
                    "sha": commit.get("oid"),
                    "message_headline": commit.get("messageHeadline"),
                    "message": commit.get("message"),
                    "author": {
                        "name": author.get("name"),
                        "email": author.get("email"),
                        "date": author.get("date")
                    }
                })

            response = {
                "success": True,
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "commits": commits,
                "count": len(commits)
            }

            logger.info(
                "get_commits tool completed successfully",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_commits",
                        "commits_count": len(commits)
                    }
                }
            )

            await ctx.info(f"Found {len(commits)} commits")

            return response

        except github_client.GitHubAPIError as e:
            logger.error(
                f"get_commits tool failed with GitHub API error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_commits",
                        "error_type": "GitHubAPIError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"GitHub API error: {str(e)}")
            raise ToolError(str(e))

        except Exception as e:
            logger.error(
                f"get_commits tool failed with unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "extra_fields": {
                        "tool": "get_commits",
                        "error_type": "UnexpectedError"
                    }
                },
                exc_info=True
            )
            await ctx.error(f"Unexpected error: {str(e)}")
            raise ToolError(f"Failed to get commits: {str(e)}")
