"""Speech recognition using OpenAI Whisper API (or local faster-whisper)"""

import logging
import numpy as np
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Transcribes audio using OpenAI Whisper API (default) or local faster-whisper"""
    
    def __init__(
        self,
        model_size: str = "tiny",
        language: str = "en",
        use_api: bool = True,  # Default to API for compatibility
        cache_dir: Optional[Path] = None,
    ):
        self.model_size = model_size
        self.language = language
        self.use_api = use_api
        self.cache_dir = cache_dir or Path.home() / "MeetingAssistant" / "cache" / "whisper_model"
        
        self._model = None
        self._api_client = None
    
    def _init_model(self):
        """Lazy-load the whisper model"""
        if self.use_api:
            if self._api_client is None:
                from openai import OpenAI
                self._api_client = OpenAI()
                logger.info("Using OpenAI Whisper API")
            return
        
        if self._model is not None:
            return
        
        try:
            from faster_whisper import WhisperModel
            
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Use CPU for compatibility, switch to cuda if available
            compute_type = "int8"
            device = "cpu"
            
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    compute_type = "float16"
                    logger.info("Using CUDA for Whisper")
            except ImportError:
                pass
            
            logger.info(f"Loading Whisper model: {self.model_size} (device={device})")
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(self.cache_dir),
            )
            logger.info("Whisper model loaded")
        except ImportError:
            logger.warning("faster-whisper not available, falling back to API")
            self.use_api = True
            self._init_model()
    
    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> Tuple[str, float]:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as float32 numpy array (normalized to -1.0 to 1.0)
            sample_rate: Sample rate of audio
            
        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        self._init_model()
        
        if self.use_api:
            return self._transcribe_api(audio, sample_rate)
        else:
            return self._transcribe_local(audio)
    
    def _transcribe_local(self, audio: np.ndarray) -> Tuple[str, float]:
        """Transcribe using local faster-whisper model"""
        try:
            segments, info = self._model.transcribe(
                audio,
                language=self.language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                ),
            )
            
            # Collect all segments
            text_parts = []
            confidences = []
            
            for segment in segments:
                text_parts.append(segment.text)
                confidences.append(segment.avg_logprob)
            
            text = " ".join(text_parts).strip()
            
            # Convert log probability to confidence (rough approximation)
            avg_confidence = 0.0
            if confidences:
                avg_log_prob = sum(confidences) / len(confidences)
                avg_confidence = min(1.0, max(0.0, 1.0 + avg_log_prob))
            
            logger.debug(f"Transcribed: '{text}' (confidence: {avg_confidence:.2f})")
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "", 0.0
    
    def _transcribe_api(self, audio: np.ndarray, sample_rate: int) -> Tuple[str, float]:
        """Transcribe using OpenAI Whisper API"""
        import tempfile
        import wave
        
        try:
            # Convert to int16 for WAV
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Write to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                with wave.open(f, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(sample_rate)
                    wav.writeframes(audio_int16.tobytes())
            
            # Send to API
            with open(temp_path, 'rb') as audio_file:
                response = self._api_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=self.language,
                )
            
            # Clean up
            import os
            os.unlink(temp_path)
            
            text = response.text.strip()
            logger.debug(f"API transcribed: '{text}'")
            return text, 0.9  # API doesn't return confidence
            
        except Exception as e:
            logger.error(f"API transcription error: {e}")
            return "", 0.0
