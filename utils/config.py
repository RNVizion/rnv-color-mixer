"""
Configuration for the RNV Color Mixer application (PyQt6).

Central source of truth for application identity (VERSION, APP_NAME),
window and widget dimensions, file paths, font management, and the
ThemeManager system supporting Dark, Light, and Image modes with
cached QPalette objects for fast theme switching.

Every color lives in utils/colors.py (#63 A, 2026-10-18), and this module
reads its colors from there.
"""

import os
import base64
from typing import TYPE_CHECKING, Any

# Every color lives in utils/colors.py: ThemeManager serves its three
# palettes from there, and the stylesheets below draw with these names.
from utils import colors
from utils.colors import (
    translucent_rgba, APP_BORDER_DARK, APP_BORDER_LIGHT, APP_BTN_HOVER_INVERSE,
    APP_BTN_PRESSED, APP_CHROME_DARK, APP_CONTROL_DIM, APP_HANDLE_EDGE_LIGHT, APP_HANDLE_LIGHT,
    APP_ITEM_HOVER_LIGHT, APP_SURFACE_DARK, APP_TEXT_DARK, APP_WINDOW_LIGHT, BRAND_DARK_GOLD,
    BRAND_DARK_GOLD_DEEP, BRAND_GOLD, COMBO_ALPHA, IMAGE_CHECKBOX_ALPHA, IMAGE_FIELD_ALPHA,
    SCROLLBAR_BG_ALPHA, SCROLLBAR_HANDLE_ALPHA, SCROLLBAR_HANDLE_ALPHA_DARK,
    SCROLL_AREA_BORDER_ALPHA, STATUS_BAR_ALPHA, TRUE_BLACK, WHITE,
)

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("Config")
except ImportError:
    logger = None


# Type hints for IDE (not imported at runtime)
if TYPE_CHECKING:
    from PyQt6.QtGui import QPalette, QFont, QPixmap
    from PyQt6.QtWidgets import QApplication, QWidget


# Application identity — single source of truth for version and name
VERSION = "3.3.3"
APP_NAME = "RNV Color Mixer"

# Debug mode - set to True to enable debug overlays
# Can also be enabled via environment variable: COLOR_MIXER_DEBUG=true
DEBUG_MODE = os.getenv('COLOR_MIXER_DEBUG', 'false').lower() == 'true'

# Application constants
MAX_SLOTS = 12
IMAGE_PREVIEW_SIZE = (400, 300)
DEFAULT_WINDOW_SIZE = (1130, 610)  # Updated to accommodate HSV label
MINIMUM_WINDOW_SIZE = (1130, 610)  # Minimum size to maintain layout with HSV

# Color settings
DEFAULT_WEIGHT = 0
DEFAULT_SAMPLE_WEIGHT = 50


# UI settings
BUTTON_SIZE = (120, 80)
CANVAS_HEIGHT = 400
PREVIEW_SIZE = (180, 120)
SWATCH_OUTPUT_SIZE = (400, 400)
SLOTS_CANVAS_WIDTH = 360  # Updated to match optimal width
SLOTS_MIN_WIDTH = 360     # Minimum width for slots panel
SLOTS_MAX_WIDTH = 450     # Maximum width for slots panel
SLOTS_MIN_HEIGHT = 506    # Minimum height for slots scroll area

# Package D Control Panel settings
PACKAGE_D_WIDTH = 630         # Locked width (min and max)
PACKAGE_D_MIN_HEIGHT = 666    # Minimum height (also logo reveal threshold)
PACKAGE_D_DEFAULT_HEIGHT = 666  # Default startup height

# Directory paths
# config.py is in utils/, so go up one level to get project root
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_THIS_DIR)  # Project root
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
BUTTON_IMAGES_DIR = os.path.join(RESOURCES_DIR, "button_images")
BACKGROUND_IMAGES_DIR = os.path.join(RESOURCES_DIR, "background_images")
DEFAULT_BACKGROUND = os.path.join(BACKGROUND_IMAGES_DIR, "background.png")

# Core module paths
CORE_DIR = os.path.join(BASE_DIR, "core")
UI_DIR = os.path.join(BASE_DIR, "ui")
UTILS_DIR = os.path.join(BASE_DIR, "utils")


