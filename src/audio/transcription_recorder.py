"""Transcription recording for capturing meeting segments"""

import threading
import time
import numpy as np
from typing import Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """A recorded transcript segment"""
    trigger: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    audio_data: np.ndarray
    transcript: str = ""


class TranscriptionRecorder:
    """Records audio segments for transcription"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        auto_stop_silence_seconds: float = 5.0,
        max_duration_seconds: float = 60.0,
    ):
        self.sample_rate = sample_rate
        self.auto_stop_silence_seconds = auto_stop_silence_seconds
        self.max_duration_seconds = max_duration_seconds
        
        self._recording = False
        self._audio_buffer: List[np.ndarray] = []
        self._start_time: Optional[datetime] = None
        self._trigger: str = ""
        self._silence_start: Optional[float] = None
        self._lock = threading.Lock()
        
        # Callbacks
        self._on_complete: Optional[Callable[[TranscriptSegment], None]] = None
    
    def start_recording(self, trigger: str, on_complete: Callable[[TranscriptSegment], None]):
        """Start recording a segment"""
        with self._lock:
            if self._recording:
                logger.warning("Already recording, ignoring start request")
                return False
            
            self._recording = True
            self._audio_buffer = []
            self._start_time = datetime.now()
            self._trigger = trigger
            self._silence_start = None
            self._on_complete = on_complete
            
            logger.info(f"Started recording (trigger: {trigger})")
            return True
    
    def stop_recording(self) -> Optional[TranscriptSegment]:
        """Stop recording and return the segment"""
        with self._lock:
            if not self._recording:
                return None
            
            self._recording = False
            end_time = datetime.now()
            
            if not self._audio_buffer:
                logger.warning("No audio captured")
                return None
            
            # Concatenate audio
            audio_data = np.concatenate(self._audio_buffer)
            duration = len(audio_data) / self.sample_rate
            
            segment = TranscriptSegment(
                trigger=self._trigger,
                start_time=self._start_time,
                end_time=end_time,
                duration_seconds=duration,
                audio_data=audio_data,
            )
            
            logger.info(f"Stopped recording: {duration:.1f}s captured")
            
            # Clear buffer
            self._audio_buffer = []
            self._start_time = None
            
            return segment
    
    def add_audio(self, audio: np.ndarray) -> Optional[TranscriptSegment]:
        """
        Add audio chunk to recording buffer.
        Returns TranscriptSegment if recording auto-stopped.
        """
        with self._lock:
            if not self._recording:
                return None
            
            self._audio_buffer.append(audio.copy())
            
            # Check duration limit
            total_samples = sum(len(chunk) for chunk in self._audio_buffer)
            duration = total_samples / self.sample_rate
            
            if duration >= self.max_duration_seconds:
                logger.info("Max duration reached, auto-stopping")
                segment = self._stop_and_get_segment()
                if segment and self._on_complete:
                    self._on_complete(segment)
                return segment
            
            # Check for silence (auto-stop)
            energy = np.sqrt(np.mean(audio ** 2))
            is_silence = energy < 0.01  # Low energy threshold
            
            if is_silence:
                if self._silence_start is None:
                    self._silence_start = time.time()
                elif time.time() - self._silence_start >= self.auto_stop_silence_seconds:
                    logger.info("Silence detected, auto-stopping")
                    segment = self._stop_and_get_segment()
                    if segment and self._on_complete:
                        self._on_complete(segment)
                    return segment
            else:
                self._silence_start = None
            
            return None
    
    def _stop_and_get_segment(self) -> Optional[TranscriptSegment]:
        """Internal stop without lock (called from within locked context)"""
        if not self._recording:
            return None
        
        self._recording = False
        end_time = datetime.now()
        
        if not self._audio_buffer:
            return None
        
        audio_data = np.concatenate(self._audio_buffer)
        duration = len(audio_data) / self.sample_rate
        
        segment = TranscriptSegment(
            trigger=self._trigger,
            start_time=self._start_time,
            end_time=end_time,
            duration_seconds=duration,
            audio_data=audio_data,
        )
        
        self._audio_buffer = []
        self._start_time = None
        
        return segment
    
    @property
    def is_recording(self) -> bool:
        return self._recording
    
    @property
    def current_duration(self) -> float:
        """Current recording duration in seconds"""
        with self._lock:
            if not self._recording or not self._audio_buffer:
                return 0.0
            total_samples = sum(len(chunk) for chunk in self._audio_buffer)
            return total_samples / self.sample_rate
