#!/usr/bin/env python3
"""Test script to verify installation."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    errors = []
    
    try:
        from src.conversation import ConversationManager
        print("✅ src.conversation")
    except Exception as e:
        errors.append(f"src.conversation: {e}")
        print(f"❌ src.conversation: {e}")
    
    try:
        from src.reasoner import MeetingReasoner
        print("✅ src.reasoner")
    except Exception as e:
        errors.append(f"src.reasoner: {e}")
        print(f"❌ src.reasoner: {e}")
    
    try:
        from src.transcriber import DeepgramTranscriber, MockTranscriber
        print("✅ src.transcriber")
    except Exception as e:
        errors.append(f"src.transcriber: {e}")
        print(f"❌ src.transcriber: {e}")
    
    try:
        from config.settings import settings
        print("✅ config.settings")
    except Exception as e:
        errors.append(f"config.settings: {e}")
        print(f"❌ config.settings: {e}")
    
    try:
        from src.web_app import app, socketio
        print("✅ src.web_app")
    except Exception as e:
        errors.append(f"src.web_app: {e}")
        print(f"❌ src.web_app: {e}")
    
    if errors:
        print(f"\n❌ {len(errors)} import error(s)")
        return 1
    else:
        print("\n✅ All modules import successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(test_imports())
