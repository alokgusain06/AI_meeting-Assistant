# AI Meeting Assistant

A real-time AI assistant that joins online meetings, transcribes conversations, and provides intelligent insights using LLMs.

## 🎯 Features

- **Live Transcription** - Real-time speech-to-text using Deepgram
- **AI Summaries** - Generate meeting summaries on-demand with Gemini
- **Q&A** - Ask questions like "What was decided?" or "Action items?"
- **Topic Detection** - Identify current discussion topics
- **Web UI** - Modern dark-themed interface with real-time updates
- **Demo Mode** - Test everything without API setup

---

## ⚡ Quick Start (5 minutes)

### Step 1: Open WSL Terminal

```bash
cd /mnt/e/ASsingment/meeting-assistant
```

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 3: Configure API Keys

```bash
# Edit the .env file
nano .env
```

Add your API keys:
```
GEMINI_API_KEY=your_gemini_key_here     # Required - Get from aistudio.google.com
DEEPGRAM_API_KEY=your_deepgram_key      # Optional - For live transcription
LIVEKIT_URL=wss://your-project.livekit.cloud  # Optional - For live meetings
LIVEKIT_API_KEY=your_livekit_key        # Optional
LIVEKIT_API_SECRET=your_livekit_secret  # Optional
```

### Step 4: Run the Demo

```bash
python -m src.web_app
```

### Step 5: Open in Browser

Go to **http://localhost:5000**

### Step 6: Try It Out

1. Click **"Start Demo"** → Watch mock transcription appear
2. Click **"Generate"** → See AI summary
3. Ask a question → "What was decided?"
4. Try quick buttons → "Action items?", "Topics discussed?"

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LiveKit Meeting Room                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ Audio Stream
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Meeting Assistant                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Transcriber │→ │ Conversation │→ │   LLM Reasoner   │   │
│  │ (Deepgram)  │  │   Manager    │  │    (Gemini)      │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Web UI (Flask)                          │
│         Real-time transcripts + Summaries + Q&A              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
meeting-assistant/
├── src/
│   ├── agent.py          # LiveKit agent
│   ├── conversation.py   # Transcript manager
│   ├── reasoner.py       # Gemini LLM integration
│   ├── transcriber.py    # Deepgram STT
│   ├── web_app.py        # Flask web server
│   └── livekit_agent.py  # Simplified LiveKit agent
├── config/settings.py    # Configuration
├── static/               # CSS & JavaScript
├── templates/            # HTML templates
├── tests/                # Unit tests
├── DESIGN.md             # Architecture documentation
├── EXPERIENCE.md         # Reflection document
└── requirements.txt      # Dependencies
```

---

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/api/summary` | GET | Generate meeting summary |
| `/api/ask` | POST | Ask a question `{"question": "..."}` |
| `/api/topic` | GET | Get current discussion topic |
| `/api/transcript` | GET | Get full transcript |

---

## 🧪 Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

---

## � Getting API Keys

| Service | Where to Get | Cost |
|---------|--------------|------|
| **Gemini** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Free |
| **Deepgram** | [deepgram.com](https://deepgram.com) | Free tier |
| **LiveKit** | [cloud.livekit.io](https://cloud.livekit.io) | Free tier |

---

## 🚧 Known Limitations

- Mock demo uses simulated conversation (not real audio)
- LiveKit audio pipeline needs additional work for production
- Long meetings may need context window tuning

---

## 🔮 Future Improvements

- [ ] Speaker diarization (identify who is speaking)
- [ ] Local LLM support with Ollama
- [ ] Meeting export (PDF, Markdown)
- [ ] Multi-language support

---

## 📜 License

MIT