# Theme Manager - From Color Picker (Superior Dark Theme System)
class ThemeManager:
    """Manages application themes with Dark Mode, Light Mode, and Image Mode"""
    
    # The palettes live in utils/colors.py (#63 A, 2026-10-18), under the
    # same names; these are the same three dicts.
    DARK_THEME = colors.DARK_THEME
    LIGHT_THEME = colors.LIGHT_THEME
    IMAGE_THEME = colors.IMAGE_THEME
    
    # CACHE OPTIMIZATION: Maximum palette cache size (one per theme type)
    MAX_PALETTE_CACHE_SIZE = 5  # Safety limit (we only have 3 themes, but allow headroom)
    
    def __init__(self) -> None:
        self.current_theme = 'dark'
        self.image_mode_available = False
        self.image_mode_active = False
        self._palette_cache = {}  # Cache QPalette objects for faster theme switching
        self._background_cache = None  # Cache background image
        
    def detect_image_resources(self) -> bool:
        """Check if custom images are available"""
        bg_path = os.path.join(BASE_DIR,"resources", "background_images", "background.png")
        has_background = os.path.exists(bg_path)
        
        button_names = ['add', 'upload', 'copy', 'save', 'export', 'import', 'clear', 'reset']
        button_count = sum(1 for name in button_names 
                          if os.path.exists(os.path.join(BASE_DIR, f"{name}_base.png")))
        
        self.image_mode_available = has_background or button_count >= 4
        
        if self.image_mode_available:
            self.image_mode_active = True
            self.current_theme = 'image'
        
        return self.image_mode_available
    
    def cycle_theme(self) -> str:
        """Cycle through available themes"""
        if self.image_mode_available:
            if self.current_theme == 'image':
                self.current_theme = 'dark'
                self.image_mode_active = False
            elif self.current_theme == 'dark':
                self.current_theme = 'light'
            else:
                self.current_theme = 'image'
                self.image_mode_active = True
        else:
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        
        return self.current_theme
    
    def get_current_theme(self) -> 'dict[str, Any] | None':
        """Get current theme dictionary"""
        if self.current_theme == 'dark':
            return self.DARK_THEME
        elif self.current_theme == 'light':
            return self.LIGHT_THEME
        elif self.current_theme == 'image':
            return self.IMAGE_THEME
        else:
            return None
    
    def get_theme_display_name(self) -> str:
        """Get display name for current theme"""
        if self.current_theme == 'image':
            return "Image Mode"
        elif self.current_theme == 'dark':
            return "Dark Mode"
        else:
            return "Light Mode"
    
    def is_image_mode(self) -> bool:
        """Check if image mode is active"""
        return self.image_mode_active
    
    def get_cached_palette(self, theme_name: str) -> 'QPalette | None':
        """Get cached QPalette for faster theme switching."""
        if theme_name in self._palette_cache:
            return self._palette_cache[theme_name]
        return None
    
    def set_cached_palette(self, theme_name: str, palette: 'QPalette') -> None:
        """Cache a QPalette for this theme with size limit enforcement."""
        # CACHE OPTIMIZATION: Enforce size limit
        if len(self._palette_cache) >= self.MAX_PALETTE_CACHE_SIZE and theme_name not in self._palette_cache:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._palette_cache))
            del self._palette_cache[oldest_key]
        self._palette_cache[theme_name] = palette
    
    def clear_palette_cache(self) -> None:
        """Clear the palette cache (useful when theme settings change)."""
        self._palette_cache = {}
    
    def get_background_cache(self) -> 'QPixmap | None':
        """Get cached background image for Image Mode."""
        return self._background_cache
    
    def set_background_cache(self, pixmap: 'QPixmap') -> None:
        """Cache the background image for Image Mode."""
        self._background_cache = pixmap


# Font settings
FONT_FAMILY = "Montserrat Black"
FONT_FILE_NAME = "Montserrat-Black.ttf"
FONT_PATH = os.path.join(RESOURCES_DIR, "fonts", FONT_FILE_NAME)
FONT_SIZES = {
    "small": 9,
    "normal": 10,
    "medium": 12,
    "large": 14,
    "xlarge": 16,
    "title": 18
}

EMBED_FONT = False
EMBEDDED_FONT_DATA = ""

