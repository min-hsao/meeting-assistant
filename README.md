# Voice-Activated Meeting Research Assistant

A real-time voice assistant for sales engineers conducting customer calls. When you say a trigger phrase like "did you say [topic]?", it automatically researches the topic and displays results in a non-intrusive overlay.

## Features

- 🎤 **Voice triggers** - "did you say X", "what is X", "tell me about X"
- 🔍 **AI-powered research** - Uses OpenAI GPT-4o-mini with web search
- 🪟 **Discreet overlay** - Non-intrusive display that doesn't steal focus
- 📝 **Session logging** - All searches logged for post-meeting review
- ⌨️ **Hotkey support** - Pause/resume, manual search, and more

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install requirements
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run

```bash
python -m src.main
```

## Usage

### Trigger Phrases

Say any of these followed by a topic:
- "Did you say [topic]?"
- "What is [topic]?"
- "Tell me about [topic]"
- "Look up [topic]"
- "Search for [topic]"

**Example:** "Did you say Kubernetes?" → Researches Kubernetes and shows summary

### Hotkeys

| Action | Default Hotkey |
|--------|---------------|
| Pause/Resume | Ctrl+Shift+P |
| Dismiss Overlay | Escape |
| Manual Search | Ctrl+Shift+F |
| Open Settings | Ctrl+Shift+, |

### System Tray

- 🟢 Green: Listening
- 🟡 Yellow: Processing
- 🔴 Red: Error
- ⏸️ Gray: Paused

Right-click for menu options.

## Configuration

Settings are stored in `~/MeetingAssistant/config/settings.yaml`.

### Meeting Context

Add per-meeting context in settings to improve relevance:
```yaml
research:
  meeting_context: "This call is about SIEM competitive analysis"
```

### Custom Triggers

Add custom trigger phrases:
```yaml
triggers:
  custom:
    - "research"
    - "explain"
```

## Logs

Session logs are saved to `~/MeetingAssistant/logs/YYYY-MM-DD/`.

Each session includes:
- All research queries and responses
- Timestamps and latency
- Meeting context

## Requirements

- Python 3.10+
- macOS, Windows, or Linux
- Microphone access
- OpenAI API key

## Troubleshooting

### Microphone not working
- Check system permissions for microphone access
- Ensure no other app has exclusive microphone access

### Triggers not detected
- Speak clearly after the trigger phrase
- Reduce background noise
- Try the `base` Whisper model for better accuracy

### Overlay not visible
- Check if it's positioned off-screen (try `position: "left"` in settings)
- Ensure no fullscreen apps are blocking it

## License

MIT
