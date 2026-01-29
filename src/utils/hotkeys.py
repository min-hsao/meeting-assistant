"""Global hotkey manager"""

import logging
from typing import Callable, Dict, Optional
from pynput import keyboard
import threading

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Manages global hotkey registration and handling"""
    
    def __init__(self):
        self._hotkeys: Dict[str, Callable] = {}
        self._listener: Optional[keyboard.GlobalHotKeys] = None
        self._running = False
    
    def register(self, hotkey: str, callback: Callable):
        """
        Register a hotkey with a callback.
        
        Args:
            hotkey: Hotkey string (e.g., "ctrl+shift+f")
            callback: Function to call when hotkey is pressed
        """
        # Convert to pynput format
        pynput_key = self._convert_hotkey(hotkey)
        self._hotkeys[pynput_key] = callback
        logger.debug(f"Registered hotkey: {hotkey} -> {pynput_key}")
    
    def _convert_hotkey(self, hotkey: str) -> str:
        """Convert hotkey string to pynput format"""
        # Replace common modifiers
        key = hotkey.lower()
        key = key.replace("ctrl+", "<ctrl>+")
        key = key.replace("alt+", "<alt>+")
        key = key.replace("shift+", "<shift>+")
        key = key.replace("cmd+", "<cmd>+")
        key = key.replace("comma", ",")
        
        # Handle standalone special keys
        special_keys = {
            "escape": "<esc>",
            "esc": "<esc>",
            "enter": "<enter>",
            "return": "<enter>",
            "space": "<space>",
            "tab": "<tab>",
            "backspace": "<backspace>",
            "delete": "<delete>",
        }
        
        if key in special_keys:
            return special_keys[key]
        
        return key
    
    def start(self):
        """Start listening for hotkeys"""
        if self._running:
            return
        
        if not self._hotkeys:
            logger.warning("No hotkeys registered")
            return
        
        try:
            self._listener = keyboard.GlobalHotKeys(self._hotkeys)
            self._listener.start()
            self._running = True
            logger.info(f"Hotkey listener started with {len(self._hotkeys)} hotkeys")
        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")
    
    def stop(self):
        """Stop listening for hotkeys"""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False
        logger.info("Hotkey listener stopped")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def clear(self):
        """Clear all registered hotkeys"""
        self.stop()
        self._hotkeys.clear()
