# Meeting Assistant - Development Log

> This file tracks project progress for continuity across sessions. Skippy updates this as we work.

## Project Overview

Voice-activated meeting research assistant for sales engineers. Listens for trigger phrases, performs research, shows overlay results. Built with Python, PyQt6, OpenAI Whisper + GPT.

**Repo:** https://github.com/min-hsao/meeting-assistant

---

## Current Status (2026-01-29)

**Phase:** Post-Phase 2, bug fixes and stabilization

**What's Working:**
- Voice trigger detection ("what is", "tell me about", etc.)
- OpenAI Whisper transcription (API mode)
- GPT-4o-mini research responses
- Overlay display with auto-dismiss
- Transcription recording mode ("can you repeat that" → "end note")
- Natural stop triggers ("thank you", "that helps")
- System tray with pause/resume

**Recent Fixes:**
- `b18d3b6` - Fixed hotkey conversion for standalone special keys (escape, enter, etc.)
  - Issue: `escape` wasn't being converted to pynput's `<esc>` format
  - Solution: Added `special_keys` mapping in `_convert_hotkey()`

---

## Known Issues

### Audio capture not working on some machines
- **Symptom:** App starts, says "listening for triggers" but never detects speech
- **Cause:** Default mic (device 0) may not be the active input, or VAD threshold too high
- **Diagnosis:** Run raw audio test to check energy levels:
  ```bash
  python -c "
  import pyaudio
  import numpy as np
  pa = pyaudio.PyAudio()
  stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1600)
  print('Speak loudly...')
  for i in range(50):
      data = stream.read(1600, exception_on_overflow=False)
      audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
      energy = np.sqrt(np.mean(audio ** 2))
      print(f'{energy:.4f} {\"█\" * int(energy * 500)}')
  stream.close()
  pa.terminate()
  "
  ```
- **Workaround:** Configure specific device index in settings, or check System Settings → Sound → Input

---

## Architecture Notes

```
src/
├── audio/          # Audio capture, VAD, transcription recorder
├── config/         # Settings manager, defaults
├── research/       # Research engine, providers (OpenAI, DeepSeek, etc.)
├── speech/         # Whisper recognition, trigger detection
├── ui/             # PyQt6 overlay, system tray
├── utils/          # Hotkeys, helpers
├── logging/        # Session logger
└── main.py         # Entry point, MeetingAssistant class
```

**Key Config:** `src/config/defaults.py` - all default settings (triggers, VAD threshold, overlay, hotkeys)

---

## Backlog / Ideas

- [ ] Add device selection to settings/UI
- [ ] Lower default VAD threshold for quieter mics
- [ ] Add visual indicator when speech is detected
- [ ] Web search integration (currently disabled)
- [ ] Multiple provider fallback

---

## Session Notes

### 2026-01-29
- Fixed hotkey escape bug
- Diagnosed audio capture issue on Min's other MacBook (MMBP-1)
  - Default mic (MacBook Pro Microphone) not capturing
  - iPhone mic (Motherbox16, device 2) works fine
  - Likely permissions or system audio routing issue
- Created this DEVLOG for continuity
