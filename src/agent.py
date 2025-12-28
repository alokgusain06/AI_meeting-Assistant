"""Main Meeting Assistant agent using LiveKit."""
import asyncio
import logging
from typing import Optional
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import deepgram, silero

from src.conversation import ConversationManager
from src.reasoner import MeetingReasoner
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meeting-assistant")


class MeetingAssistant:
    """AI Meeting Assistant that listens, transcribes, and provides insights."""
    
    def __init__(self, room: rtc.Room):
        self.room = room
        self.conversation = ConversationManager(
            context_window_minutes=settings.CONTEXT_WINDOW_MINUTES
        )
        self.reasoner = MeetingReasoner()
        self._running = False
        self._summary_task: Optional[asyncio.Task] = None
        self._current_speaker = "Participant"
    
    async def start(self):
        """Start the meeting assistant."""
        self._running = True
        
        # Start periodic summary generation
        self._summary_task = asyncio.create_task(self._periodic_summary())
        
        logger.info("Meeting Assistant started")
    
    async def stop(self):
        """Stop the meeting assistant."""
        self._running = False
        
        if self._summary_task:
            self._summary_task.cancel()
            try:
                await self._summary_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Meeting Assistant stopped")
    
    async def handle_transcript(self, text: str, speaker: str = "Participant"):
        """Handle incoming transcript text."""
        await self.conversation.add_segment(text, speaker=speaker)
        logger.info(f"[{speaker}]: {text}")
    
    async def get_summary(self) -> str:
        """Get current meeting summary."""
        context = await self.conversation.get_recent_context()
        return await self.reasoner.generate_summary(context)
    
    async def ask_question(self, question: str) -> str:
        """Ask a question about the meeting."""
        context = await self.conversation.get_recent_context()
        return await self.reasoner.answer_question(question, context)
    
    async def get_current_topic(self) -> str:
        """Get the current topic being discussed."""
        context = await self.conversation.get_recent_context()
        return await self.reasoner.identify_current_topic(context)
    
    async def _periodic_summary(self):
        """Generate summaries periodically."""
        while self._running:
            await asyncio.sleep(settings.SUMMARY_INTERVAL_SECONDS)
            if self._running:
                try:
                    summary = await self.get_summary()
                    logger.info(f"[Auto Summary]\n{summary}")
                except Exception as e:
                    logger.error(f"Error generating periodic summary: {e}")


async def entrypoint(ctx: JobContext):
    """LiveKit agent entrypoint."""
    
    logger.info(f"Connecting to room: {ctx.room.name}")
    
    # Create the meeting assistant
    assistant = MeetingAssistant(ctx.room)
    
    # Set up Speech-to-Text using Deepgram
    stt = deepgram.STT(
        api_key=settings.DEEPGRAM_API_KEY,
        model="nova-2",
        language="en",
        punctuate=True,
        interim_results=True,
    )
    
    # Voice Activity Detection
    vad = silero.VAD.load()
    
    async def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle when we subscribe to a participant's audio track."""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(f"Subscribed to audio from: {participant.identity}")
            
            audio_stream = rtc.AudioStream(track)
            
            # Process audio frames
            async for frame_event in audio_stream:
                # Check for voice activity
                vad_result = await vad.detect(frame_event.frame)
                
                if vad_result.speech_detected:
                    # Transcribe the audio
                    async for event in stt.stream(frame_event.frame):
                        if event.alternatives and event.alternatives[0].text:
                            text = event.alternatives[0].text
                            is_final = event.is_final
                            
                            if is_final and text.strip():
                                await assistant.handle_transcript(
                                    text, 
                                    speaker=participant.identity or "Participant"
                                )
    
    # Subscribe to track events
    ctx.room.on("track_subscribed", on_track_subscribed)
    
    # Start the assistant
    await assistant.start()
    
    # Keep running until disconnected
    await ctx.room.disconnected


def run_agent():
    """Run the LiveKit agent."""
    # Validate settings
    missing = settings.validate()
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        logger.error("Please copy .env.example to .env and fill in your API keys")
        return
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            ws_url=settings.LIVEKIT_URL,
        )
    )


if __name__ == "__main__":
    run_agent()
