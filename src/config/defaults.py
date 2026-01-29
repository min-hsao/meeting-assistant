"""Default configuration values"""

DEFAULT_RESEARCH_CONTEXT = """You are a research assistant for a sales engineer at a cybersecurity company.
Provide brief, technically accurate summaries relevant to enterprise security, networking, IT infrastructure, and related technologies.

Focus on:
- What it is (1-2 sentences)
- Key features or capabilities
- Relevance to enterprise/security if applicable
- Any competitive context if it's a product

Keep responses under 150 words. Be accurate - this will be used in live customer conversations."""

DEFAULT_SETTINGS = {
    "audio": {
        "device": "default",
        "sample_rate": 16000,
        "chunk_duration_ms": 100,
        "vad_threshold": 0.5,
    },
    "speech": {
        "model": "whisper-1",  # API model (or tiny/base/small for local)
        "language": "en",
        "use_api": True,  # Use OpenAI API for better compatibility
    },
    "triggers": {
        "research": [
            "did you say",
            "what is",
            "tell me about",
            "look up",
            "search for",
        ],
        "transcription_start": [
            "can you repeat that",
            "let me note that down",
            "that's important",
        ],
        "transcription_stop": [
            "thank you",
            "that helps",
            "got it",
            "end note",
            "stop recording",
        ],
        "custom": [],
    },
    "research": {
        "default_provider": "openai",
        "context": DEFAULT_RESEARCH_CONTEXT,
        "meeting_context": "",
        "max_tokens": 250,
        "temperature": 0.3,
        "timeout_seconds": 15,
        "web_search": True,
    },
    "api": {
        "openai": {
            "model": "gpt-4o-mini",
            "enabled": True,
        },
        "deepseek": {
            "model": "deepseek-chat",
            "enabled": False,
        },
        "gemini": {
            "model": "gemini-1.5-flash",
            "enabled": False,
        },
        "glm": {
            "model": "glm-4",
            "enabled": False,
        },
    },
    "overlay": {
        "position": "right",
        "width": 400,
        "opacity": 0.9,
        "auto_dismiss": True,
        "dismiss_seconds": 30,
        "max_visible": 3,
        "animation_ms": 200,
    },
    "transcription": {
        "auto_stop_silence_seconds": 5,
        "max_duration_seconds": 60,
        "save_audio": False,
    },
    "hotkeys": {
        "manual_search": "ctrl+shift+f",
        "pause_resume": "ctrl+shift+p",
        "dismiss_overlay": "escape",
        "start_transcription": "ctrl+shift+r",
        "stop_transcription": "ctrl+shift+s",
        "open_settings": "ctrl+shift+comma",
        "open_history": "ctrl+shift+h",
    },
    "logging": {
        "level": "INFO",
        "log_dir": "~/MeetingAssistant/logs",
        "retain_days": 30,
    },
}
