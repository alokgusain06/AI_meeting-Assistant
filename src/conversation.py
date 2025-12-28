"""Conversation context manager for tracking meeting transcripts."""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import json


@dataclass
class TranscriptSegment:
    """A segment of transcribed speech."""
    text: str
    speaker: str
    timestamp: datetime
    is_final: bool = True
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "speaker": self.speaker,
            "timestamp": self.timestamp.isoformat(),
            "is_final": self.is_final
        }


class ConversationManager:
    """Manages the conversation history with a sliding window for memory efficiency."""
    
    def __init__(self, context_window_minutes: int = 10):
        self.context_window = timedelta(minutes=context_window_minutes)
        self.segments: list[TranscriptSegment] = []
        self.full_transcript: list[TranscriptSegment] = []  # Keep full history
        self._lock = asyncio.Lock()
        self._listeners: list[asyncio.Queue] = []
    
    async def add_segment(self, text: str, speaker: str = "Unknown", is_final: bool = True) -> TranscriptSegment:
        """Add a new transcript segment."""
        segment = TranscriptSegment(
            text=text.strip(),
            speaker=speaker,
            timestamp=datetime.now(),
            is_final=is_final
        )
        
        async with self._lock:
            if is_final:
                self.segments.append(segment)
                self.full_transcript.append(segment)
                # Notify listeners
                for queue in self._listeners:
                    await queue.put(segment)
        
        return segment
    
    async def get_recent_context(self, max_chars: int = 8000) -> str:
        """Get recent conversation within the context window, limited by character count."""
        async with self._lock:
            cutoff = datetime.now() - self.context_window
            recent = [s for s in self.segments if s.timestamp >= cutoff and s.is_final]
            
            # Build context string, respecting max chars
            lines = []
            total_chars = 0
            for segment in reversed(recent):
                line = f"[{segment.speaker}]: {segment.text}"
                if total_chars + len(line) > max_chars:
                    break
                lines.insert(0, line)
                total_chars += len(line) + 1
            
            return "\n".join(lines)
    
    async def get_full_transcript(self) -> str:
        """Get the complete transcript of the meeting."""
        async with self._lock:
            lines = [f"[{s.speaker}]: {s.text}" for s in self.full_transcript if s.is_final]
            return "\n".join(lines)
    
    async def get_segment_count(self) -> int:
        """Get number of transcript segments."""
        async with self._lock:
            return len(self.full_transcript)
    
    def subscribe(self) -> asyncio.Queue:
        """Subscribe to new transcript segments. Returns a queue that receives new segments."""
        queue = asyncio.Queue()
        self._listeners.append(queue)
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from transcript updates."""
        if queue in self._listeners:
            self._listeners.remove(queue)
    
    async def clear(self):
        """Clear all transcript history."""
        async with self._lock:
            self.segments.clear()
            self.full_transcript.clear()
    
    async def prune_old_segments(self):
        """Remove segments outside the context window from active memory."""
        async with self._lock:
            cutoff = datetime.now() - self.context_window
            self.segments = [s for s in self.segments if s.timestamp >= cutoff]
    
    async def export_json(self) -> str:
        """Export full transcript as JSON."""
        async with self._lock:
            return json.dumps([s.to_dict() for s in self.full_transcript], indent=2)
