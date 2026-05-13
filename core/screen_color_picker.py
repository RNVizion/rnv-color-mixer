"""
Cross-platform screen color picker.

Captures the entire virtual desktop — including all connected monitors —
into a cached QImage, then renders a magnified crosshair overlay that
follows the cursor. Supports monitors at different resolutions and
positions, pre-caches all QColor/QFont/QPen objects, and uses a single
captured frame (rather than repeated conversions) for smooth 60fps
hovering without race conditions.

Python 3.13 optimized — using modern type hints.
"""

import traceback

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPixmap, QImage, QCursor, QPaintEvent,
    QMouseEvent, QKeyEvent, QFont, QCloseEvent
)


# Import logger for consistent logging (Final Optimization)
try:
    from utils.logger import Logger
    logger = Logger("ScreenPicker")
except ImportError:
    logger = None

# Import SignalMixin for signal connection tracking
from utils.signal_manager import SignalMixin

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False

# =============================================================================
# MODULE-LEVEL CACHED OBJECTS (shared across all instances, never recreated)
# =============================================================================

# Colors - created once, used forever
_OVERLAY_COLOR = QColor(0, 0, 0, 50)
_GOLD_BRAND = QColor('#d2bc93')
_GOLD_TRANSPARENT = QColor(191, 177, 69, 50)
_INFO_BG = QColor(0, 0, 0, 180)

# Pens - pre-created with correct settings
_PEN_GOLD_2 = QPen(_GOLD_BRAND, 2)
_PEN_GOLD_3 = QPen(_GOLD_BRAND, 3)
_PEN_GRID = QPen(_GOLD_TRANSPARENT, 1)

# Fonts - created once
_FONT_BOLD = QFont("Arial", 9, QFont.Weight.Bold)
_FONT_SMALL = QFont("Arial", 7)