# Updated Stylesheets using new theme system with LARGER BUTTONS
DARK_STYLESHEET = f"""
QMainWindow {{
    background-color: {TRUE_BLACK};
    color: {APP_TEXT_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QWidget {{
    background-color: {TRUE_BLACK};
    color: {APP_TEXT_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton {{
    background-color: {APP_SURFACE_DARK};
    color: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    padding: 2px;
    border-radius: 4px;
    font-weight: bold;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton:hover {{
    background-color: {APP_BORDER_DARK};
    border-color: {APP_BORDER_DARK};
}}

QPushButton:pressed {{
    background-color: {APP_BTN_PRESSED};
    color: {TRUE_BLACK};
    border-color: {APP_BORDER_DARK};
}}

QLineEdit {{
    background-color: {APP_SURFACE_DARK};
    color: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
    min-height: 16px;
    selection-background-color: {BRAND_GOLD};
    selection-color: {TRUE_BLACK};
}}

QLineEdit:focus {{
    border-color: {BRAND_GOLD};
}}

QLabel {{
    color: {APP_TEXT_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QSlider::groove:horizontal {{
    border: 1px solid {APP_BORDER_DARK};
    height: 8px;
    background: {APP_SURFACE_DARK};
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    width: 18px;
    border-radius: 9px;
    margin: -5px 0;
}}

QSlider::handle:horizontal:hover {{
    background: {BRAND_GOLD};
}}

QScrollArea {{
    background-color: {TRUE_BLACK};
    border: 1px solid {APP_BORDER_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 15px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {translucent_rgba(APP_BORDER_DARK, SCROLLBAR_HANDLE_ALPHA_DARK)};
    min-height: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {BRAND_GOLD};
}}

QScrollBar::sub-page:vertical {{
    background-color: transparent;
}}

QScrollBar::add-page:vertical {{
    background-color: transparent;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 15px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {translucent_rgba(APP_BORDER_DARK, SCROLLBAR_HANDLE_ALPHA_DARK)};
    min-width: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {BRAND_GOLD};
}}

QScrollBar::sub-page:horizontal {{
    background-color: transparent;
}}

QScrollBar::add-page:horizontal {{
    background-color: transparent;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    border: none;
    background: none;
}}

QStatusBar {{
    background-color: {APP_SURFACE_DARK};
    color: {APP_TEXT_DARK};
    border-top: 1px solid {APP_BORDER_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QStatusBar QLabel {{
    background-color: {APP_SURFACE_DARK};
    color: {APP_TEXT_DARK};
    padding: 2px 4px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QCheckBox {{
    color: {APP_TEXT_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    background-color: {APP_SURFACE_DARK};
    border: 1px solid {APP_BORDER_DARK};
}}

QCheckBox::indicator:checked {{
    background-color: {BRAND_GOLD};
    border-color: {BRAND_GOLD};
}}

QSplitter::handle {{
    background-color: {APP_BORDER_DARK};
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QComboBox {{
    background-color: {APP_SURFACE_DARK};
    color: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QComboBox:hover {{
    border-color: {BRAND_GOLD};
}}

QComboBox QAbstractItemView {{
    background-color: {APP_SURFACE_DARK};
    color: {APP_TEXT_DARK};
    selection-background-color: {BRAND_GOLD};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {APP_BORDER_DARK};
    color: {BRAND_GOLD};
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {BRAND_GOLD};
    color: {TRUE_BLACK};
}}
"""

