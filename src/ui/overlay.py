"""Overlay window for displaying research results"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
    QPushButton, QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    pyqtSignal, QPoint
)
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor

from ..research.providers.base import ResearchResult


class OverlayWindow(QWidget):
    """Non-intrusive overlay window for research results"""
    
    dismissed = pyqtSignal()  # Emitted when overlay is dismissed
    
    def __init__(
        self,
        position: str = "right",
        width: int = 400,
        opacity: float = 0.9,
        auto_dismiss: bool = True,
        dismiss_seconds: int = 30,
        animation_ms: int = 200,
    ):
        super().__init__()
        
        self.position = position
        self._width = width
        self._opacity = opacity
        self.auto_dismiss = auto_dismiss
        self.dismiss_seconds = dismiss_seconds
        self.animation_ms = animation_ms
        
        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        self._setup_timers()
    
    def _setup_window(self):
        """Configure window properties"""
        # Frameless, always on top, tool window (no taskbar entry)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Transparent background for rounded corners
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Don't steal focus
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.setFixedWidth(self._width)
    
    def _setup_ui(self):
        """Setup UI components"""
        # Main container with background
        self.container = QWidget(self)
        self.container.setObjectName("overlayContainer")
        self.container.setStyleSheet(f"""
            #overlayContainer {{
                background-color: rgba(30, 30, 35, {int(self._opacity * 255)});
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 12, 16, 12)
        container_layout.setSpacing(8)
        
        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        self.icon_label = QLabel("🔍")
        self.icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(self.icon_label)
        
        self.title_label = QLabel("Topic")
        self.title_label.setFont(QFont("system-ui", 14, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        header_layout.addWidget(self.title_label, 1)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.6);
                border: none;
                font-size: 14px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.dismiss)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        header_layout.addWidget(self.close_btn)
        
        container_layout.addLayout(header_layout)
        
        # Divider
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        container_layout.addWidget(divider)
        
        # Content
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 13px;
            line-height: 1.4;
        """)
        self.content_label.setTextFormat(Qt.TextFormat.PlainText)
        container_layout.addWidget(self.content_label)
        
        # Footer divider
        footer_divider = QWidget()
        footer_divider.setFixedHeight(1)
        footer_divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        container_layout.addWidget(footer_divider)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        
        self.provider_label = QLabel("📡 Provider")
        self.provider_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 11px;")
        footer_layout.addWidget(self.provider_label)
        
        footer_layout.addStretch()
        
        self.latency_label = QLabel("⏱️ 0.0s")
        self.latency_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 11px;")
        footer_layout.addWidget(self.latency_label)
        
        container_layout.addLayout(footer_layout)
    
    def _setup_animations(self):
        """Setup fade animations"""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(self.animation_ms)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(self.animation_ms)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self._on_fade_out_complete)
    
    def _setup_timers(self):
        """Setup auto-dismiss timer"""
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.dismiss)
    
    def show_result(self, result: ResearchResult):
        """Display a research result"""
        self.title_label.setText(result.topic)
        
        if result.success:
            self.content_label.setText(result.summary)
            self.icon_label.setText("🔍")
        else:
            self.content_label.setText(f"Error: {result.error}")
            self.icon_label.setText("⚠️")
        
        self.provider_label.setText(f"📡 {result.provider.title()} {result.model}")
        self.latency_label.setText(f"⏱️ {result.latency_ms / 1000:.1f}s")
        
        # Adjust size and position
        self.adjustSize()
        self._position_window()
        
        # Show with animation
        self.show()
        self.fade_in_anim.start()
        
        # Start auto-dismiss timer
        if self.auto_dismiss:
            self.dismiss_timer.start(self.dismiss_seconds * 1000)
    
    def _position_window(self):
        """Position window based on settings"""
        screen = QApplication.primaryScreen().availableGeometry()
        margin = 20
        
        if self.position == "right":
            x = screen.right() - self.width() - margin
            y = screen.top() + margin
        elif self.position == "left":
            x = screen.left() + margin
            y = screen.top() + margin
        elif self.position == "top":
            x = screen.center().x() - self.width() // 2
            y = screen.top() + margin
        else:  # bottom
            x = screen.center().x() - self.width() // 2
            y = screen.bottom() - self.height() - margin
        
        self.move(x, y)
    
    def dismiss(self):
        """Dismiss the overlay with animation"""
        self.dismiss_timer.stop()
        self.fade_out_anim.start()
    
    def _on_fade_out_complete(self):
        """Handle fade out completion"""
        self.hide()
        self.dismissed.emit()
    
    def mousePressEvent(self, event):
        """Click anywhere to dismiss"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dismiss()
        super().mousePressEvent(event)
