"""Custom exceptions for the bot."""


class BotException(Exception):
    """Base exception for bot errors."""
    pass


class ContentExtractionError(BotException):
    """Raised when content extraction fails."""
    pass


class RAGError(BotException):
    """Raised when RAG operations fail."""
    pass


class StorageError(BotException):
    """Raised when storage operations fail."""
    pass


class ConfigurationError(BotException):
    """Raised when configuration is invalid."""
    pass
