"""
UI handling and theme management for the Color Mixer application (PyQt6 version).
Now uses PIL for background image loading (same as Icon Builder)
Fixed canvas styling in Image Mode - applies IMAGE_THEME stylesheet
Handles dark/light/image modes and UI styling.
"""

import os
import traceback
import io
from typing import Callable
from PIL import Image
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QPixmap, QBrush
from utils import config

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("UIHandler")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False


class UIHandler(QObject):
    """Handles UI theming and visual components with ThemeManager (PyQt6 version)."""
    
    # Signals
    theme_changed = pyqtSignal(bool)  # is_dark
    
    def __init__(self):
        super().__init__()
        self.theme_manager = config.ThemeManager()
        self.theme_manager.detect_image_resources()
        self._background_pixmap: QPixmap | None = None
        # Load background image once at startup if available
        if self.theme_manager.image_mode_available:
            self._background_pixmap = self._load_background_image()
        
        # Debouncing timer for background resize (prevents excessive scaling)
        from PyQt6.QtCore import QTimer
        self._resize_debounce_timer = QTimer()
        self._resize_debounce_timer.setSingleShot(True)
        self._resize_pending_window = None

    def initialize_theme(self, main_window: QMainWindow, status_callback: Callable[[str], None] | None = None) -> None:
        """Initialize theme based on available resources."""
        try:
            # Clear palette cache so Highlight/HighlightedText roles are rebuilt fresh
            self.theme_manager.clear_palette_cache()
            # Apply initial theme
            self.apply_theme(main_window)
            
            if status_callback:
                status_callback(f"Theme initialized: {self.theme_manager.get_theme_display_name()}")
                
        except Exception as ex:
            logger.error("Error initializing theme", error=ex) if logger else print(f"Error: {ex}")
            if status_callback:
                status_callback("Theme initialization error - using dark mode")

    def apply_theme(self, main_window: QMainWindow) -> None:
        """Apply current theme to the application."""
        try:
            theme = self.theme_manager.get_current_theme()
            
            if theme:
                if self.theme_manager.is_image_mode():
                    # Image mode - apply both image and stylesheet
                    self._apply_image_mode(main_window)
                else:
                    # Themed mode (Dark or Light)
                    self._apply_themed_mode(main_window, theme)
            else:
                # Fallback - shouldn't happen now that IMAGE_THEME exists
                self._apply_image_mode(main_window)
            
            # Apply theme to color slots if available
            self._apply_slot_themes(main_window)
            
            # Force UI update
            main_window.update()
            QApplication.processEvents()
            
            is_dark = self.theme_manager.current_theme == 'dark'
            self.theme_changed.emit(is_dark)
            
        except Exception as e:
            logger.error("Error applying theme", error=e) if logger else print(f"Error: {e}")

    def _apply_themed_mode(self, main_window: QMainWindow, theme: dict) -> None:
        """Apply dark or light theme."""
        try:
            app = QApplication.instance()
            if not app:
                return
            
            # Use cached palette for faster theme switching
            theme_name = theme['name'].lower()
            palette = self.theme_manager.get_cached_palette(theme_name)
            
            if palette is None:
                # Create palette and cache it
                palette = QPalette()
                
                window_color = QColor(theme['window_bg'])
                text_color = QColor(theme['text_color'])
                button_color = QColor(theme['button_bg'])
                button_text_color = QColor(theme['button_text'])
                base_color = QColor(theme['scroll_area_bg'])
                border_color = QColor(theme['border_color'])
                
                # CRITICAL: Clear background image brush
                palette.setBrush(QPalette.ColorRole.Window, QBrush(window_color))
                
                # Brand accent color for highlight/selection — sourced from theme dict
                accent_color   = QColor(theme['accent'])
                accent_on_text = QColor(theme['accent_on'])

                # Set colors for all states
                for color_group in [QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive]:
                    palette.setColor(color_group, QPalette.ColorRole.Window, window_color)
                    palette.setColor(color_group, QPalette.ColorRole.WindowText, text_color)
                    palette.setColor(color_group, QPalette.ColorRole.Base, base_color)
                    palette.setColor(color_group, QPalette.ColorRole.AlternateBase, button_color)
                    palette.setColor(color_group, QPalette.ColorRole.Text, text_color)
                    palette.setColor(color_group, QPalette.ColorRole.Button, button_color)
                    palette.setColor(color_group, QPalette.ColorRole.ButtonText, button_text_color)
                    palette.setColor(color_group, QPalette.ColorRole.BrightText, text_color)
                    # Brand gold for text selection and focus highlight — replaces system blue
                    palette.setColor(color_group, QPalette.ColorRole.Highlight, accent_color)
                    palette.setColor(color_group, QPalette.ColorRole.HighlightedText, accent_on_text)
                    palette.setColor(color_group, QPalette.ColorRole.Link, accent_color)
                
                # Disabled state
                disabled_text = border_color
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, window_color)
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, window_color)
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)
                
                # Cache for future use
                self.theme_manager.set_cached_palette(theme_name, palette)
            
            app.setPalette(palette)
            
            # Apply stylesheet
            stylesheet = config.get_stylesheet(self.theme_manager)
            main_window.setStyleSheet(stylesheet)
            
            
            # Hide background label in non-image modes
            if hasattr(main_window, 'background_label') and main_window.background_label:
                main_window.background_label.hide()
            # Force update
            main_window.update()
            QApplication.processEvents()
            
        except Exception as e:
            logger.error(f"Error applying themed mode: {e}")

    def _apply_image_mode(self, main_window: QMainWindow) -> None:
        """Apply image mode theme with background image AND dark theme styling."""
        try:
            app = QApplication.instance()
            if not app:
                return
            
            # FIRST: Set palette to allow transparency
            palette = QPalette()
            transparent_color = QColor(0, 0, 0, 0)
            
            # Set all background roles to transparent
            palette.setColor(QPalette.ColorRole.Window, transparent_color)
            palette.setColor(QPalette.ColorRole.Base, transparent_color)
            palette.setColor(QPalette.ColorRole.AlternateBase, transparent_color)
            palette.setColor(QPalette.ColorRole.Button, transparent_color)
            palette.setColor(QPalette.ColorRole.Mid, transparent_color)
            palette.setColor(QPalette.ColorRole.Dark, transparent_color)
            palette.setColor(QPalette.ColorRole.Light, transparent_color)
            
            # Keep text colors visible — sourced from IMAGE_THEME
            text_color = QColor(config.ThemeManager.IMAGE_THEME['text_color'])
            palette.setColor(QPalette.ColorRole.WindowText, text_color)
            palette.setColor(QPalette.ColorRole.Text, text_color)
            
            app.setPalette(palette)
            logger.success("Set transparent palette for Image Mode")
            
            # SECOND: Show background image
            bg_image = self._background_pixmap
            if bg_image and not bg_image.isNull() and hasattr(main_window, 'background_label'):
                from PyQt6.QtCore import Qt
                
                # Scale and set background image on background label
                scaled_bg = bg_image.scaled(
                    main_window.central_widget.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                main_window.background_label.setPixmap(scaled_bg)
                main_window.background_label.setGeometry(0, 0, 
                    main_window.central_widget.width(), 
                    main_window.central_widget.height())
                main_window.background_label.lower()  # Ensure it's behind everything
                main_window.background_label.show()
                
                logger.success("Applied background image") if logger else None
            else:
                logger.warning("No background image or background label available") if logger else None
            
            # THIRD: Apply IMAGE_THEME stylesheet for UI element styling
            # This applies to child widgets (buttons, labels, etc.) but NOT the main window background
            stylesheet = config.get_stylesheet(self.theme_manager)
            main_window.setStyleSheet(stylesheet)
            logger.debug("Applied IMAGE_THEME stylesheet") if logger else None
            
            # Force update
            main_window.update()
            QApplication.processEvents()
            
        except Exception as e:
            logger.error("Error applying image mode", error=e) if logger else print(f"Error: {e}")
            traceback.print_exc()

    def _load_background_image(self) -> QPixmap | None:
        """Load background image if available using PIL (same approach as Icon Builder)."""
        try:
            if os.path.exists(config.DEFAULT_BACKGROUND):
                # Use PIL to load and optionally resize
                img = Image.open(config.DEFAULT_BACKGROUND)
                
                try:
                    # Optional: Resize if too large (over 4K)
                    max_dimension = 3840
                    if img.width > max_dimension or img.height > max_dimension:
                        ratio = min(max_dimension / img.width, max_dimension / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        logger.debug(f"Resized background image to {new_size[0]}x{new_size[1]}")
                    
                    # Convert to QPixmap via BytesIO
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    pixmap = QPixmap()
                    if pixmap.loadFromData(buffer.getvalue()):
                        self._background_pixmap = pixmap
                        logger.info(f"Loaded background image: {img.width}x{img.height}")
                        return pixmap
                    else:
                        logger.error("Failed to load background image into QPixmap")
                        return None
                finally:
                    # MEMORY FIX: Always close PIL image after use
                    img.close()
                    
        except Exception as e:
            logger.error("Error loading background image", error=e) if logger else None
        return None

    def _apply_slot_themes(self, main_window: QMainWindow) -> None:
        """Apply theme to color slots."""
        try:
            if hasattr(main_window, 'slots'):
                for slot in main_window.slots:
                    if hasattr(slot, 'set_theme'):
                        is_dark = self.theme_manager.current_theme == 'dark'
                        slot.set_theme(is_dark, main_window.ui_handler if hasattr(main_window, 'ui_handler') else None)
        except Exception as e:
            logger.error(f"Error applying slot themes: {e}")

    def cycle_theme(self, main_window: QMainWindow) -> str:
        """Cycle through available themes and apply."""
        try:
            new_theme = self.theme_manager.cycle_theme()
            # Clear cache so new theme's Highlight colors are rebuilt
            self.theme_manager.clear_palette_cache()
            self.apply_theme(main_window)
            return self.theme_manager.get_theme_display_name()
        except Exception as e:
            logger.error(f"Error cycling theme: {e}")
            return "Error"

    def is_dark_mode(self) -> bool:
        """Check if dark mode is currently active."""
        return self.theme_manager.current_theme == 'dark'

    def is_image_mode(self) -> bool:
        """Check if image mode is active."""
        return self.theme_manager.is_image_mode()

    def get_current_theme_name(self) -> str:
        """Get display name of current theme."""
        return self.theme_manager.get_theme_display_name()

    def get_current_theme_dict(self) -> dict | None:
        """Get current theme dictionary."""
        return self.theme_manager.get_current_theme()

    def set_window_style(self, window: QWidget) -> None:
        """Set window-specific styling."""
        try:
            theme = self.theme_manager.get_current_theme()
            if theme:
                stylesheet = f"""
                    QDialog, QWidget {{
                        background-color: {theme['window_bg']};
                        color: {theme['text_color']};
                        font-family: "{config.FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
                    }}
                    QPushButton {{
                        background-color: {theme['button_bg']};
                        color: {theme['button_text']};
                        border: 1px solid {theme['border_color']};
                        padding: 2px 2px;
                        border-radius: 4px;
                        font-family: "{config.FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
                    }}
                    QPushButton:hover {{
                        background-color: {theme['button_hover_bg']};
                    }}
                    QLabel {{
                        color: {theme['text_color']};
                        font-family: "{config.FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
                    }}
                """
                window.setStyleSheet(stylesheet)
        except Exception as e:
            logger.error(f"Error setting window style: {e}")

    def on_resize(self, main_window: QMainWindow) -> None:
        """Handle window resize for image mode background scaling with debouncing."""
        try:
            if self.theme_manager.is_image_mode():
                # Debounce background scaling - only rescale after 150ms of no resize events
                self._resize_pending_window = main_window
                self._resize_debounce_timer.stop()
                self._resize_debounce_timer.timeout.disconnect()
                self._resize_debounce_timer.timeout.connect(self._debounced_resize)
                self._resize_debounce_timer.start(150)  # 150ms delay
        except Exception as e:
            logger.error(f"Error handling resize: {e}")
    
    def _debounced_resize(self) -> None:
        """Debounced background resize - called after window stops resizing."""
        try:
            main_window = self._resize_pending_window
            if not main_window:
                return
            
            if self.theme_manager.is_image_mode():
                # Update background label
                bg_image = self._background_pixmap
                if bg_image and not bg_image.isNull() and hasattr(main_window, "background_label"):
                    from PyQt6.QtCore import Qt
                    scaled_bg = bg_image.scaled(
                        main_window.central_widget.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    main_window.background_label.setPixmap(scaled_bg)
        except Exception as e:
            logger.error(f"Error in debounced resize: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
        Stops the timer and disconnects signals.
        """
        try:
            if hasattr(self, '_resize_debounce_timer') and self._resize_debounce_timer:
                self._resize_debounce_timer.stop()
                try:
                    self._resize_debounce_timer.timeout.disconnect()
                except Exception:
                    pass  # May not be connected
                if logger:
                    logger.debug("UIHandler resize timer stopped")
            
            # Clear background pixmap
            self._background_pixmap = None
            
        except Exception as e:
            if logger:
                logger.error(f"Error during UIHandler cleanup: {e}")