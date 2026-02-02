"""Per-user Chroma DB embedding storage."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any


class EmbeddingStore:
    """Manages per-user Chroma DB instances."""

    def __init__(self, db_path: str):
        """Initialize embedding store for a user.

        Args:
            db_path: Path to user's Chroma DB directory
        """
        self.db_path = db_path
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )

    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Add document to embedding store.

        Args:
            doc_id: Unique document identifier
            content: Document content to embed
            metadata: Document metadata
        """
        # Check if document already exists
        existing = self.collection.get(ids=[doc_id])
        if existing and existing['ids']:
            # Update existing document
            self.collection.update(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )
        else:
            # Add new document
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )

    async def query(
        self,
        query_text: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Query embedding store for relevant documents.

        Args:
            query_text: Query text
            n_results: Number of results to return

        Returns:
            List of relevant documents with metadata
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count())
        )

        if not results['documents'] or not results['documents'][0]:
            return []

        # Format results
        documents = []
        for i in range(len(results['ids'][0])):
            documents.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results.get('distances') else None
            })

        return documents

    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from embedding store.

        Args:
            doc_id: Document identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except:
            return False

    async def clear_all(self) -> int:
        """Clear all documents from embedding store.

        Returns:
            Number of documents deleted
        """
        count = self.collection.count()
        self.client.delete_collection(name="documents")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        return count

    def get_document_count(self) -> int:
        """Get number of documents in store.

        Returns:
            Document count
        """
        return self.collection.count()
