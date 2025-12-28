# Design Document: Real-Time AI Meeting Assistant

## Overview

This document describes the architecture and design decisions for the Real-Time AI Meeting Assistant, a system that joins online meetings, transcribes conversations, and provides AI-powered insights.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         MEETING ROOM (LiveKit)                       │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│   │ Participant│  │ Participant│  │ AI Agent   │                    │
│   │     A      │  │     B      │  │ (Listener) │                    │
│   └─────┬──────┘  └─────┬──────┘  └─────▲──────┘                    │
│         │               │               │                            │
│         └───────────────┴───────────────┘                            │
│                    Audio Streams                                     │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      SPEECH-TO-TEXT LAYER                            │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  Deepgram Streaming API                                      │   │
│   │  - Model: Nova-2                                             │   │
│   │  - Interim results enabled                                   │   │
│   │  - Punctuation enabled                                       │   │
│   │  - Voice Activity Detection (Silero VAD)                     │   │
│   └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION MANAGER                              │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  - Rolling transcript storage                                │   │
│   │  - 10-minute context window (configurable)                   │   │
│   │  - Speaker attribution                                       │   │
│   │  - Pub/Sub for real-time updates                            │   │
│   └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       LLM REASONER                                   │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  OpenAI GPT-4o-mini                                          │   │
│   │  - Summary generation                                        │   │
│   │  - Question answering                                        │   │
│   │  - Topic identification                                      │   │
│   │  - Streaming responses for low latency                       │   │
│   └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. LiveKit Agent (`agent.py`)

The agent uses the LiveKit Agents SDK to:
- Connect to meeting rooms
- Subscribe to audio tracks from participants
- Route audio to the transcription pipeline

**Key decisions:**
- Uses LiveKit's native audio handling rather than raw WebRTC
- Subscribes to all participant tracks automatically
- Maintains participant identity for speaker attribution

### 2. Transcriber (`transcriber.py`)

**Choice: Deepgram streaming API**

| Alternative | Pros | Cons |
|-------------|------|------|
| Deepgram (chosen) | Low latency (~300ms), interim results | Requires API key |
| OpenAI Whisper | High accuracy, free locally | Higher latency, batch only |
| Google STT | Good accuracy | Higher cost |

**Design:**
- WebSocket connection for streaming
- Voice Activity Detection (VAD) to reduce API calls
- Interim results for perceived lower latency
- Callback-based interface for loose coupling

### 3. Conversation Manager (`conversation.py`)

**Purpose:** Store and manage transcript segments

**Key features:**
- **Rolling context window:** Only keep last N minutes in active memory
- **Full transcript:** Maintain complete history for export
- **Pub/Sub pattern:** Components subscribe to new segments
- **Thread-safe:** Async locks prevent race conditions

**Memory management decision:**
- Context window = 10 minutes by default
- Max context chars = 8000 (leaves room for prompt in LLM context)
- This prevents token overflow while preserving recent context

### 4. LLM Reasoner (`reasoner.py`)

**Choice: GPT-4o-mini**

| Alternative | Latency | Cost | Quality |
|-------------|---------|------|---------|
| GPT-4o-mini (chosen) | ~2s | Low | Good |
| GPT-4o | ~3s | High | Best |
| Claude 3 Haiku | ~1.5s | Low | Good |
| Local (Ollama) | Varies | Free | Medium |

**Prompt engineering:**
- System prompt defines assistant role and output format
- Low temperature (0.2-0.3) for consistent outputs
- Streaming responses available for Q&A

### 5. Web Application (`web_app.py`)

**Stack:** Flask + Socket.IO

- REST API for summaries and Q&A
- WebSocket for real-time transcript updates
- Demo mode with mock transcription for testing

## Key Trade-offs

### Latency vs. Accuracy

| Choice | Impact |
|--------|--------|
| Streaming STT | Lower latency, slightly less accurate |
| Interim results | Immediate feedback, may show corrections |
| GPT-4o-mini over GPT-4o | Faster responses, slightly lower quality |

### Context Window Size

- **Smaller (5 min):** Faster processing, may miss earlier context
- **Larger (15+ min):** More context, higher token cost, slower
- **Chosen (10 min):** Balance for typical meeting discussions

### Summary Frequency

- **Continuous:** High cost, overwhelming
- **On-demand only:** User must remember to request
- **Periodic (2 min):** Reasonable balance (configurable)

## Known Limitations

1. **Speaker diarization:** Basic speaker identification based on LiveKit participant identity, not audio features
2. **Overlapping speech:** May produce concatenated or garbled transcripts
3. **Long meetings:** Context window may lose early important points
4. **Offline use:** Requires internet for Deepgram and OpenAI APIs

## Future Enhancements

1. **Local LLM support** (Ollama) for offline/private use
2. **Advanced diarization** using speaker embeddings
3. **Action item extraction** with structured output
4. **Meeting export** (PDF, Notion, etc.)
5. **Multi-language support**
