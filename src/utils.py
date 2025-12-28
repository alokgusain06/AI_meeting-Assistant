"""Utility functions for the Meeting Assistant."""
import os
import sys


def ensure_directories():
    """Ensure required directories exist."""
    dirs = ['logs', 'exports']
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def check_environment():
    """Check if all required environment variables are set."""
    required = [
        'LIVEKIT_URL',
        'LIVEKIT_API_KEY', 
        'LIVEKIT_API_SECRET',
        'DEEPGRAM_API_KEY',
        'OPENAI_API_KEY'
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print("⚠️  Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease copy .env.example to .env and fill in your API keys.")
        return False
    
    return True


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
