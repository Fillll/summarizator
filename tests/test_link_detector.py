"""Tests for link detection and classification."""
import pytest
from bot.utils.link_detector import LinkDetector


def test_extract_url_from_text():
    """Test extracting URL from text."""
    text = "Check out this link: https://example.com/article"
    url = LinkDetector.extract_url(text)
    assert url == "https://example.com/article"


def test_extract_url_with_multiple_urls():
    """Test extracting first URL when multiple present."""
    text = "Links: https://first.com and https://second.com"
    url = LinkDetector.extract_url(text)
    assert url == "https://first.com"


def test_extract_url_no_url():
    """Test when no URL present."""
    text = "This is just plain text with no links"
    url = LinkDetector.extract_url(text)
    assert url is None


def test_classify_youtube_url():
    """Test classifying YouTube URLs."""
    urls = [
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=abc123",
        "https://youtu.be/xyz789"
    ]
    for url in urls:
        content_type = LinkDetector.classify_url(url)
        assert content_type == "youtube"


def test_classify_github_url():
    """Test classifying GitHub URLs."""
    urls = [
        "https://github.com/anthropics/claude-code",
        "https://github.com/user/repo",
        "https://github.com/org/project"
    ]
    for url in urls:
        content_type = LinkDetector.classify_url(url)
        assert content_type == "github"


def test_classify_pdf_url():
    """Test classifying PDF URLs."""
    urls = [
        "https://example.com/document.pdf",
        "https://example.com/paper.PDF",
        "https://example.com/file.pdf?download=true",
        "https://example.com/doc.pdf#page=1"
    ]
    for url in urls:
        content_type = LinkDetector.classify_url(url)
        assert content_type == "pdf"


def test_classify_web_url():
    """Test classifying regular web URLs."""
    urls = [
        "https://example.com/article",
        "https://news.site.com/story/123",
        "https://blog.example.org/post"
    ]
    for url in urls:
        content_type = LinkDetector.classify_url(url)
        assert content_type == "web"


def test_is_url_true():
    """Test checking if text contains URL."""
    texts = [
        "Check this: https://example.com",
        "Visit http://site.com for more",
        "https://example.com"
    ]
    for text in texts:
        assert LinkDetector.is_url(text) is True


def test_is_url_false():
    """Test checking if text doesn't contain URL."""
    texts = [
        "No links here",
        "Just plain text",
        "example.com without protocol"
    ]
    for text in texts:
        assert LinkDetector.is_url(text) is False


def test_extract_url_with_parameters():
    """Test extracting URL with query parameters."""
    text = "Link: https://example.com/page?param=value&other=123"
    url = LinkDetector.extract_url(text)
    assert url == "https://example.com/page?param=value&other=123"


def test_classify_priority_youtube_over_web():
    """Test that YouTube classification takes priority."""
    url = "https://youtube.com/watch?v=abc123"
    content_type = LinkDetector.classify_url(url)
    assert content_type == "youtube"


def test_classify_priority_github_over_web():
    """Test that GitHub classification takes priority."""
    url = "https://github.com/user/repo"
    content_type = LinkDetector.classify_url(url)
    assert content_type == "github"


def test_classify_priority_pdf_over_web():
    """Test that PDF classification takes priority."""
    url = "https://example.com/document.pdf"
    content_type = LinkDetector.classify_url(url)
    assert content_type == "pdf"
