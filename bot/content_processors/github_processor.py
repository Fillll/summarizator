"""GitHub repository content processor."""
import re
import aiohttp
from bot.content_processors.base import ContentProcessor


class GitHubProcessor(ContentProcessor):
    """Processor for GitHub repositories (extracts README)."""

    def _parse_github_url(self, url: str) -> tuple[str, str]:
        """Parse GitHub URL to extract owner and repo.

        Args:
            url: GitHub URL

        Returns:
            Tuple of (owner, repo)

        Raises:
            ValueError: If URL cannot be parsed
        """
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, url)

        if not match:
            raise ValueError(f"Could not parse GitHub URL: {url}")

        owner = match.group(1)
        repo = match.group(2)

        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]

        return owner, repo

    async def extract_content(self, url: str) -> str:
        """Extract README from GitHub repository.

        Args:
            url: The GitHub repository URL

        Returns:
            Markdown-formatted README content

        Raises:
            Exception: If content extraction fails
        """
        owner, repo = self._parse_github_url(url)

        # Try to fetch README using GitHub raw content
        readme_urls = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/Readme.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/Readme.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/readme.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/readme.md",
        ]

        async with aiohttp.ClientSession() as session:
            for readme_url in readme_urls:
                try:
                    async with session.get(readme_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            content = await response.text()
                            return content.strip()
                except:
                    continue

        raise Exception(f"Could not find README for {owner}/{repo}. Repository may not have a README file.")

    async def get_document_name(self, url: str, content: str) -> str:
        """Generate short document name from repository name.

        Args:
            url: The source URL
            content: The extracted content

        Returns:
            Short, readable document name
        """
        try:
            owner, repo = self._parse_github_url(url)
            name = f"{owner}/{repo}"

            if len(name) > 60:
                # If too long, just use repo name
                name = repo
                if len(name) > 60:
                    name = name[:57] + "..."

            return name
        except:
            return "GitHub Repository"

    def get_prompt_template_name(self) -> str:
        """Return name of prompt template to use.

        Returns:
            'github'
        """
        return "github"