class ScreenColorPicker(QWidget, SignalMixin):
    """
    Fullscreen overlay for picking colors from anywhere on screen.
    Shows a magnified view of the area under the cursor.
    
    PHASE 2 OPTIMIZATIONS:
    - QImage converted once at capture, not per-frame
    - Pre-cached colors, pens, fonts for zero-allocation painting
    - Race condition protection with _is_active flag
    
    PHASE 3 MULTI-MONITOR:
    - Captures and composites all screens into single virtual desktop image
    - Overlay widget spans entire virtual desktop geometry
    - Cursor coordinates mapped to virtual desktop space
    """
    
    # Signals
    color_picked = pyqtSignal(tuple)  # Emits RGB tuple when color is picked
    picker_cancelled = pyqtSignal()   # Emits when picker is cancelled (Esc)
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        
        # Initialize signal tracking
        self.init_signal_tracking()
        
        # Widget setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # Screen capture - PHASE 2: Store both pixmap AND image
        self.screenshot: QPixmap | None = None
        self._screenshot_image: QImage | None = None  # Cached QImage for color lookup
        
        # PHASE 3: Multi-monitor support - virtual desktop geometry
        self._virtual_geometry = QRect()  # Combined geometry of all screens
        self._screen_offset = QPoint(0, 0)  # Top-left of virtual desktop (can be negative!)
        
        # Current state
        self.current_color: tuple[int, int, int] = (0, 0, 0)
        self.cursor_pos = QPoint(0, 0)
        
        # PHASE 2: Pre-computed display strings (updated on color change)
        self._hex_text: str = "#000000"
        self._rgb_text: str = "RGB: 0, 0, 0"
        self._current_color_qcolor = QColor(0, 0, 0)
        
        # Magnifier settings
        self.magnifier_size = 140  # Size of magnifier square
        self.zoom_factor = 8       # How much to zoom
        self._pixel_size = self.magnifier_size // self.zoom_factor  # Pre-computed
        
        # PHASE 2: Timer with race condition protection
        self._is_active = False
        self.update_timer = QTimer(self)
        # Track timer signal connection
        self.track_connection(self.update_timer, self.update_timer.timeout, self._update_cursor_position, "update_timer")
        
    def start_picking(self) -> None:
        """Start the color picking process with multi-monitor support."""
        try:
            # Mark as active BEFORE starting
            self._is_active = True
            
            # Capture all screens (multi-monitor)
            self._capture_all_screens()
            
            if not self.screenshot or not self._screenshot_image:
                logger.error("Failed to capture screen") if logger else None
                self._is_active = False
                self.close()
                return
            
            # PHASE 3: Set geometry to cover entire virtual desktop
            self.setGeometry(self._virtual_geometry)
            self.showFullScreen()
            
            # Start cursor tracking (only if active)
            if self._is_active:
                self.update_timer.start(16)  # ~60 FPS
            
            # Grab keyboard for Esc key
            self.grabKeyboard()
            
            # Log multi-monitor info
            screens = QApplication.screens()
            logger.success(f"Screen color picker started - {len(screens)} monitor(s) detected") if logger else None
            logger.info(f"  Virtual desktop: {self._virtual_geometry.width()}x{self._virtual_geometry.height()}") if logger else None
            logger.info(f"  Offset: ({self._screen_offset.x()}, {self._screen_offset.y()})") if logger else None
            logger.info("  Click to pick, Esc to cancel") if logger else None
            
        except Exception as e:
            logger.error(f"Error starting color picker: {e}") if logger else None
            self._is_active = False
            self.close()
    
    def _capture_all_screens(self) -> None:
        """
        Capture the entire virtual desktop (all monitors).
        
        PHASE 3 MULTI-MONITOR:
        - Gets virtual geometry spanning all screens
        - Captures each screen individually
        - Composites into single image at correct positions
        
        PHASE 2: Convert to QImage ONCE here, not on every frame.
        """
        try:
            screens = QApplication.screens()
            if not screens:
                logger.error("No screens detected") if logger else None
                return
            
            # Single monitor - use simple capture (faster)
            if len(screens) == 1:
                screen = screens[0]
                self._virtual_geometry = screen.geometry()
                self._screen_offset = self._virtual_geometry.topLeft()
                self.screenshot = screen.grabWindow(0)
                self._screenshot_image = self.screenshot.toImage()
                logger.success(f"Single monitor capture: {self.screenshot.width()}x{self.screenshot.height()}") if logger else None
                return
            
            # Multi-monitor - calculate virtual desktop geometry
            # This handles monitors at any position (including negative coordinates)
            min_x = min(s.geometry().left() for s in screens)
            min_y = min(s.geometry().top() for s in screens)
            max_x = max(s.geometry().right() for s in screens)
            max_y = max(s.geometry().bottom() for s in screens)
            
            # Virtual desktop dimensions
            virtual_width = max_x - min_x + 1
            virtual_height = max_y - min_y + 1
            
            self._virtual_geometry = QRect(min_x, min_y, virtual_width, virtual_height)
            self._screen_offset = QPoint(min_x, min_y)
            
            logger.info("Multi-monitor layout detected:") if logger else None
            for i, screen in enumerate(screens):
                geo = screen.geometry()
                logger.info(f"  Monitor {i+1}: {geo.width()}x{geo.height()} at ({geo.x()}, {geo.y()})") if logger else None
            
            # Create composite pixmap for entire virtual desktop
            composite = QPixmap(virtual_width, virtual_height)
            composite.fill(Qt.GlobalColor.black)  # Fill with black for any gaps
            
            painter = QPainter(composite)
            
            # Capture and paint each screen at its correct position
            for screen in screens:
                screen_geo = screen.geometry()
                
                # Capture this screen
                screen_pixmap = screen.grabWindow(0)
                
                # Calculate position relative to virtual desktop origin
                rel_x = screen_geo.x() - min_x
                rel_y = screen_geo.y() - min_y
                
                # Paint to composite
                painter.drawPixmap(rel_x, rel_y, screen_pixmap)
            
            painter.end()
            
            self.screenshot = composite
            self._screenshot_image = self.screenshot.toImage()
            
            logger.success(f"Multi-monitor capture: {virtual_width}x{virtual_height} ({len(screens)} screens)") if logger else None
            logger.debug(f"  Image format: {self._screenshot_image.format().name}") if logger else None
            
        except Exception as e:
            logger.error(f"Error capturing screens: {e}") if logger else None
            traceback.print_exc()
            self.screenshot = None
            self._screenshot_image = None
    
    def _update_cursor_position(self) -> None:
        """
        Update cursor position and current color.
        
        PHASE 2: Uses cached QImage instead of converting every frame.
        PHASE 3: Maps global cursor to virtual desktop coordinates.
        """
        # Race condition protection
        if not self._is_active:
            return
        
        try:
            # Get global cursor position
            self.cursor_pos = QCursor.pos()
            
            # Get color at cursor position using CACHED image
            if self._screenshot_image and not self._screenshot_image.isNull():
                # PHASE 3: Map global cursor to virtual desktop image coordinates
                # Subtract the virtual desktop origin (which can be negative)
                x = self.cursor_pos.x() - self._screen_offset.x()
                y = self.cursor_pos.y() - self._screen_offset.y()
                
                # Clamp to image bounds
                x = max(0, min(x, self._screenshot_image.width() - 1))
                y = max(0, min(y, self._screenshot_image.height() - 1))
                
                # PHASE 2: Use cached image (no conversion!)
                color = self._screenshot_image.pixelColor(x, y)
                new_color = (color.red(), color.green(), color.blue())
                
                # Only update strings if color changed
                if new_color != self.current_color:
                    self.current_color = new_color
                    self._update_color_strings()
            
            # Trigger repaint
            self.update()
            
        except Exception as e:
            logger.error(f"Error updating cursor: {e}") if logger else None
    
    def _update_color_strings(self) -> None:
        """
        Update pre-computed display strings when color changes.
        
        PHASE 2: Move string formatting OUT of paint loop.
        """
        r, g, b = self.current_color
        self._hex_text = f"#{r:02X}{g:02X}{b:02X}"
        self._rgb_text = f"RGB: {r}, {g}, {b}"
        self._current_color_qcolor = QColor(r, g, b)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Draw the magnifier and crosshair.
        
        PHASE 2: Uses pre-cached colors, pens, fonts - zero allocations.
        """
        if not self._is_active:
            return
        
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw semi-transparent overlay (using cached color)
            painter.fillRect(self.rect(), _OVERLAY_COLOR)
            
            # Draw magnifier
            self._draw_magnifier(painter)
            
            # Draw crosshair
            self._draw_crosshair(painter)
            
            # Draw color info
            self._draw_color_info(painter)
            
        except Exception as e:
            logger.error(f"Error in paint event: {e}") if logger else None
    
    def _draw_magnifier(self, painter: QPainter) -> None:
        """
        Draw the magnified view of area under cursor.
        
        PHASE 2: Uses pre-cached pens and pre-computed pixel_size.
        PHASE 3: Source coordinates mapped to virtual desktop.
        """
        if not self.screenshot or self.screenshot.isNull():
            return
        
        try:
            # Calculate magnifier position (offset from cursor)
            mag_offset = 60
            local_pos = self.mapFromGlobal(self.cursor_pos)
            mag_x = local_pos.x() + mag_offset
            mag_y = local_pos.y() + mag_offset
            
            # Keep magnifier on screen
            if mag_x + self.magnifier_size > self.width():
                mag_x = local_pos.x() - mag_offset - self.magnifier_size
            if mag_y + self.magnifier_size > self.height():
                mag_y = local_pos.y() - mag_offset - self.magnifier_size
            
            # PHASE 3: Calculate source rectangle in virtual desktop coordinates
            # local_pos is already in virtual desktop space (widget coords = virtual coords)
            src_x = max(0, local_pos.x() - self._pixel_size // 2)
            src_y = max(0, local_pos.y() - self._pixel_size // 2)
            src_rect = QRect(src_x, src_y, self._pixel_size, self._pixel_size)
            
            # Destination rectangle
            dest_rect = QRect(mag_x, mag_y, self.magnifier_size, self.magnifier_size)
            
            # Draw magnified screenshot
            painter.drawPixmap(dest_rect, self.screenshot, src_rect)
            
            # Draw grid (using cached pen)
            self._draw_magnifier_grid(painter, dest_rect)
            
            # Draw center pixel highlight
            center_x = dest_rect.center().x()
            center_y = dest_rect.center().y()
            highlight_rect = QRect(
                center_x - self._pixel_size // 2,
                center_y - self._pixel_size // 2,
                self._pixel_size,
                self._pixel_size
            )
            painter.setPen(_PEN_GOLD_2)  # Cached pen
            painter.drawRect(highlight_rect)
            
            # Draw border around magnifier
            painter.setPen(_PEN_GOLD_3)  # Cached pen
            painter.drawRect(dest_rect)
            
        except Exception as e:
            logger.error(f"Error drawing magnifier: {e}") if logger else None
    
    def _draw_magnifier_grid(self, painter: QPainter, rect: QRect) -> None:
        """
        Draw grid lines in magnifier.
        
        PHASE 2: Uses cached pen and pre-computed pixel_size.
        """
        try:
            painter.setPen(_PEN_GRID)  # Cached pen
            
            # Draw vertical lines
            for i in range(self.zoom_factor + 1):
                x = rect.left() + i * self._pixel_size
                painter.drawLine(x, rect.top(), x, rect.bottom())
            
            # Draw horizontal lines
            for i in range(self.zoom_factor + 1):
                y = rect.top() + i * self._pixel_size
                painter.drawLine(rect.left(), y, rect.right(), y)
                
        except Exception as e:
            logger.error(f"Error drawing grid: {e}") if logger else None
    
    def _draw_crosshair(self, painter: QPainter) -> None:
        """
        Draw crosshair at cursor position.
        
        PHASE 2: Uses cached pen.
        """
        try:
            local_pos = self.mapFromGlobal(self.cursor_pos)
            
            painter.setPen(_PEN_GOLD_2)  # Cached pen
            
            # Vertical line
            painter.drawLine(local_pos.x(), 0, local_pos.x(), self.height())
            
            # Horizontal line
            painter.drawLine(0, local_pos.y(), self.width(), local_pos.y())
            
            # Draw center circle
            painter.drawEllipse(local_pos, 20, 20)
            
        except Exception as e:
            logger.error(f"Error drawing crosshair: {e}") if logger else None
    
    def _draw_color_info(self, painter: QPainter) -> None:
        """
        Draw color information near cursor.
        
        PHASE 2: Uses cached colors, fonts, and pre-formatted strings.
        """
        try:
            local_pos = self.mapFromGlobal(self.cursor_pos)
            info_x = local_pos.x() - 60
            info_y = local_pos.y() + 30
            
            # Keep on screen
            if info_y + 60 > self.height():
                info_y = local_pos.y() - 90
            if info_x < 0:
                info_x = 10
            if info_x + 120 > self.width():
                info_x = self.width() - 130
            
            # Draw background (cached color)
            info_rect = QRect(info_x, info_y, 120, 60)
            painter.fillRect(info_rect, _INFO_BG)
            painter.setPen(_PEN_GOLD_2)  # Cached pen
            painter.drawRect(info_rect)
            
            # Draw color swatch (using cached QColor)
            swatch_rect = QRect(info_x + 5, info_y + 5, 30, 30)
            painter.fillRect(swatch_rect, self._current_color_qcolor)
            painter.drawRect(swatch_rect)
            
            # Draw color text (cached font and pre-formatted strings)
            painter.setPen(_GOLD_BRAND)
            painter.setFont(_FONT_BOLD)  # Cached font
            painter.drawText(info_x + 40, info_y + 15, self._hex_text)
            
            painter.setFont(_FONT_SMALL)  # Cached font
            painter.drawText(info_x + 40, info_y + 30, self._rgb_text)
            
            # Instructions (static text)
            painter.drawText(info_x + 5, info_y + 50, "Click to pick")
            
        except Exception as e:
            logger.error(f"Error drawing color info: {e}") if logger else None
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click - pick the color."""
        if not self._is_active:
            return
        
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.color_picked.emit(self.current_color)
                logger.success(f"Color picked: {self.current_color}") if logger else None
                self._cleanup_and_close()
                
        except Exception as e:
            logger.error(f"Error in mouse press: {e}") if logger else None
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press - Esc to cancel."""
        if not self._is_active:
            return
        
        try:
            if event.key() == Qt.Key.Key_Escape:
                logger.info("Color picker cancelled") if logger else None
                self.picker_cancelled.emit()
                self._cleanup_and_close()
                
        except Exception as e:
            logger.error(f"Error in key press: {e}") if logger else None
    
    def _cleanup_and_close(self) -> None:
        """
        Clean up resources before closing.
        
        PHASE 2: Proper cleanup sequence to prevent race conditions.
        """
        # Mark inactive FIRST to stop timer callbacks
        self._is_active = False
        
        # Stop timer
        self.update_timer.stop()
        
        # Release keyboard
        self.releaseKeyboard()
        
        # Clear large resources
        self.screenshot = None
        self._screenshot_image = None
        
        # Close widget
        self.close()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Clean up when closing.
        
        PHASE 2: Ensures cleanup even if close() called directly.
Properly disconnects tracked signals.
        """
        try:
            # Mark inactive
            self._is_active = False
            
            # Stop timer
            self.update_timer.stop()
            
            # Disconnect tracked signals
            self.cleanup_signals()
            
            # Release keyboard
            self.releaseKeyboard()
            
            # Clear screenshot resources
            self.screenshot = None
            self._screenshot_image = None
            
        except Exception as e:
            logger.error(f"Error in close event: {e}") if logger else None
        
        event.accept()