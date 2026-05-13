"""
Debug overlay widget for displaying dimension information.
Shows real-time window dimensions with semi-transparent overlay.

USAGE IN YOUR APPLICATION:
1. Save this file as 'debug_overlay.py' in your project directory
2. Import in RNV_Color_Mixer.py:
   from debug_overlay import DebugOverlay
   
3. Add to ColorMixerApp.__init__ after UI is built (after self._safe_build_ui()):
   # Debug overlays (temporary)
   self.debug_overlay_main = DebugOverlay(self.central_widget, "App Window")
   self.debug_overlay_main.show()
   
   self.debug_overlay_slots = DebugOverlay(self.slots_scroll_area.viewport(), "Slots Panel")
   self.debug_overlay_slots.show()

4. To remove overlays later, just delete or comment out the above lines
"""

from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QEvent, QObject
from PyQt6.QtGui import QShowEvent, QResizeEvent

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("DebugOverlay")
except ImportError:
    logger = None

# Import SignalMixin for signal connection tracking
from utils.signal_manager import SignalMixin


class DebugOverlay(QLabel, SignalMixin):
    """Semi-transparent overlay showing dimension information as a child widget."""
    
    def __init__(self, parent: QWidget | None = None, label_text: str = "Debug", color: str = "rgba(255, 100, 100, 200)") -> None:
        super().__init__(parent)
        
        # Initialize signal tracking
        self.init_signal_tracking()
        
        self.label_prefix = label_text
        self.bg_color = color
        
        # Style the overlay
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.bg_color};
                color: white;
                padding: 8px 12px;
                border: 2px solid rgba(255, 255, 255, 230);
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                font-family: "Courier New", "Consolas", monospace;
            }}
        """)
        
        # Make it stay on top within parent but allow clicks through
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.Widget)
        self.raise_()  # Bring to front
        
        # Set initial text
        self.setText(f"{self.label_prefix}: 0 x 0")
        self.adjustSize()
        
        # Timer for updates with tracked connection
        self.update_timer = QTimer(self)
        self.track_connection(self.update_timer, self.update_timer.timeout, self.update_dimensions, "update_timer")
        self.update_timer.start(250)  # Update every 250ms - balanced performance
        
        # Install event filter on parent to track resizes
        if self.parent():
            self.parent().installEventFilter(self)
        
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter parent events to update position on resize."""
        if obj == self.parent() and event.type() == QEvent.Type.Resize:
            self.update_dimensions()
        return super().eventFilter(obj, event)
        
    def update_dimensions(self) -> None:
        """Update the dimension display."""
        if self.parent():
            width = self.parent().width()
            height = self.parent().height()
            self.setText(f"{self.label_prefix}: {width} x {height}")
            self.adjustSize()
            self.position_overlay()
            self.raise_()  # Keep on top
    
    def position_overlay(self) -> None:
        """Position the overlay in the top-right corner of parent."""
        if self.parent():
            parent_width = self.parent().width()
            overlay_width = self.width()
            
            # Position in top-right with 10px margin
            x = parent_width - overlay_width - 10
            y = 10
            
            self.move(x, y)
    
    def showEvent(self, event: QShowEvent) -> None:
        """Handle show event."""
        super().showEvent(event)
        self.update_dimensions()
        self.raise_()
        
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize event."""
        super().resizeEvent(event)
        self.position_overlay()
        self.raise_()


# Alternative version that shows additional info
class DebugOverlayDetailed(QLabel, SignalMixin):
    """Debug overlay with additional information."""
    
    def __init__(self, parent: QWidget | None = None, label_text: str = "Debug", color: str = "rgba(255, 100, 100, 200)") -> None:
        super().__init__(parent)
        
        # Initialize signal tracking
        self.init_signal_tracking()
        
        self.label_prefix = label_text
        self.bg_color = color
        
        # Style the overlay
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.bg_color};
                color: white;
                padding: 10px 14px;
                border: 2px solid rgba(255, 255, 255, 230);
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                font-family: "Courier New", "Consolas", monospace;
            }}
        """)
        
        # Make it stay on top within parent but allow clicks through
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.Widget)
        self.raise_()
        
        # Set initial text
        self.setText(f"{self.label_prefix}:\n0 x 0")
        self.adjustSize()
        
        # Timer for updates with tracked connection
        self.update_timer = QTimer(self)
        self.track_connection(self.update_timer, self.update_timer.timeout, self.update_dimensions, "update_timer")
        self.update_timer.start(250)  # Update every 250ms
        
        # Install event filter on parent
        if self.parent():
            self.parent().installEventFilter(self)
        
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter parent events."""
        if obj == self.parent() and event.type() == QEvent.Type.Resize:
            self.update_dimensions()
        return super().eventFilter(obj, event)
        
    def update_dimensions(self) -> None:
        """Update the dimension display with additional info."""
        if self.parent():
            width = self.parent().width()
            height = self.parent().height()
            
            # Get additional info if available
            visible_text = "Visible" if self.parent().isVisible() else "Hidden"
            
            info_text = f"{self.label_prefix}:\n{width} x {height}\n{visible_text}"
            
            self.setText(info_text)
            self.adjustSize()
            self.position_overlay()
            self.raise_()
    
    def position_overlay(self) -> None:
        """Position the overlay in the top-right corner of parent."""
        if self.parent():
            parent_width = self.parent().width()
            overlay_width = self.width()
            
            x = parent_width - overlay_width - 10
            y = 10
            
            self.move(x, y)
    
    def showEvent(self, event: QShowEvent) -> None:
        """Handle show event."""
        super().showEvent(event)
        self.update_dimensions()
        self.raise_()
        
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize event."""
        super().resizeEvent(event)
        self.position_overlay()
        self.raise_()