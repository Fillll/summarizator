"""Tests for text utilities."""
import pytest
from datetime import datetime

from bot.utils.text_utils import format_document_list, truncate_text, escape_markdown
from bot.storage.models import Document


def test_format_document_list_empty():
    """Test formatting empty document list."""
    result = format_document_list([])
    assert result == "No documents in your collection yet."


def test_format_document_list_single():
    """Test formatting single document."""
    doc = Document(
        doc_id="doc1",
        url="https://example.com",
        title="Test Document",
        content_type="web",
        added_at=datetime.now(),
        content_preview="Preview"
    )

    result = format_document_list([doc])
    assert "Your document collection:" in result
    assert "[Test Document](https://example.com)" in result


def test_format_document_list_multiple():
    """Test formatting multiple documents."""
    docs = [
        Document(
            doc_id="doc1",
            url="https://example.com/1",
            title="First Doc",
            content_type="web",
            added_at=datetime.now(),
            content_preview="Preview 1"
        ),
        Document(
            doc_id="doc2",
            url="https://example.com/2",
            title="Second Doc",
            content_type="pdf",
            added_at=datetime.now(),
            content_preview="Preview 2"
        )
    ]

    result = format_document_list(docs)
    assert "[First Doc](https://example.com/1)" in result
    assert "[Second Doc](https://example.com/2)" in result


def test_truncate_text_short():
    """Test truncating text shorter than max length."""
    text = "Short text"
    result = truncate_text(text, max_length=100)
    assert result == "Short text"


def test_truncate_text_exact():
    """Test truncating text at exact max length."""
    text = "a" * 200
    result = truncate_text(text, max_length=200)
    assert result == text


def test_truncate_text_long():
    """Test truncating text longer than max length."""
    text = "a" * 300
    result = truncate_text(text, max_length=200)
    assert len(result) == 200
    assert result.endswith("...")
    assert result == ("a" * 197) + "..."


def test_truncate_text_custom_length():
    """Test truncating with custom max length."""
    text = "This is a longer piece of text that should be truncated"
    result = truncate_text(text, max_length=20)
    assert len(result) == 20
    assert result.endswith("...")
    # Note: Truncation keeps the space if it falls at the cut point
    assert result == "This is a longer ..."


def test_escape_markdown_underscore():
    """Test escaping underscore in markdown."""
    text = "text_with_underscores"
    result = escape_markdown(text)
    assert result == r"text\_with\_underscores"


def test_escape_markdown_asterisk():
    """Test escaping asterisk in markdown."""
    text = "text*with*asterisks"
    result = escape_markdown(text)
    assert result == r"text\*with\*asterisks"


def test_escape_markdown_brackets():
    """Test escaping brackets in markdown."""
    text = "[link](url)"
    result = escape_markdown(text)
    assert result == r"\[link\]\(url\)"


def test_escape_markdown_multiple():
    """Test escaping multiple special characters."""
    text = "Special chars: _*[]()~`>#+-=|{}.!"
    result = escape_markdown(text)
    # All special chars should be escaped
    assert "\\_" in result
    assert "\\*" in result
    assert "\\[" in result
    assert "\\]" in result


def test_escape_markdown_normal_text():
    """Test that normal text is unchanged."""
    text = "Normal text with spaces and numbers 123"
    result = escape_markdown(text)
    assert result == text


def test_truncate_empty_string():
    """Test truncating empty string."""
    result = truncate_text("", max_length=100)
    assert result == ""


def test_truncate_with_spaces():
    """Test truncating text with spaces."""
    text = "Word " * 100  # 500 chars
    result = truncate_text(text, max_length=50)
    assert len(result) == 50
    assert result.endswith("...")
