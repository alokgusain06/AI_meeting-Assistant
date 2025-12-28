"""Speech-to-text transcription using Deepgram."""
import asyncio
from typing import Callable, Optional
import aiohttp
import json
from config.settings import settings


class DeepgramTranscriber:
    """Real-time speech-to-text transcription using Deepgram's streaming API."""
    
    DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen"
    
    def __init__(self, on_transcript: Callable[[str, bool], None]):
        """
        Initialize transcriber.
        
        Args:
            on_transcript: Callback function(text, is_final) called when transcript is received.
        """
        self.on_transcript = on_transcript
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
    
    async def start(self, sample_rate: int = 16000, channels: int = 1):
        """Start the transcription websocket connection."""
        if self._running:
            return
        
        # Build URL with query parameters
        params = {
            "encoding": "linear16",
            "sample_rate": str(sample_rate),
            "channels": str(channels),
            "model": "nova-2",
            "punctuate": "true",
            "interim_results": "true",
            "endpointing": "300",
            "vad_events": "true"
        }
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.DEEPGRAM_URL}?{query}"
        
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}"
        }
        
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(url, headers=headers)
        self._running = True
        
        # Start receiving messages
        self._receive_task = asyncio.create_task(self._receive_loop())
        print("[Transcriber] Connected to Deepgram")
    
    async def _receive_loop(self):
        """Receive and process transcription results."""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._process_response(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"[Transcriber] WebSocket error: {msg.data}")
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Transcriber] Error in receive loop: {e}")
    
    async def _process_response(self, data: dict):
        """Process a Deepgram response."""
        if data.get("type") == "Results":
            channel = data.get("channel", {})
            alternatives = channel.get("alternatives", [])
            
            if alternatives:
                transcript = alternatives[0].get("transcript", "")
                is_final = data.get("is_final", False)
                
                if transcript.strip():
                    # Call the callback
                    if asyncio.iscoroutinefunction(self.on_transcript):
                        await self.on_transcript(transcript, is_final)
                    else:
                        self.on_transcript(transcript, is_final)
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data for transcription."""
        if self._ws and self._running:
            try:
                await self._ws.send_bytes(audio_data)
            except Exception as e:
                print(f"[Transcriber] Error sending audio: {e}")
    
    async def stop(self):
        """Stop the transcription connection."""
        self._running = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
        
        if self._session:
            await self._session.close()
        
        print("[Transcriber] Disconnected from Deepgram")


class MockTranscriber:
    """Mock transcriber for testing without Deepgram API."""
    
    def __init__(self, on_transcript: Callable[[str, bool], None]):
        self.on_transcript = on_transcript
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, sample_rate: int = 16000, channels: int = 1):
        """Start mock transcription."""
        self._running = True
        self._task = asyncio.create_task(self._simulate_transcripts())
        print("[MockTranscriber] Started")
    
    async def _simulate_transcripts(self):
        """Simulate receiving transcripts."""
        sample_phrases = [
            "Hello everyone, let's get started with the meeting.",
            "Today we need to discuss the project timeline.",
            "I think we should prioritize the backend API first.",
            "That's a good point. What about the frontend?",
            "We can work on both in parallel if we have enough resources.",
            "Let's set a deadline for next Friday.",
            "I'll take the action item to prepare the documentation.",
            "Does everyone agree with this approach?",
            "Yes, that sounds good to me.",
            "Great, let's move on to the next topic."
        ]
        
        idx = 0
        while self._running:
            await asyncio.sleep(3)  # Simulate speech every 3 seconds
            if self._running and idx < len(sample_phrases):
                phrase = sample_phrases[idx]
                if asyncio.iscoroutinefunction(self.on_transcript):
                    await self.on_transcript(phrase, True)
                else:
                    self.on_transcript(phrase, True)
                idx = (idx + 1) % len(sample_phrases)
    
    async def send_audio(self, audio_data: bytes):
        """Mock audio send - does nothing."""
        pass
    
    async def stop(self):
        """Stop mock transcription."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[MockTranscriber] Stopped")