LIGHT_STYLESHEET = f"""
QMainWindow {{
    background-color: {APP_WINDOW_LIGHT};
    color: {TRUE_BLACK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QWidget {{
    background-color: {APP_WINDOW_LIGHT};
    color: {TRUE_BLACK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton {{
    background-color: {WHITE};
    color: {TRUE_BLACK};
    border: 1px solid {APP_BORDER_LIGHT};
    padding: 2px;
    border-radius: 4px;
    font-weight: bold;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton:hover {{
    background-color: {APP_BTN_HOVER_INVERSE};
    border-color: {APP_BORDER_LIGHT};
}}

QPushButton:pressed {{
    background-color: {APP_BTN_PRESSED};
    color: {WHITE};
    border-color: {APP_BORDER_LIGHT};
}}

QLineEdit {{
    background-color: {WHITE};
    color: {TRUE_BLACK};
    border: 1px solid {APP_BORDER_LIGHT};
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
    min-height: 16px;
    selection-background-color: {BRAND_DARK_GOLD};
    selection-color: {WHITE};
}}

QLineEdit:focus {{
    border-color: {BRAND_DARK_GOLD};
}}

QLabel {{
    color: {TRUE_BLACK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QSlider::groove:horizontal {{
    border: 1px solid {APP_BORDER_LIGHT};
    height: 8px;
    background: {WHITE};
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {APP_HANDLE_LIGHT};
    border: 1px solid {APP_HANDLE_EDGE_LIGHT};
    width: 18px;
    border-radius: 9px;
    margin: -5px 0;
}}

QSlider::handle:horizontal:hover {{
    background: {BRAND_DARK_GOLD};
}}

QScrollArea {{
    background-color: {WHITE};
    border: 1px solid {APP_BORDER_LIGHT};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QScrollBar:vertical {{
    background-color: {APP_WINDOW_LIGHT};
    width: 15px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {APP_BORDER_LIGHT};
    min-height: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {BRAND_DARK_GOLD};
}}

QScrollBar::sub-page:vertical {{
    background-color: {APP_WINDOW_LIGHT};
}}

QScrollBar::add-page:vertical {{
    background-color: {APP_WINDOW_LIGHT};
}}

QScrollBar:horizontal {{
    background-color: {APP_WINDOW_LIGHT};
    height: 15px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {APP_BORDER_LIGHT};
    min-width: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {BRAND_DARK_GOLD};
}}

QScrollBar::sub-page:horizontal {{
    background-color: {APP_WINDOW_LIGHT};
}}

QScrollBar::add-page:horizontal {{
    background-color: {APP_WINDOW_LIGHT};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    border: none;
    background: none;
}}

QStatusBar {{
    background-color: {APP_WINDOW_LIGHT};
    color: {TRUE_BLACK};
    border-top: 1px solid {APP_BORDER_LIGHT};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QStatusBar QLabel {{
    background-color: {APP_WINDOW_LIGHT};
    color: {TRUE_BLACK};
    padding: 2px 4px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QCheckBox {{
    color: {TRUE_BLACK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    background-color: {WHITE};
    border: 1px solid {APP_BORDER_LIGHT};
}}

QCheckBox::indicator:checked {{
    background-color: {BRAND_DARK_GOLD};
    border-color: {BRAND_DARK_GOLD};
}}

QSplitter::handle {{
    background-color: {APP_BORDER_LIGHT};
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QComboBox {{
    background-color: {WHITE};
    color: {TRUE_BLACK};
    border: 1px solid {APP_BORDER_LIGHT};
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QComboBox:hover {{
    border-color: {BRAND_DARK_GOLD};
}}

QComboBox QAbstractItemView {{
    background-color: {WHITE};
    color: {TRUE_BLACK};
    selection-background-color: {BRAND_DARK_GOLD};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {APP_ITEM_HOVER_LIGHT};
    color: {BRAND_DARK_GOLD_DEEP};
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {BRAND_DARK_GOLD};
    color: {WHITE};
}}
"""

