"""LiveKit room integration for the Meeting Assistant."""
import asyncio
import os
import sys
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit import api, rtc
from config.settings import settings
from src.conversation import ConversationManager
from src.transcriber import DeepgramTranscriber
from src.reasoner import MeetingReasoner


class LiveKitMeetingAgent:
    """Agent that joins a LiveKit room and transcribes audio."""
    
    def __init__(self, room_name: str):
        self.room_name = room_name
        self.room = rtc.Room()
        self.conversation = ConversationManager(
            context_window_minutes=settings.CONTEXT_WINDOW_MINUTES
        )
        self.reasoner = MeetingReasoner()
        self.transcriber: Optional[DeepgramTranscriber] = None
        self._running = False
        
    async def connect(self):
        """Connect to the LiveKit room."""
        # Generate access token
        token = api.AccessToken(
            settings.LIVEKIT_API_KEY,
            settings.LIVEKIT_API_SECRET
        )
        token.with_identity("ai-meeting-assistant")
        token.with_name("AI Assistant")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=self.room_name
        ))
        
        jwt = token.to_jwt()
        
        # Set up event handlers
        @self.room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"[LiveKit] Audio track from: {participant.identity}")
                asyncio.create_task(self._process_audio_track(track, participant.identity))
        
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            print(f"[LiveKit] Participant joined: {participant.identity}")
        
        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            print(f"[LiveKit] Participant left: {participant.identity}")
        
        # Connect to room
        print(f"[LiveKit] Connecting to room: {self.room_name}")
        await self.room.connect(settings.LIVEKIT_URL, jwt)
        print(f"[LiveKit] Connected! Room SID: {self.room.sid}")
        self._running = True
        
    async def _process_audio_track(self, track: rtc.Track, speaker: str):
        """Process audio from a track."""
        audio_stream = rtc.AudioStream(track)
        
        # Create transcriber for this track
        async def on_transcript(text: str, is_final: bool):
            if is_final and text.strip():
                await self.conversation.add_segment(text, speaker=speaker)
                print(f"[{speaker}]: {text}")
        
        transcriber = DeepgramTranscriber(on_transcript)
        await transcriber.start()
        
        try:
            async for frame_event in audio_stream:
                if self._running:
                    # Send audio to transcriber
                    audio_bytes = frame_event.frame.data.tobytes()
                    await transcriber.send_audio(audio_bytes)
        finally:
            await transcriber.stop()
    
    async def get_summary(self) -> str:
        """Get meeting summary."""
        context = await self.conversation.get_recent_context()
        return await self.reasoner.generate_summary(context)
    
    async def ask_question(self, question: str) -> str:
        """Ask a question about the meeting."""
        context = await self.conversation.get_recent_context()
        return await self.reasoner.answer_question(question, context)
    
    async def disconnect(self):
        """Disconnect from room."""
        self._running = False
        await self.room.disconnect()
        print("[LiveKit] Disconnected")


async def main():
    """Run the agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LiveKit Meeting Assistant Agent")
    parser.add_argument("--room", "-r", default="test-room", help="Room name to join")
    args = parser.parse_args()
    
    # Validate settings
    missing = settings.validate()
    if missing:
        print(f"❌ Missing required environment variables: {missing}")
        print("Please fill in your .env file")
        return
    
    agent = LiveKitMeetingAgent(args.room)
    
    try:
        await agent.connect()
        print("\n✅ Agent is running! Join the room to start transcription.")
        print(f"   Room: {args.room}")
        print("   Press Ctrl+C to stop\n")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
