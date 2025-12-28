"""Tests for ConversationManager."""
import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.conversation import ConversationManager, TranscriptSegment


@pytest.fixture
def conversation_manager():
    """Create a ConversationManager instance."""
    return ConversationManager(context_window_minutes=10)


@pytest.mark.asyncio
async def test_add_segment(conversation_manager):
    """Test adding a transcript segment."""
    segment = await conversation_manager.add_segment("Hello world", speaker="Alice")
    
    assert segment.text == "Hello world"
    assert segment.speaker == "Alice"
    assert segment.is_final == True


@pytest.mark.asyncio
async def test_get_recent_context(conversation_manager):
    """Test getting recent conversation context."""
    await conversation_manager.add_segment("First message", speaker="Alice")
    await conversation_manager.add_segment("Second message", speaker="Bob")
    
    context = await conversation_manager.get_recent_context()
    
    assert "[Alice]: First message" in context
    assert "[Bob]: Second message" in context


@pytest.mark.asyncio
async def test_get_segment_count(conversation_manager):
    """Test counting segments."""
    await conversation_manager.add_segment("Message 1", speaker="Alice")
    await conversation_manager.add_segment("Message 2", speaker="Bob")
    await conversation_manager.add_segment("Message 3", speaker="Alice")
    
    count = await conversation_manager.get_segment_count()
    assert count == 3


@pytest.mark.asyncio
async def test_clear(conversation_manager):
    """Test clearing conversation history."""
    await conversation_manager.add_segment("Some message", speaker="Alice")
    await conversation_manager.clear()
    
    count = await conversation_manager.get_segment_count()
    assert count == 0


@pytest.mark.asyncio
async def test_export_json(conversation_manager):
    """Test exporting transcript as JSON."""
    await conversation_manager.add_segment("Test message", speaker="Alice")
    
    json_export = await conversation_manager.export_json()
    
    assert "Test message" in json_export
    assert "Alice" in json_export


@pytest.mark.asyncio
async def test_subscribe_to_updates(conversation_manager):
    """Test subscribing to transcript updates."""
    queue = conversation_manager.subscribe()
    
    await conversation_manager.add_segment("New message", speaker="Bob")
    
    # Check that the message was received
    segment = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert segment.text == "New message"
    assert segment.speaker == "Bob"
    
    conversation_manager.unsubscribe(queue)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
