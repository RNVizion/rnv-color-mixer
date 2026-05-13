"""
RNV Color Mixer — Professional Desktop Color Mixing Application (PyQt6).

Main application entry point. Defines the top-level ColorMixerApp window,
custom themed tooltip widget, safe timer wrapper, and a signal-slot error
decorator. Button loading uses a cached, event-filter-driven pattern for
efficient hover/press state management in all themes including Image Mode.
"""

import sys
import os
import traceback
from types import TracebackType
from typing import Callable, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QFrame, QLabel, QPushButton, QStatusBar, QCheckBox,
    QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QPoint, pyqtSignal, QMimeData, QObject, QSize
from PyQt6.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent, QPainter, QCursor, QPen, QPainterPath, QColor, QPaintEvent, QResizeEvent, QCloseEvent
from ui.debug_overlay import DebugOverlay
from core.screen_color_picker import ScreenColorPicker

from ui.about_dialog import AboutDialog  # About page (Ctrl+/)

# Add core and ui modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ui'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

# Import logger first (before other modules)
from utils.logger import Logger, header, separator

# Create module logger
logger = Logger("ColorMixer")

from utils import config

# Print application banner FIRST (before any imports log messages)
app_info = config.get_app_info()
header(f"{app_info['name']} v{app_info['version']}")
logger.info("Loading modules...")

# ROBUST IMPORTS 
try:
    from core.color_slot import ColorSlot
    from core.image_handler import ImageHandler
    from ui.canvas_view import CanvasView
    from ui.ui_handler import UIHandler
    from utils.file_utils import FileUtils
    from utils.clipboard import ClipboardUtils
    from utils.error_handler import ErrorHandler
    logger.success("Core modules loaded")
except ImportError as e2:
    logger.critical("Cannot import required modules", error=e2)
    sys.exit(1)

# These should work with the provided files
try:
    from core.color_math import ColorMath
    from core.palette_formats import PaletteFormats
except ImportError as e:
    logger.critical("Core module import failed", error=e)
    sys.exit(1)

# Package D - Control Panel
try:
    from core.package_d_panel import PackageDPanel
    logger.success("Package D Control Panel loaded")
except ImportError as e:
    logger.warning("Package D panel not available", details=str(e))
    PackageDPanel = None

# Package D - Color History
try:
    from core.color_history import ColorHistory
    logger.success("Color History module loaded")
except ImportError as e:
    logger.warning("Color History not available", details=str(e))
    ColorHistory = None

# Package D - Preset Palettes
try:
    from core.preset_palettes import PresetPalettes
    logger.success("Preset Palettes module loaded")
except ImportError as e:
    logger.warning("Preset Palettes not available", details=str(e))
    PresetPalettes = None

# Package D - Settings Manager
try:
    from utils.settings_manager import SettingsManager
    logger.success("Settings Manager loaded")
except ImportError as e:
    logger.warning("Settings Manager not available", details=str(e))
    SettingsManager = None

# Signal Connection Manager - Prevents memory leaks from untracked signals
try:
    from utils.signal_manager import SignalConnectionManager
    logger.success("Signal Connection Manager loaded")
except ImportError as e:
    logger.warning("Signal Connection Manager not available", details=str(e))
    SignalConnectionManager = None


# Import DebugButton from debug_button.py (complete implementation with drag-off handling)
from ui.debug_button import DebugButton



# Signal handler decorator for consistent error handling
def safe_slot(status_message: str = "Operation failed") -> Callable[[Callable], Callable]:
    """Decorator for safe signal/slot handlers with consistent error handling."""
    import functools
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}", error=e)
                traceback.print_exc()
                if hasattr(self, 'status_updated'):
                    self.status_updated.emit(status_message)
        return wrapper
    return decorator


class SafeQTimer(QObject):
    """Safe timer wrapper that catches exceptions"""
    
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        
    @staticmethod
    def safe_single_shot(msec: int, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Execute function with exception handling"""
        def safe_wrapper() -> None:
            try:
                if args or kwargs:
                    func(*args, **kwargs)
                else:
                    func()
            except Exception as e:
                logger.error("Timer callback error", error=e)
                traceback.print_exc()
        
        QTimer.singleShot(msec, safe_wrapper)


class _ThemedToolTip(QLabel):
    """
    Custom tooltip that bypasses native Windows tooltip rendering.

    Native QToolTip on Windows creates an OS-level popup window with its own
    frame that cannot be styled via CSS. This class creates a frameless Qt
    widget with WA_TranslucentBackground and paints its own rounded-rect
    background, giving pixel-perfect themed tooltips in all modes.
    """

    _instance: '_ThemedToolTip | None' = None
    _OFFSET_X: int = 16
    _OFFSET_Y: int = 20
    _HIDE_DELAY_MS: int = 5000
    _MAX_WIDTH: int = 400
    _BORDER_RADIUS: int = 4

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWordWrap(True)
        self.setMaximumWidth(self._MAX_WIDTH)
        self.hide()

        # Colors for paintEvent (updated on each show) — defaults from DARK_THEME
        self._bg_color = QColor(config.ThemeManager.DARK_THEME['tooltip_bg'])
        self._border_color = QColor(config.ThemeManager.DARK_THEME['tooltip_border'])

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    @classmethod
    def instance(cls) -> '_ThemedToolTip':
        """Get or create the singleton tooltip instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint rounded-rect background and border manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw filled rounded rectangle
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                           float(rect.width()), float(rect.height()),
                           self._BORDER_RADIUS, self._BORDER_RADIUS)
        painter.fillPath(path, self._bg_color)

        # Draw border
        painter.setPen(QPen(self._border_color, 1.0))
        painter.drawPath(path)
        painter.end()

        # Let QLabel paint the text on top
        super().paintEvent(event)

    def show_tip(self, global_pos: QPoint, text: str,
                 colors: dict, font_family: str) -> None:
        """Show themed tooltip at the given global position."""
        # Store colors for paintEvent — fallback to DARK_THEME if key missing
        self._bg_color = QColor(colors.get('tooltip_bg', config.ThemeManager.DARK_THEME['tooltip_bg']))
        self._border_color = QColor(colors.get('tooltip_border', config.ThemeManager.DARK_THEME['tooltip_border']))

        # Keep original tooltip text (no case transformation)
        self.setText(text)

        # Stylesheet for text only (background/border painted in paintEvent)
        text_color = colors.get('text_color', config.ThemeManager.DARK_THEME['text_color'])
        self.setStyleSheet(
            f"color: {text_color};"
            f"padding: 4px 8px;"
            f"font-family: '{font_family}';"
            f"background: transparent;"
        )
        self.adjustSize()

        # Position below-right of cursor
        x = global_pos.x() + self._OFFSET_X
        y = global_pos.y() + self._OFFSET_Y

        # Keep tooltip on screen
        screen = QApplication.screenAt(global_pos)
        if screen:
            rect = screen.availableGeometry()
            if x + self.width() > rect.right():
                x = global_pos.x() - self.width() - 4
            if y + self.height() > rect.bottom():
                y = global_pos.y() - self.height() - 4

        self.move(x, y)
        self.show()
        self._hide_timer.start(self._HIDE_DELAY_MS)

    def hide_tip(self) -> None:
        """Hide the tooltip and cancel auto-hide timer."""
        self._hide_timer.stop()
        self.hide()


