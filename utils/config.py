"""
Configuration for the RNV Color Mixer application (PyQt6).

Central source of truth for application identity (VERSION, APP_NAME),
window and widget dimensions, file paths, font management, and the
ThemeManager system supporting Dark, Light, and Image modes with
cached QPalette objects for fast theme switching.
"""

import os
import base64
from typing import TYPE_CHECKING, Any, Final

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

# ---------------------------------------------------------------- brand gold
# Mirrored from RNVizion/rnv-brand engine/brand.py. Do not hand-write a gold
# here: derive it, so that a change to the base carries.
#
# The register holds TWO golds and derives the rest. Each mode renders the
# registered gold plus ONE derivative:
#
#   light   BRAND_DARK_GOLD          fills, borders, pressed
#           BRAND_DARK_GOLD_DEEP     text, and hover (which moves DEEPER on a
#                                    light ground -- away from it, not toward)
#   dark    BRAND_GOLD               fills, borders, pressed, text
#           BRAND_GOLD_HOVER         hover (lighter, again away from the ground)
#
# Pressed returns to the accent in both modes. On light that is forced -- no
# darker pressed shade keeps black legible on it. On dark the register records
# the question as OPEN and permits either; this app takes the accent, which is
# what holds the count at two and matches rnv-color-picker and
# rnv-text-transformer.
#
# COVERAGE BOUNDARY: BRAND_DARK_GOLD_DEEP carries text down to #e8e8e8 and no
# further. Below that, gold does not carry text -- a ruling, not a gap. Going
# darker does not help: -29 clears #d0d0d0 and then fails black-on-fill at
# 3.0219, the same exclusion one step down.


def _to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def lighten(hex_color: str, step: int) -> str:
    """Shift every channel by the same number of 8-bit steps.

    Uniform per-channel, which holds hue exactly -- BRAND_DARK_GOLD and its
    derivative both measure 42.4 degrees. Non-uniform steps do not, which is
    why the hand-written variants this replaces all drifted in hue.
    """
    r, g, b = _to_rgb(hex_color)
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, c + step)) for c in (r, g, b))


BRAND_GOLD: Final[str] = "#d2bc93"                       # registered
BRAND_DARK_GOLD: Final[str] = "#8c7337"             # registered

# Derived. Steps published in rnv-brand engine/brand.py, rev 17.
BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)   # #7e6529
BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)             # #dfc9a0

# Aliases. Named so every rendered hex has a key, even where it repeats.
BRAND_DARK_GOLD_HOVER: Final[str] = BRAND_DARK_GOLD_DEEP
BRAND_DARK_GOLD_PRESSED: Final[str] = BRAND_DARK_GOLD
BRAND_GOLD_PRESSED: Final[str] = BRAND_GOLD

BRAND_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_GOLD)
BRAND_DARK_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_DARK_GOLD)

# Declarative provenance, read by tests/test_brand_mirror.py. A classification
# that lives only in a test drifts from the thing it classifies.
GOLD_PROVENANCE: Final[dict[str, str]] = {
    "BRAND_GOLD": "register",
    "BRAND_DARK_GOLD": "register",
    "BRAND_DARK_GOLD_DEEP": "derived",
    "BRAND_GOLD_HOVER": "derived",
    "BRAND_DARK_GOLD_HOVER": "alias",
    "BRAND_DARK_GOLD_PRESSED": "alias",
    "BRAND_GOLD_PRESSED": "alias",
}

# ==================== APP NEUTRALS ====================
#
# WHY THESE EXIST. The three stylesheet templates below used to carry 120 hex
# literals -- 40 dark, 50 light, 30 image -- while the golds twenty lines up
# were already interpolated from constants. A literal cannot follow its base:
# move a value here and the templates keep the old one, silently, with nothing
# to report it. Every rendered hex now has a key, which is the same rule the
# gold aliases above were written for.
#
# NAMED BY ROLE, NOT BY BYTE. A step is named for the job it does, and where
# one value does two jobs the comment says both rather than minting a second
# constant. The one exception is APP_BTN_HOVER_INVERSE, which is assigned FROM
# its base rather than repeating the value, so the two move together.
#
# THIS IS A REWIRE, NOT A RETUNE. Every value below is exactly what the
# templates already rendered. tests/test_snapshots.py compares the three
# stylesheets byte-for-byte against frozen references; if those pass without
# regeneration, nothing moved.

TRUE_BLACK: Final[str] = "#000000"
"""Window and scroll-area ground in dark; primary text in light; the label on
a pressed control in dark; the selection foreground in every mode."""

WHITE: Final[str] = "#ffffff"
"""Control surface in light -- button, input, combo, scroll area -- and the
label on a pressed control in light."""

# ---- dark and image ----
APP_SURFACE_DARK: Final[str] = "#1a1a1a"
"""Control surface in dark and image: button, input, combo, status bar, and
the slider groove."""

