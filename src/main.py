"""
Voice-Activated Meeting Research Assistant
Main entry point
"""

import sys
import signal
import logging
import threading
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.logging import RichHandler

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from .config import SettingsManager
from .audio import AudioCapture
from .speech import SpeechRecognizer, TriggerDetector
from .research import ResearchEngine
from .research.providers.base import ResearchResult
from .ui import OverlayWindow, SystemTray
from .logging import SessionLogger
from .utils import HotkeyManager


# Load environment variables
load_dotenv()


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_time=True,
                show_path=False,
            )
        ]
    )


class AudioProcessor(QObject):
    """Processes audio in background thread, emits signals for UI updates"""
    
    result_ready = pyqtSignal(object)  # ResearchResult
    status_changed = pyqtSignal(str)   # Status string
    
    def __init__(
        self,
        audio_capture: AudioCapture,
        recognizer: SpeechRecognizer,
        trigger_detector: TriggerDetector,
        research_engine: ResearchEngine,
        session_logger: SessionLogger,
    ):
        super().__init__()
        self.audio = audio_capture
        self.recognizer = recognizer
        self.trigger_detector = trigger_detector
        self.research = research_engine
        self.logger = session_logger
        
        self._processing = False
    
    def on_audio(self, audio_data):
        """Handle audio data from capture"""
        if self._processing:
            return
        
        self._processing = True
        self.status_changed.emit('processing')
        
        try:
            # Transcribe
            text, confidence = self.recognizer.transcribe(audio_data)
            
            if text and confidence > 0.3:
                logging.getLogger(__name__).debug(f"Transcribed: '{text}'")
                
                # Check for triggers
                match = self.trigger_detector.detect(text)
                
                if match and match.trigger_type == 'research' and match.topic:
                    # Research the topic
                    result = self.research.research_sync(match.topic)
                    self.logger.log_search(result, match.trigger_phrase)
                    logging.getLogger(__name__).info(f"Emitting result_ready signal for: {result.topic}")
                    self.result_ready.emit(result)
                    logging.getLogger(__name__).info("Signal emitted")
        
        except Exception as e:
            logging.getLogger(__name__).error(f"Processing error: {e}")
        
        finally:
            self._processing = False
            self.status_changed.emit('listening')


class MeetingAssistant:
    """Main application class"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load settings
        self.settings = SettingsManager()
        
        # Initialize components
        self._init_audio()
        self._init_speech()
        self._init_research()
        self._init_logging()
    
    def _init_audio(self):
        """Initialize audio capture"""
        audio_config = self.settings.get('audio')
        self.audio = AudioCapture(
            sample_rate=audio_config.get('sample_rate', 16000),
            chunk_duration_ms=audio_config.get('chunk_duration_ms', 100),
            vad_threshold=audio_config.get('vad_threshold', 0.5),
        )
    
    def _init_speech(self):
        """Initialize speech recognition"""
        speech_config = self.settings.get('speech')
        self.recognizer = SpeechRecognizer(
            model_size=speech_config.get('model', 'tiny'),
            language=speech_config.get('language', 'en'),
            use_api=speech_config.get('use_api', False),
        )
        
        triggers_config = self.settings.get('triggers')
        self.trigger_detector = TriggerDetector(triggers_config)
    
    def _init_research(self):
        """Initialize research engine"""
        self.research = ResearchEngine(self.settings.all)
    
    def _init_logging(self):
        """Initialize session logging"""
        log_dir = self.settings.get_log_dir()
        self.session_logger = SessionLogger(log_dir)
    
    def run(self):
        """Run the application"""
        # Create Qt application
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        # Create UI components
        overlay_config = self.settings.get('overlay')
        self.overlay = OverlayWindow(
            position=overlay_config.get('position', 'right'),
            width=overlay_config.get('width', 400),
            opacity=overlay_config.get('opacity', 0.9),
            auto_dismiss=overlay_config.get('auto_dismiss', True),
            dismiss_seconds=overlay_config.get('dismiss_seconds', 30),
            animation_ms=overlay_config.get('animation_ms', 200),
        )
        
        self.tray = SystemTray(app)
        
        # Create audio processor
        self.processor = AudioProcessor(
            self.audio,
            self.recognizer,
            self.trigger_detector,
            self.research,
            self.session_logger,
        )
        
        # Connect signals (use QueuedConnection for thread safety)
        from PyQt6.QtCore import Qt
        self.processor.result_ready.connect(self._on_result, Qt.ConnectionType.QueuedConnection)
        self.processor.status_changed.connect(self._on_status_changed, Qt.ConnectionType.QueuedConnection)
        
        self.tray.pause_resume_clicked.connect(self._on_pause_resume)
        self.tray.quit_clicked.connect(self._on_quit)
        
        # Setup hotkeys
        self._setup_hotkeys()
        
        # Start audio capture
        self.audio.start(self.processor.on_audio)
        self.logger.info("Meeting Assistant started - listening for triggers")
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, lambda *args: self._on_quit())
        
        # Run Qt event loop
        return app.exec()
    
    def _setup_hotkeys(self):
        """Setup global hotkeys"""
        self.hotkeys = HotkeyManager()
        hotkey_config = self.settings.get('hotkeys')
        
        if hotkey_config.get('pause_resume'):
            self.hotkeys.register(hotkey_config['pause_resume'], self._on_pause_resume)
        
        if hotkey_config.get('dismiss_overlay'):
            self.hotkeys.register(hotkey_config['dismiss_overlay'], self._on_dismiss_overlay)
        
        self.hotkeys.start()
    
    def _on_result(self, result: ResearchResult):
        """Handle research result"""
        self.logger.info(f"_on_result called with topic: {result.topic}")
        self.logger.info(f"Result success: {result.success}, summary length: {len(result.summary)}")
        
        try:
            self.overlay.show_result(result)
            self.logger.info("Overlay show_result called")
        except Exception as e:
            self.logger.error(f"Error showing overlay: {e}")
        
        if result.success:
            self.tray.show_message(
                f"🔍 {result.topic}",
                result.summary[:100] + "..." if len(result.summary) > 100 else result.summary
            )
    
    def _on_status_changed(self, status: str):
        """Handle status change"""
        self.tray.set_status(status)
    
    def _on_pause_resume(self):
        """Toggle pause/resume"""
        if self.audio.is_paused:
            self.audio.resume()
            self.tray.set_status('listening')
        else:
            self.audio.pause()
            self.tray.set_status('paused')
    
    def _on_dismiss_overlay(self):
        """Dismiss current overlay"""
        self.overlay.dismiss()
    
    def _on_quit(self):
        """Clean shutdown"""
        self.logger.info("Shutting down...")
        
        self.audio.stop()
        self.hotkeys.stop()
        self.session_logger.end_session()
        
        QApplication.instance().quit()


def main():
    """Entry point"""
    setup_logging("INFO")
    
    try:
        assistant = MeetingAssistant()
        sys.exit(assistant.run())
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        logging.getLogger(__name__).exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