class ColorMixerApp(QMainWindow):
    """Main Color Mixer Application with Icon Builder pattern for button loading."""
    
    # Custom signals
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Install global exception handler
        sys.excepthook = self.handle_exception
        
        app_info = config.get_app_info()
        self.setWindowTitle(f"{app_info['name']} v{app_info['version']}")
        self.setMinimumSize(1130, 610)  # Increased from 580 to 610 for HSV label
        self.resize(1130, 610)          # Set default startup size
        
        # Load and set application icon
        self._load_app_icon()
        
        try:
            # Ensure required directories exist
            config.ensure_directories()
            
            # Initialize UI handler with new ThemeManager
            self.ui_handler = UIHandler()
            
            # Initialize Settings Manager
            if SettingsManager:
                self.settings_manager = SettingsManager()
                self.settings_manager.load_settings()
                logger.success("Settings Manager initialized and loaded")
                
                # Restore window size/position from settings
                remember_size = self.settings_manager.get('window.remember_size', True)
                if remember_size:
                    saved_width = self.settings_manager.get('window.main_width', 1130)
                    saved_height = self.settings_manager.get('window.main_height', 610)
                    self.resize(saved_width, saved_height)
                    logger.success(f"Restored window size: {saved_width}x{saved_height}")
                
                remember_position = self.settings_manager.get('window.remember_position', False)
                if remember_position:
                    saved_x = self.settings_manager.get('window.main_x', None)
                    saved_y = self.settings_manager.get('window.main_y', None)
                    if saved_x is not None and saved_y is not None:
                        self.move(saved_x, saved_y)
                        logger.success(f"Restored window position: ({saved_x}, {saved_y})")
            else:
                self.settings_manager = None
                logger.warning("Settings Manager not available")
            
            # Initialize core components
            self.image_handler = ImageHandler()
            self.palette_formats = PaletteFormats()
            self.file_utils = FileUtils(self)
            self.clipboard_utils = ClipboardUtils()
            
            # Package D - Color History
            if ColorHistory:
                self.color_history = ColorHistory(max_entries=20)
                logger.success(f"Color History initialized", details=f"{len(self.color_history.get_entries())} entries loaded")
            else:
                self.color_history = None
                logger.warning("Color History not available")
            
            # Package D - Preset Palettes
            if PresetPalettes:
                self.preset_palettes = PresetPalettes()
                logger.success("Preset Palettes initialized", details=f"{len(self.preset_palettes.get_all_presets())} presets available")
            else:
                self.preset_palettes = None
                logger.warning("Preset Palettes not available")
            
            # === SESSION MANAGER WITH AUTO-SAVE ===
            from utils.session_manager import SessionManager
            self.session_manager = SessionManager()
            # === END SESSION MANAGER ===
            
            # === SIGNAL CONNECTION MANAGER ===
            if SignalConnectionManager:
                self.signal_manager = SignalConnectionManager()
                logger.success("Signal Connection Manager initialized")
            else:
                self.signal_manager = None
            # === END SIGNAL CONNECTION MANAGER ===
            
            # Color slots
            self.slots: list[ColorSlot] = []
            
            # Buttons list
            self.buttons = []
            
            # UI components
            self.central_widget: QWidget | None = None
            self.button_bar: QWidget | None = None
            self.content_splitter: QSplitter | None = None
            self.slots_scroll_area: QScrollArea | None = None
            self.slots_container: QWidget | None = None
            self.slots_layout = None
            self.preview_widget: QWidget | None = None
            self.preview_label: QLabel | None = None
            self.preview_container: QWidget | None = None  # Container for preview + labels
            self.canvas_view: CanvasView | None = None
            self.hex_label: QLabel | None = None
            self.rgb_label: QLabel | None = None
            self.pixel_info_label: QLabel | None = None
            self.zoom_label: QLabel | None = None
            self.theme_button: QPushButton | None = None

            # State
            self.current_mixed_color = config.INITIAL_COLOR_TUPLE
            self.current_hex = config.INITIAL_COLOR_HEX
            self.current_rgb = config.INITIAL_COLOR_RGB
            
            # Debouncing timer for color mixing (prevents excessive calculations during slider drag)
            self._mix_debounce_timer = QTimer(self)
            self._mix_debounce_timer.setSingleShot(True)
            self._mix_debounce_timer.timeout.connect(self._debounced_mix_colors)
            
            # Color mix cache for performance
            self._color_cache = {}
            self._cache_max_size = 100
            
            # Connect signals safely
            try:
                self.status_updated.connect(self.update_status_bar)
            except Exception as e:
                logger.error("Signal connection error", error=e)
            
            # Build UI and initialize
            logger.info("Building UI...")
            self._safe_build_ui()
            logger.info("Initializing components...")
            self._safe_initialize_components()
            logger.info("Setting up keyboard shortcuts...")
            self._setup_keyboard_shortcuts()
            # Font is applied once at app level in main() - no need for redundant calls
            SafeQTimer.safe_single_shot(100, self._force_initial_theme_update)
            # Apply initial preview visibility based on settings
            SafeQTimer.safe_single_shot(150, lambda: self._update_preview(self.current_mixed_color))


            # Debug overlays for panels (optional - toggle with F12)
            # Initialize as None - will be created by settings if enabled
            self.debug_overlay_main = None
            self.debug_overlay_slots = None
            
            # Tooltip storage for F11 toggle feature
            self._stored_tooltips = {}
            
            # MASTER TOOLTIP DEFINITIONS - Source of truth for all tooltips
            # Used by tooltip toggle to reliably restore tooltips
            self._tooltip_definitions = {
                # Main button bar tooltips
                "Add Color Slot": "Add a new color slot (Ctrl+N)",
                "Upload Image": "Load an image to sample colors (Ctrl+O)",
                "Copy Hex Color": "Copy the mixed color as hex (Ctrl+C)",
                "Save Color Swatch": "Save the mixed color as an image (Ctrl+S)",
                "Export Palette": "Export the color palette to a file",
                "Import Palette": "Import a color palette from a file",
                "Save Instruction": "Save mixing instructions as an image",
                "Reset Canvas": "Clear the image canvas",
                "Reset Zoom": "Reset image zoom to fit window",
                # Theme button
                "Theme": "Switch between Dark Mode, Light Mode, and Image Mode",
                # Settings gear button
                "Settings": "Settings & Features (Ctrl+, or Ctrl+P)",
                # Color slot remove button
                "Remove": "Remove this color slot",
            }
            
            # Enable drag and drop
            self.setAcceptDrops(True)
            
            # === AUTO-SAVE AND CRASH RECOVERY ===
            # Start auto-save timer
            if hasattr(self, 'session_manager') and self.session_manager:
                self.session_manager.start_autosave(self)
                
                # Check for crash recovery
                SafeQTimer.safe_single_shot(500, self._check_crash_recovery)
            # === END AUTO-SAVE ===
            
            logger.success("ColorMixerApp initialization completed successfully")
            
            # Install application-level event filter for custom themed tooltips
            # (bypasses native Windows tooltip rendering that ignores CSS border-radius)
            QApplication.instance().installEventFilter(self)
            
        except Exception as e:
            logger.critical("Initialization failed", error=e)
            traceback.print_exc()
            QMessageBox.critical(None, "Initialization Error", 
                               f"Failed to initialize application:\n{str(e)}")
            sys.exit(1)


    # ===== AUTO-SAVE SUPPORT METHODS =====
    
    def _check_crash_recovery(self) -> None:
        """Check for autosave from previous crash on startup."""
        try:
            if not hasattr(self, 'session_manager') or not self.session_manager:
                return
            
            autosave_path = self.session_manager.check_for_autosave()
            if autosave_path:
                reply = QMessageBox.question(
                    self,
                    "Recover Previous Session?",
                    "It looks like the application didn't close properly last time.\n\n"
                    "Would you like to recover your previous session?\n\n"
                    "(Your color palette will be restored)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Load the autosave session
                    self._load_session_file(autosave_path)
                    self.status_updated.emit("Previous session recovered!")
                
                # Delete autosave either way
                self.session_manager.delete_autosave()
                
        except Exception as e:
            logger.error("Error checking crash recovery", error=e)
    
    def get_current_state(self) -> dict:
        """
        Get current app state for auto-save.
        
        Returns:
            Dictionary containing slots data, mixed color, and settings
        """
        try:
            slots_data = []
            for slot in self.slots:
                slot_info = {
                    'color': list(slot.get_color()) if slot.get_color() else [200, 200, 200],
                    'weight': slot.get_weight(),
                    'label': getattr(slot, 'label_text', f"Color {len(slots_data)+1}")
                }
                slots_data.append(slot_info)
            
            # Get current theme name safely
            current_theme_name = 'Dark'  # Default
            if hasattr(self, 'ui_handler') and self.ui_handler:
                try:
                    theme = self.ui_handler.theme_manager.get_current_theme()
                    current_theme_name = theme.get('name', 'Dark')
                except Exception:
                    pass
            
            return {
                'slots': slots_data,
                'mixed_color': self.current_mixed_color,
                'settings': {
                    'current_theme': current_theme_name
                }
            }
        except Exception as e:
            logger.error("Error getting current state", error=e)
            return {'slots': [], 'mixed_color': None, 'settings': {}}
    
    def _load_session_file(self, filepath: str) -> bool:
        """
        Load a session from file path (used by crash recovery).
        
        Args:
            filepath: Path to session file
            
        Returns:
            True if successful
        """
        try:
            session_data = self.session_manager.load_session(filepath)
            if not session_data:
                return False
            
            # Restore slots
            slots_data = session_data.get('slots', [])
            for i, slot_info in enumerate(slots_data):
                if i < len(self.slots):
                    color = tuple(slot_info.get('color', [200, 200, 200]))
                    weight = slot_info.get('weight', 0)
                    self.slots[i].set_color(color)
                    self.slots[i].set_weight(weight)
            
            # Update mixed color
            self.auto_mix_colors()
            
            return True
            
        except Exception as e:
            logger.error("Error loading session file", error=e)
            return False
    
    # ===== END AUTO-SAVE SUPPORT =====

    def handle_exception(self, exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None) -> None:
        """Global exception handler to prevent crashes"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        error_msg = f"Uncaught exception: {exc_type.__name__}: {exc_value}"
        logger.error(error_msg)
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        
        try:
            QMessageBox.critical(self, "Application Error", 
                               f"An error occurred:\n{error_msg}\n\nCheck console for details.")
        except Exception:
            logger.warning("Could not show error dialog")

    def _load_app_icon(self) -> None:
        """Load and set the application icon."""
        def load_icon() -> None:
            icon_path = os.path.join(config.BASE_DIR, "resources", "icons", "icon.png")
            
            if os.path.exists(icon_path):
                from PyQt6.QtGui import QIcon
                app_icon = QIcon(icon_path)
                self.setWindowIcon(app_icon)
                
                # Also set for the application (for taskbar)
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(app_icon)
                
                logger.success(f"Loaded application icon from: {icon_path}")
            else:
                logger.warning(f"Application icon not found at: {icon_path}")
        
        ErrorHandler.safe_execute(load_icon, "loading application icon", print)

    def _safe_build_ui(self) -> None:
        """Build UI with exception handling"""
        ErrorHandler.safe_execute(lambda: self._build_ui(), "building UI", print, reraise=True)

    def _safe_initialize_components(self) -> None:
        """Initialize components with exception handling"""
        ErrorHandler.safe_execute(lambda: self._initialize_components(), "initializing components", print)

    def _force_initial_theme_update(self) -> None:
        """Force theme update after UI is fully constructed."""
        ErrorHandler.safe_execute(
            lambda: self.ui_handler.apply_theme(self),
            "forcing initial theme update",
            print
        )


    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common actions."""
        def setup_shortcuts() -> None:
            from PyQt6.QtGui import QShortcut, QKeySequence
            
            # Ctrl+O - Open Image
            shortcut_open = QShortcut(QKeySequence.StandardKey.Open, self)
            shortcut_open.activated.connect(self.safe_upload_image)
            
            # Ctrl+S - Save Color Swatch
            shortcut_save = QShortcut(QKeySequence.StandardKey.Save, self)
            shortcut_save.activated.connect(self.safe_save_color_swatch)
            
            # Ctrl+C - Copy Hex Color
            shortcut_copy = QShortcut(QKeySequence.StandardKey.Copy, self)
            shortcut_copy.activated.connect(self.safe_copy_hex_color)
            
            # Ctrl+N - Add Color Slot
            shortcut_new = QShortcut(QKeySequence.StandardKey.New, self)
            shortcut_new.activated.connect(self.safe_add_color_slot)
            
            # Ctrl+, - Open Package D Panel (Settings & Features)
            shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
            shortcut_settings.activated.connect(self.open_package_d_panel)
            
            # Ctrl+P - Alternative shortcut for Package D Panel
            shortcut_panel = QShortcut(QKeySequence("Ctrl+P"), self)
            shortcut_panel.activated.connect(self.open_package_d_panel)
            
            # F11 - Toggle Tooltips
            shortcut_tooltips = QShortcut(Qt.Key.Key_F11, self)
            shortcut_tooltips.activated.connect(self.toggle_tooltips)
            
            # F12 - Toggle Debug Overlays
            shortcut_debug = QShortcut(Qt.Key.Key_F12, self)
            shortcut_debug.activated.connect(self.toggle_debug_overlays)
            
            # Ctrl+Shift+C - Screen Color Picker
            shortcut_screen_picker = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
            shortcut_screen_picker.activated.connect(self.launch_screen_color_picker)
            
            # Ctrl+/ - About Dialog
            shortcut_about = QShortcut(QKeySequence("Ctrl+/"), self)
            shortcut_about.activated.connect(self.open_about_dialog)
            
            logger.success("Keyboard shortcuts initialized")
            logger.indent("Ctrl+O - Upload Image")
            logger.indent("Ctrl+S - Save Color Swatch")
            logger.indent("Ctrl+C - Copy Hex Color")
            logger.indent("Ctrl+N - Add Color Slot")
            logger.indent("Ctrl+Shift+C - Screen Color Picker")
            logger.indent("Ctrl+, or Ctrl+P - Settings & Features")
            logger.indent("Ctrl+/ - About Dialog")
            logger.indent("F11 - Toggle Tooltips")
            logger.indent("F12 - Toggle Debug Overlays")
        
        ErrorHandler.safe_execute(setup_shortcuts, "setting up keyboard shortcuts", print)

    def _build_ui(self) -> None:
        """Build the main user interface."""
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Background label for Image Mode (positioned behind everything)
        self.background_label = QLabel(self.central_widget)
        self.background_label.setScaledContents(True)
        self.background_label.lower()  # Send to back
        self.background_label.hide()  # Hidden by default
        
        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # Build UI sections
        self._build_button_bar(main_layout)
        self._build_content_area(main_layout)
        self._build_status_bar()
        # Font is applied once at app level in main() - removed redundant call

    def _build_button_bar(self, parent_layout: QVBoxLayout) -> None:
        """Build the top button bar with Icon Builder pattern."""
        self.button_bar = QFrame()
        button_layout = QHBoxLayout(self.button_bar)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
    
        # Button definitions (text, callback)
    
        # Button tooltips with keyboard shortcuts
        button_tooltips = {
            "Add Color Slot": "Add a new color slot (Ctrl+N)",
            "Upload Image": "Load an image to sample colors (Ctrl+O)",
            "Copy Hex Color": "Copy the mixed color as hex (Ctrl+C)",
            "Save Color Swatch": "Save the mixed color as an image (Ctrl+S)",
            "Export Palette": "Export the color palette to a file",
            "Import Palette": "Import a color palette from a file",
            "Save Instruction": "Save mixing instructions as an image",
            "Reset Canvas": "Clear the image canvas",
            "Reset Zoom": "Reset image zoom to fit window",
        }
        button_defs = [
            ("Add Color Slot", self.safe_add_color_slot),
            ("Upload Image", self.safe_upload_image),
            ("Copy Hex Color", self.safe_copy_hex_color),
            ("Save Color Swatch", self.safe_save_color_swatch),
            ("Export Palette", self.safe_export_palette),
            ("Import Palette", self.safe_import_palette),
            ("Save Instruction", self.safe_save_instruction_image),
            ("Reset Canvas", self.safe_reset_canvas),
            ("Reset Zoom", self.safe_reset_zoom)
        ]
    
        # Create action buttons - FIXED at 110x40
        for text, command in button_defs:
            # Convert button text to file name pattern: "Add Color Slot" -> "add-color-slot"
            file_name = text.lower().replace(' ', '-')
        
            # Load button images (base, hover, pressed)
            base_path = os.path.join(config.BUTTON_IMAGES_DIR, f"{file_name}_base.png")
            hover_path = os.path.join(config.BUTTON_IMAGES_DIR, f"{file_name}_hover.png")
            pressed_path = os.path.join(config.BUTTON_IMAGES_DIR, f"{file_name}_pressed.png")
        
            # Create button with images if they exist
            if os.path.exists(base_path):
                btn = DebugButton(
                    text=text,
                    base_img=base_path,
                    hover_img=hover_path if os.path.exists(hover_path) else base_path,
                    pressed_img=pressed_path if os.path.exists(pressed_path) else base_path
                )
                logger.debug(f"Loaded button images: {text}")
            else:
                btn = DebugButton(text=text)
                logger.warning(f"Button images not found for: {text}")
            
            btn.setFixedSize(110, 40)  # Action buttons: 110px wide, 40px tall
            btn.clicked.connect(command)
            btn.set_theme_manager(self.ui_handler.theme_manager)
            
            # Store button name as property
            btn.setProperty("button_name", text)
            
            # Set tooltip if available
            if text in button_tooltips:
                btn.setToolTip(button_tooltips[text])
        
            button_layout.addWidget(btn)
            self.buttons.append(btn)
    
        button_layout.addStretch()
    
        # Theme button - FIXED at 105x55 (wider to fit text)
        self.theme_button = QPushButton(self.ui_handler.get_current_theme_name())
        self.theme_button.setFixedSize(105, 55)  # Theme button: 105px wide, 55px tall
        self.theme_button.setProperty("button_name", "Theme")  # For tooltip restoration
        self.theme_button.setToolTip("Switch between Dark Mode, Light Mode, and Image Mode")
        self.theme_button.clicked.connect(self._on_theme_button_clicked)
        button_layout.addWidget(self.theme_button)
    
        parent_layout.addWidget(self.button_bar)

    def _on_theme_button_clicked(self) -> None:
        """Handle theme button click to cycle through themes."""
        def cycle_theme() -> None:
            new_theme_name = self.ui_handler.cycle_theme(self)
            self.theme_button.setText(new_theme_name)
            self.status_updated.emit(f"Theme: {new_theme_name}")
            
            # Apply theme to buttons using cached images (Icon Builder pattern)
            self._apply_theme_to_buttons()
            
            # Apply theme to other components
            self._apply_theme_to_all()
            
            # Apply theme to Package D panel if it exists
            if hasattr(self, '_package_d_panel') and self._package_d_panel is not None:
                # Use dark styling for both Dark Mode AND Image Mode
                is_dark = self.ui_handler.is_dark_mode() or self.ui_handler.is_image_mode()
                self._package_d_panel.set_theme(is_dark)
                logger.debug(f"Theme applied to Package D panel (dark={is_dark})")
        
        ErrorHandler.safe_execute(cycle_theme, "cycling theme", print)

    def _apply_theme_to_buttons(self) -> None:
        """Apply theme to buttons - DebugButton handles Image Mode automatically."""
        def apply_theme() -> None:
            is_image_mode = self.ui_handler.is_image_mode()
            # Always use standard button size (110x40)
            from PyQt6.QtCore import QSize
            button_width, button_height = 110, 40
            icon_size = QSize(110, 40)
            
            for btn in self.buttons:
                if not isinstance(btn, DebugButton):
                    continue
                    
                btn_name = btn.property("button_name")
                
                # CRITICAL: Set button physical size FIRST (regardless of theme/mode)
                btn.setFixedSize(button_width, button_height)
                
                if is_image_mode:
                    # Image Mode - hide text and set base icon explicitly
                    if btn.text() != "":
                        btn.setText("")
                    
                    # Set the base icon from the button's stored image path
                    if hasattr(btn, 'base_img') and btn.base_img and os.path.exists(btn.base_img):
                        from PyQt6.QtGui import QIcon
                        btn.setIcon(QIcon(btn.base_img))
                        # Set icon size to match button
                        btn.setIconSize(icon_size)
                        logger.debug(f"Set icon for {btn_name}")
                else:
                    # Dark/Light Mode - ALWAYS restore text and remove icons (regardless of current state)
                    if btn_name:
                        btn.setText(btn_name)  # Always set text, even if it already has text
                    from PyQt6.QtGui import QIcon
                    btn.setIcon(QIcon())  # Always clear icon
                    # Still set icon size to maintain consistency (even though no icon)
                    btn.setIconSize(icon_size)
                
                btn.update()
                btn.repaint()  # Force immediate repaint
        
        ErrorHandler.safe_execute(apply_theme, "applying theme to buttons", print)

    def _apply_theme_to_all(self) -> None:
        """Apply theme to all UI components."""
        def apply_theme() -> None:
            is_dark = self.ui_handler.is_dark_mode()
            
            if self.canvas_view:
                self.canvas_view.set_theme(is_dark, self.ui_handler)
            
            for slot in self.slots:
                if hasattr(slot, 'set_theme'):
                    slot.set_theme(is_dark, self.ui_handler)
        
        ErrorHandler.safe_execute(apply_theme, "applying theme to components", print)

    def _build_content_area(self, parent_layout: QVBoxLayout) -> None:
        """Build the main content area."""
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Color slots
        self._build_slots_area()
        self.content_splitter.addWidget(self.slots_scroll_area)
        
        # Right side: Preview and image
        right_widget = QWidget()
        right_widget.setAutoFillBackground(False)  # Ensure transparency
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(8)  # Increased spacing between preview and image sections
        
        self._build_preview_section(right_layout)
        self._build_image_section(right_layout)
        
        self.content_splitter.addWidget(right_widget)
        self.content_splitter.setStretchFactor(0, 0)
        self.content_splitter.setStretchFactor(1, 1)
        self.content_splitter.setSizes([config.SLOTS_MIN_WIDTH, config.DEFAULT_WINDOW_SIZE[0] - config.SLOTS_MIN_WIDTH])  # Slots at minimum, right gets remainder
        
        try:
            self.content_splitter.splitterMoved.connect(self._safe_on_splitter_moved)
        except Exception as e:
            logger.error("Error connecting splitter signal", error=e)
        
        parent_layout.addWidget(self.content_splitter, 1)

    def _build_slots_area(self) -> None:
        #Build the scrollable color slots area
        self.slots_scroll_area = QScrollArea()
        self.slots_scroll_area.setWidgetResizable(True)
        self.slots_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.slots_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.slots_scroll_area.setMinimumWidth(config.SLOTS_MIN_WIDTH)
        self.slots_scroll_area.setMaximumWidth(config.SLOTS_MAX_WIDTH)
        self.slots_scroll_area.setMinimumHeight(config.SLOTS_MIN_HEIGHT)
        
        
        # CRITICAL: Disable auto-fill background for transparency
        self.slots_scroll_area.setAutoFillBackground(False)
        self.slots_scroll_area.viewport().setAutoFillBackground(False)
        self.slots_container = QWidget()
        # CRITICAL: Disable auto-fill background on container for transparency
        self.slots_container.setAutoFillBackground(False)
        
        
        self.slots_layout = QVBoxLayout(self.slots_container)
        self.slots_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.slots_layout.setContentsMargins(5, 5, 5, 5)
        self.slots_layout.setSpacing(2)
        
        from PyQt6.QtWidgets import QSizePolicy
        self.slots_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.slots_scroll_area.setWidget(self.slots_container)

    def _build_preview_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the color preview section."""
        # Title with gear icon
        title_container = QWidget()
        title_container.setAutoFillBackground(False)  # Ensure transparency
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_label = QLabel("Mixed Color Preview:")
        title_label.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['medium']}px; background-color: transparent;")
        title_label.setAutoFillBackground(False)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Gear icon button (Package D control panel) - uses images in ALL modes
        settings_base = os.path.join(config.BUTTON_IMAGES_DIR, "settings_gear_base.png")
        settings_hover = os.path.join(config.BUTTON_IMAGES_DIR, "settings_gear_hover.png")
        settings_pressed = os.path.join(config.BUTTON_IMAGES_DIR, "settings_gear_pressed.png")
        
        self.package_d_button = DebugButton(
            text="",  # No text, image only
            base_img=settings_base if os.path.exists(settings_base) else None,
            hover_img=settings_hover if os.path.exists(settings_hover) else None,
            pressed_img=settings_pressed if os.path.exists(settings_pressed) else None,
            always_show_images=True  # Show images in ALL modes (Dark, Light, Image)
        )
        self.package_d_button.setFixedSize(50, 50)  # Large, prominent settings button
        self.package_d_button.setProperty("button_name", "Settings")  # For tooltip restoration
        self.package_d_button.setToolTip("Settings & Features (Ctrl+, or Ctrl+P)")
        self.package_d_button.setStyleSheet("background-color: transparent; border: none; padding: 0px;")
        self.package_d_button.set_theme_manager(self.ui_handler.theme_manager)
        self.package_d_button.clicked.connect(self.open_package_d_panel)
        title_layout.addWidget(self.package_d_button)
        
        # Title container has fixed height (gear button height)
        title_container.setFixedHeight(50)
        parent_layout.addWidget(title_container, 0)  # Stretch factor 0
        
        preview_container = QWidget()
        preview_container.setAutoFillBackground(False)  # Ensure transparency
        self.preview_container = preview_container  # Store reference for resize updates
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.setContentsMargins(10, 10, 10, 15)  # Increased bottom margin for HSV
        
        # Color preview square
        square_container = QWidget()
        square_container.setAutoFillBackground(False)  # Ensure transparency
        square_layout = QHBoxLayout(square_container)
        square_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        square_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel()
        initial_size = self._calculate_preview_size()
        self.preview_label.setFixedSize(initial_size, initial_size)
        self.preview_label.setStyleSheet(f"border: 2px solid {config.ThemeManager.DARK_THEME['border_color']}; background-color: {config.INITIAL_COLOR_HEX}; border-radius: 8px;")
        
        from PyQt6.QtWidgets import QSizePolicy
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        square_layout.addWidget(self.preview_label)
        preview_layout.addWidget(square_container)
        
        # Color value labels
        values_container = QWidget()
        values_container.setAutoFillBackground(False)  # Ensure transparency
        values_layout = QVBoxLayout(values_container)
        values_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        values_layout.setContentsMargins(0, 10, 0, 5)  # Added 5px bottom margin
        values_layout.setSpacing(5)
        
        self.hex_label = QLabel(config.INITIAL_COLOR_HEX)
        self.hex_label.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['large']}px; background-color: transparent;")
        self.hex_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hex_label.setMinimumHeight(25)  # Prevent compression
        self.hex_label.setAutoFillBackground(False)
        values_layout.addWidget(self.hex_label)
        
        self.rgb_label = QLabel(config.INITIAL_COLOR_RGB)
        self.rgb_label.setStyleSheet(f"font-size: {config.FONT_SIZES['medium']}px; background-color: transparent;")
        self.rgb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rgb_label.setMinimumHeight(20)  # Prevent compression
        self.rgb_label.setAutoFillBackground(False)
        values_layout.addWidget(self.rgb_label)
        
        # HSV label
        self.hsv_label = QLabel("hsv(0°, 0%, 0%)")
        self.hsv_label.setStyleSheet(f"font-size: {config.FONT_SIZES['small']}px; background-color: transparent;")
        self.hsv_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hsv_label.setMinimumHeight(18)  # Prevent compression
        self.hsv_label.setAutoFillBackground(False)  # Ensure no background fill
        values_layout.addWidget(self.hsv_label)
        
        # Set fixed minimum height on values container (hex + rgb + hsv + margins + spacing)
        values_container.setMinimumHeight(25 + 20 + 18 + 10 + 10)  # ~83px minimum
        values_container.setMaximumHeight(100)  # Prevent excessive growth
        preview_layout.addWidget(values_container)
        
        # Container height = preview square + margins + hex label + rgb label + hsv label + spacing + border
        # initial_size + 10 (top margin) + 15 (bottom margin) + 25 (hex) + 20 (rgb) + 18 (hsv) + 15 (spacing) + 4 (border) = ~117
        container_height = initial_size + 125  # Increased buffer for HSV label visibility
        
        # Use minimum height instead of fixed height to allow container to grow if needed
        # This prevents HSV label from being clipped in Dark/Light modes
        preview_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        preview_container.setMinimumHeight(container_height)
        preview_container.setMaximumHeight(container_height + 50)  # Allow some growth but not excessive
        
        # Add with stretch factor 0 (won't grow/shrink)
        parent_layout.addWidget(preview_container, 0)

    def _build_image_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the image display section."""
        image_label = QLabel("Image (drag to sample / double-click to pick):")
        image_label.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['medium']}px; background-color: transparent;")
        image_label.setMinimumHeight(20)  # Ensure label doesn't shrink
        image_label.setMaximumHeight(25)  # Prevent excessive growth
        image_label.setAutoFillBackground(False)  # Ensure no background fill
        parent_layout.addWidget(image_label, 0)  # Stretch factor 0 - won't grow
        
        try:
            self.canvas_view = CanvasView(self.image_handler)
            self.canvas_view.setMinimumSize(400, 200)
            
            from PyQt6.QtWidgets import QSizePolicy
            self.canvas_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Connect canvas signals safely with SignalConnectionManager
            try:
                if self.signal_manager:
                    self.signal_manager.connect(self.canvas_view, self.canvas_view.pixel_hovered, self._safe_on_pixel_hover, track_as="canvas_pixel_hovered")
                    self.signal_manager.connect(self.canvas_view, self.canvas_view.pixel_sampled, self._safe_on_pixel_sample, track_as="canvas_pixel_sampled")
                    self.signal_manager.connect(self.canvas_view, self.canvas_view.region_sampled, self._safe_on_region_sample, track_as="canvas_region_sampled")
                    self.signal_manager.connect(self.canvas_view, self.canvas_view.zoom_changed, self._safe_on_zoom_change, track_as="canvas_zoom_changed")
                else:
                    self.canvas_view.pixel_hovered.connect(self._safe_on_pixel_hover)
                    self.canvas_view.pixel_sampled.connect(self._safe_on_pixel_sample)
                    self.canvas_view.region_sampled.connect(self._safe_on_region_sample)
                    self.canvas_view.zoom_changed.connect(self._safe_on_zoom_change)
            except Exception as e:
                logger.error("Error connecting canvas signals", error=e)
            
            parent_layout.addWidget(self.canvas_view, 3)
            
        except Exception as e:
            logger.error("Error creating canvas view", error=e)
            placeholder = QLabel("Canvas view failed to initialize")
            placeholder.setMinimumSize(400, 200)
            placeholder.setStyleSheet("background-color: #ffcccc; border: 2px solid red;")
            parent_layout.addWidget(placeholder, 3)

    def _build_status_bar(self) -> None:
        """Build the status bar."""
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")
        
        self.pixel_info_label = QLabel("Pixel: -")
        self.pixel_info_label.setMinimumWidth(200)
        status_bar.addPermanentWidget(self.pixel_info_label)
        
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setMinimumWidth(100)
        status_bar.addPermanentWidget(self.zoom_label)

    def _initialize_components(self) -> None:
        """Initialize components safely."""
        try:
            self.ui_handler.initialize_theme(self, self.status_updated.emit)
            
            # Apply settings from settings manager FIRST so default weight is available
            #
            if self.settings_manager:
                logger.info("Loading saved settings...")
                self._apply_all_settings()
                logger.success("Settings loaded on startup")
            
            # Add initial slots (will use default weight from settings)
            logger.info("Adding initial color slots...")
            for i in range(2):
                self.add_color_slot()
            logger.success("Initial slots added")
            
            # Apply theme to all components including newly created slots
            logger.info("Applying theme to all components...")
            self._apply_theme_to_buttons()
            self._apply_theme_to_all()
            logger.success("Initial theme application complete")
            
        except Exception as e:
            logger.error("Error in component initialization", error=e)

    def _calculate_preview_size(self) -> int:
        """Calculate preview size safely."""
        def calculate() -> None:
            if hasattr(self, 'width') and callable(self.width):
                window_width = self.width()
                window_height = self.height()
            else:
                window_width, window_height = config.DEFAULT_WINDOW_SIZE
            
            width_based = window_width * 0.18
            height_based = window_height * 0.25
            available_space = min(width_based, height_based)
            
            min_size = 120
            max_size = 300
            
            return max(min_size, min(max_size, int(available_space)))
        
        result = ErrorHandler.safe_execute(calculate, "calculating preview size", print)
        return result if result is not None else 150

    def _get_default_weight(self) -> int:
        """Get default slot weight from settings."""
        default_weight = 50  # Fallback default
        if self.settings_manager:
            default_weight = self.settings_manager.get('preferences.default_slot_weight', 50)
        return default_weight

    # Safe wrapper methods for button callbacks

    def toggle_debug_overlays(self) -> None:
        """Toggle debug overlays on/off with F12."""
        def toggle() -> None:
            # Create overlays if they don't exist
            if not hasattr(self, 'debug_overlay_main') or self.debug_overlay_main is None:
                self.debug_overlay_main = DebugOverlay(self.central_widget, "App Window", config.DEBUG_OVERLAY_COLORS['app_window'])
                self.debug_overlay_slots = DebugOverlay(self.slots_scroll_area.viewport(), "Slots Panel", config.DEBUG_OVERLAY_COLORS['slots_panel'])
                self.debug_overlay_main.show()
                self.debug_overlay_slots.show()
                self.status_updated.emit("Debug overlays enabled")
                logger.success("Debug overlays enabled")
            else:
                # Toggle visibility
                visible = self.debug_overlay_main.isVisible()
                self.debug_overlay_main.setVisible(not visible)
                self.debug_overlay_slots.setVisible(not visible)
                status = "enabled" if not visible else "disabled"
                self.status_updated.emit(f"Debug overlays {status}")
                logger.success(f"Debug overlays {status}")
        
        ErrorHandler.safe_execute(toggle, "toggling debug overlays", print)
    
    def toggle_tooltips(self) -> None:
        """Toggle tooltips on/off with F11."""
        def toggle() -> None:
            # Get current state from settings
            current_state = True
            if self.settings_manager:
                current_state = self.settings_manager.get("preferences.show_tooltips", True)
            
            # Toggle state
            new_state = not current_state
            
            # Save to settings
            if self.settings_manager:
                self.settings_manager.set("preferences.show_tooltips", new_state)
            
            # Apply the tooltip setting
            self._apply_tooltips_setting(new_state)
            
            # Update Package D panel checkbox if open
            if hasattr(self, '_package_d_panel') and self._package_d_panel:
                if hasattr(self._package_d_panel, 'tooltips_check'):
                    self._package_d_panel.tooltips_check.setChecked(new_state)
            
            status = "enabled" if new_state else "disabled"
            self.status_updated.emit(f"Tooltips {status}")
            logger.success(f"Tooltips {status} (F11)")
        
        ErrorHandler.safe_execute(toggle, "toggling tooltips", print)
    
    def _set_tooltips_recursive(self, widget: QWidget, show_tooltips: bool) -> None:
        """
        Enable/disable tooltips on all child widgets using definition-based restoration.
        
        Caches findChildren result for subsequent calls.
        """
        # Get tooltip definitions (fallback to empty dict if not yet initialized)
        tooltip_defs = getattr(self, '_tooltip_definitions', {})
        
        def process_widget(w: QWidget) -> None:
            """Process a single widget for tooltip enable/disable."""
            if not show_tooltips:
                # Clear tooltip
                w.setToolTip("")
            else:
                # Restore tooltip from definitions using button_name property
                button_name = w.property("button_name")
                if button_name and button_name in tooltip_defs:
                    w.setToolTip(tooltip_defs[button_name])
        
        # Process the main widget
        process_widget(widget)
        
        # Always do a fresh findChildren scan — no caching.
        # Caching caused newly added widgets (e.g. color slots added after
        # tooltips were disabled) to be missed on subsequent toggle calls.
        for child in widget.findChildren(QWidget):
            process_widget(child)
    
    def launch_screen_color_picker(self) -> None:
        """Launch screen color picker (Ctrl+Shift+C)"""
        def launch() -> None:
            logger.info("Launching Screen Color Picker...")
            
            # Create color picker
            self.screen_picker = ScreenColorPicker(self)
            
            # Connect signals with SignalConnectionManager
            if self.signal_manager:
                self.signal_manager.connect(self.screen_picker, self.screen_picker.color_picked, self._on_screen_color_picked, track_as="screen_picker_color_picked")
                self.signal_manager.connect(self.screen_picker, self.screen_picker.picker_cancelled, self._on_screen_picker_cancelled, track_as="screen_picker_cancelled")
            else:
                self.screen_picker.color_picked.connect(self._on_screen_color_picked)
                self.screen_picker.picker_cancelled.connect(self._on_screen_picker_cancelled)
            
            # Start picking
            self.screen_picker.start_picking()
            
            # Hide main window temporarily for cleaner screenshot
            self.setWindowOpacity(0.0)
        
        ErrorHandler.safe_execute(launch, "launching screen color picker", print)
    
    def _on_screen_color_picked(self, color: tuple) -> None:
        """Handle color picked from screen."""
        def handle_picked() -> None:
            logger.success(f"Color picked from screen: {color}")
            
            # Restore window
            self.setWindowOpacity(1.0)
            
            # Add color to a slot with default weight
            default_weight = 50
            if self.settings_manager:
                default_weight = self.settings_manager.get('preferences.default_slot_weight', 50)
            
            self.add_color_to_slot(color, default_weight)
            
            # Show status
            hex_color = ColorMath.rgb_to_hex(color)
            self.status_updated.emit(f"Picked color from screen: {hex_color}")
        
        # Always restore window opacity on error
        try:
            ErrorHandler.safe_execute(handle_picked, "handling picked color", print)
        except Exception:
            self.setWindowOpacity(1.0)
    
    def _on_screen_picker_cancelled(self) -> None:
        """Handle screen picker cancelled."""
        def handle_cancelled() -> None:
            logger.info("Screen picker cancelled")
            
            # Restore window
            self.setWindowOpacity(1.0)
            
            self.status_updated.emit("Screen picker cancelled")
        
        # Always restore window opacity on error
        try:
            ErrorHandler.safe_execute(handle_cancelled, "handling picker cancel", print)
        except Exception:
            self.setWindowOpacity(1.0)

    def open_package_d_panel(self) -> None:
        """Open the Package D control panel (Ctrl+,)"""
        def open_panel() -> None:
            if PackageDPanel is None:
                QMessageBox.warning(self, "Feature Unavailable", 
                                  "Package D Control Panel is not available.")
                return
            
            # Create or show the panel
            if not hasattr(self, '_package_d_panel') or self._package_d_panel is None:
                self._package_d_panel = PackageDPanel(
                    self, 
                    self.color_history,
                    self.preset_palettes,
                    self.settings_manager  # Pass settings manager
                )
                
                # Apply current theme (use dark styling for Dark Mode AND Image Mode)
                is_dark = self.ui_handler.is_dark_mode() or self.ui_handler.is_image_mode()
                self._package_d_panel.set_theme(is_dark)
                
                # Connect signals with SignalConnectionManager
                if self.signal_manager:
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.load_history_color, self._on_load_history_color, track_as="panel_load_history_color")
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.load_preset, self._on_load_preset, track_as="panel_load_preset")
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.save_as_preset, self._on_save_as_preset, track_as="panel_save_as_preset")
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.apply_harmony, self._on_apply_harmony, track_as="panel_apply_harmony")
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.save_session, self._on_save_session, track_as="panel_save_session")
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.load_session, self._on_load_session, track_as="panel_load_session")
                    # Quick Actions signals
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.export_current_mix, self.safe_save_color_swatch, track_as="panel_export_current_mix")
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.generate_quick_palette, self._on_generate_quick_palette, track_as="panel_generate_quick_palette")
                    self.signal_manager.connect(self._package_d_panel, self._package_d_panel.pick_screen_color, self.launch_screen_color_picker, track_as="panel_pick_screen_color")
                    # Settings signals
                    if hasattr(self._package_d_panel, 'settings_changed'):
                        self.signal_manager.connect(self._package_d_panel, self._package_d_panel.settings_changed, self._on_settings_changed, track_as="panel_settings_changed")
                        logger.debug("Settings change signal connected")
                else:
                    self._package_d_panel.load_history_color.connect(self._on_load_history_color)
                    self._package_d_panel.load_preset.connect(self._on_load_preset)
                    self._package_d_panel.save_as_preset.connect(self._on_save_as_preset)
                    self._package_d_panel.apply_harmony.connect(self._on_apply_harmony)
                    self._package_d_panel.save_session.connect(self._on_save_session)
                    self._package_d_panel.load_session.connect(self._on_load_session)
                    # Quick Actions signals
                    self._package_d_panel.export_current_mix.connect(self.safe_save_color_swatch)
                    self._package_d_panel.generate_quick_palette.connect(self._on_generate_quick_palette)
                    self._package_d_panel.pick_screen_color.connect(self.launch_screen_color_picker)
                    # Settings signals
                    if hasattr(self._package_d_panel, 'settings_changed'):
                        self._package_d_panel.settings_changed.connect(self._on_settings_changed)
                        logger.debug("Settings change signal connected")
                
                logger.success("Package D Control Panel created")
            else:
                # Refresh displays when reopening
                if hasattr(self._package_d_panel, 'refresh_history'):
                    self._package_d_panel.refresh_history()
                if hasattr(self._package_d_panel, 'refresh_presets'):
                    self._package_d_panel.refresh_presets()
                if hasattr(self._package_d_panel, '_refresh_sessions_list'):
                    self._package_d_panel._refresh_sessions_list()
            
            # Update base color options for harmony tab
            current_colors = [(s.get_color(), s.get_weight()) for s in self.slots]
            if hasattr(self._package_d_panel, 'update_base_color_options'):
                self._package_d_panel.update_base_color_options(current_colors)
            
            # Show the panel
            self._package_d_panel.show()
            self._package_d_panel.raise_()
            self._package_d_panel.activateWindow()
            
            self.status_updated.emit("Package D Control Panel opened")
        
        ErrorHandler.safe_execute(open_panel, "opening Package D panel", print)
    
    def open_about_dialog(self) -> None:
        """Open the About dialog (Ctrl+/) - Shows application information and help."""
        def open_about() -> None:
            # Create or show the about dialog
            if not hasattr(self, '_about_dialog') or self._about_dialog is None:
                self._about_dialog = AboutDialog(self, self.ui_handler)
                
                # Apply current theme (use dark styling for Dark Mode AND Image Mode)
                is_dark = self.ui_handler.is_dark_mode() or self.ui_handler.is_image_mode()
                self._about_dialog.set_theme(is_dark)
                
                logger.success("About dialog created")
            else:
                # Update theme in case it changed
                is_dark = self.ui_handler.is_dark_mode() or self.ui_handler.is_image_mode()
                self._about_dialog.set_theme(is_dark)
            
            # Show the dialog
            self._about_dialog.show()
            self._about_dialog.raise_()
            self._about_dialog.activateWindow()
            
            self.status_updated.emit("About dialog opened")
        
        ErrorHandler.safe_execute(open_about, "opening About dialog", print)
    
    def _on_load_history_color(self, color: tuple) -> None:
        """Handle loading a color from history."""
        def load_history_color() -> None:
            # Find first empty slot (weight = 0)
            empty_slot = next((s for s in self.slots if s.get_weight() == 0), None)
            
            if empty_slot is None:
                # No empty slots, add a new one
                self.add_color_slot()
                empty_slot = self.slots[-1] if self.slots else None
            
            if empty_slot:
                empty_slot.set_color(color)
                empty_slot.set_weight(self._get_default_weight())  # Use settings default
                
                hex_color = ColorMath.rgb_to_hex(color)
                logger.success(f"Loaded {hex_color} from history into slot {empty_slot.index + 1}")
        
        ErrorHandler.safe_execute(load_history_color, "loading color from history", print)
    
    def _on_load_preset(self, colors: list, preset_name: str) -> None:
        """Handle loading a preset palette."""
        def load_preset() -> None:
            logger.info(f"Loading preset: {preset_name} with {len(colors)} colors")
            
            # Clear existing slots or create new ones as needed
            slots_needed = len(colors)
            
            # Ensure we have enough slots
            while len(self.slots) < slots_needed:
                self.add_color_slot()
            
            # Load colors into slots
            for i, color in enumerate(colors):
                if i < len(self.slots):
                    self.slots[i].set_color(color)
                    self.slots[i].set_weight(self._get_default_weight())  # Use settings default
            
            self.status_updated.emit(f"Loaded preset: {preset_name} ({len(colors)} colors)")
            logger.success(f"Preset loaded: {preset_name}")
        
        ErrorHandler.safe_execute(load_preset, "loading preset", print)
    
    def _on_save_as_preset(self, name: str, description: str) -> None:
        """Handle saving current colors as a preset."""
        def save_preset() -> None:
            # Get current colors (non-zero weights only)
            colors = [slot.get_color() for slot in self.slots if slot.get_weight() > 0]
            
            if not colors:
                QMessageBox.warning(self, "No Colors", 
                    "No colors with non-zero weights to save as preset.")
                return
            
            if not self.preset_palettes:
                QMessageBox.warning(self, "Not Available", 
                    "Preset Palettes feature is not available.")
                return
            
            # Create and save preset
            preset = self.preset_palettes.create_preset_from_current_colors(
                colors=colors,
                name=name,
                description=description or f"{len(colors)} custom colors",
                category="Custom",
                icon="⭐"
            )
            
            if preset:
                QMessageBox.information(self, "Preset Saved", 
                    f"Preset '{name}' saved successfully with {len(colors)} colors!")
                
                # Refresh the presets panel if it's open
                if hasattr(self, '_package_d_panel') and self._package_d_panel:
                    self._package_d_panel.refresh_presets()
                
                self.status_updated.emit(f"Saved preset: {name}")
                logger.success(f"Preset saved: {name}", details=f"{len(colors)} colors")
            else:
                QMessageBox.warning(self, "Save Failed", 
                    "Failed to save preset. Name may already exist.")
        
        ErrorHandler.safe_execute(save_preset, "saving preset", print)
    
    def _on_apply_harmony(self, harmony_type: str, base_color: tuple) -> None:
        """Handle applying color harmony to slots."""
        def apply_harmony() -> None:
            # Import color harmony
            try:
                from core.color_harmony import ColorHarmony, HarmonyType
            except ImportError:
                QMessageBox.warning(self, "Not Available", 
                    "Color Harmony feature is not available.")
                return
            
            # Find matching HarmonyType
            harmony_type_enum = None
            for ht in HarmonyType:
                if ht.value == harmony_type:
                    harmony_type_enum = ht
                    break
            
            if not harmony_type_enum:
                QMessageBox.warning(self, "Invalid Type", 
                    f"Unknown harmony type: {harmony_type}")
                return
            
            # Generate harmony colors
            harmony_colors = ColorHarmony.generate_harmony(base_color, harmony_type_enum)
            
            if not harmony_colors:
                QMessageBox.warning(self, "Generation Failed", 
                    "Failed to generate harmony colors.")
                return
            
            # Apply colors to slots
            # Strategy: Fill from the beginning, replacing existing colors
            for i, color in enumerate(harmony_colors):
                if i >= len(self.slots):
                    # Need more slots - add them
                    self.add_color_slot()
                
                if i < len(self.slots):
                    # Set color and weight
                    self.slots[i].set_color(color)
                    self.slots[i].set_weight(self._get_default_weight())  # Use settings default
            
            # Trigger color mixing update
            self.on_slot_change()
            
            # Show success
            self.status_updated.emit(f"Applied {harmony_type} harmony ({len(harmony_colors)} colors)")
            logger.success(f"Applied {harmony_type} harmony", details=f"{len(harmony_colors)} colors")
        
        ErrorHandler.safe_execute(apply_harmony, "applying color harmony", print)
    
    def _on_generate_quick_palette(self, palette_type: str) -> None:
        """Handle quick palette generation from current mixed color."""
        def generate_palette() -> None:
            # Get current mixed color as base
            base_color = self.current_mixed_color
            
            # Import color harmony for palette generation
            try:
                from core.color_harmony import ColorHarmony, HarmonyType
            except ImportError:
                QMessageBox.warning(self, "Not Available", 
                    "Color Harmony feature is not available.")
                return
            
            # Map palette type to HarmonyType
            type_mapping = {
                'complementary': HarmonyType.COMPLEMENTARY,
                'analogous': HarmonyType.ANALOGOUS,
                'triadic': HarmonyType.TRIADIC,
                'split_complementary': HarmonyType.SPLIT_COMPLEMENTARY,
            }
            
            harmony_type = type_mapping.get(palette_type)
            if not harmony_type:
                QMessageBox.warning(self, "Invalid Type", 
                    f"Unknown palette type: {palette_type}")
                return
            
            # Generate palette colors
            palette_colors = ColorHarmony.generate_harmony(base_color, harmony_type)
            
            if not palette_colors:
                QMessageBox.warning(self, "Generation Failed", 
                    "Failed to generate palette colors.")
                return
            
            # Apply colors to slots
            for i, color in enumerate(palette_colors):
                if i >= len(self.slots):
                    # Need more slots - add them
                    self.add_color_slot()
                
                if i < len(self.slots):
                    # Set color and weight
                    self.slots[i].set_color(color)
                    self.slots[i].set_weight(self._get_default_weight())  # Use settings default
            
            # Trigger color mixing update
            self.on_slot_change()
            
            # Show success
            palette_name = palette_type.replace('_', ' ').title()
            self.status_updated.emit(f"Generated {palette_name} palette ({len(palette_colors)} colors)")
            logger.success(f"Generated {palette_name} palette", details=f"{len(palette_colors)} colors")
        
        ErrorHandler.safe_execute(generate_palette, "generating quick palette", print)
    
    def _on_save_session(self, filepath: str) -> None:
        """Handle saving current session to file."""
        def save_session() -> None:
            # Import session manager
            try:
                from utils.session_manager import SessionManager
            except ImportError:
                QMessageBox.warning(self, "Not Available", 
                    "Session Manager is not available.")
                return
            
            # Collect all slot data
            slots_data = []
            for slot in self.slots:
                slot_data = {
                    'index': slot.index,
                    'color': list(slot.get_color()),
                    'weight': slot.get_weight()
                }
                slots_data.append(slot_data)
            
            # Collect current settings
            settings = {
                'theme': self.ui_handler.theme_manager.current_theme if hasattr(self, 'ui_handler') else 'dark',
                'zoom_level': self.image_handler.zoom_level if hasattr(self, 'image_handler') else 1.0,
                'window_size': [self.width(), self.height()],
                'window_position': [self.x(), self.y()]
            }
            
            # Get session name from filepath
            import os
            session_name = os.path.splitext(os.path.basename(filepath))[0]
            
            # Save session
            session_manager = SessionManager()
            success = session_manager.save_session(
                filepath=filepath,
                slots_data=slots_data,
                mixed_color=self.current_mixed_color,
                settings=settings,
                name=session_name,
                description=f"Session with {sum(1 for s in slots_data if s['weight'] > 0)} colors"
            )
            
            if success:
                self.status_updated.emit(f"Session saved: {session_name}")
                logger.success(f"Session saved: {filepath}")
            else:
                QMessageBox.warning(self, "Save Failed", 
                    "Failed to save session. Check console for details.")
                self.status_updated.emit("Failed to save session")
        
        ErrorHandler.safe_execute(save_session, "saving session", print)
    
    def _on_load_session(self, filepath: str) -> None:
        """Handle loading session from file."""
        def load_session() -> None:
            # Import session manager
            try:
                from utils.session_manager import SessionManager
            except ImportError:
                QMessageBox.warning(self, "Not Available", 
                    "Session Manager is not available.")
                return
            
            # Load session data
            session_manager = SessionManager()
            session_data = session_manager.load_session(filepath)
            
            if not session_data:
                QMessageBox.warning(self, "Load Failed", 
                    "Failed to load session. File may be corrupted.")
                return
            
            # Get slots data
            slots_data = session_data.get('slots', [])
            
            if not slots_data:
                QMessageBox.warning(self, "Empty Session", 
                    "Session file contains no color data.")
                return
            
            # Ensure we have enough slots
            while len(self.slots) < len(slots_data):
                self.add_color_slot()
            
            # Restore slot data
            for slot_data in slots_data:
                index = slot_data.get('index', 0)
                color = tuple(slot_data.get('color', [200, 200, 200]))
                weight = slot_data.get('weight', 0)
                
                if index < len(self.slots):
                    self.slots[index].set_color(color)
                    self.slots[index].set_weight(weight)
            
            # Clear any extra slots (if session had fewer slots)
            for i in range(len(slots_data), len(self.slots)):
                self.slots[i].set_color((200, 200, 200))
                self.slots[i].set_weight(0)
            
            # Restore settings (optional)
            settings = session_data.get('settings', {})
            
            # Restore theme (if preference)
            if settings.get('theme'):
                # Could restore theme here if desired
                pass
            
            # Trigger color mixing
            self.on_slot_change()
            
            # Show success
            session_name = session_data.get('name', 'Session')
            color_count = sum(1 for s in slots_data if s.get('weight', 0) > 0)
            
            self.status_updated.emit(f"Loaded session: {session_name} ({color_count} colors)")
            logger.success(f"Session loaded: {session_name}", details=f"{len(slots_data)} slots")
            
            QMessageBox.information(self, "Session Loaded", 
                f"Session '{session_name}' loaded successfully!\n\n"
                f"{color_count} colors with {len(slots_data)} total slots.")
        
        ErrorHandler.safe_execute(load_session, "loading session", print)
    
    def _on_settings_changed(self, setting_key: str = None, value: any = None) -> None:
        """
        Handle settings changes from Package D.
        Applies settings to main application immediately.
        
        Args:
            setting_key: Specific setting that changed (e.g. 'theme', 'auto_save_colors')
            value: New value for the setting
        """
        def handle_settings_change() -> None:
            if not self.settings_manager:
                return
            
            # If no specific key provided, apply all settings
            if setting_key is None:
                self._apply_all_settings()
                return
            
            # Apply specific setting
            logger.debug(f"Applying setting: {setting_key} = {value}")
            
            # === THEME CHANGES ===
            if setting_key == 'theme':
                self._apply_theme_setting(value)
            
            # === TOOLTIPS ===
            elif setting_key == 'show_tooltips':
                self._apply_tooltips_setting(value)
            
            # === DEBUG OVERLAYS ===
            elif setting_key == 'show_debug_overlays':
                self._apply_debug_overlays_setting(value)
            
            # === DEFAULT SLOT WEIGHT ===
            elif setting_key == 'default_slot_weight':
                # This will be used when creating new slots
                logger.debug(f"Default slot weight updated to: {value}")
            
            # === MAX COLOR SLOTS ===
            elif setting_key == 'max_color_slots':
                # This will be enforced in add_color_slot()
                logger.debug(f"Max color slots updated to: {value}")
            
            # === HISTORY SETTINGS ===
            elif setting_key == 'history_enabled':
                if self.color_history:
                    # Update history enabled state
                    logger.debug(f"History enabled: {value}")
            
            elif setting_key == 'enable_animations':
                # Could enable/disable animations here
                logger.debug(f"Animations enabled: {value}")
            
            # === PREVIEW VALUE SETTINGS ===
            elif setting_key == 'show_rgb_values':
                # Refresh preview to show/hide RGB values
                logger.debug(f"RGB values display: {value}")
                self._update_preview(self.current_mixed_color)
            
            elif setting_key == 'show_hsv_values':
                # Refresh preview to show/hide HSV values
                logger.debug(f"HSV values display: {value}")
                self._update_preview(self.current_mixed_color)
            
            # Settings applied successfully
            self.status_updated.emit(f"Setting applied: {setting_key}")
        
        ErrorHandler.safe_execute(handle_settings_change, f"applying setting {setting_key}", print)
    
    def _apply_all_settings(self) -> None:
        """Apply all settings from settings manager."""
        def apply_settings() -> None:
            if not self.settings_manager:
                return
            
            settings = self.settings_manager.settings
            prefs = settings.get('preferences', {})
            
            # Apply theme
            theme = prefs.get('theme', 'dark')
            self._apply_theme_setting(theme)
            
            # Apply tooltips
            show_tooltips = prefs.get('show_tooltips', True)
            self._apply_tooltips_setting(show_tooltips)
            
            # Apply debug overlays
            show_debug = prefs.get('show_debug_overlays', False)
            self._apply_debug_overlays_setting(show_debug)
            
            # Apply RGB/HSV visibility
            # This will show/hide the labels in the preview
            self._update_preview(self.current_mixed_color)
            
            logger.success("All settings applied")
        
        ErrorHandler.safe_execute(apply_settings, "applying all settings", print)
    
    def _apply_theme_setting(self, theme: str) -> None:
        """Apply theme setting with full UI update."""
        def apply_theme() -> None:
            if not self.ui_handler:
                return
            
            # DEBUG: Log what theme is being applied
            logger.debug(f"Applying theme setting: {theme}")
            
            # Map setting to theme manager
            theme_map = {
                'dark': 'dark',
                'light': 'light',
                'image': 'image',
                'auto': 'dark'  # Default to dark for auto
            }
            
            target_theme = theme_map.get(theme, 'dark')
            current_theme = self.ui_handler.theme_manager.current_theme
            
            # DEBUG: Log target vs current
            logger.debug(f"Theme change: {current_theme} -> {target_theme}")
            
            if target_theme != current_theme:
                logger.debug(f"Theme mismatch, cycling from {current_theme} to {target_theme}")
                # Cycle theme to match
                cycle_count = 0
                while self.ui_handler.theme_manager.current_theme != target_theme:
                    self.ui_handler.cycle_theme(self)
                    cycle_count += 1
                    logger.debug(f"Theme cycle #{cycle_count}: {self.ui_handler.theme_manager.current_theme}")
                    if cycle_count > 5:  # Safety break
                        logger.warning("Too many theme cycles, breaking")
                        break
                
                # CRITICAL: Apply theme to all UI components (same as button click)
                self._apply_theme_to_buttons()
                self._apply_theme_to_all()
                
                # Update Package D panel if it exists
                if hasattr(self, '_package_d_panel') and self._package_d_panel is not None:
                    is_dark = self.ui_handler.is_dark_mode() or self.ui_handler.is_image_mode()
                    self._package_d_panel.set_theme(is_dark)
                
                # Update theme button text
                if self.theme_button:
                    self.theme_button.setText(self.ui_handler.get_current_theme_name())
                
                # Force UI update and repaint
                self.update()
                
                logger.success(f"Theme changed to: {target_theme}")
            else:
                # Even if theme matches, ensure UI is fully updated
                logger.debug("Theme already matches, refreshing UI")
                self._apply_theme_to_buttons()
                self._apply_theme_to_all()
                self.update()
                logger.success(f"Theme already set to: {target_theme}")
        
        ErrorHandler.safe_execute(apply_theme, "applying theme setting", print)
    
    def _apply_tooltips_setting(self, show: bool) -> None:
        """Enable or disable tooltips globally."""
        def apply_tooltips() -> None:
            # Apply to all child widgets recursively
            self._set_tooltips_recursive(self, show)
            logger.success(f"Tooltips {'enabled' if show else 'disabled'}")
        
        ErrorHandler.safe_execute(apply_tooltips, "applying tooltips setting", print)
    
    def _apply_debug_overlays_setting(self, show: bool) -> None:
        """Show or hide debug overlays (panel overlays only)."""
        def apply_debug_overlays() -> None:
            # Check if animations are enabled
            animations_enabled = False
            if self.settings_manager:
                animations_enabled = self.settings_manager.get('preferences.enable_animations', True)
            
            if show:
                # Create overlays if they don't exist
                if not hasattr(self, 'debug_overlay_main') or self.debug_overlay_main is None:
                    self.debug_overlay_main = DebugOverlay(
                        self.central_widget, "App Window", config.DEBUG_OVERLAY_COLORS['app_window']
                    )
                if not hasattr(self, 'debug_overlay_slots') or self.debug_overlay_slots is None:
                    self.debug_overlay_slots = DebugOverlay(
                        self.slots_scroll_area.viewport(), "Slots Panel", config.DEBUG_OVERLAY_COLORS['slots_panel']
                    )
                
                # Show overlays (with fade animation if enabled)
                if self.debug_overlay_main:
                    if animations_enabled:
                        self._animate_fade(self.debug_overlay_main, fade_in=True)
                    else:
                        self.debug_overlay_main.show()
                if self.debug_overlay_slots:
                    if animations_enabled:
                        self._animate_fade(self.debug_overlay_slots, fade_in=True)
                    else:
                        self.debug_overlay_slots.show()
                
                logger.success("Debug overlays shown")
            else:
                # Hide overlays (with fade animation if enabled)
                if hasattr(self, 'debug_overlay_main') and self.debug_overlay_main:
                    if animations_enabled:
                        self._animate_fade(self.debug_overlay_main, fade_in=False)
                    else:
                        self.debug_overlay_main.hide()
                if hasattr(self, 'debug_overlay_slots') and self.debug_overlay_slots:
                    if animations_enabled:
                        self._animate_fade(self.debug_overlay_slots, fade_in=False)
                    else:
                        self.debug_overlay_slots.hide()
                
                logger.success("Debug overlays hidden")
        
        ErrorHandler.safe_execute(apply_debug_overlays, "applying debug overlays setting", print)
    
    def _animate_resize(self, widget: QWidget, from_w: int, from_h: int, to_w: int, to_h: int, duration: int = 200) -> None:
        """Animate widget resize."""
        def animate() -> None:
            from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve
            
            # Create animation for geometry
            animation = QPropertyAnimation(widget, b"geometry")
            animation.setDuration(duration)
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            
            # Get current position
            x, y = widget.x(), widget.y()
            
            # Set start and end geometry
            animation.setStartValue(QRect(x, y, from_w, from_h))
            animation.setEndValue(QRect(x, y, to_w, to_h))
            
            # Start animation
            animation.start()
            
            # Keep reference to prevent garbage collection
            if not hasattr(self, '_active_animations'):
                self._active_animations = []
            self._active_animations.append(animation)
            
            # Remove from list when done
            animation.finished.connect(lambda: self._active_animations.remove(animation) if animation in self._active_animations else None)
        
        result = ErrorHandler.safe_execute(animate, "animating resize", print)
        if result is None:
            # Fallback to instant resize if animation fails
            widget.setFixedSize(to_w, to_h)
    
    def _animate_fade(self, widget: QWidget, fade_in: bool = True, duration: int = 150) -> None:
        """Animate widget fade in/out."""
        def animate() -> None:
            from PyQt6.QtCore import QPropertyAnimation
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            
            # Create opacity effect if it doesn't exist
            if not widget.graphicsEffect():
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)
            
            effect = widget.graphicsEffect()
            
            # Create animation
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            
            if fade_in:
                animation.setStartValue(0.0)
                animation.setEndValue(1.0)
                widget.show()
            else:
                animation.setStartValue(1.0)
                animation.setEndValue(0.0)
                animation.finished.connect(widget.hide)
            
            # Start animation
            animation.start()
            
            # Keep reference
            if not hasattr(self, '_active_animations'):
                self._active_animations = []
            self._active_animations.append(animation)
            
            # Remove from list when done
            animation.finished.connect(lambda: self._active_animations.remove(animation) if animation in self._active_animations else None)
        
        result = ErrorHandler.safe_execute(animate, "animating fade", print)
        if result is None:
            # Fallback to instant show/hide
            if fade_in:
                widget.show()
            else:
                widget.hide()


    @safe_slot("Failed to add color slot")
    def safe_add_color_slot(self, *args: Any) -> None:
        """Add a new color slot"""
        self.add_color_slot()

    @safe_slot("Image upload failed")
    def safe_upload_image(self, *args: Any) -> None:
        """Upload an image file"""
        self.upload_image()

    @safe_slot("Copy failed")
    def safe_copy_hex_color(self, *args: Any) -> None:
        """Copy hex color to clipboard"""
        self.copy_hex_color()

    @safe_slot("Save failed")
    def safe_save_color_swatch(self, *args: Any) -> None:
        """Save color swatch to file"""
        self.save_color_swatch()

    @safe_slot("Export failed")
    def safe_export_palette(self, *args: Any) -> None:
        """Export palette to file"""
        self.export_palette()

    @safe_slot("Import failed")
    def safe_import_palette(self, *args: Any) -> None:
        """Import palette from file"""
        self.import_palette()

    @safe_slot("Save instruction failed")
    def safe_save_instruction_image(self, *args: Any) -> None:
        """Save instruction image to file"""
        self.save_instruction_image()

    @safe_slot("Reset failed")
    def safe_reset_canvas(self, *args: Any) -> None:
        """Reset the canvas"""
        self.reset_canvas()

    @safe_slot("Zoom reset failed")
    def safe_reset_zoom(self, *args: Any) -> None:
        """Reset zoom to fit window"""
        self.reset_zoom()

    # Safe signal handlers
    def _safe_on_pixel_hover(self, img_x: int, img_y: int, color: tuple) -> None:
        """Handle pixel hover event."""
        def handle_hover() -> None:
            hex_color = ColorMath.rgb_to_hex(color)
            if self.pixel_info_label:
                self.pixel_info_label.setText(f"Pixel: ({img_x},{img_y}) - {hex_color} rgb{color}")
        
        ErrorHandler.safe_execute(handle_hover, "handling pixel hover", print)

    def _safe_on_pixel_sample(self, color: tuple) -> None:
        """Handle pixel sample event."""
        def handle_sample() -> None:
            self.add_color_to_slot(color, config.DEFAULT_SAMPLE_WEIGHT)
        
        ErrorHandler.safe_execute(handle_sample, "handling pixel sample", print)

    def _safe_on_region_sample(self, color: tuple) -> None:
        """Handle region sample event."""
        def handle_sample() -> None:
            self.add_color_to_slot(color, config.DEFAULT_SAMPLE_WEIGHT)
        
        ErrorHandler.safe_execute(handle_sample, "handling region sample", print)

    def _safe_on_zoom_change(self, zoom_level: float) -> None:
        """Handle zoom change event."""
        def handle_zoom() -> None:
            if self.zoom_label:
                self.zoom_label.setText(f"Zoom: {int(zoom_level * 100)}%")
        
        ErrorHandler.safe_execute(handle_zoom, "handling zoom change", print)

    def _safe_on_splitter_moved(self, pos: int, index: int) -> None:
        """Handle splitter moved event."""
        def handle_move() -> None:
            self._on_splitter_moved(pos, index)
        
        ErrorHandler.safe_execute(handle_move, "handling splitter move", print)

    # Core methods
    def upload_image(self) -> None:
        """Upload image with comprehensive error handling."""
        logger.info("Starting image upload...")
        
        def upload() -> None:
            path = self.file_utils.select_image_file("Select Image File")
            if not path:
                logger.info("No file selected")
                return
            
            logger.info(f"Selected file: {path}")
            
            if not os.path.exists(path):
                self.status_updated.emit("File does not exist")
                return
            
            if not os.access(path, os.R_OK):
                self.status_updated.emit("File is not readable")
                return
            
            logger.debug("File validation passed")
            filename = os.path.basename(path)
            self.status_updated.emit(f"Loading {filename}...")
            
            SafeQTimer.safe_single_shot(50, self._do_image_load, path)
            logger.success("Image upload initiated successfully")
        
        ErrorHandler.safe_execute(upload, "uploading image", print)

    def _do_image_load(self, path: str) -> None:
        """Perform image loading with extensive error handling."""
        logger.info("Executing image load...")
        
        def load_image() -> None:
            logger.info(f"Loading image from: {path}")
            
            if not self.image_handler.load_image(path):
                logger.error("Image handler failed to load image")
                self.status_updated.emit("Failed to load image - unsupported format")
                return
            
            logger.success("Image loaded successfully by handler")
            
            # CACHE OPTIMIZATION: Clear color cache when new image loads
            # Old cached colors are no longer relevant to new image
            if hasattr(self, '_color_cache'):
                self._color_cache.clear()
                logger.debug("Cleared color cache for new image")
            
            if not self.canvas_view:
                logger.error("Canvas view is None!")
                self.status_updated.emit("Canvas not available")
                return
            
            logger.debug("Canvas view is available")
            
            canvas_size = self.canvas_view.size()
            logger.debug(f"Canvas size: {canvas_size.width()}x{canvas_size.height()}")
            
            if canvas_size.width() > 100 and canvas_size.height() > 100:
                container_size = (canvas_size.width() - 20, canvas_size.height() - 20)
                self.image_handler.fit_to_container(container_size)
                logger.debug("Image fitted to container")
            
            logger.debug("Displaying image...")
            self.canvas_view.display_image()
            logger.success("Image displayed on canvas")
            
            zoom_level = self.image_handler.zoom_level
            self._safe_on_zoom_change(zoom_level)
            logger.debug(f"Zoom level: {zoom_level}")
            
            try:
                self.canvas_view.hide_preview()
                logger.debug("Preview hidden")
            except Exception as e:
                logger.error("Error hiding preview", error=e)
            
            filename = os.path.basename(path)
            self.status_updated.emit(f"Image loaded: {filename}")
            logger.success(f"Image load completed: {filename}")
        
        ErrorHandler.safe_execute(load_image, "loading image", print)

    def update_status_bar(self, message: str) -> None:
        """Update status bar safely."""
        ErrorHandler.safe_execute(
            lambda: self.statusBar().showMessage(message),
            "updating status bar",
            print
        )

    def add_color_slot(self) -> None:
        """Add color slot safely (respects settings)."""
        def add_slot() -> None:
            # Get max slots from settings
            max_slots = config.MAX_SLOTS
            if self.settings_manager:
                max_slots = self.settings_manager.get('preferences.max_color_slots', config.MAX_SLOTS)
            
            if len(self.slots) >= max_slots:
                self.status_updated.emit(f"Maximum {max_slots} slots reached")
                return
                
            slot = ColorSlot(len(self.slots), self.on_slot_change)
            
            # Set default weight from settings
            default_weight = self._get_default_weight()
            slot.set_weight(default_weight)
            
            # Track signal connection with SignalConnectionManager
            logger.debug(f"Connecting remove signal for slot {len(self.slots)}")
            try:
                if self.signal_manager:
                    self.signal_manager.connect(
                        slot,
                        slot.remove_requested,
                        self.remove_color_slot,
                        track_as=f"slot_{len(self.slots)}_remove"
                    )
                else:
                    slot.remove_requested.connect(self.remove_color_slot)
                logger.debug(f"Remove signal connected for slot {len(self.slots)}")
            except Exception as e:
                logger.error("Error connecting remove signal", error=e)
                traceback.print_exc()
            
            try:
                is_dark = self.ui_handler.is_dark_mode()
                slot.set_theme(is_dark, self.ui_handler)
            except Exception as e:
                logger.error("Error applying theme to slot", error=e)
            
            self.slots_layout.addWidget(slot)
            self.slots.append(slot)
            
            self.status_updated.emit(f"Added color slot {len(self.slots)}")
        
        ErrorHandler.safe_execute(add_slot, "adding color slot", print)

    def remove_color_slot(self, slot: ColorSlot) -> None:
        """Remove a specific color slot safely with race condition protection."""
        def remove_slot() -> None:
            logger.debug(f"Attempting to remove slot {slot.index}")
            
            # PHASE 1.5: Prevent duplicate removal (race condition guard)
            if not hasattr(slot, '_being_removed'):
                slot._being_removed = False
            
            if slot._being_removed:
                logger.warning("Slot already being removed, skipping")
                return
            
            slot._being_removed = True
            
            if slot not in self.slots:
                logger.warning("Slot not found in slots list")
                slot._being_removed = False  # Reset flag
                return
            
            
            # Disconnect signals to prevent memory leaks
            try:
                slot.remove_requested.disconnect()
                slot.color_changed.disconnect()
                slot.weight_changed.disconnect()
                logger.debug(f"Disconnected signals for slot {slot.index}")
            except Exception as disconnect_error:
                # Signal might not be connected, which is fine
                logger.debug(f"Some signals were not connected: {disconnect_error}")
            self.slots_layout.removeWidget(slot)
            logger.debug("Removed from layout")
            
            self.slots.remove(slot)
            logger.debug("Removed from list")
            
            slot.deleteLater()
            logger.debug("Widget scheduled for deletion")
            
            # Use direct method instead of findChildren (O(n) instead of O(n²))
            for i, remaining_slot in enumerate(self.slots):
                remaining_slot.update_index_label(i)
                logger.debug(f"Updated slot label to Color {i + 1}")
            
            logger.debug(f"Remaining slots: {len(self.slots)}")
            self.on_slot_change()
            self.status_updated.emit(f"Removed color slot (now {len(self.slots)} slots)")
            
            # Reset flag after successful removal
            SafeQTimer.safe_single_shot(100, lambda: setattr(slot, '_being_removed', False) if hasattr(slot, '_being_removed') else None)
        
        ErrorHandler.safe_execute(remove_slot, "removing color slot", print)

    def on_slot_change(self) -> None:
        """Handle slot changes safely."""
        def handle_change() -> None:
            # Debounce color mixing - only recalculate after 100ms of no changes
            self._mix_debounce_timer.stop()
            self._mix_debounce_timer.start(100)  # 100ms delay
        
        ErrorHandler.safe_execute(handle_change, "handling slot change", print)

    def _debounced_mix_colors(self) -> None:
        """Debounced color mixing - called after slider stops moving."""
        ErrorHandler.safe_execute(lambda: self.auto_mix_colors(), "debounced color mixing", print)

    def auto_mix_colors(self) -> None:
        """Mix colors safely with caching."""
        def mix_colors() -> None:
            colors_weights = [(s.get_color(), s.get_weight()) for s in self.slots if s.get_weight() > 0]
            
            if not colors_weights:
                self.current_mixed_color = config.INITIAL_COLOR_TUPLE
                self.current_hex = config.INITIAL_COLOR_HEX
                self.current_rgb = config.INITIAL_COLOR_RGB
                self._update_preview((0, 0, 0))
                if self.canvas_view:
                    self.canvas_view.hide_preview()
                return
            
            # PHASE 1.4: Check cache first for performance boost
            cache_key = (
                tuple(tuple(c) for c, _ in colors_weights),
                tuple(w for _, w in colors_weights)
            )
            
            if cache_key in self._color_cache:
                # Cache hit - use cached result
                mixed_color = self._color_cache[cache_key]
                logger.debug(f"Cache hit: {mixed_color}")
            else:
                # Cache miss - calculate and cache
                mixed_color = ColorMath.weighted_rgb_mix(colors_weights)
                
                if mixed_color:
                    # Store in cache
                    self._color_cache[cache_key] = mixed_color
                    
                    # Limit cache size (FIFO eviction)
                    if len(self._color_cache) > self._cache_max_size:
                        # Remove oldest entry
                        oldest_key = next(iter(self._color_cache))
                        del self._color_cache[oldest_key]
                    
                    logger.debug(f"Cached new color: {mixed_color}")
                
            if mixed_color:
                self.current_mixed_color = mixed_color
                self.current_hex = ColorMath.rgb_to_hex(mixed_color)
                self.current_rgb = f"rgb{mixed_color}"
                self._update_preview(mixed_color)
                
                # Track color in history (only non-black colors)
                should_auto_save = True
                if self.settings_manager:
                    should_auto_save = self.settings_manager.get('preferences.auto_save_colors', True)
                
                if should_auto_save and self.color_history and mixed_color != (0, 0, 0):
                    self.color_history.add_color(mixed_color)
                
                if self.canvas_view:
                    self.canvas_view.hide_preview()
                
                self.status_updated.emit(f"Auto-mixed {self.current_hex}")
        
        ErrorHandler.safe_execute(mix_colors, "auto-mixing colors", print)

    def _update_preview(self, color: tuple) -> None:
        """Update preview safely with RGB/HSV values based on settings."""
        def update() -> None:
            if not color:
                color_to_use = (0, 0, 0)
            else:
                color_to_use = color
            
            hex_color = ColorMath.rgb_to_hex(color_to_use)
            
            if self.preview_label:
                current_size = self.preview_label.width() if hasattr(self, 'preview_label') else 140
                border_width = max(2, current_size // 50)
                border_radius = max(8, current_size // 18)
                
                _theme = self.ui_handler.get_current_theme_dict() if self.ui_handler else config.ThemeManager.DARK_THEME
                self.preview_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {hex_color};
                        border: {border_width}px solid {_theme['border_color']};
                        border-radius: {border_radius}px;
                    }}
                """)
            
            # Always show hex
            if self.hex_label:
                self.hex_label.setText(hex_color)
            
            # RGB values
            if self.rgb_label:
                show_rgb = True
                if self.settings_manager:
                    show_rgb = self.settings_manager.get('advanced.show_rgb_values', True)
                
                if show_rgb:
                    self.rgb_label.setText(f"rgb{color_to_use}")
                    self.rgb_label.show()
                else:
                    self.rgb_label.hide()
            
            # HSV values
            if hasattr(self, 'hsv_label') and self.hsv_label:
                show_hsv = False
                if self.settings_manager:
                    show_hsv = self.settings_manager.get('advanced.show_hsv_values', False)
                
                if show_hsv:
                    h, s, v = ColorMath.rgb_to_hsv(color_to_use)
                    hsv_str = f"hsv({h*360:.0f}°, {s*100:.0f}%, {v*100:.0f}%)"
                    self.hsv_label.setText(hsv_str)
                    self.hsv_label.show()
                else:
                    self.hsv_label.hide()
        
        ErrorHandler.safe_execute(update, "updating preview", print)

    def add_color_to_slot(self, color: tuple, weight: int) -> None:
        """Add color to slot safely."""
        def add_color() -> None:
            empty_slot = next((s for s in self.slots if s.get_weight() == 0), None)
            if empty_slot is None:
                self.add_color_slot()
                slot = self.slots[-1] if self.slots else None
            else:
                slot = empty_slot
                
            if slot:
                slot.set_color(color)
                slot.set_weight(weight)
        
        ErrorHandler.safe_execute(add_color, "adding color to slot", print)

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Handle splitter movement safely."""
        def handle_splitter_move() -> None:
            sizes = self.content_splitter.sizes()
            if len(sizes) >= 2:
                total_width = sum(sizes)
                left_width = sizes[0]
            
                min_left = config.SLOTS_MIN_WIDTH
                max_left = min(config.SLOTS_MAX_WIDTH, total_width - 400)
            
                if left_width < min_left:
                    sizes[0] = min_left
                    sizes[1] = total_width - min_left
                    self.content_splitter.setSizes(sizes)
                elif left_width > max_left:
                    sizes[0] = max_left
                    sizes[1] = total_width - max_left
                    self.content_splitter.setSizes(sizes)
        
        ErrorHandler.safe_execute(handle_splitter_move, "splitter move", print)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize safely."""
        def handle_resize() -> None:
            super(ColorMixerApp, self).resizeEvent(event)
        
            # Resize background label for Image Mode
            if hasattr(self, 'background_label') and self.background_label:
                self.background_label.setGeometry(0, 0, self.central_widget.width(), self.central_widget.height())
        
            if hasattr(self, 'content_splitter') and self.content_splitter:
                total_width = self.width() - 40
                # Maintain slots panel between config min-max width
                left_width = max(config.SLOTS_MIN_WIDTH, min(config.SLOTS_MAX_WIDTH, total_width * 0.32))
                right_width = total_width - left_width
                self.content_splitter.setSizes([int(left_width), int(right_width)])
            
            self._update_preview_size()
            
            if (hasattr(self, 'canvas_view') and self.canvas_view and 
                hasattr(self, 'image_handler') and self.image_handler.is_loaded()):
                SafeQTimer.safe_single_shot(100, self._update_image_display)
        
        ErrorHandler.safe_execute(handle_resize, "handling resize event", print)

    def _update_preview_size(self) -> None:
        """Update preview size safely."""
        def update_size() -> None:
            if hasattr(self, 'preview_label') and self.preview_label:
                new_size = self._calculate_preview_size()
                self.preview_label.setFixedSize(new_size, new_size)
                
                # Also update the preview container height to match
                if hasattr(self, 'preview_container') and self.preview_container:
                    # Container height = preview square + labels (~125px for hex/rgb/hsv + margins + borders)
                    # Minimum container height = 120 (min preview) + 125 = 245
                    container_height = max(245, new_size + 125)
                    self.preview_container.setMinimumHeight(container_height)
                    self.preview_container.setMaximumHeight(container_height + 50)
        
        ErrorHandler.safe_execute(update_size, "updating preview size", print)

    def _update_image_display(self) -> None:
        """Update image display safely."""
        def update_display() -> None:
            if self.canvas_view and self.image_handler.is_loaded():
                self.canvas_view.display_image()
        
        ErrorHandler.safe_execute(update_display, "updating image display", print)

    def copy_hex_color(self) -> None:
        """Copy hex color safely."""
        def copy() -> None:
            if self.clipboard_utils.copy_text(self.current_hex):
                self.status_updated.emit(f"Copied {self.current_hex}")
            else:
                self.status_updated.emit("Copy failed")
        
        ErrorHandler.safe_execute(copy, "copying hex color", print)

    def reset_canvas(self) -> None:
        """Reset canvas safely."""
        def reset() -> None:
            self.image_handler.clear_image()
            self.canvas_view.clear_canvas()
            if self.zoom_label:
                self.zoom_label.setText("Zoom: 100%")
            if self.pixel_info_label:
                self.pixel_info_label.setText("Pixel: -")
            self.status_updated.emit("Canvas cleared")
        
        ErrorHandler.safe_execute(reset, "resetting canvas", print)

    def reset_zoom(self) -> None:
        """Reset zoom safely."""
        def reset() -> None:
            if self.image_handler.is_loaded():
                self.canvas_view.reset_zoom()
                self.status_updated.emit("Zoom reset")
            else:
                self.status_updated.emit("No image loaded")
        
        ErrorHandler.safe_execute(reset, "resetting zoom", print)

    def save_color_swatch(self) -> None:
        """Save swatch safely."""
        def save_swatch() -> None:
            path = self.file_utils.select_save_location("Save Color Swatch")
            if not path:
                return
                
            from PIL import Image, ImageDraw, ImageFont
            
            color_rgb = self.current_mixed_color
            img = Image.new("RGB", config.SWATCH_OUTPUT_SIZE, color_rgb)
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except Exception:
                font = ImageFont.load_default()
                
            center_x, center_y = config.SWATCH_OUTPUT_SIZE[0] // 2, config.SWATCH_OUTPUT_SIZE[1] // 2
            brightness = sum(color_rgb) / 3
            text_color = "white" if brightness < 128 else "black"
            
            draw.text((center_x, center_y), self.current_hex, fill=text_color, anchor="mm", font=font)
            
            ext = os.path.splitext(path)[1].lower()
            if ext in [".jpg", ".jpeg"]:
                img = img.convert("RGB")
                img.save(path, "JPEG")
            else:
                img.save(path, "PNG")
                
            self.status_updated.emit(f"Saved swatch: {os.path.basename(path)}")
        
        ErrorHandler.safe_execute(save_swatch, "saving color swatch", print)

    def export_palette(self) -> None:
        """Export palette safely."""
        def export() -> None:
            colors = [(s.get_color(), s.get_weight()) for s in self.slots if s.get_weight() > 0]
            if not colors:
                QMessageBox.warning(self, "No Colors", "No colors to export")
                return
                
            path = self.file_utils.select_palette_export_location()
            if not path:
                return
                
            self.palette_formats.export_palette(path, colors)
            self.status_updated.emit(f"Exported: {os.path.basename(path)}")
        
        ErrorHandler.safe_execute(export, "exporting palette", print)

    def import_palette(self) -> None:
        """Import palette safely."""
        def import_pal() -> None:
            path = self.file_utils.select_palette_import_file()
            if not path:
                return
                
            colors = self.palette_formats.import_palette(path)
            
            for i, (color, weight) in enumerate(colors):
                if i >= len(self.slots):
                    self.add_color_slot()
                if i < len(self.slots):
                    self.slots[i].set_color(color)
                    self.slots[i].set_weight(weight)
                    
            self.status_updated.emit(f"Imported: {os.path.basename(path)}")
        
        ErrorHandler.safe_execute(import_pal, "importing palette", print)

    def save_instruction_image(self) -> None:
        """Save instruction image safely."""
        def save_instruction() -> None:
            colors = [(s.get_color(), s.get_weight()) for s in self.slots if s.get_weight() > 0]
            if not colors:
                QMessageBox.warning(self, "No Colors", "No colors for instruction image")
                return
                
            path = self.file_utils.select_save_location("Save Instruction Image")
            if not path:
                return
                
            from PIL import Image, ImageDraw
            
            img = Image.new("RGB", (800, 600), "white")
            draw = ImageDraw.Draw(img)
            
            x, y = 50, 50
            for i, (color, weight) in enumerate(colors):
                draw.rectangle([x, y, x+100, y+100], fill=color)
                x += 120
                if x > 600:
                    x = 50
                    y += 120
            
            img.save(path, "PNG")
            self.status_updated.emit(f"Saved instruction: {os.path.basename(path)}")
        
        ErrorHandler.safe_execute(save_instruction, "saving instruction image", print)

    # Drag and drop
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter safely."""
        def handle_drag() -> None:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
        
        ErrorHandler.safe_execute(handle_drag, "handling drag enter", print)

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop safely."""
        def handle_drop() -> None:
            if event.mimeData().hasUrls():
                url = event.mimeData().urls()[0]
                path = url.toLocalFile()
                
                if path and os.path.exists(path):
                    self.status_updated.emit(f"Loading dropped: {os.path.basename(path)}")
                    SafeQTimer.safe_single_shot(10, self._do_image_load, path)
                else:
                    self.status_updated.emit("Invalid dropped file")
                    
                event.acceptProposedAction()
        
        ErrorHandler.safe_execute(handle_drop, "handling drop event", print)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Application-level event filter for custom themed tooltips.

        Intercepts QEvent.ToolTip to show our custom _ThemedToolTip
        instead of the native OS tooltip (which ignores CSS border-radius
        on Windows Light/Image modes).
        """
        event_type = event.type()

        if event_type == QEvent.Type.ToolTip:
            # If tooltips are disabled, consume the event silently — this
            # catches widgets added after the disable call (e.g. new color
            # slots) whose toolTip() string was never cleared.
            tooltips_enabled = True
            if hasattr(self, 'settings_manager') and self.settings_manager:
                tooltips_enabled = self.settings_manager.get('preferences.show_tooltips', True)
            
            if not tooltips_enabled:
                _ThemedToolTip.instance().hide_tip()
                return True  # Consume — suppress both custom and native tooltip
            
            if isinstance(obj, QWidget) and obj.toolTip():
                # Get current theme colors from ThemeManager
                theme_colors = self.ui_handler.theme_manager.get_current_theme()
                if theme_colors:
                    _ThemedToolTip.instance().show_tip(
                        QCursor.pos(),
                        obj.toolTip(),
                        theme_colors,
                        config.FONT_FAMILY
                    )
                return True  # Consume event — prevent native tooltip
        elif event_type in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress,
                            QEvent.Type.WindowDeactivate, QEvent.Type.Wheel):
            _ThemedToolTip.instance().hide_tip()

        return super().eventFilter(obj, event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle close event safely - save settings before closing."""
        def handle_close() -> None:
            logger.info("Application closing...")
            
            # Remove custom tooltip event filter and hide any visible tooltip
            QApplication.instance().removeEventFilter(self)
            _ThemedToolTip.instance().hide_tip()
            
            # Save window geometry to settings
            if self.settings_manager:
                # Save window size
                self.settings_manager.set('window.main_width', self.width())
                self.settings_manager.set('window.main_height', self.height())
                
                # Save window position if enabled
                remember_position = self.settings_manager.get('window.remember_position', False)
                if remember_position:
                    self.settings_manager.set('window.main_x', self.x())
                    self.settings_manager.set('window.main_y', self.y())
                
                # Save all settings
                self.settings_manager.save_settings()
                logger.success("Settings saved on close")
            
            # === AUTO-SAVE CLEANUP ===
            if hasattr(self, 'session_manager') and self.session_manager:
                # Stop auto-save timer
                self.session_manager.stop_autosave()
                # Delete autosave file (clean exit)
                self.session_manager.delete_autosave()
            # === END AUTO-SAVE CLEANUP ===
            
            # === MEMORY CLEANUP: TIMERS ===
            # Stop debounce timer
            if hasattr(self, '_mix_debounce_timer') and self._mix_debounce_timer:
                self._mix_debounce_timer.stop()
                logger.debug("Stopped mix debounce timer")
            
            # Stop debug overlay timers
            if hasattr(self, 'debug_overlay_main') and self.debug_overlay_main:
                if hasattr(self.debug_overlay_main, 'update_timer'):
                    self.debug_overlay_main.update_timer.stop()
            if hasattr(self, 'debug_overlay_slots') and self.debug_overlay_slots:
                if hasattr(self.debug_overlay_slots, 'update_timer'):
                    self.debug_overlay_slots.update_timer.stop()
            # === END TIMER CLEANUP ===
            
            # === MEMORY CLEANUP: ANIMATIONS ===
            if hasattr(self, '_active_animations'):
                # Stop all running animations
                for anim in self._active_animations:
                    try:
                        anim.stop()
                    except Exception:
                        pass
                self._active_animations.clear()
                logger.debug("Cleared active animations")
            # === END ANIMATION CLEANUP ===
            
            # === MEMORY CLEANUP: IMAGE HANDLER ===
            if hasattr(self, 'image_handler') and self.image_handler:
                self.image_handler.clear_image()
                logger.debug("Cleared image handler")
            # === END IMAGE CLEANUP ===
            
            # === COLOR HISTORY THREAD CLEANUP ===
            # Stop any background save thread before closing to prevent
            # QThread "destroyed while still running" crash on quick exit
            if hasattr(self, 'color_history') and self.color_history:
                try:
                    self.color_history.cleanup()
                    logger.debug("Color history cleanup complete")
                except Exception as e:
                    logger.debug(f"Color history cleanup: {e}")
            # === END COLOR HISTORY CLEANUP ===

            # === MEMORY CLEANUP: SIGNAL DISCONNECTIONS ===
            try:
                # Use SignalConnectionManager if available
                if hasattr(self, 'signal_manager') and self.signal_manager:
                    disconnected = self.signal_manager.disconnect_all()
                    logger.debug(f"SignalConnectionManager disconnected {disconnected} signals")
                else:
                    # Fallback: Manual signal disconnection
                    # Disconnect canvas view signals
                    if hasattr(self, 'canvas_view') and self.canvas_view:
                        try:
                            self.canvas_view.pixel_hovered.disconnect()
                            self.canvas_view.pixel_sampled.disconnect()
                            self.canvas_view.region_sampled.disconnect()
                            self.canvas_view.zoom_changed.disconnect()
                        except Exception:
                            pass
                    
                    # Disconnect package d panel signals
                    if hasattr(self, '_package_d_panel') and self._package_d_panel:
                        try:
                            self._package_d_panel.load_history_color.disconnect()
                            self._package_d_panel.load_preset.disconnect()
                            self._package_d_panel.save_as_preset.disconnect()
                            self._package_d_panel.apply_harmony.disconnect()
                            self._package_d_panel.save_session.disconnect()
                            self._package_d_panel.load_session.disconnect()
                            self._package_d_panel.export_current_mix.disconnect()
                            self._package_d_panel.generate_quick_palette.disconnect()
                            self._package_d_panel.pick_screen_color.disconnect()
                            self._package_d_panel.settings_changed.disconnect()
                        except Exception:
                            pass
                    
                    # Disconnect color slot signals
                    if hasattr(self, 'slots') and self.slots:
                        for slot in self.slots:
                            try:
                                slot.color_changed.disconnect()
                                slot.weight_changed.disconnect()
                                slot.remove_requested.disconnect()
                            except Exception:
                                pass
                    
                    # Disconnect screen picker signals
                    if hasattr(self, 'screen_picker') and self.screen_picker:
                        try:
                            self.screen_picker.color_picked.disconnect()
                            self.screen_picker.picker_cancelled.disconnect()
                        except Exception:
                            pass
                    
                    # Disconnect timer signals
                    if hasattr(self, '_mix_debounce_timer') and self._mix_debounce_timer:
                        try:
                            self._mix_debounce_timer.timeout.disconnect()
                        except Exception:
                            pass
                
                logger.debug("Disconnected signals")
            except Exception as e:
                logger.debug(f"Signal disconnect cleanup: {e}")
            # === END SIGNAL CLEANUP ===
            
            event.accept()
        
        result = ErrorHandler.safe_execute(handle_close, "handling close event", print)
        if result is None:
            # Even if error handling fails, accept close event
            event.accept()

    def _ensure_fonts_applied(self) -> None:
        """
        Ensure fonts are applied to all components.
        
        Uses stylesheet instead of findChildren() loops.
        Qt automatically propagates stylesheets to child widgets.
        """
        def apply_fonts() -> None:
            # Use stylesheet for efficient font application to all children
            font_style = f"font-family: '{config.FONT_FAMILY}'; font-size: {config.FONT_SIZES['normal']}px;"
            
            # Apply to main window (propagates to all children)
            current_style = self.styleSheet() or ""
            if font_style not in current_style:
                self.setStyleSheet(f"QWidget {{ {font_style} }} {current_style}")
            
            logger.success("Fonts enforced via stylesheet")
        
        ErrorHandler.safe_execute(apply_fonts, "enforcing fonts", print)


def main() -> int:
    """Main entry point with comprehensive exception handling."""
    try:
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")  # Consistent cross-platform rendering (supports custom tooltip system)
        app.setApplicationName(app_info['name'])
        app.setApplicationVersion(app_info['version'])
        
        # Use FontManager for efficient one-time font loading
        font_manager = config.FontManager()
        font_manager.apply_to_app(app)
        
        # Apply universal font stylesheet
        try:
            app.setStyleSheet(config.get_font_stylesheet())
            logger.success("Universal font stylesheet applied")
        except Exception as e:
            logger.warning(f"Could not apply font stylesheet", error=e)
        # Create main window
        logger.info("Creating main window...")
        window = ColorMixerApp()
        
        # Font already applied at app level via FontManager.apply_to_app()
        
        logger.info("Showing window...")
        window.show()
        
        logger.success("Application ready!")
        separator()
        # separator already added
        
        return app.exec()
        
    except Exception as e:
        logger.critical("Error in main()", error=e)
        traceback.print_exc()
        
        try:
            QMessageBox.critical(None, "Startup Failed", 
                               f"Application failed to start:\n{str(e)}")
        except Exception:
            pass
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    logger.info(f"Application exited with code: {exit_code}")
    sys.exit(exit_code)