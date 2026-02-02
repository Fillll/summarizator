"""File-based storage implementation."""
import json
import os
from pathlib import Path
from typing import List, Optional
import aiofiles
from bot.storage.base import BaseStorage
from bot.storage.models import Document, Message


class FileStorage(BaseStorage):
    """File-based storage implementation."""

    def __init__(self, data_dir: str = "data"):
        """Initialize file storage.

        Args:
            data_dir: Base directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def _get_user_dir(self, user_id: str) -> Path:
        """Get user's data directory, creating if needed."""
        user_dir = self.data_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)
        return user_dir

    def _get_documents_file(self, user_id: str) -> Path:
        """Get path to user's documents.json file."""
        return self._get_user_dir(user_id) / "documents.json"

    def _get_messages_file(self, user_id: str) -> Path:
        """Get path to user's messages.jsonl file."""
        return self._get_user_dir(user_id) / "messages.jsonl"

    def get_user_db_path(self, user_id: str) -> str:
        """Get path to user's vector database directory."""
        db_path = self._get_user_dir(user_id) / "chroma_db"
        db_path.mkdir(exist_ok=True)
        return str(db_path)

    async def save_document(self, user_id: str, document: Document) -> None:
        """Save document metadata for a user."""
        documents_file = self._get_documents_file(user_id)

        # Load existing documents
        documents = await self.get_documents(user_id)

        # Check if document already exists and update or append
        existing_idx = None
        for idx, doc in enumerate(documents):
            if doc.doc_id == document.doc_id:
                existing_idx = idx
                break

        if existing_idx is not None:
            documents[existing_idx] = document
        else:
            documents.append(document)

        # Save back to file
        async with aiofiles.open(documents_file, 'w') as f:
            data = [doc.to_dict() for doc in documents]
            await f.write(json.dumps(data, indent=2))

    async def get_documents(self, user_id: str) -> List[Document]:
        """Retrieve all documents for a user."""
        documents_file = self._get_documents_file(user_id)

        if not documents_file.exists():
            return []

        async with aiofiles.open(documents_file, 'r') as f:
            content = await f.read()
            data = json.loads(content)
            return [Document.from_dict(doc_dict) for doc_dict in data]

    async def get_document(self, user_id: str, doc_id: str) -> Optional[Document]:
        """Retrieve a specific document for a user."""
        documents = await self.get_documents(user_id)
        for doc in documents:
            if doc.doc_id == doc_id:
                return doc
        return None

    async def delete_document(self, user_id: str, doc_id: str) -> bool:
        """Delete a specific document for a user."""
        documents = await self.get_documents(user_id)
        new_documents = [doc for doc in documents if doc.doc_id != doc_id]

        if len(new_documents) == len(documents):
            return False  # Document not found

        # Save updated list
        documents_file = self._get_documents_file(user_id)
        async with aiofiles.open(documents_file, 'w') as f:
            data = [doc.to_dict() for doc in new_documents]
            await f.write(json.dumps(data, indent=2))

        return True

    async def clear_documents(self, user_id: str) -> int:
        """Delete all documents for a user."""
        documents = await self.get_documents(user_id)
        count = len(documents)

        documents_file = self._get_documents_file(user_id)
        if documents_file.exists():
            async with aiofiles.open(documents_file, 'w') as f:
                await f.write(json.dumps([], indent=2))

        return count

    async def save_message(self, user_id: str, message: Message) -> None:
        """Save conversation message (append to JSONL file)."""
        messages_file = self._get_messages_file(user_id)

        async with aiofiles.open(messages_file, 'a') as f:
            await f.write(message.to_json() + '\n')

    async def get_messages(self, user_id: str, limit: Optional[int] = None) -> List[Message]:
        """Retrieve recent conversation history."""
        messages_file = self._get_messages_file(user_id)

        if not messages_file.exists():
            return []

        messages = []
        async with aiofiles.open(messages_file, 'r') as f:
            async for line in f:
                line = line.strip()
                if line:
                    messages.append(Message.from_json(line))

        # Return most recent messages if limit specified
        if limit is not None and len(messages) > limit:
            messages = messages[-limit:]

        return messages

    async def get_user_stats(self, user_id: str) -> dict:
        """Get statistics for a user."""
        documents = await self.get_documents(user_id)
        messages = await self.get_messages(user_id)

        # Calculate storage size
        user_dir = self._get_user_dir(user_id)
        storage_size = 0
        for file_path in user_dir.rglob('*'):
            if file_path.is_file():
                storage_size += file_path.stat().st_size

        return {
            'num_documents': len(documents),
            'num_messages': len(messages),
            'storage_size_bytes': storage_size,
            'storage_size_mb': round(storage_size / (1024 * 1024), 2)
        }
