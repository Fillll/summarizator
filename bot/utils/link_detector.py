"""URL detection and classification utilities."""
import re
from typing import Optional, Literal


ContentType = Literal["web", "youtube", "pdf", "github"]


class LinkDetector:
    """Detects and classifies URLs in messages."""

    YOUTUBE_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w-]+'
    )
    GITHUB_PATTERN = re.compile(
        r'https?://github\.com/[\w-]+/[\w-]+'
    )
    PDF_PATTERN = re.compile(r'\.pdf(?:\?|$|#)', re.IGNORECASE)
    URL_PATTERN = re.compile(r'https?://[^\s]+')

    @staticmethod
    def extract_url(text: str) -> Optional[str]:
        """Extract first URL from message text.

        Args:
            text: Message text

        Returns:
            URL string if found, None otherwise
        """
        match = LinkDetector.URL_PATTERN.search(text)
        return match.group(0) if match else None

    @staticmethod
    def classify_url(url: str) -> ContentType:
        """Determine content type from URL.

        Args:
            url: URL to classify

        Returns:
            Content type (web, youtube, pdf, github)
        """
        if LinkDetector.YOUTUBE_PATTERN.search(url):
            return "youtube"
        elif LinkDetector.GITHUB_PATTERN.search(url):
            return "github"
        elif LinkDetector.PDF_PATTERN.search(url):
            return "pdf"
        else:
            return "web"

    @staticmethod
    def is_url(text: str) -> bool:
        """Check if text contains a URL.

        Args:
            text: Text to check

        Returns:
            True if text contains URL, False otherwise
        """
        return LinkDetector.extract_url(text) is not None
