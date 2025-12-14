import os
from dotenv import load_dotenv

load_dotenv()


class GitHubConfig:
    """Configuration for GitHub API access."""

    def __init__(self):
        self.api_key = os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com/graphql"
        self.timeout = int(os.getenv("GITHUB_TIMEOUT", "60"))

    @property
    def headers(self) -> dict:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def is_configured(self) -> bool:
        """Check if configuration is valid."""
        return self.api_key is not None and len(self.api_key.strip()) > 0


config = GitHubConfig()
