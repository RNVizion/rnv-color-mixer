"""
Configuration for the RNV Color Mixer application (PyQt6).

Central source of truth for application identity (VERSION, APP_NAME),
window and widget dimensions, file paths, font management, and the
ThemeManager system supporting Dark, Light, and Image modes with
cached QPalette objects for fast theme switching.
"""

import os
import base64
from typing import TYPE_CHECKING, Any

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
DEFAULT_COLOR = (200, 200, 200)
DEFAULT_WEIGHT = 0
DEFAULT_SAMPLE_WEIGHT = 50

# Initial state — the color shown before the user mixes anything.
# Centralised here so a single change updates preview swatch, hex label,
# rgb label, and any other display that starts at "no color yet".
INITIAL_COLOR_TUPLE = (0, 0, 0)
INITIAL_COLOR_HEX   = "#000000"
INITIAL_COLOR_RGB   = "rgb(0,0,0)"

# Debug overlay colors — diagnostic identifiers for the F12 overlay system.
# Red = main app window overlay, Blue = slots panel overlay.
# Centralised so both creation sites (toggle function + settings apply) stay in sync.
DEBUG_OVERLAY_COLORS = {
    'app_window':  'rgba(255, 80, 80, 220)',
    'slots_panel': 'rgba(80, 80, 255, 220)',
}

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
    
    DARK_THEME = {
        'name': 'Dark',
        'window_bg': '#000000',
        'text_color': '#E0E0E0',
        'border_color': '#333333',
        'hover_color': '#444444',
        'button_bg': '#1A1A1A',
        'button_text': '#E0E0E0',
        'button_hover_bg': '#333333',
        'button_pressed_bg': '#d2bc93',
        'button_pressed_text': '#000000',
        'button_pressed_border': '#d2bc93',
        'checkbox_bg': 'rgba(26, 26, 26, 230)',
        'checkbox_border': '#333333',
        'canvas_bg': '#0A0A0A',
        'scroll_area_bg': '#000000',
        'input_bg': '#1A1A1A',
        'input_text': '#E0E0E0',
        'slot_border': '#E0E0E0',
        'slot_border_width': 2,
        'label_bg': '#1A1A1A',
        'label_border': '#333333',
        'tooltip_bg': '#2A2A2A',
        'tooltip_border': '#d2bc93',
        'text_disabled': '#555555',
        'accent': '#d2bc93',
        'accent_hover': '#dcc9a3',
        'accent_on': '#000000',
        'panel_bg': '#1A1A1A',
        'panel_secondary': '#2A2A2A',
        'panel_hover': '#3A3A3A',
        'tab_selected_bg': '#0A0A0A',
        'scrollbar_bg': '#1A1A1A',
        'scrollbar_handle': '#333333',
        'scrollbar_hover': '#d2bc93',
        'slider_handle': '#E0E0E0',
        'text_hint': '#888888',
        'menu_disabled': '#666666',
    }
    
    LIGHT_THEME = {
        'name': 'Light',
        'window_bg': '#F5F5F5',
        'text_color': '#000000',
        'border_color': '#CCCCCC',
        'hover_color': '#E0E0E0',
        'button_bg': '#FFFFFF',
        'button_text': '#000000',
        'button_hover_bg': '#333333',
        'button_pressed_bg': '#b19145',
        'button_pressed_text': '#FFFFFF',
        'button_pressed_border': '#b19145',
        'checkbox_bg': 'rgba(255, 255, 255, 200)',
        'checkbox_border': 'gray',
        'canvas_bg': '#FFFFFF',
        'scroll_area_bg': '#FFFFFF',
        'input_bg': '#FFFFFF',
        'input_text': '#000000',
        'slot_border': '#000000',
        'slot_border_width': 1,
        'label_bg': 'white',
        'label_border': 'black',
        'tooltip_bg': '#FFFFFF',
        'tooltip_border': '#b19145',
        'text_disabled': '#AAAAAA',
        'accent': '#b19145',
        'accent_hover': '#c4a458',
        'accent_on': '#FFFFFF',
        'panel_bg': '#F5F5F5',
        'panel_secondary': '#FFFFFF',
        'panel_hover': '#EEEEEE',
        'tab_selected_bg': '#FFFFFF',
        'scrollbar_bg': '#F5F5F5',
        'scrollbar_handle': '#CCCCCC',
        'scrollbar_hover': '#b19145',
        'slider_handle': '#666666',
        'text_hint': '#888888',
        'menu_disabled': '#999999',
    }
    
    # NEW: Image Theme - Copy of Dark Theme for Image Mode
    IMAGE_THEME = {
        'name': 'Image',
        'window_bg': '#000000',
        'text_color': '#E0E0E0',
        'border_color': '#333333',
        'hover_color': '#444444',
        'button_bg': '#1A1A1A',
        'button_text': '#E0E0E0',
        'button_hover_bg': '#333333',
        'button_pressed_bg': '#d2bc93',
        'button_pressed_text': '#000000',
        'button_pressed_border': '#d2bc93',
        'checkbox_bg': 'rgba(26, 26, 26, 230)',
        'checkbox_border': '#333333',
        'canvas_bg': '#0A0A0A',
        'scroll_area_bg': '#000000',
        'input_bg': '#1A1A1A',
        'input_text': '#E0E0E0',
        'slot_border': '#E0E0E0',
        'slot_border_width': 2,
        'label_bg': '#1A1A1A',
        'label_border': '#333333',
        'tooltip_bg': '#2A2A2A',
        'tooltip_border': '#d2bc93',
        'text_disabled': '#555555',
        'accent': '#d2bc93',
        'accent_hover': '#dcc9a3',
        'accent_on': '#000000',
        'panel_bg': '#1A1A1A',
        'panel_secondary': '#2A2A2A',
        'panel_hover': '#3A3A3A',
        'tab_selected_bg': '#0A0A0A',
        'scrollbar_bg': '#1A1A1A',
        'scrollbar_handle': '#333333',
        'scrollbar_hover': '#d2bc93',
        'slider_handle': '#E0E0E0',
        'text_hint': '#888888',
        'menu_disabled': '#666666',
    }
    
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

