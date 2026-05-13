"""
Clipboard utilities for the Color Mixer application (PyQt6 version).
Handles copying and pasting of color values and other data.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QClipboard
from core.color_math import ColorMath

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("Clipboard")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False



class ClipboardUtils:
    """Utilities for clipboard operations (PyQt6 version)."""
    
    def __init__(self):
        self.app = QApplication.instance()
        if not self.app:
            raise RuntimeError("QApplication instance required")
    
    def copy_text(self, text: str) -> bool:
        """
        Copy text to clipboard.
        
        Args:
            text: Text to copy
            
        Returns:
            True if successful, False otherwise
        """
        try:
            clipboard = self.app.clipboard()
            clipboard.setText(text)
            return True
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return False
    
    def copy_hex_color(self, rgb: tuple[int, int, int]) -> bool:
        """
        Copy color as hex string to clipboard.
        
        Args:
            rgb: RGB color tuple
            
        Returns:
            True if successful, False otherwise
        """
        hex_color = ColorMath.rgb_to_hex(rgb)
        return self.copy_text(hex_color)
    
    def copy_rgb_color(self, rgb: tuple[int, int, int]) -> bool:
        """
        Copy color as RGB string to clipboard.
        
        Args:
            rgb: RGB color tuple
            
        Returns:
            True if successful, False otherwise
        """
        rgb_string = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
        return self.copy_text(rgb_string)
    
    def copy_hsv_color(self, rgb: tuple[int, int, int]) -> bool:
        """
        Copy color as HSV string to clipboard.
        
        Args:
            rgb: RGB color tuple
            
        Returns:
            True if successful, False otherwise
        """
        h, s, v = ColorMath.rgb_to_hsv(rgb)
        hsv_string = f"hsv({h*360:.1f}, {s*100:.1f}%, {v*100:.1f}%)"
        return self.copy_text(hsv_string)
    
    def copy_hsl_color(self, rgb: tuple[int, int, int]) -> bool:
        """
        Copy color as HSL string to clipboard.
        
        Args:
            rgb: RGB color tuple
            
        Returns:
            True if successful, False otherwise
        """
        h, l, s = ColorMath.rgb_to_hsl(rgb)
        hsl_string = f"hsl({h*360:.1f}, {s*100:.1f}%, {l*100:.1f}%)"
        return self.copy_text(hsl_string)
    
    def get_clipboard_text(self) -> str | None:
        """
        Get text from clipboard.
        
        Returns:
            Clipboard text or None if empty/error
        """
        try:
            clipboard = self.app.clipboard()
            text = clipboard.text()
            return text if text else None
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
            return None
    
    def try_parse_color_from_clipboard(self) -> tuple[int, int, int] | None:
        """
        Try to parse a color from clipboard text.
        Supports hex, rgb(), hsv(), hsl() formats.
        
        Returns:
            RGB color tuple or None if no valid color found
        """
        text = self.get_clipboard_text()
        if not text:
            return None
            
        text = text.strip()
        
        # Try hex format
        if text.startswith('#') and len(text) in [4, 7]:
            try:
                return ColorMath.hex_to_rgb(text)
            except Exception:
                # Not a valid hex color — try the next supported format
                pass
        
        # Try rgb() format
        if text.startswith('rgb(') and text.endswith(')'):
            try:
                values = text[4:-1].split(',')
                if len(values) == 3:
                    r, g, b = [int(v.strip()) for v in values]
                    return ColorMath.validate_rgb((r, g, b))
            except Exception:
                # Not a valid rgb() string — try the next supported format
                pass
        
        # Try hsv() format
        if text.startswith('hsv(') and text.endswith(')'):
            try:
                values = text[4:-1].split(',')
                if len(values) == 3:
                    h = float(values[0].strip()) / 360.0
                    s = float(values[1].strip().rstrip('%')) / 100.0
                    v = float(values[2].strip().rstrip('%')) / 100.0
                    return ColorMath.hsv_to_rgb((h, s, v))
            except Exception:
                # Not a valid hsv() string — try the next supported format
                pass
        
        # Try hsl() format
        if text.startswith('hsl(') and text.endswith(')'):
            try:
                values = text[4:-1].split(',')
                if len(values) == 3:
                    h = float(values[0].strip()) / 360.0
                    s = float(values[1].strip().rstrip('%')) / 100.0
                    l = float(values[2].strip().rstrip('%')) / 100.0
                    return ColorMath.hsl_to_rgb((h, s, l))
            except Exception:
                # Not a valid hsl() string — fall through, no format matched
                pass
        
        return None
    
    def copy_color_palette(self, colors: list[tuple[tuple[int, int, int], int]]) -> bool:
        """
        Copy a list of colors as formatted text.
        
        Args:
            colors: List of (color, weight) tuples
            
        Returns:
            True if successful, False otherwise
        """
        try:
            lines = []
            lines.append("Color Palette:")
            lines.append("-" * 20)
            
            for i, (color, weight) in enumerate(colors, 1):
                hex_color = ColorMath.rgb_to_hex(color)
                lines.append(f"{i:2d}. {hex_color} rgb{color} (weight: {weight})")
            
            palette_text = '\n'.join(lines)
            return self.copy_text(palette_text)
        except Exception as e:
            logger.error(f"Error copying palette: {e}")
            return False
    
    def clear_clipboard(self) -> bool:
        """
        Clear the clipboard.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            clipboard = self.app.clipboard()
            clipboard.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")
            return False
    
    def has_text(self) -> bool:
        """
        Check if clipboard contains text.
        
        Returns:
            True if clipboard contains text
        """
        try:
            clipboard = self.app.clipboard()
            mime_data = clipboard.mimeData()
            return mime_data.hasText() if mime_data else False
        except Exception:
            # Clipboard access can fail on platform or permission issues — treat as empty
            return False
    
    def has_image(self) -> bool:
        """
        Check if clipboard contains image data.
        
        Returns:
            True if clipboard contains image data
        """
        try:
            clipboard = self.app.clipboard()
            mime_data = clipboard.mimeData()
            return mime_data.hasImage() if mime_data else False
        except Exception:
            # Clipboard access can fail on platform or permission issues — treat as empty
            return False
    
    def copy_color_as_css(self, rgb: tuple[int, int, int], variable_name: str = "primary-color") -> bool:
        """
        Copy color as CSS variable.
        
        Args:
            rgb: RGB color tuple
            variable_name: CSS variable name
            
        Returns:
            True if successful, False otherwise
        """
        hex_color = ColorMath.rgb_to_hex(rgb)
        css_text = f"--{variable_name}: {hex_color};"
        return self.copy_text(css_text)
    
    def copy_multiple_formats(self, rgb: tuple[int, int, int]) -> bool:
        """
        Copy color in multiple formats (hex, rgb, hsl, hsv).
        
        Args:
            rgb: RGB color tuple
            
        Returns:
            True if successful, False otherwise
        """
        try:
            hex_color = ColorMath.rgb_to_hex(rgb)
            rgb_string = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
            
            h, s, v = ColorMath.rgb_to_hsv(rgb)
            hsv_string = f"hsv({h*360:.1f}, {s*100:.1f}%, {v*100:.1f}%)"
            
            h, l, s = ColorMath.rgb_to_hsl(rgb)
            hsl_string = f"hsl({h*360:.1f}, {s*100:.1f}%, {l*100:.1f}%)"
            
            multi_format = f"""Color Formats:
HEX: {hex_color}
RGB: {rgb_string}
HSV: {hsv_string}
HSL: {hsl_string}"""
            
            return self.copy_text(multi_format)
        except Exception as e:
            logger.error(f"Error copying multiple formats: {e}")
            return False