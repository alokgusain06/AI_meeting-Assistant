"""Configuration settings for the Meeting Assistant."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # LiveKit Configuration
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")
    
    # Deepgram Configuration
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    
    # Gemini Configuration (Primary LLM)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # OpenAI Configuration (Optional fallback)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Agent Settings
    SUMMARY_INTERVAL_SECONDS: int = int(os.getenv("SUMMARY_INTERVAL_SECONDS", "120"))
    CONTEXT_WINDOW_MINUTES: int = int(os.getenv("CONTEXT_WINDOW_MINUTES", "10"))
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required settings are present. Returns list of missing keys."""
        missing = []
        if not cls.LIVEKIT_URL:
            missing.append("LIVEKIT_URL")
        if not cls.LIVEKIT_API_KEY:
            missing.append("LIVEKIT_API_KEY")
        if not cls.LIVEKIT_API_SECRET:
            missing.append("LIVEKIT_API_SECRET")
        if not cls.DEEPGRAM_API_KEY:
            missing.append("DEEPGRAM_API_KEY")
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        return missing


settings = Settings()