# NEW: Image Mode Stylesheet (modified from Dark theme to allow background image)
IMAGE_STYLESHEET = f"""
QMainWindow {{
    color: {APP_TEXT_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QMainWindow > QWidget {{
    background-color: transparent;
}}

QWidget {{
    background-color: transparent;
    color: {APP_TEXT_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QFrame, QScrollArea, QLabel {{
    background-color: transparent;
}}

QPushButton {{
    background-color: {APP_SURFACE_DARK};
    color: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    padding: 2px;
    border-radius: 4px;
    font-weight: bold;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton:hover {{
    background-color: {APP_BORDER_DARK};
    border-color: {APP_BORDER_DARK};
}}

QPushButton:pressed {{
    background-color: {APP_BTN_PRESSED};
    color: {TRUE_BLACK};
    border-color: {APP_BORDER_DARK};
}}

QLineEdit {{
    background-color: {translucent_rgba(TRUE_BLACK, IMAGE_FIELD_ALPHA)};
    color: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
    min-height: 16px;
    selection-background-color: {BRAND_GOLD};
    selection-color: {TRUE_BLACK};
}}

QLineEdit:focus {{
    border-color: {BRAND_GOLD};
}}

QLabel {{
    color: {APP_TEXT_DARK};
    background-color: transparent;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QSlider::groove:horizontal {{
    border: 1px solid {APP_BORDER_DARK};
    height: 8px;
    background: {APP_SURFACE_DARK};
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    width: 18px;
    border-radius: 9px;
    margin: -5px 0;
}}

QSlider::handle:horizontal:hover {{
    background: {BRAND_GOLD};
}}

QScrollArea {{
    background-color: transparent;
    border: 1px solid {translucent_rgba(APP_BORDER_DARK, SCROLL_AREA_BORDER_ALPHA)};
    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;
}}

QScrollArea::viewport {{
    background-color: transparent;
}}

QScrollArea QWidget {{
    background-color: transparent;
}}

QScrollArea::corner {{
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {translucent_rgba(APP_BORDER_DARK, SCROLLBAR_BG_ALPHA)};
    width: 15px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {translucent_rgba(APP_CHROME_DARK, SCROLLBAR_HANDLE_ALPHA)};
    min-height: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {BRAND_GOLD};
}}

QScrollBar::sub-page:vertical {{
    background-color: transparent;
}}

QScrollBar::add-page:vertical {{
    background-color: transparent;
}}

QScrollBar:horizontal {{
    background-color: {translucent_rgba(APP_BORDER_DARK, SCROLLBAR_BG_ALPHA)};
    height: 15px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {translucent_rgba(APP_CHROME_DARK, SCROLLBAR_HANDLE_ALPHA)};
    min-width: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {BRAND_GOLD};
}}

QScrollBar::sub-page:horizontal {{
    background-color: transparent;
}}

QScrollBar::add-page:horizontal {{
    background-color: transparent;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    border: none;
    background: none;
}}

QStatusBar {{
    background-color: {translucent_rgba(APP_SURFACE_DARK, STATUS_BAR_ALPHA)};
    color: {APP_TEXT_DARK};
    border-top: 1px solid {APP_BORDER_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QStatusBar QLabel {{
    background-color: transparent;
    color: {APP_TEXT_DARK};
    padding: 2px 4px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QCheckBox {{
    color: {APP_TEXT_DARK};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    background-color: {translucent_rgba(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA)};
    border: 1px solid {APP_CONTROL_DIM};
}}

QCheckBox::indicator:checked {{
    background-color: {BRAND_GOLD};
    border-color: {BRAND_GOLD};
}}

QSplitter::handle {{
    background-color: {APP_BORDER_DARK};
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QComboBox {{
    background-color: {translucent_rgba(APP_SURFACE_DARK, COMBO_ALPHA)};
    color: {APP_TEXT_DARK};
    border: 1px solid {APP_BORDER_DARK};
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QComboBox:hover {{
    border-color: {BRAND_GOLD};
}}

QComboBox QAbstractItemView {{
    background-color: {translucent_rgba(APP_SURFACE_DARK, COMBO_ALPHA)};
    color: {APP_TEXT_DARK};
    selection-background-color: {BRAND_GOLD};
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {APP_BORDER_DARK};
    color: {BRAND_GOLD};
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {BRAND_GOLD};
    color: {TRUE_BLACK};
}}
"""

# Helper functions
def get_button_image_path(name: str, state: str) -> str:
    """Get the full path for a button image."""
    return os.path.join(BUTTON_IMAGES_DIR, f"{name}_{state}.png")

def get_background_image_path() -> str:
    """Get the full path for the background image."""
    return DEFAULT_BACKGROUND


def get_stylesheet(theme_manager: 'ThemeManager | None' = None, dark_mode: bool = False) -> str:
    """Get stylesheet for the given theme mode."""
    if theme_manager:
        if theme_manager.current_theme == 'dark':
            return DARK_STYLESHEET
        elif theme_manager.current_theme == 'light':
            return LIGHT_STYLESHEET
        elif theme_manager.current_theme == 'image':
            return IMAGE_STYLESHEET
    return DARK_STYLESHEET if dark_mode else LIGHT_STYLESHEET