APP_BORDER_DARK: Final[str] = "#333333"
"""Every border in dark and image. Also the hover ground and the splitter
handle -- in dark the hover fill deliberately equals the border step, so a
hovered control reads as its own outline filling in."""

APP_TEXT_DARK: Final[str] = "#dddddd"
"""Primary text in dark and image. Also the slider handle, which takes the
brightest step in the ramp rather than a colour of its own."""

APP_HANDLE_HOVER_DARK: Final[str] = "#eeeeee"
"""Slider handle when hovered, dark and image. One step above the
text: grey(14), where APP_TEXT_DARK is grey(13), on the published
ink grid. Held #f0f0f0 until 2026-08-28, when the gap to #e0e0e0 was
0x10 -- the surface ladder step, not the grid step -- and the
sentence was true by accident."""

# ---- light ----
APP_WINDOW_LIGHT: Final[str] = "#f5f5f5"
"""Window ground in light, the status bar, and the scrollbar track."""

APP_BORDER_LIGHT: Final[str] = "#cccccc"
"""Every border in light. Also the scrollbar handle at rest and the splitter
handle, on the same reasoning as APP_BORDER_DARK."""

APP_ITEM_HOVER_LIGHT: Final[str] = "#eeeeee"
"""Combo-box item under the cursor, light. The list hover, not the button
hover -- those are different schemes, see APP_BTN_HOVER_INVERSE."""

APP_HANDLE_LIGHT: Final[str] = "#666666"
"""Slider handle at rest, light."""

APP_HANDLE_EDGE_LIGHT: Final[str] = "#999999"
"""The emphasised edge of a light handle: the slider handle's border, and the
scrollbar handle when hovered."""

APP_CONTROL_DIM: Final[str] = "#555555"
"""Two unrelated jobs on one step: the light slider handle when hovered, and
the image-mode checkbox indicator border. Worth knowing that dark mode draws
that same checkbox border with APP_BORDER_DARK while rnv-color-picker and
rnv-icon-builder use this step in both -- an inconsistency this pass records
and does not change, because nothing here may move a pixel."""

# ---- the inverse button scheme, both modes ----
APP_BTN_HOVER_INVERSE: Final[str] = APP_BORDER_DARK
"""The basic button's hover ground. Light mode borrows the dark step on
purpose: the scheme inverts on hover, and the label stays put. Assigned from
APP_BORDER_DARK rather than repeating the value so the two cannot drift
apart."""

APP_BTN_PRESSED: Final[str] = "#444444"
"""The basic button's pressed fill, identical in all three modes. The label
flips instead -- TRUE_BLACK on dark, WHITE on light."""

# Declarative provenance, read by tests/test_neutral_ramp.py, in the same
# shape as GOLD_PROVENANCE above. A classification that lives only in a test
# drifts from the thing it classifies.
NEUTRAL_PROVENANCE: Final[dict[str, str]] = {
    "TRUE_BLACK": "anchor",
    "WHITE": "anchor",
    "APP_SURFACE_DARK": "step",
    "APP_BORDER_DARK": "step",
    "APP_TEXT_DARK": "step",
    "APP_HANDLE_HOVER_DARK": "step",
    "APP_WINDOW_LIGHT": "step",
    "APP_BORDER_LIGHT": "step",
    "APP_ITEM_HOVER_LIGHT": "step",
    "APP_HANDLE_LIGHT": "step",
    "APP_HANDLE_EDGE_LIGHT": "step",
    "APP_CONTROL_DIM": "step",
    "APP_BTN_PRESSED": "step",
    "APP_BTN_HOVER_INVERSE": "alias",
}


