"""Text formatting and utility functions."""
from typing import List
from bot.storage.models import Document


def format_document_list(documents: List[Document]) -> str:
    """Format list of documents as markdown.

    Args:
        documents: List of Document objects

    Returns:
        Markdown-formatted list of documents
    """
    if not documents:
        return "No documents in your collection yet."

    lines = ["Your document collection:"]
    for doc in documents:
        lines.append(f"- [{doc.title}]({doc.url})")

    return "\n".join(lines)


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    """Escape special markdown characters in text.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for markdown
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