# Legacy color dictionaries (for backward compatibility)
DARK_THEME_LEGACY = ThemeManager.DARK_THEME
LIGHT_THEME_LEGACY = ThemeManager.LIGHT_THEME

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
    background-color: #000000;
    color: #E0E0E0;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QWidget {{
    background-color: #000000;
    color: #E0E0E0;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton {{
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 2px;
    border-radius: 4px;
    font-weight: bold;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton:hover {{
    background-color: #333333;
    border-color: #333333;
}}

QPushButton:pressed {{
    background-color: #444444;
    color: #000000;
    border-color: #333333;
}}

QLineEdit {{
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
    min-height: 16px;
    selection-background-color: #d2bc93;
    selection-color: #000000;
}}

QLineEdit:focus {{
    border-color: #d2bc93;
}}

QLabel {{
    color: #E0E0E0;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QSlider::groove:horizontal {{
    border: 1px solid #333333;
    height: 8px;
    background: #1A1A1A;
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: #E0E0E0;
    border: 1px solid #333333;
    width: 18px;
    border-radius: 9px;
    margin: -5px 0;
}}

QSlider::handle:horizontal:hover {{
    background: #F0F0F0;
}}

QScrollArea {{
    background-color: #000000;
    border: 1px solid #333333;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 15px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: rgba(51, 51, 51, 0.7);
    min-height: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: rgba(68, 68, 68, 0.9);
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
    background-color: rgba(51, 51, 51, 0.7);
    min-width: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: rgba(68, 68, 68, 0.9);
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
    background-color: #1A1A1A;
    color: #E0E0E0;
    border-top: 1px solid #333333;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QStatusBar QLabel {{
    background-color: #1A1A1A;
    color: #E0E0E0;
    padding: 2px 4px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QCheckBox {{
    color: #E0E0E0;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    background-color: #1A1A1A;
    border: 1px solid #333333;
}}

QCheckBox::indicator:checked {{
    background-color: #d2bc93;
    border-color: #d2bc93;
}}

QSplitter::handle {{
    background-color: #333333;
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QComboBox {{
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QComboBox:hover {{
    border-color: #d2bc93;
}}

QComboBox QAbstractItemView {{
    background-color: #1A1A1A;
    color: #E0E0E0;
    selection-background-color: #d2bc93;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: #333333;
    color: #d2bc93;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: #d2bc93;
    color: #000000;
}}
"""

LIGHT_STYLESHEET = f"""
QMainWindow {{
    background-color: #F5F5F5;
    color: #000000;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QWidget {{
    background-color: #F5F5F5;
    color: #000000;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton {{
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    padding: 2px;
    border-radius: 4px;
    font-weight: bold;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton:hover {{
    background-color: #333333;
    border-color: #CCCCCC;
}}

QPushButton:pressed {{
    background-color: #444444;
    color: #FFFFFF;
    border-color: #CCCCCC;
}}

QLineEdit {{
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
    min-height: 16px;
    selection-background-color: #b19145;
    selection-color: #FFFFFF;
}}

QLineEdit:focus {{
    border-color: #b19145;
}}

QLabel {{
    color: #000000;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QSlider::groove:horizontal {{
    border: 1px solid #CCCCCC;
    height: 8px;
    background: #FFFFFF;
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: #666666;
    border: 1px solid #999999;
    width: 18px;
    border-radius: 9px;
    margin: -5px 0;
}}

QSlider::handle:horizontal:hover {{
    background: #555555;
}}

QScrollArea {{
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QScrollBar:vertical {{
    background-color: #F5F5F5;
    width: 15px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: #CCCCCC;
    min-height: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #999999;
}}

QScrollBar::sub-page:vertical {{
    background-color: #F5F5F5;
}}

QScrollBar::add-page:vertical {{
    background-color: #F5F5F5;
}}

QScrollBar:horizontal {{
    background-color: #F5F5F5;
    height: 15px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: #CCCCCC;
    min-width: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #999999;
}}

QScrollBar::sub-page:horizontal {{
    background-color: #F5F5F5;
}}

QScrollBar::add-page:horizontal {{
    background-color: #F5F5F5;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    border: none;
    background: none;
}}

QStatusBar {{
    background-color: #F5F5F5;
    color: #000000;
    border-top: 1px solid #CCCCCC;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QStatusBar QLabel {{
    background-color: #F5F5F5;
    color: #000000;
    padding: 2px 4px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QCheckBox {{
    color: #000000;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
}}

QCheckBox::indicator:checked {{
    background-color: #b19145;
    border-color: #b19145;
}}

QSplitter::handle {{
    background-color: #CCCCCC;
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QComboBox {{
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QComboBox:hover {{
    border-color: #b19145;
}}

QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    color: #000000;
    selection-background-color: #b19145;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: #EEEEEE;
    color: #b19145;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: #b19145;
    color: #FFFFFF;
}}
"""

# NEW: Image Mode Stylesheet (modified from Dark theme to allow background image)
IMAGE_STYLESHEET = f"""
QMainWindow {{
    color: #E0E0E0;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QMainWindow > QWidget {{
    background-color: transparent;
}}

QWidget {{
    background-color: transparent;
    color: #E0E0E0;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QFrame, QScrollArea, QLabel {{
    background-color: transparent;
}}

QPushButton {{
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 2px;
    border-radius: 4px;
    font-weight: bold;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QPushButton:hover {{
    background-color: #333333;
    border-color: #333333;
}}

QPushButton:pressed {{
    background-color: #444444;
    color: #000000;
    border-color: #333333;
}}

QLineEdit {{
    background-color: rgba(0, 0, 0, 171);
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
    min-height: 16px;
    selection-background-color: #d2bc93;
    selection-color: #000000;
}}

QLineEdit:focus {{
    border-color: #d2bc93;
}}

QLabel {{
    color: #E0E0E0;
    background-color: transparent;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QSlider::groove:horizontal {{
    border: 1px solid #333333;
    height: 8px;
    background: #1A1A1A;
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: #E0E0E0;
    border: 1px solid #333333;
    width: 18px;
    border-radius: 9px;
    margin: -5px 0;
}}

QSlider::handle:horizontal:hover {{
    background: #F0F0F0;
}}

QScrollArea {{
    background-color: transparent;
    border: 1px solid rgba(51, 51, 51, 100);
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
    background-color: rgba(51, 51, 51, 100);
    width: 15px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: rgba(80, 80, 80, 150);
    min-height: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: rgba(100, 100, 100, 200);
}}

QScrollBar::sub-page:vertical {{
    background-color: transparent;
}}

QScrollBar::add-page:vertical {{
    background-color: transparent;
}}

QScrollBar:horizontal {{
    background-color: rgba(51, 51, 51, 100);
    height: 15px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: rgba(80, 80, 80, 150);
    min-width: 20px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: rgba(100, 100, 100, 200);
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
    background-color: rgba(26, 26, 26, 200);
    color: #E0E0E0;
    border-top: 1px solid #333333;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QStatusBar QLabel {{
    background-color: transparent;
    color: #E0E0E0;
    padding: 2px 4px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["small"]}px;
}}

QCheckBox {{
    color: #E0E0E0;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    background-color: rgba(0, 0, 0, 100);
    border: 1px solid #555555;
}}

QCheckBox::indicator:checked {{
    background-color: #d2bc93;
    border-color: #d2bc93;
}}

QSplitter::handle {{
    background-color: #333333;
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QComboBox {{
    background-color: rgba(26, 26, 26, 191);
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 4px;
    border-radius: 3px;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
    font-size: {FONT_SIZES["normal"]}px;
}}

QComboBox:hover {{
    border-color: #d2bc93;
}}

QComboBox QAbstractItemView {{
    background-color: rgba(26, 26, 26, 191);
    color: #E0E0E0;
    selection-background-color: #d2bc93;
    font-family: "{FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: #333333;
    color: #d2bc93;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: #d2bc93;
    color: #000000;
}}
"""

# Helper functions
def get_button_image_path(name: str, state: str) -> str:
    """Get the full path for a button image."""
    return os.path.join(BUTTON_IMAGES_DIR, f"{name}_{state}.png")

def get_background_image_path() -> str:
    """Get the full path for the background image."""
    return DEFAULT_BACKGROUND

def get_theme_colors(theme_manager: 'ThemeManager | None' = None, dark_mode: bool = False) -> 'dict[str, Any]':
    """Get theme colors based on mode or theme manager."""
    if theme_manager:
        current = theme_manager.get_current_theme()
        if current:
            return current
    return DARK_THEME_LEGACY if dark_mode else LIGHT_THEME_LEGACY

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