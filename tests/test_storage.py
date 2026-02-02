"""Tests for storage layer."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from bot.storage.file_storage import FileStorage
from bot.storage.models import Document, Message


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    yield storage
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_save_and_get_document(temp_storage):
    """Test saving and retrieving documents."""
    doc = Document(
        doc_id="test123",
        url="https://example.com",
        title="Test Document",
        content_type="web",
        added_at=datetime.now(),
        content_preview="This is a test preview"
    )

    await temp_storage.save_document("user1", doc)
    documents = await temp_storage.get_documents("user1")

    assert len(documents) == 1
    assert documents[0].doc_id == "test123"
    assert documents[0].title == "Test Document"


@pytest.mark.asyncio
async def test_get_document_by_id(temp_storage):
    """Test retrieving specific document."""
    doc = Document(
        doc_id="test456",
        url="https://example.com/test",
        title="Another Test",
        content_type="pdf",
        added_at=datetime.now(),
        content_preview="Preview text"
    )

    await temp_storage.save_document("user1", doc)
    retrieved = await temp_storage.get_document("user1", "test456")

    assert retrieved is not None
    assert retrieved.doc_id == "test456"
    assert retrieved.content_type == "pdf"


@pytest.mark.asyncio
async def test_delete_document(temp_storage):
    """Test deleting documents."""
    doc = Document(
        doc_id="delete_me",
        url="https://example.com",
        title="Delete Test",
        content_type="web",
        added_at=datetime.now(),
        content_preview="Preview"
    )

    await temp_storage.save_document("user1", doc)
    success = await temp_storage.delete_document("user1", "delete_me")

    assert success is True
    documents = await temp_storage.get_documents("user1")
    assert len(documents) == 0


@pytest.mark.asyncio
async def test_clear_documents(temp_storage):
    """Test clearing all documents."""
    for i in range(3):
        doc = Document(
            doc_id=f"doc{i}",
            url=f"https://example.com/{i}",
            title=f"Document {i}",
            content_type="web",
            added_at=datetime.now(),
            content_preview=f"Preview {i}"
        )
        await temp_storage.save_document("user1", doc)

    count = await temp_storage.clear_documents("user1")
    assert count == 3

    documents = await temp_storage.get_documents("user1")
    assert len(documents) == 0


@pytest.mark.asyncio
async def test_save_and_get_messages(temp_storage):
    """Test saving and retrieving messages."""
    msg1 = Message(
        message_id="msg1",
        user_id="user1",
        timestamp=datetime.now(),
        content="Hello bot",
        is_bot=False
    )
    msg2 = Message(
        message_id="msg2",
        user_id="user1",
        timestamp=datetime.now(),
        content="Hello user",
        is_bot=True
    )

    await temp_storage.save_message("user1", msg1)
    await temp_storage.save_message("user1", msg2)

    messages = await temp_storage.get_messages("user1")
    assert len(messages) == 2
    assert messages[0].content == "Hello bot"
    assert messages[1].is_bot is True


@pytest.mark.asyncio
async def test_get_messages_with_limit(temp_storage):
    """Test retrieving limited number of messages."""
    for i in range(10):
        msg = Message(
            message_id=f"msg{i}",
            user_id="user1",
            timestamp=datetime.now(),
            content=f"Message {i}",
            is_bot=i % 2 == 0
        )
        await temp_storage.save_message("user1", msg)

    messages = await temp_storage.get_messages("user1", limit=5)
    assert len(messages) == 5
    # Should get last 5 messages
    assert messages[-1].content == "Message 9"


@pytest.mark.asyncio
async def test_user_stats(temp_storage):
    """Test getting user statistics."""
    doc = Document(
        doc_id="stats_test",
        url="https://example.com",
        title="Stats Test",
        content_type="web",
        added_at=datetime.now(),
        content_preview="Preview"
    )
    await temp_storage.save_document("user1", doc)

    msg = Message(
        message_id="stats_msg",
        user_id="user1",
        timestamp=datetime.now(),
        content="Test message",
        is_bot=False
    )
    await temp_storage.save_message("user1", msg)

    stats = await temp_storage.get_user_stats("user1")
    assert stats['num_documents'] == 1
    assert stats['num_messages'] == 1
    assert stats['storage_size_bytes'] > 0


@pytest.mark.asyncio
async def test_multiple_users_isolation(temp_storage):
    """Test that users' data is isolated."""
    doc1 = Document(
        doc_id="user1_doc",
        url="https://example.com/1",
        title="User 1 Doc",
        content_type="web",
        added_at=datetime.now(),
        content_preview="User 1 preview"
    )
    doc2 = Document(
        doc_id="user2_doc",
        url="https://example.com/2",
        title="User 2 Doc",
        content_type="web",
        added_at=datetime.now(),
        content_preview="User 2 preview"
    )

    await temp_storage.save_document("user1", doc1)
    await temp_storage.save_document("user2", doc2)

    user1_docs = await temp_storage.get_documents("user1")
    user2_docs = await temp_storage.get_documents("user2")

    assert len(user1_docs) == 1
    assert len(user2_docs) == 1
    assert user1_docs[0].doc_id == "user1_doc"
    assert user2_docs[0].doc_id == "user2_doc"