def get_font_stylesheet() -> str:
    """Get a universal font stylesheet that can be applied to any widget."""
    return f"""
        * {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
        }}
        QWidget {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
            font-size: {FONT_SIZES["normal"]}px;
        }}
        QLabel {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
        }}
        QPushButton {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
            font-weight: bold;
        }}
        QLineEdit {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
        }}
        QComboBox {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
        }}
        QCheckBox {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
        }}
        QStatusBar {{
            font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
        }}
    """

def get_font_path() -> str:
    """Get the full path for the Montserrat font file."""
    return FONT_PATH


# Font Manager - Singleton for efficient font loading
class FontManager:
    """Singleton font manager for efficient one-time font loading."""
    _instance = None
    _font_loaded = False
    _font_id = -1
    _font_family = FONT_FAMILY
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def ensure_font_loaded(self) -> bool:
        """Load font once and cache the result."""
        if self._font_loaded:
            return True
        
        try:
            from PyQt6.QtGui import QFontDatabase
            from PyQt6.QtCore import QByteArray
            
            # Try embedded font first
            if EMBED_FONT and EMBEDDED_FONT_DATA:
                try:
                    font_bytes = base64.b64decode(EMBEDDED_FONT_DATA)
                    byte_array = QByteArray(font_bytes)
                    self._font_id = QFontDatabase.addApplicationFontFromData(byte_array)
                    
                    if self._font_id != -1:
                        logger.success("Font loaded from embedded data")
                        self._font_loaded = True
                        return True
                except Exception as e:
                    logger.error(f"Embedded font failed: {e}, trying file...")
            
            # Try font file
            if self._font_id == -1 and os.path.exists(FONT_PATH):
                self._font_id = QFontDatabase.addApplicationFont(FONT_PATH)
                if self._font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(self._font_id)
                    if font_families:
                        self._font_family = font_families[0]
                        logger.success(f"Font loaded from file: {FONT_PATH}")
                        self._font_loaded = True
                        return True
            
            logger.warning(" Custom font not available, using system font")
            return False
            
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            return False
    
    def get_font(self, size: int = None, bold: bool = False) -> 'QFont':
        """Get a QFont instance with the custom font family."""
        from PyQt6.QtGui import QFont
        
        self.ensure_font_loaded()
        
        if size is None:
            size = FONT_SIZES["normal"]
        
        font = QFont(self._font_family, size)
        font.setBold(bold)
        return font
    
    def apply_to_app(self, app: 'QApplication') -> None:
        """Apply font to entire application."""
        if self.ensure_font_loaded():
            app.setFont(self.get_font())
            logger.success(f"Applied font '{self._font_family}' to application")
    
    def get_family_name(self) -> str:
        """Get the actual loaded font family name."""
        return self._font_family


def apply_font_to_widget(widget: 'QWidget') -> None:
    """
    Apply font to a widget and all its children.
    
    Uses stylesheet instead of findChildren() loop.
    Qt automatically propagates stylesheets to child widgets.
    """
    try:
        # Use stylesheet for efficient font application
        font_style = f"font-family: '{FONT_FAMILY}'; font-size: {FONT_SIZES['normal']}px;"
        current_style = widget.styleSheet() or ""
        if font_style not in current_style:
            widget.setStyleSheet(f"* {{ {font_style} }} {current_style}")
                    
    except Exception as e:
        logger.error(f"Error applying font to widget: {e}")

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [RESOURCES_DIR, BUTTON_IMAGES_DIR, BACKGROUND_IMAGES_DIR, 
            os.path.join(RESOURCES_DIR, "fonts")]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

def get_app_info() -> dict:
    """Get application information."""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "description": "Professional Desktop Color Mixing Application",
        "author": "RNV Development",
        "framework": "PyQt6",
        "theme": "Color Picker Dark Theme"
    }

# PyQt6 specific constants
QT_WINDOW_FLAGS = None
QT_SIZE_POLICY_EXPANDING = 7
QT_SIZE_POLICY_PREFERRED = 5

# Application settings
APP_SETTINGS = {
    "geometry": {
        "width": 900,
        "height": 600,
        "min_width": 800,
        "min_height": 500
    },
    "ui": {
        "dark_mode": True,
        "show_tooltips": True,
        "auto_save": True
    },
    "colors": {
        "max_slots": MAX_SLOTS,
        "default_weight": DEFAULT_SAMPLE_WEIGHT,
        "mixing_algorithm": "weighted_rgb"
    }
}
