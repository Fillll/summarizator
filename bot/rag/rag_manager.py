"""RAG operations manager."""
from typing import List, Dict, Any
from datetime import datetime
import hashlib
from openai import AsyncOpenAI
from bot.rag.embedding_store import EmbeddingStore
from bot.storage.base import BaseStorage
from bot.storage.models import Document, Message
from bot.prompts.manager import PromptManager
from bot.utils.config import Config


class RAGManager:
    """Manages RAG operations for a user."""

    def __init__(
        self,
        user_id: str,
        storage: BaseStorage,
        config: Config,
        prompt_manager: PromptManager
    ):
        """Initialize RAG manager.

        Args:
            user_id: User's unique identifier
            storage: Storage implementation
            config: Configuration object
            prompt_manager: Prompt manager instance
        """
        self.user_id = user_id
        self.storage = storage
        self.config = config
        self.prompt_manager = prompt_manager

        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=config.openai_api_key)

        # Initialize embedding store
        db_path = storage.get_user_db_path(user_id)
        self.embedding_store = EmbeddingStore(db_path)

    async def add_document(
        self,
        url: str,
        content: str,
        title: str,
        content_type: str
    ) -> Document:
        """Add document to RAG index.

        Args:
            url: Document URL
            content: Document content (markdown)
            title: Document title
            content_type: Type of content (web, youtube, pdf, github)

        Returns:
            Created Document object
        """
        # Generate document ID from URL
        doc_id = hashlib.md5(url.encode()).hexdigest()

        # Create document metadata
        content_preview = content[:self.config.max_document_preview_length]
        document = Document(
            doc_id=doc_id,
            url=url,
            title=title,
            content_type=content_type,
            added_at=datetime.now(),
            content_preview=content_preview
        )

        # Save to storage
        await self.storage.save_document(self.user_id, document)

        # Add to embedding store
        await self.embedding_store.add_document(
            doc_id=doc_id,
            content=content,
            metadata={
                'url': url,
                'title': title,
                'content_type': content_type,
                'added_at': document.added_at.isoformat()
            }
        )

        return document

    async def query(
        self,
        question: str,
        conversation_history: List[Message],
        n_results: int = 3
    ) -> str:
        """Query RAG with conversation context.

        Args:
            question: User's question
            conversation_history: Recent conversation messages
            n_results: Number of documents to retrieve

        Returns:
            Generated answer
        """
        # Query embedding store for relevant documents
        relevant_docs = await self.embedding_store.query(question, n_results=n_results)

        # Format conversation history
        history_text = self._format_conversation_history(conversation_history)

        # Format retrieved documents
        docs_text = self._format_retrieved_documents(relevant_docs)

        # Get RAG prompt template
        prompt_template = self.prompt_manager.get_rag_prompt()

        # Fill in template
        prompt = prompt_template.format(
            conversation_history=history_text,
            retrieved_documents=docs_text,
            question=question
        )

        # Call OpenAI API
        response = await self.openai_client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content

    async def get_document_list(self) -> List[Document]:
        """Get list of all documents in RAG.

        Returns:
            List of Document objects
        """
        return await self.storage.get_documents(self.user_id)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from RAG.

        Args:
            doc_id: Document identifier

        Returns:
            True if deleted, False if not found
        """
        # Delete from embedding store
        embedding_deleted = await self.embedding_store.delete_document(doc_id)

        # Delete from storage
        storage_deleted = await self.storage.delete_document(self.user_id, doc_id)

        return embedding_deleted or storage_deleted

    async def clear_all_documents(self) -> int:
        """Clear all documents from RAG.

        Returns:
            Number of documents deleted
        """
        # Clear from embedding store
        await self.embedding_store.clear_all()

        # Clear from storage
        count = await self.storage.clear_documents(self.user_id)

        return count

    def _format_conversation_history(self, messages: List[Message]) -> str:
        """Format conversation history for prompt.

        Args:
            messages: List of Message objects

        Returns:
            Formatted conversation history
        """
        if not messages:
            return "No previous conversation."

        lines = []
        for msg in messages:
            role = "Assistant" if msg.is_bot else "User"
            lines.append(f"{role}: {msg.content}")

        return "\n".join(lines)

    def _format_retrieved_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents for prompt.

        Args:
            documents: List of retrieved document dicts

        Returns:
            Formatted documents
        """
        if not documents:
            return "No relevant documents found."

        lines = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            title = metadata.get('title', 'Untitled')
            url = metadata.get('url', '')
            content = doc.get('content', '')

            lines.append(f"Document {i}: {title}")
            lines.append(f"URL: {url}")
            lines.append(f"Content: {content[:500]}...")  # Truncate to 500 chars
            lines.append("")

        return "\n".join(lines)
