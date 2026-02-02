"""Web page content processor."""
import aiohttp
from bs4 import BeautifulSoup
import html2text
from bot.content_processors.base import ContentProcessor


class WebProcessor(ContentProcessor):
    """Processor for web pages (HTML to markdown)."""

    def __init__(self):
        """Initialize web processor."""
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # Don't wrap text

    async def extract_content(self, url: str) -> str:
        """Extract content from web page and convert to markdown.

        Args:
            url: The web page URL

        Returns:
            Markdown-formatted content

        Raises:
            Exception: If content extraction fails
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; SummarizatorBot/1.0; +https://github.com/yourrepo/summarizator)'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                html = await response.text()

        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Convert to markdown
        markdown = self.html_converter.handle(str(soup))

        # Clean up excessive newlines
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):
                cleaned_lines.append(line)
            prev_empty = is_empty

        return '\n'.join(cleaned_lines).strip()

    async def get_document_name(self, url: str, content: str) -> str:
        """Generate short document name from page title.

        Args:
            url: The source URL
            content: The extracted content

        Returns:
            Short, readable document name
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; SummarizatorBot/1.0; +https://github.com/yourrepo/summarizator)'
        }

        # Try to extract title from content
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')

        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            # Truncate if too long
            if len(title) > 60:
                title = title[:57] + "..."
            return title

        # Fallback to domain name
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or "Web Page"

    def get_prompt_template_name(self) -> str:
        """Return name of prompt template to use.

        Returns:
            'web'
        """
        return "web"
