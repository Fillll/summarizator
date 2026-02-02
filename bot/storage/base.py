"""Abstract base class for storage implementations."""
from abc import ABC, abstractmethod
from typing import List, Optional
from bot.storage.models import Document, Message


class BaseStorage(ABC):
    """Abstract storage interface for future database migration."""

    @abstractmethod
    async def save_document(self, user_id: str, document: Document) -> None:
        """Save document metadata for a user.

        Args:
            user_id: User's unique identifier
            document: Document object to save
        """
        pass

    @abstractmethod
    async def get_documents(self, user_id: str) -> List[Document]:
        """Retrieve all documents for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            List of Document objects
        """
        pass

    @abstractmethod
    async def get_document(self, user_id: str, doc_id: str) -> Optional[Document]:
        """Retrieve a specific document for a user.

        Args:
            user_id: User's unique identifier
            doc_id: Document identifier

        Returns:
            Document object if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_document(self, user_id: str, doc_id: str) -> bool:
        """Delete a specific document for a user.

        Args:
            user_id: User's unique identifier
            doc_id: Document identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def clear_documents(self, user_id: str) -> int:
        """Delete all documents for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            Number of documents deleted
        """
        pass

    @abstractmethod
    async def save_message(self, user_id: str, message: Message) -> None:
        """Save conversation message.

        Args:
            user_id: User's unique identifier
            message: Message object to save
        """
        pass

    @abstractmethod
    async def get_messages(self, user_id: str, limit: Optional[int] = None) -> List[Message]:
        """Retrieve recent conversation history.

        Args:
            user_id: User's unique identifier
            limit: Maximum number of messages to retrieve (None for all)

        Returns:
            List of Message objects, most recent last
        """
        pass

    @abstractmethod
    async def get_user_stats(self, user_id: str) -> dict:
        """Get statistics for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            Dictionary with stats (num_documents, num_messages, etc.)
        """
        pass

    @abstractmethod
    def get_user_db_path(self, user_id: str) -> str:
        """Get path to user's vector database directory.

        Args:
            user_id: User's unique identifier

        Returns:
            Path to user's Chroma DB directory
        """
        pass
