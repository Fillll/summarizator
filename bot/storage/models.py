"""Data models for storage layer."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class Document:
    """Represents a document stored in the RAG system."""
    doc_id: str
    url: str
    title: str
    content_type: str  # web, youtube, pdf, github
    added_at: datetime
    content_preview: str  # First 200 chars

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['added_at'] = self.added_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create Document from dictionary."""
        data = data.copy()
        data['added_at'] = datetime.fromisoformat(data['added_at'])
        return cls(**data)


@dataclass
class Message:
    """Represents a conversation message."""
    message_id: str
    user_id: str
    timestamp: datetime
    content: str
    is_bot: bool
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create Message from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string for JSONL storage."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create Message from JSON string."""
        return cls.from_dict(json.loads(json_str))
