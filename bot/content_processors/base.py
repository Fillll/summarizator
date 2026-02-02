"""Abstract base class for content processors."""
from abc import ABC, abstractmethod


class ContentProcessor(ABC):
    """Abstract base class for content processors."""

    @abstractmethod
    async def extract_content(self, url: str) -> str:
        """Extract content from URL and return as markdown.

        Args:
            url: The URL to extract content from

        Returns:
            Markdown-formatted content

        Raises:
            Exception: If content extraction fails
        """
        pass

    @abstractmethod
    async def get_document_name(self, url: str, content: str) -> str:
        """Generate short document name for display.

        Args:
            url: The source URL
            content: The extracted content

        Returns:
            Short, readable document name
        """
        pass

    @abstractmethod
    def get_prompt_template_name(self) -> str:
        """Return name of prompt template to use for summarization.

        Returns:
            Template name (e.g., 'web', 'youtube', 'pdf', 'github')
        """
        pass
