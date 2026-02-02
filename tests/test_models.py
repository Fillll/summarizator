"""Tests for data models."""
import pytest
from datetime import datetime
import json

from bot.storage.models import Document, Message


def test_document_to_dict():
    """Test Document serialization to dict."""
    now = datetime.now()
    doc = Document(
        doc_id="test123",
        url="https://example.com",
        title="Test Doc",
        content_type="web",
        added_at=now,
        content_preview="Preview text"
    )

    doc_dict = doc.to_dict()

    assert doc_dict['doc_id'] == "test123"
    assert doc_dict['url'] == "https://example.com"
    assert doc_dict['title'] == "Test Doc"
    assert doc_dict['content_type'] == "web"
    assert doc_dict['added_at'] == now.isoformat()
    assert doc_dict['content_preview'] == "Preview text"


def test_document_from_dict():
    """Test Document deserialization from dict."""
    now = datetime.now()
    doc_dict = {
        'doc_id': "test456",
        'url': "https://example.com/article",
        'title': "Article Title",
        'content_type': "pdf",
        'added_at': now.isoformat(),
        'content_preview': "Article preview"
    }

    doc = Document.from_dict(doc_dict)

    assert doc.doc_id == "test456"
    assert doc.url == "https://example.com/article"
    assert doc.title == "Article Title"
    assert doc.content_type == "pdf"
    assert doc.added_at == now
    assert doc.content_preview == "Article preview"


def test_document_roundtrip():
    """Test Document serialization roundtrip."""
    original = Document(
        doc_id="roundtrip",
        url="https://example.com/test",
        title="Roundtrip Test",
        content_type="youtube",
        added_at=datetime.now(),
        content_preview="Testing roundtrip"
    )

    doc_dict = original.to_dict()
    restored = Document.from_dict(doc_dict)

    assert restored.doc_id == original.doc_id
    assert restored.url == original.url
    assert restored.title == original.title
    assert restored.content_type == original.content_type
    assert restored.content_preview == original.content_preview
    # Compare timestamps (may have microsecond differences)
    assert abs((restored.added_at - original.added_at).total_seconds()) < 1


def test_message_to_dict():
    """Test Message serialization to dict."""
    now = datetime.now()
    msg = Message(
        message_id="msg123",
        user_id="user456",
        timestamp=now,
        content="Hello, bot!",
        is_bot=False,
        metadata={"key": "value"}
    )

    msg_dict = msg.to_dict()

    assert msg_dict['message_id'] == "msg123"
    assert msg_dict['user_id'] == "user456"
    assert msg_dict['timestamp'] == now.isoformat()
    assert msg_dict['content'] == "Hello, bot!"
    assert msg_dict['is_bot'] is False
    assert msg_dict['metadata'] == {"key": "value"}


def test_message_from_dict():
    """Test Message deserialization from dict."""
    now = datetime.now()
    msg_dict = {
        'message_id': "msg789",
        'user_id': "user999",
        'timestamp': now.isoformat(),
        'content': "Hello, user!",
        'is_bot': True,
        'metadata': None
    }

    msg = Message.from_dict(msg_dict)

    assert msg.message_id == "msg789"
    assert msg.user_id == "user999"
    assert msg.timestamp == now
    assert msg.content == "Hello, user!"
    assert msg.is_bot is True
    assert msg.metadata is None


def test_message_to_json():
    """Test Message JSON serialization."""
    now = datetime.now()
    msg = Message(
        message_id="json_test",
        user_id="user1",
        timestamp=now,
        content="Test message",
        is_bot=False
    )

    json_str = msg.to_json()
    parsed = json.loads(json_str)

    assert parsed['message_id'] == "json_test"
    assert parsed['content'] == "Test message"
    assert parsed['is_bot'] is False


def test_message_from_json():
    """Test Message JSON deserialization."""
    now = datetime.now()
    json_str = json.dumps({
        'message_id': "from_json",
        'user_id': "user2",
        'timestamp': now.isoformat(),
        'content': "From JSON",
        'is_bot': True,
        'metadata': {"source": "test"}
    })

    msg = Message.from_json(json_str)

    assert msg.message_id == "from_json"
    assert msg.user_id == "user2"
    assert msg.content == "From JSON"
    assert msg.is_bot is True
    assert msg.metadata == {"source": "test"}


def test_message_roundtrip():
    """Test Message serialization roundtrip."""
    original = Message(
        message_id="roundtrip_msg",
        user_id="user_rt",
        timestamp=datetime.now(),
        content="Roundtrip message",
        is_bot=False,
        metadata={"test": True}
    )

    msg_dict = original.to_dict()
    restored = Message.from_dict(msg_dict)

    assert restored.message_id == original.message_id
    assert restored.user_id == original.user_id
    assert restored.content == original.content
    assert restored.is_bot == original.is_bot
    assert restored.metadata == original.metadata


def test_message_without_metadata():
    """Test Message with None metadata."""
    msg = Message(
        message_id="no_meta",
        user_id="user3",
        timestamp=datetime.now(),
        content="No metadata",
        is_bot=True
    )

    msg_dict = msg.to_dict()
    assert msg_dict['metadata'] is None

    restored = Message.from_dict(msg_dict)
    assert restored.metadata is None
