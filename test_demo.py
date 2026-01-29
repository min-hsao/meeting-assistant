#!/usr/bin/env python3
"""
Demo script to test Meeting Assistant components without full audio capture.
Run with: python test_demo.py
"""

import sys
import asyncio
from pathlib import Path

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import SettingsManager
from src.speech import TriggerDetector
from src.research import ResearchEngine
from src.logging import SessionLogger


def test_triggers():
    """Test trigger detection"""
    print("\n=== Testing Trigger Detection ===")
    
    settings = SettingsManager()
    detector = TriggerDetector(settings.get('triggers'))
    
    test_phrases = [
        "did you say kubernetes",
        "what is SIEM",
        "tell me about Splunk",
        "look up zero trust architecture",
        "search for exabeam",
        "can you repeat that",
        "hello world",  # No trigger
    ]
    
    for phrase in test_phrases:
        result = detector.detect(phrase)
        if result:
            print(f"  ✓ '{phrase}'")
            print(f"    → Type: {result.trigger_type}, Topic: {result.topic}")
        else:
            print(f"  ✗ '{phrase}' (no trigger)")


def test_research():
    """Test research engine (requires valid API key)"""
    print("\n=== Testing Research Engine ===")
    
    settings = SettingsManager()
    engine = ResearchEngine(settings.all)
    
    print(f"  Available providers: {engine.available_providers}")
    print(f"  Default provider: {engine.default_provider}")
    
    if not engine.available_providers:
        print("  ⚠ No providers available (check API keys)")
        return
    
    topic = "Kubernetes"
    print(f"\n  Researching: {topic}")
    
    result = engine.research_sync(topic)
    
    if result.success:
        print(f"  ✓ Success in {result.latency_ms}ms")
        print(f"  Summary: {result.summary[:300]}...")
    else:
        print(f"  ✗ Failed: {result.error}")


def test_logging():
    """Test session logging"""
    print("\n=== Testing Session Logging ===")
    
    settings = SettingsManager()
    log_dir = settings.get_log_dir()
    
    logger = SessionLogger(log_dir)
    print(f"  Session ID: {logger.session_id}")
    print(f"  Log dir: {log_dir}")
    
    # Log a test search
    from src.research.providers.base import ResearchResult
    result = ResearchResult(
        topic="Test Topic",
        summary="This is a test summary",
        provider="test",
        model="test-model",
        latency_ms=100,
        success=True
    )
    logger.log_search(result, "did you say")
    print(f"  ✓ Logged test search")
    
    logger.end_session()
    print(f"  ✓ Session ended")


def test_ui():
    """Test UI components"""
    print("\n=== Testing UI Components ===")
    
    from PyQt6.QtWidgets import QApplication
    from src.ui import OverlayWindow, SystemTray
    from src.research.providers.base import ResearchResult
    
    app = QApplication(sys.argv)
    
    # Create overlay
    overlay = OverlayWindow(
        position="right",
        width=400,
        opacity=0.9,
        auto_dismiss=True,
        dismiss_seconds=10,
    )
    
    # Create test result
    result = ResearchResult(
        topic="Kubernetes",
        summary="""Kubernetes (K8s) is an open-source container orchestration platform originally developed by Google.

Key features:
• Automated deployment and scaling
• Self-healing capabilities
• Service discovery and load balancing
• Storage orchestration

Widely used in enterprise environments for managing containerized applications.""",
        provider="openai",
        model="gpt-4o-mini",
        latency_ms=2500,
        success=True
    )
    
    # Show overlay
    overlay.show_result(result)
    print("  ✓ Overlay displayed (will auto-dismiss in 10s)")
    
    # Create tray
    tray = SystemTray(app)
    print("  ✓ System tray created")
    
    # Run for a few seconds to show the overlay
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(10000, app.quit)
    
    return app.exec()


if __name__ == "__main__":
    print("Meeting Assistant - Component Test")
    print("=" * 40)
    
    test_triggers()
    test_research()
    test_logging()
    
    # UI test runs the Qt event loop
    if "--no-ui" not in sys.argv:
        print("\nStarting UI test (close overlay or wait 10s)...")
        test_ui()
    
    print("\n" + "=" * 40)
    print("Tests complete!")
