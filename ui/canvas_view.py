"""
Canvas view for image display and color sampling.

Provides a scrollable image canvas with click-to-sample, drag-to-region,
and wheel-zoom interactions. Supports theme-aware rendering with a
persistent dark canvas background across all application themes
(Dark, Light, and Image mode).
"""

import traceback

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QScrollArea, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QTimer, QPoint, QEvent
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QMouseEvent, QWheelEvent, 
    QResizeEvent, QPaintEvent, QEnterEvent, QFont, QImage, QBrush
)

if TYPE_CHECKING:
    from core.image_handler import ImageHandler
    from ui.ui_handler import UIHandler

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("CanvasView")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False

# Import SignalMixin for signal connection tracking
from utils.signal_manager import SignalMixin

try:
    from core.color_math import ColorMath
except ImportError:
    if logger:
        logger.warning("ColorMath not available")
    ColorMath = None

try:
    from utils import config
except ImportError:
    logger.warning("Warning: config not available")
    config = None


class ImageDisplayLabel(QLabel):
    """Custom QLabel with drag selection for color sampling"""
    
    # Signals
    mouse_moved = pyqtSignal(int, int)
    mouse_pressed = pyqtSignal(int, int, int)
    mouse_released = pyqtSignal(int, int, int)
    mouse_double_clicked = pyqtSignal(int, int)
    wheel_event = pyqtSignal(int, int, int)
    mouse_entered = pyqtSignal()
    mouse_left = pyqtSignal()
    
    region_selected = pyqtSignal(int, int, int, int)
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(1, 1)
        self.setMouseTracking(True)
        # Enable transparency support
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        # State
        self.crosshair_pos: tuple[int, int] | None = None
        self.selection_start: tuple[int, int] | None = None
        self.selection_end: tuple[int, int] | None = None
        self.selection_rect: QRect | None = None
        self.is_selecting = False
        self.is_dragging = False
        
        # Color preview
        self.preview_color = (0, 0, 0)
        self.preview_size = 120
        self.show_preview = False
        self.preview_opacity = 0.9
        
        # Theme
        self.is_dark = True
        
        # Drag threshold (pixels to move before it counts as drag)
        self.drag_threshold = 5

    def set_preview_color(self, color: tuple[int, int, int], show: bool = True) -> None:
        """Set color preview safely"""
        try:
            self.preview_color = color
            self.show_preview = show
            self.update()
        except Exception as e:
            logger.error(f"Error setting preview color: {e}")

    def hide_preview(self) -> None:
        """Hide preview safely"""
        try:
            self.show_preview = False
            self.update()
        except Exception as e:
            logger.error(f"Error hiding preview: {e}")

    def set_preview_size(self, size: int) -> None:
        """Set preview size safely"""
        try:
            self.preview_size = max(80, min(200, size))
            self.update()
        except Exception as e:
            logger.error(f"Error setting preview size: {e}")

    def set_theme(self, is_dark: bool) -> None:
        """Set theme for preview colors."""
        self.is_dark = is_dark
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move - updated for drag selection"""
        try:
            x, y = int(event.position().x()), int(event.position().y())
            self.crosshair_pos = (x, y)
            
            if self.is_selecting and self.selection_start:
                start_x, start_y = self.selection_start
                
                distance = ((x - start_x)**2 + (y - start_y)**2)**0.5
                
                if distance > self.drag_threshold:
                    self.is_dragging = True
                
                if self.is_dragging:
                    self.selection_end = (x, y)
                    
                    left = min(start_x, x)
                    top = min(start_y, y)
                    width = abs(x - start_x)
                    height = abs(y - start_y)
                    
                    self.selection_rect = QRect(left, top, width, height)
            
            self.mouse_moved.emit(x, y)
            self.update()
            
        except Exception as e:
            logger.error(f"Error in mouseMoveEvent: {e}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - start selection"""
        try:
            x, y = int(event.position().x()), int(event.position().y())
            
            if event.button() == Qt.MouseButton.LeftButton:
                self.selection_start = (x, y)
                self.selection_end = None
                self.selection_rect = None
                self.is_selecting = True
                self.is_dragging = False
                logger.debug(f"Selection started at ({x}, {y})")
            
            self.mouse_pressed.emit(x, y, int(event.button()))
            
        except Exception as e:
            logger.error(f"Error in mousePressEvent: {e}")

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release - complete selection"""
        try:
            x, y = int(event.position().x()), int(event.position().y())
            
            if event.button() == Qt.MouseButton.LeftButton:
                if self.is_dragging and self.selection_rect and not self.selection_rect.isEmpty():
                    logger.debug(f"Drag completed: {self.selection_rect}")
                    
                    rect = self.selection_rect
                    x1, y1 = rect.left(), rect.top()
                    x2, y2 = rect.right(), rect.bottom()
                    
                    self.region_selected.emit(x1, y1, x2, y2)
                    
                    QTimer.singleShot(200, self._clear_selection)
                else:
                    self._clear_selection()
                
                self.is_selecting = False
                self.is_dragging = False
            
            self.mouse_released.emit(x, y, int(event.button()))
            
        except Exception as e:
            logger.error(f"Error in mouseReleaseEvent: {e}")

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handle double click - single pixel sample"""
        try:
            x, y = int(event.position().x()), int(event.position().y())
            logger.debug(f"Double-click at ({x}, {y})")
            self.mouse_double_clicked.emit(x, y)
        except Exception as e:
            logger.error(f"Error in mouseDoubleClickEvent: {e}")

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel event safely"""
        try:
            delta = event.angleDelta().y()
            pos = event.position()
            self.wheel_event.emit(int(pos.x()), int(pos.y()), delta)
        except Exception as e:
            logger.error(f"Error in wheelEvent: {e}")

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle enter event safely"""
        try:
            self.mouse_entered.emit()
        except Exception as e:
            logger.error(f"Error in enterEvent: {e}")

    def leaveEvent(self, event: QEvent) -> None:
        """Handle leave event safely"""
        try:
            self.crosshair_pos = None
            self.mouse_left.emit()
            self.update()
        except Exception as e:
            logger.error(f"Error in leaveEvent: {e}")

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint event with drag selection visualization"""
        try:
            super().paintEvent(event)
            
            if not self.pixmap() or self.pixmap().isNull():
                return
            
            painter = QPainter(self)
            if not painter.isActive():
                return
            
            try:
                # Get theme colors
                theme = config.ThemeManager().get_current_theme() if config else None
                
                # Draw selection rectangle if dragging
                if self.is_dragging and self.selection_rect and not self.selection_rect.isEmpty():
                    # Determine colors based on theme
                    if theme and theme['name'] == 'Dark':
                        overlay_color = QColor(theme['accent'])
                        border_color = QColor(theme['accent'])
                        corner_color = QColor(theme['accent'])
                        text_color = QColor(255, 255, 255)
                    else:
                        _accent = theme['accent'] if theme else config.ThemeManager.DARK_THEME['accent']
                        overlay_color = QColor(_accent)
                        border_color = QColor(_accent)
                        corner_color = QColor(_accent)
                        text_color = QColor(0, 0, 0)
                    
                    # Draw semi-transparent overlay
                    painter.fillRect(self.selection_rect, overlay_color)
                    
                    # Draw selection border
                    pen = QPen(border_color, 2, Qt.PenStyle.SolidLine)
                    painter.setPen(pen)
                    painter.drawRect(self.selection_rect)
                    
                    # Draw corner indicators
                    corner_size = 6
                    rect = self.selection_rect
                    corners = [
                        (rect.left(), rect.top()),
                        (rect.right(), rect.top()),
                        (rect.left(), rect.bottom()),
                        (rect.right(), rect.bottom())
                    ]
                    
                    painter.setBrush(QBrush(corner_color))
                    for cx, cy in corners:
                        painter.drawRect(cx - corner_size//2, cy - corner_size//2, 
                                       corner_size, corner_size)
                    
                    # Draw size info
                    if rect.width() > 50 and rect.height() > 30:
                        size_text = f"{rect.width()}×{rect.height()}"
                        font = QFont("Montserrat Black" if config else "Arial", 10)
                        painter.setFont(font)
                        
                        text_rect = painter.boundingRect(rect, Qt.AlignmentFlag.AlignCenter, size_text)
                        bg_rect = text_rect.adjusted(-4, -2, 4, 2)
                        
                        if theme and theme['name'] == 'Dark':
                            painter.fillRect(bg_rect, QColor(0, 0, 0, 180))
                        else:
                            painter.fillRect(bg_rect, QColor(200, 200, 200, 180))
                        
                        painter.setPen(text_color)
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, size_text)
                
                # Draw crosshair if mouse is over image (but not while dragging)
                elif self.crosshair_pos and not self.is_dragging:
                    x, y = self.crosshair_pos
                    
                    if theme and theme['name'] == 'Dark':
                        pen = QPen(QColor(config.ThemeManager.LIGHT_THEME['accent']), 1)
                    else:
                        pen = QPen(QColor(config.ThemeManager.LIGHT_THEME['accent']), 1)
                    
                    painter.setPen(pen)
                    
                    crosshair_size = 10
                    painter.drawLine(int(x) - crosshair_size, int(y), 
                                   int(x) + crosshair_size, int(y))
                    painter.drawLine(int(x), int(y) - crosshair_size, 
                                   int(x), int(y) + crosshair_size)
                
                # Draw color preview if enabled (and not dragging)
                if self.show_preview and not self.is_dragging:
                    self._draw_color_preview(painter, theme)
                    
            finally:
                painter.end()
                
        except Exception as e:
            logger.error(f"Error in paintEvent: {e}")

    def _draw_color_preview(self, painter: QPainter, theme: dict | None = None) -> None:
        """Draw color preview overlay safely"""
        if not ColorMath:
            return
            
        try:
            center_x = self.width() // 2
            center_y = self.height() // 2
            half_size = self.preview_size // 2
            
            preview_rect = QRect(
                center_x - half_size,
                center_y - half_size,
                self.preview_size,
                self.preview_size
            )
            
            # Background
            if theme and theme['name'] == 'Dark':
                bg_color = QColor(0, 0, 0, 200)
                border_color = QColor(230, 230, 230)
            else:
                bg_color = QColor(255, 255, 255, 200)
                border_color = QColor(0, 0, 0)
            
            painter.fillRect(preview_rect, bg_color)
            
            # Color square
            preview_color = QColor(*self.preview_color)
            preview_color.setAlphaF(self.preview_opacity)
            color_rect = preview_rect.adjusted(8, 8, -8, -8)
            painter.fillRect(color_rect, preview_color)
            
            # Border
            border_pen = QPen(border_color, 2)
            painter.setPen(border_pen)
            painter.drawRect(color_rect)
            
            # Text
            hex_color = ColorMath.rgb_to_hex(self.preview_color)
            font_size = config.FONT_SIZES["medium"] if config else 12
            font = QFont("Montserrat Black" if config else "Arial Black", font_size)
            font.setBold(True)
            painter.setFont(font)
            
            text_y = preview_rect.bottom() + 20
            text_rect = QRect(center_x - 60, text_y, 120, 25)
            
            # Text shadow
            if theme and theme['name'] == 'Dark':
                shadow_pen = QPen(QColor(255, 255, 255), 1)
                text_color = QColor(0, 0, 0)
            else:
                shadow_pen = QPen(QColor(0, 0, 0), 1)
                text_color = QColor(255, 255, 255)
            
            painter.setPen(shadow_pen)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        shadow_rect = text_rect.adjusted(dx, dy, dx, dy)
                        painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, hex_color)
            
            # Main text
            painter.setPen(text_color)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, hex_color)
            
            # RGB text
            rgb_font = QFont("Montserrat Black" if config else "Arial Black", font_size - 2)
            painter.setFont(rgb_font)
            rgb_text = f"rgb{self.preview_color}"
            rgb_rect = QRect(center_x - 80, text_y + 25, 160, 20)
            
            painter.setPen(shadow_pen)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        shadow_rect = rgb_rect.adjusted(dx, dy, dx, dy)
                        painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, rgb_text)
            
            painter.setPen(text_color)
            painter.drawText(rgb_rect, Qt.AlignmentFlag.AlignCenter, rgb_text)
            
        except Exception as e:
            logger.error(f"Error in _draw_color_preview: {e}")

    def _clear_selection(self) -> None:
        """Clear selection safely"""
        try:
            self.selection_rect = None
            self.selection_start = None
            self.selection_end = None
            self.is_selecting = False
            self.is_dragging = False
            self.update()
        except Exception as e:
            logger.error(f"Error clearing selection: {e}")


class CanvasView(QScrollArea, SignalMixin):
    """Interactive canvas with drag color selection and theme support"""
    
    # Signals
    pixel_hovered = pyqtSignal(int, int, tuple)
    pixel_sampled = pyqtSignal(tuple)
    region_sampled = pyqtSignal(tuple)
    zoom_changed = pyqtSignal(float)
    
    def __init__(self, image_handler: "ImageHandler") -> None:
        super().__init__()
        
        # Initialize signal tracking
        self.init_signal_tracking()
        
        logger.debug("CanvasView: Initializing...")
        
        self.image_handler = image_handler
        self.image_label = ImageDisplayLabel()
        
        try:
            self.setWidget(self.image_label)
            self.setWidgetResizable(False)
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # CRITICAL: Disable auto-fill background for transparency in Image Mode
            self.setAutoFillBackground(False)
            self.viewport().setAutoFillBackground(False)
            
            from PyQt6.QtWidgets import QSizePolicy
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        except Exception as e:
            logger.error(f"Error configuring scroll area: {e}")
        
        self._connect_signals_safely()
        
        logger.debug("CanvasView: Initialization complete")

    def _connect_signals_safely(self) -> None:
        """Connect signals with error handling and tracking for proper cleanup"""
        try:
            # Track all signal connections
            self.track_connection(self.image_label, self.image_label.mouse_moved, self._on_mouse_move, "mouse_moved")
            self.track_connection(self.image_label, self.image_label.mouse_double_clicked, self._on_double_click, "double_clicked")
            self.track_connection(self.image_label, self.image_label.wheel_event, self._on_wheel_event, "wheel_event")
            self.track_connection(self.image_label, self.image_label.mouse_left, self._on_mouse_leave, "mouse_left")
            self.track_connection(self.image_label, self.image_label.region_selected, self._on_region_selected, "region_selected")
            
            self.track_connection(self.image_handler, self.image_handler.zoom_changed, self.zoom_changed.emit, "zoom_changed")
            logger.debug("CanvasView: All signals connected with tracking")
        except Exception as e:
            logger.error(f"Error connecting signals: {e}")

    def _on_region_selected(self, widget_x1: int, widget_y1: int, 
                           widget_x2: int, widget_y2: int) -> None:
        """Handle region selection from drag"""
        try:
            logger.debug(f"Region selected: ({widget_x1},{widget_y1}) to ({widget_x2},{widget_y2})")
            
            if not self.image_handler.is_loaded():
                logger.info("No image loaded")
                return
            
            img_x1, img_y1 = self._widget_to_image_coords(widget_x1, widget_y1)
            img_x2, img_y2 = self._widget_to_image_coords(widget_x2, widget_y2)
            
            logger.debug(f"Image coords: ({img_x1},{img_y1}) to ({img_x2},{img_y2})")
            
            avg_color = self.image_handler.sample_region(
                min(img_x1, img_x2), min(img_y1, img_y2),
                max(img_x1, img_x2), max(img_y1, img_y2)
            )
            
            if avg_color:
                logger.debug(f"Average color: {avg_color}")
                self.region_sampled.emit(avg_color)
            else:
                logger.error("Failed to sample region")
                
        except Exception as e:
            logger.error(f"Error in _on_region_selected: {e}")
            traceback.print_exc()

    def set_preview_color(self, color: tuple[int, int, int], show: bool = True) -> None:
        """Set preview color safely"""
        try:
            if self.image_label:
                self.image_label.set_preview_color(color, show)
        except Exception as e:
            logger.error(f"Error setting preview color: {e}")

    def hide_preview(self) -> None:
        """Hide preview safely"""
        try:
            if self.image_label:
                self.image_label.hide_preview()
        except Exception as e:
            logger.error(f"Error hiding preview: {e}")

    def display_image(self) -> None:
        """Display image using cached QImage for performance"""
        logger.debug("CanvasView.display_image(): Starting...")
        
        try:
            if not self.image_handler.is_loaded():
                logger.info("CanvasView.display_image(): No image loaded")
                self.clear_canvas()
                return
            
            logger.debug("CanvasView.display_image(): Getting cached QImage...")
            qimage = self.image_handler.get_qimage()
            
            if not qimage or qimage.isNull():
                logger.error("CanvasView.display_image(): Failed to get QImage")
                return
            
            logger.debug(f"CanvasView.display_image(): QImage ready: {qimage.size()}")
            
            pixmap = QPixmap.fromImage(qimage)
            
            if pixmap.isNull():
                logger.error("CanvasView.display_image(): QPixmap conversion failed!")
                return
            
            logger.info(f"CanvasView.display_image(): QPixmap created: {pixmap.size()}")
            
            self.image_label.setPixmap(pixmap)
            self.image_label.resize(pixmap.size())
            
            logger.debug("CanvasView.display_image(): Image display complete!")
            
        except Exception as e:
            logger.error(f"CRITICAL ERROR in display_image: {e}")
            traceback.print_exc()

    def clear_canvas(self) -> None:
        """Clear canvas safely"""
        try:
            logger.debug("CanvasView.clear_canvas(): Clearing...")
            self.image_label.clear()
            self.image_label.resize(1, 1)  # Minimal size when no image
            self.image_label.hide_preview()
            logger.debug("CanvasView.clear_canvas(): Complete")
        except Exception as e:
            logger.error(f"Error clearing canvas: {e}")

    def reset_zoom(self) -> None:
        """Reset zoom safely"""
        try:
            if not self.image_handler.is_loaded():
                return
            
            available_size = self.viewport().size()
            container_size = (available_size.width() - 20, available_size.height() - 20)
            
            self.image_handler.fit_to_container(container_size)
            self.display_image()
        except Exception as e:
            logger.error(f"Error resetting zoom: {e}")

    def _on_mouse_move(self, widget_x: int, widget_y: int) -> None:
        """Handle mouse move safely"""
        try:
            if not self.image_handler.is_loaded():
                return
            
            img_x, img_y = self._widget_to_image_coords(widget_x, widget_y)
            color = self.image_handler.get_pixel_at_coordinates(img_x, img_y)
            
            if color:
                self.pixel_hovered.emit(img_x, img_y, color)
        except Exception as e:
            logger.error(f"Error in _on_mouse_move: {e}")

    def _on_double_click(self, widget_x: int, widget_y: int) -> None:
        """Handle double click safely"""
        try:
            if not self.image_handler.is_loaded():
                return
            
            img_x, img_y = self._widget_to_image_coords(widget_x, widget_y)
            color = self.image_handler.get_pixel_at_coordinates(img_x, img_y)
            
            if color:
                logger.debug(f"Double-click sampled color: {color}")
                self.pixel_sampled.emit(color)
        except Exception as e:
            logger.error(f"Error in _on_double_click: {e}")

    def _on_wheel_event(self, widget_x: int, widget_y: int, delta: int) -> None:
        """Handle wheel event safely"""
        try:
            if not self.image_handler.is_loaded():
                return
            
            scroll_x = self.horizontalScrollBar().value() + widget_x
            scroll_y = self.verticalScrollBar().value() + widget_y
            
            zoom_factor = 1.1 if delta > 0 else 0.9
            scroll_x_frac, scroll_y_frac = self.image_handler.zoom_at_point(
                zoom_factor, (scroll_x, scroll_y)
            )
            
            self.display_image()
            
            if self.image_label.pixmap():
                pixmap_size = self.image_label.pixmap().size()
                self.horizontalScrollBar().setValue(int(scroll_x_frac * pixmap_size.width()))
                self.verticalScrollBar().setValue(int(scroll_y_frac * pixmap_size.height()))
        except Exception as e:
            logger.error(f"Error in _on_wheel_event: {e}")

    def _on_mouse_leave(self) -> None:
        """Handle mouse leave safely"""
        pass

    def _widget_to_image_coords(self, widget_x: int, widget_y: int) -> tuple[int, int]:
        """Convert widget to image coordinates safely"""
        try:
            if not self.image_handler.is_loaded() or not self.image_label.pixmap():
                return (0, 0)
            
            pixmap = self.image_label.pixmap()
            pixmap_w, pixmap_h = pixmap.width(), pixmap.height()
            label_w, label_h = self.image_label.width(), self.image_label.height()
            
            if label_w >= pixmap_w:
                image_left = (label_w - pixmap_w) // 2
                if widget_x < image_left or widget_x >= image_left + pixmap_w:
                    widget_x = max(image_left, min(image_left + pixmap_w - 1, widget_x))
                canvas_x = widget_x - image_left
            else:
                canvas_x = widget_x
            
            if label_h >= pixmap_h:
                image_top = (label_h - pixmap_h) // 2
                if widget_y < image_top or widget_y >= image_top + pixmap_h:
                    widget_y = max(image_top, min(image_top + pixmap_h - 1, widget_y))
                canvas_y = widget_y - image_top
            else:
                canvas_y = widget_y
            
            return self.image_handler.canvas_to_image_coords(canvas_x, canvas_y)
        except Exception as e:
            logger.error(f"Error in _widget_to_image_coords: {e}")
            return (0, 0)

    def set_theme(self, is_dark: bool, ui_handler: "UIHandler | None" = None) -> None:
        """Set theme safely - dark background for dark/image modes, light for light mode"""
        try:
            self.image_label.set_theme(is_dark)
            
            # Check if we're in Image Mode
            is_image_mode = False
            if ui_handler:
                is_image_mode = ui_handler.is_image_mode()
            
            # Use dark canvas for Dark Mode AND Image Mode
            # Use light canvas for Light Mode only
            if is_image_mode:
                # Image Mode - semi-transparent canvas so background shows through
                canvas_bg = 'transparent'  # Fully transparent
                border_color = config.ThemeManager.IMAGE_THEME['border_color']
            elif is_dark:
                # Dark Mode - solid dark canvas
                canvas_bg = config.ThemeManager.DARK_THEME['canvas_bg']
                border_color = config.ThemeManager.DARK_THEME['border_color']
            else:
                # Light Mode - light canvas
                canvas_bg = config.ThemeManager.LIGHT_THEME['canvas_bg']
                border_color = config.ThemeManager.LIGHT_THEME['border_color']
            
            self.setStyleSheet(f"""
                QScrollArea {{ 
                    background-color: {canvas_bg}; 
                    border: 1px solid {border_color}; 
                }}
                QScrollArea::viewport {{
                    background-color: rgba(0, 0, 0, 0);
                }}
            """)
            
            # Set canvas background, but make label transparent in Image Mode
            if is_image_mode:
                self.image_label.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
            else:
                self.image_label.setStyleSheet(f"background-color: {canvas_bg};")
            
            logger.debug(f"CanvasView: Applied canvas background (is_dark={is_dark}, is_image_mode={is_image_mode}, bg={canvas_bg})")
            
        except Exception as e:
            logger.error(f"Error setting theme: {e}")

    def get_current_zoom(self) -> float:
        """Get zoom level safely"""
        try:
            return self.image_handler.zoom_level
        except Exception:
            return 1.0

    def zoom_in(self) -> None:
        """Zoom in safely"""
        try:
            if self.image_handler.is_loaded():
                self.image_handler.zoom_in()
                self.display_image()
        except Exception as e:
            logger.error(f"Error zooming in: {e}")

    def zoom_out(self) -> None:
        """Zoom out safely"""
        try:
            if self.image_handler.is_loaded():
                self.image_handler.zoom_out()
                self.display_image()
        except Exception as e:
            logger.error(f"Error zooming out: {e}")

    def fit_image(self) -> None:
        """Fit image safely"""
        try:
            self.reset_zoom()
        except Exception as e:
            logger.error(f"Error fitting image: {e}")

    def actual_size(self) -> None:
        """Show actual size safely"""
        try:
            if self.image_handler.is_loaded():
                self.image_handler.reset_zoom()
                self.display_image()
        except Exception as e:
            logger.error(f"Error showing actual size: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
        Properly disconnects all tracked signals.
        """
        logger.debug("CanvasView: Cleaning up signals...")
        self.cleanup_signals()
        logger.debug("CanvasView: Cleanup complete")