"""System tray icon and menu"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtCore import pyqtSignal, QObject


class SystemTray(QObject):
    """System tray icon with status indicators and menu"""
    
    # Signals
    pause_resume_clicked = pyqtSignal()
    manual_search_clicked = pyqtSignal()
    start_transcription_clicked = pyqtSignal()
    view_history_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    quit_clicked = pyqtSignal()
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self._is_listening = True
        
        # Create icons
        self._icons = {
            'listening': self._create_icon(QColor(76, 175, 80)),    # Green
            'processing': self._create_icon(QColor(255, 193, 7)),   # Yellow
            'error': self._create_icon(QColor(244, 67, 54)),        # Red
            'paused': self._create_icon(QColor(158, 158, 158)),     # Gray
        }
        
        # Create tray icon
        self.tray = QSystemTrayIcon(self._icons['listening'], self.app)
        self.tray.setToolTip("Meeting Assistant - Listening")
        
        # Create menu
        self._create_menu()
        
        self.tray.show()
    
    def _create_icon(self, color: QColor) -> QIcon:
        """Create a colored circle icon"""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(QColor(0, 0, 0, 0))
        
        # Draw filled circle
        margin = 4
        painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_menu(self):
        """Create context menu"""
        self.menu = QMenu()
        
        # Status (non-clickable)
        self.status_action = self.menu.addAction("🟢 Listening")
        self.status_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        # Pause/Resume
        self.pause_action = self.menu.addAction("⏸️ Pause Listening")
        self.pause_action.triggered.connect(self._on_pause_resume)
        
        # Manual search
        search_action = self.menu.addAction("🔍 Manual Search...")
        search_action.triggered.connect(self.manual_search_clicked.emit)
        
        # Transcription
        transcription_action = self.menu.addAction("📝 Start Transcription")
        transcription_action.triggered.connect(self.start_transcription_clicked.emit)
        
        self.menu.addSeparator()
        
        # History
        history_action = self.menu.addAction("📋 View History")
        history_action.triggered.connect(self.view_history_clicked.emit)
        
        # Settings
        settings_action = self.menu.addAction("⚙️ Settings")
        settings_action.triggered.connect(self.settings_clicked.emit)
        
        self.menu.addSeparator()
        
        # Quit
        quit_action = self.menu.addAction("🚪 Quit")
        quit_action.triggered.connect(self.quit_clicked.emit)
        
        self.tray.setContextMenu(self.menu)
    
    def _on_pause_resume(self):
        """Handle pause/resume toggle"""
        self._is_listening = not self._is_listening
        if self._is_listening:
            self.set_status('listening')
            self.pause_action.setText("⏸️ Pause Listening")
        else:
            self.set_status('paused')
            self.pause_action.setText("▶️ Resume Listening")
        self.pause_resume_clicked.emit()
    
    def set_status(self, status: str):
        """
        Set tray icon status.
        
        Args:
            status: One of 'listening', 'processing', 'error', 'paused'
        """
        if status in self._icons:
            self.tray.setIcon(self._icons[status])
            
            status_text = {
                'listening': '🟢 Listening',
                'processing': '🟡 Processing...',
                'error': '🔴 Error',
                'paused': '⏸️ Paused',
            }
            
            self.status_action.setText(status_text.get(status, status))
            self.tray.setToolTip(f"Meeting Assistant - {status_text.get(status, status)}")
    
    def show_message(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information):
        """Show a system notification"""
        self.tray.showMessage(title, message, icon, 5000)
    
    @property
    def is_listening(self) -> bool:
        return self._is_listening