class ThemeManager:
    """Manages application themes with Dark Mode, Light Mode, and Image Mode"""
    
    DARK_THEME = {
        'name': 'Dark',
        'window_bg': '#000000',
        'text_color': APP_TEXT_DARK,
        'border_color': '#333333',
        'hover_color': '#444444',
        'button_bg': '#1a1a1a',
        'button_text': APP_TEXT_DARK,
        'button_hover_bg': '#333333',
        'button_pressed_bg': BRAND_GOLD_PRESSED,
        'button_pressed_text': '#000000',
        'button_pressed_border': BRAND_GOLD,
        'checkbox_bg': 'rgba(26, 26, 26, 230)',
        'checkbox_border': '#333333',
        'canvas_bg': '#0a0a0a',
        'scroll_area_bg': '#000000',
        'input_bg': '#1a1a1a',
        'input_text': APP_TEXT_DARK,
        'slot_border': APP_TEXT_DARK,
        'slot_border_width': 2,
        'label_bg': '#1a1a1a',
        'label_border': '#333333',
        'tooltip_bg': '#2a2a2a',
        'tooltip_border': BRAND_GOLD,
        'text_disabled': '#555555',
        'accent': BRAND_GOLD,
        'accent_ink': BRAND_GOLD,
        'accent_hover': BRAND_GOLD_HOVER,
        'accent_text': '#000000',
        'panel_bg': '#1a1a1a',
        'panel_secondary': '#2a2a2a',
        'panel_hover': '#3a3a3a',
        'tab_selected_bg': '#0a0a0a',
        'scrollbar_bg': '#1a1a1a',
        'scrollbar_handle': '#333333',
        'scrollbar_hover': BRAND_GOLD,
        'slider_handle': APP_TEXT_DARK,
        'text_hint': '#888888',
        'menu_disabled': '#666666',
    }
    
    LIGHT_THEME = {
        'name': 'Light',
        'window_bg': '#f5f5f5',
        'text_color': '#000000',
        'border_color': '#cccccc',
        'hover_color': '#e0e0e0',
        'button_bg': '#ffffff',
        'button_text': '#000000',
        'button_hover_bg': '#333333',
        'button_pressed_bg': BRAND_DARK_GOLD_PRESSED,
        'button_pressed_text': '#ffffff',
        'button_pressed_border': BRAND_DARK_GOLD,
        'checkbox_bg': 'rgba(255, 255, 255, 200)',
        'checkbox_border': 'gray',
        'canvas_bg': '#ffffff',
        'scroll_area_bg': '#ffffff',
        'input_bg': '#ffffff',
        'input_text': '#000000',
        'slot_border': '#000000',
        'slot_border_width': 1,
        'label_bg': 'white',
        'label_border': 'black',
        'tooltip_bg': '#ffffff',
        'tooltip_border': BRAND_DARK_GOLD,
        'text_disabled': '#aaaaaa',
        'accent': BRAND_DARK_GOLD,
        'accent_ink': BRAND_DARK_GOLD_DEEP,
        'accent_hover': BRAND_DARK_GOLD_HOVER,
        'accent_text': '#ffffff',
        'panel_bg': '#f5f5f5',
        'panel_secondary': '#ffffff',
        'panel_hover': '#eeeeee',
        'tab_selected_bg': '#ffffff',
        'scrollbar_bg': '#f5f5f5',
        'scrollbar_handle': '#cccccc',
        'scrollbar_hover': BRAND_DARK_GOLD,
        'slider_handle': '#666666',
        # The 10px hint under each fine-tune slider is the only consumer, and
        # it sits on the QFrame that section builds -- panel_secondary, not
        # panel_bg. #888888 read 3.5407:1 there, below AA for text this
        # size. #666666 clears 4.5 on every light ground in this app.
        'text_hint': '#666666',
        'menu_disabled': '#999999',
    }
    
    # NEW: Image Theme - Copy of Dark Theme for Image Mode
    IMAGE_THEME = {
        'name': 'Image',
        'window_bg': '#000000',
        'text_color': APP_TEXT_DARK,
        'border_color': '#333333',
        'hover_color': '#444444',
        'button_bg': '#1a1a1a',
        'button_text': APP_TEXT_DARK,
        'button_hover_bg': '#333333',
        'button_pressed_bg': BRAND_GOLD_PRESSED,
        'button_pressed_text': '#000000',
        'button_pressed_border': BRAND_GOLD,
        'checkbox_bg': 'rgba(26, 26, 26, 230)',
        'checkbox_border': '#333333',
        'canvas_bg': '#0a0a0a',
        'scroll_area_bg': '#000000',
        'input_bg': '#1a1a1a',
        'input_text': APP_TEXT_DARK,
        'slot_border': APP_TEXT_DARK,
        'slot_border_width': 2,
        'label_bg': '#1a1a1a',
        'label_border': '#333333',
        'tooltip_bg': '#2a2a2a',
        'tooltip_border': BRAND_GOLD,
        'text_disabled': '#555555',
        'accent': BRAND_GOLD,
        'accent_ink': BRAND_GOLD,
        'accent_hover': BRAND_GOLD_HOVER,
        'accent_text': '#000000',
        'panel_bg': '#1a1a1a',
        'panel_secondary': '#2a2a2a',
        'panel_hover': '#3a3a3a',
        'tab_selected_bg': '#0a0a0a',
        'scrollbar_bg': '#1a1a1a',
        'scrollbar_handle': '#333333',
        'scrollbar_hover': BRAND_GOLD,
        'slider_handle': APP_TEXT_DARK,
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
    background: {APP_HANDLE_HOVER_DARK};
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
    background: {APP_CONTROL_DIM};
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
    background-color: {APP_HANDLE_EDGE_LIGHT};
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
    background-color: {APP_HANDLE_EDGE_LIGHT};
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
    background-color: rgba(0, 0, 0, 171);
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
    background: {APP_HANDLE_HOVER_DARK};
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
    background-color: rgba(0, 0, 0, 100);
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
    background-color: rgba(26, 26, 26, 191);
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
    background-color: rgba(26, 26, 26, 191);
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