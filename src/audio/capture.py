"""Audio capture from microphone with voice activity detection"""

import threading
import queue
import numpy as np
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures audio from microphone with VAD filtering"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 100,
        vad_threshold: float = 0.5,
        device_index: Optional[int] = None,
    ):
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.vad_threshold = vad_threshold
        self.device_index = device_index
        
        # Calculate chunk size
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        
        # Audio buffer for accumulating speech
        self.audio_queue: queue.Queue = queue.Queue()
        
        # Control flags
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        
        # PyAudio instance (lazy init)
        self._pyaudio = None
        self._stream = None
        
        # Callbacks
        self._on_audio: Optional[Callable[[np.ndarray], None]] = None
        
        # VAD state
        self._silence_chunks = 0
        self._speech_buffer = []
        self._in_speech = False
        
        # VAD settings
        self._speech_start_chunks = 3  # Chunks of speech to start
        self._silence_end_chunks = 10  # Chunks of silence to end
    
    def start(self, on_audio: Callable[[np.ndarray], None]) -> None:
        """Start capturing audio"""
        if self._running:
            return
        
        self._on_audio = on_audio
        self._running = True
        self._paused = False
        
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Audio capture started")
    
    def stop(self) -> None:
        """Stop capturing audio"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._cleanup()
        logger.info("Audio capture stopped")
    
    def pause(self) -> None:
        """Pause audio capture"""
        self._paused = True
        logger.info("Audio capture paused")
    
    def resume(self) -> None:
        """Resume audio capture"""
        self._paused = False
        logger.info("Audio capture resumed")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def is_paused(self) -> bool:
        return self._paused
    
    def _init_pyaudio(self):
        """Initialize PyAudio"""
        import pyaudio
        self._pyaudio = pyaudio.PyAudio()
        
        # Open stream
        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk_size,
        )
    
    def _cleanup(self):
        """Cleanup PyAudio resources"""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
    
    def _capture_loop(self):
        """Main capture loop running in thread"""
        try:
            self._init_pyaudio()
            
            while self._running:
                if self._paused:
                    import time
                    time.sleep(0.1)
                    continue
                
                try:
                    # Read audio chunk
                    data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                    audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Process with VAD
                    self._process_chunk(audio)
                    
                except Exception as e:
                    logger.error(f"Error reading audio: {e}")
                    import time
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
        finally:
            self._cleanup()
    
    def _process_chunk(self, audio: np.ndarray):
        """Process audio chunk with VAD"""
        # Simple energy-based VAD
        energy = np.sqrt(np.mean(audio ** 2))
        is_speech = energy > self.vad_threshold * 0.01
        
        if is_speech:
            self._silence_chunks = 0
            self._speech_buffer.append(audio)
            
            if not self._in_speech and len(self._speech_buffer) >= self._speech_start_chunks:
                self._in_speech = True
                logger.debug("Speech started")
        else:
            if self._in_speech:
                self._silence_chunks += 1
                self._speech_buffer.append(audio)
                
                if self._silence_chunks >= self._silence_end_chunks:
                    # Speech ended, send accumulated audio
                    if self._speech_buffer and self._on_audio:
                        full_audio = np.concatenate(self._speech_buffer)
                        self._on_audio(full_audio)
                    
                    self._speech_buffer = []
                    self._in_speech = False
                    self._silence_chunks = 0
                    logger.debug("Speech ended")
            else:
                # Keep a small buffer for context
                self._speech_buffer.append(audio)
                if len(self._speech_buffer) > 5:
                    self._speech_buffer.pop(0)
    
    @staticmethod
    def list_devices() -> list:
        """List available audio input devices"""
        import pyaudio
        pa = pyaudio.PyAudio()
        devices = []
        
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'sample_rate': int(info['defaultSampleRate']),
                })
        
        pa.terminate()
        return devices
