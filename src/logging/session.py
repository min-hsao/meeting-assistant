"""Session logging for research and transcription"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from ..research.providers.base import ResearchResult

logger = logging.getLogger(__name__)


class SessionLogger:
    """Manages session logging for searches and transcriptions"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._session_id = str(uuid.uuid4())
        self._started_at = datetime.utcnow()
        self._meeting_context = ""
        
        self._searches: List[Dict[str, Any]] = []
        self._transcripts: List[Dict[str, Any]] = []
        
        # Create date-based directory
        self._date_dir = self.log_dir / datetime.now().strftime("%Y-%m-%d")
        self._date_dir.mkdir(exist_ok=True)
        self._transcripts_dir = self._date_dir / "transcripts"
        self._transcripts_dir.mkdir(exist_ok=True)
        
        # Session file path
        self._session_file = self._date_dir / f"session_{self._started_at.strftime('%H-%M-%S')}.json"
        
        logger.info(f"Session started: {self._session_id}")
    
    def set_meeting_context(self, context: str):
        """Set the meeting context for this session"""
        self._meeting_context = context
        self._save()
    
    def log_search(self, result: ResearchResult, trigger_phrase: str = ""):
        """Log a research search"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trigger_phrase": trigger_phrase,
            "topic": result.topic,
            "response": result.summary,
            "provider": result.provider,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "success": result.success,
            "error": result.error,
        }
        self._searches.append(entry)
        self._save()
        logger.debug(f"Logged search: {result.topic}")
    
    def log_transcript_segment(
        self,
        trigger: str,
        transcript: str,
        duration_seconds: float,
    ) -> str:
        """
        Log a transcript segment.
        
        Returns:
            Filename of saved transcript
        """
        segment_num = len(self._transcripts) + 1
        filename = f"segment_{segment_num:03d}.txt"
        filepath = self._transcripts_dir / filename
        
        # Save transcript text
        with open(filepath, 'w') as f:
            f.write(transcript)
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trigger": trigger,
            "duration_seconds": duration_seconds,
            "transcript": transcript[:500] + ("..." if len(transcript) > 500 else ""),
            "file": f"transcripts/{filename}",
        }
        self._transcripts.append(entry)
        self._save()
        
        logger.debug(f"Logged transcript segment: {filename}")
        return filename
    
    def _save(self):
        """Save session data to file"""
        data = {
            "session_id": self._session_id,
            "started_at": self._started_at.isoformat() + "Z",
            "ended_at": None,
            "meeting_context": self._meeting_context,
            "searches": self._searches,
            "transcript_segments": self._transcripts,
        }
        
        with open(self._session_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def end_session(self):
        """End the current session"""
        data = self._load_session()
        data["ended_at"] = datetime.utcnow().isoformat() + "Z"
        
        with open(self._session_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Session ended: {self._session_id}")
    
    def _load_session(self) -> dict:
        """Load current session data"""
        if self._session_file.exists():
            with open(self._session_file, 'r') as f:
                return json.load(f)
        return {}
    
    @property
    def session_id(self) -> str:
        return self._session_id
    
    @property
    def search_count(self) -> int:
        return len(self._searches)
    
    @property
    def transcript_count(self) -> int:
        return len(self._transcripts)
    
    @staticmethod
    def list_sessions(log_dir: Path) -> List[Dict[str, Any]]:
        """List all sessions in the log directory"""
        sessions = []
        log_dir = Path(log_dir)
        
        for date_dir in sorted(log_dir.iterdir(), reverse=True):
            if date_dir.is_dir() and date_dir.name != "transcripts":
                for session_file in sorted(date_dir.glob("session_*.json"), reverse=True):
                    try:
                        with open(session_file, 'r') as f:
                            data = json.load(f)
                            sessions.append({
                                "file": str(session_file),
                                "session_id": data.get("session_id"),
                                "started_at": data.get("started_at"),
                                "ended_at": data.get("ended_at"),
                                "search_count": len(data.get("searches", [])),
                                "transcript_count": len(data.get("transcript_segments", [])),
                            })
                    except Exception as e:
                        logger.error(f"Error loading session {session_file}: {e}")
        
        return sessions
