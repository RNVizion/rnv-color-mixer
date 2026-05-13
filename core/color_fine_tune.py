"""
Color Fine-Tune Dialog - Right-click context menu for color adjustments
Provides sliders for:
- Lighten / Darken
- Saturate / Desaturate  
- Hue shift
- Temperature (warm/cool)
- Tint / Shade generator
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QGridLayout, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap, QPainter, QBrush, QPen
import colorsys

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("ColorFineTune")
except ImportError:
    logger = None

# Import config
try:
    from utils import config
except ImportError:
    config = None

# Import ColorMath
try:
    from core.color_math import ColorMath
except ImportError:
    ColorMath = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False


class ColorFineTuneDialog(QDialog):
    """Dialog for fine-tuning color properties with sliders."""
    
    # Signal emitted when color is applied
    color_applied = pyqtSignal(tuple)  # (r, g, b)
    
    def __init__(self, parent: QWidget | None = None, original_color: tuple[int, int, int] = (200, 200, 200), is_dark: bool = True) -> None:
        super().__init__(parent)
        
        self.original_color = original_color
        self.current_color = original_color
        self._is_dark = is_dark
        
        # Store adjustment values (all start at neutral)
        self._adjustments = {
            'lighten': 0,      # -100 to 100 (negative = darken)
            'saturate': 0,     # -100 to 100 (negative = desaturate)
            'hue_shift': 0,    # -180 to 180 degrees
            'temperature': 0,  # -100 to 100 (negative = cool, positive = warm)
            'tint_shade': 0,   # -100 to 100 (negative = shade, positive = tint)
        }
        
        self.setWindowTitle("Fine-Tune Color")
        self.setModal(True)
        self.setMinimumSize(400, 480)
        self.setMaximumSize(500, 600)
        self.resize(420, 520)
        
        self._build_ui()
        self._apply_theme()
        self._update_preview()
        
        if logger:
            logger.success("Color Fine-Tune dialog initialized")
    
    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Color preview section
        preview_frame = self._create_preview_section()
        layout.addWidget(preview_frame)
        
        # Adjustment sliders
        sliders_frame = self._create_sliders_section()
        layout.addWidget(sliders_frame)
        
        # Buttons
        button_layout = self._create_buttons()
        layout.addLayout(button_layout)
    
    def _create_preview_section(self) -> QFrame:
        """Create the color preview section with original and adjusted colors."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # Original color
        original_container = QVBoxLayout()
        original_label = QLabel("Original")
        original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        original_label.setStyleSheet("font-weight: bold;")
        original_container.addWidget(original_label)
        
        self.original_preview = QLabel()
        self.original_preview.setFixedSize(80, 80)
        self.original_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        original_container.addWidget(self.original_preview, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.original_hex_label = QLabel()
        self.original_hex_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        original_container.addWidget(self.original_hex_label)
        
        layout.addLayout(original_container)
        
        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(arrow_label)
        
        # Adjusted color
        adjusted_container = QVBoxLayout()
        adjusted_label = QLabel("Adjusted")
        adjusted_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        adjusted_label.setStyleSheet("font-weight: bold;")
        adjusted_container.addWidget(adjusted_label)
        
        self.adjusted_preview = QLabel()
        self.adjusted_preview.setFixedSize(80, 80)
        self.adjusted_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        adjusted_container.addWidget(self.adjusted_preview, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.adjusted_hex_label = QLabel()
        self.adjusted_hex_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        adjusted_container.addWidget(self.adjusted_hex_label)
        
        layout.addLayout(adjusted_container)
        
        return frame
    
    def _create_sliders_section(self) -> QFrame:
        """Create the adjustment sliders section."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Adjustments")
        _t = config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME
        title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {_t['accent']};")
        layout.addWidget(title)
        
        # Create each slider
        sliders_data = [
            ("Lighten / Darken", "lighten", -100, 100, 0, "← Darken | Lighten →"),
            ("Saturate / Desaturate", "saturate", -100, 100, 0, "← Desaturate | Saturate →"),
            ("Hue Shift", "hue_shift", -180, 180, 0, "← Shift Left | Shift Right →"),
            ("Temperature", "temperature", -100, 100, 0, "← Cool | Warm →"),
            ("Tint / Shade", "tint_shade", -100, 100, 0, "← Shade (black) | Tint (white) →"),
        ]
        
        self.sliders = {}
        self.value_labels = {}
        
        for label_text, key, min_val, max_val, default, hint in sliders_data:
            slider_widget = self._create_slider_row(label_text, key, min_val, max_val, default, hint)
            layout.addWidget(slider_widget)
        
        # Reset button
        reset_btn = QPushButton("Reset All")
        reset_btn.setFixedHeight(30)
        reset_btn.clicked.connect(self._reset_all)
        layout.addWidget(reset_btn)
        
        return frame
    
    def _create_slider_row(self, label_text: str, key: str, min_val: int, max_val: int, 
                           default: int, hint: str) -> QWidget:
        """Create a single slider row with label and value display."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        _t = config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME
        
        # Label row
        label_row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold;")
        label_row.addWidget(label)
        label_row.addStretch()
        
        value_label = QLabel(str(default))
        value_label.setFixedWidth(40)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        value_label.setStyleSheet(f"font-weight: bold; color: {_t['accent']};")
        self.value_labels[key] = value_label
        label_row.addWidget(value_label)
        
        layout.addLayout(label_row)
        
        # Slider
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval((max_val - min_val) // 4)
        slider.valueChanged.connect(lambda v, k=key: self._on_slider_changed(k, v))
        self.sliders[key] = slider
        layout.addWidget(slider)
        
        # Hint label
        hint_label = QLabel(hint)
        hint_label.setStyleSheet(f"font-size: 10px; color: {_t['text_hint']};")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
        
        return widget
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create the dialog buttons."""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(90, 35)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedSize(90, 35)
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self._apply_changes)
        layout.addWidget(apply_btn)
        
        return layout
    
    def _on_slider_changed(self, key: str, value: int) -> None:
        """Handle slider value changes."""
        self._adjustments[key] = value
        self.value_labels[key].setText(str(value))
        self._update_preview()
    
    def _calculate_adjusted_color(self) -> tuple:
        """Calculate the adjusted color based on all slider values."""
        r, g, b = self.original_color
        
        # Convert to HSV for most adjustments
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        
        # Apply hue shift (convert to degrees, apply shift, convert back)
        hue_shift = self._adjustments['hue_shift'] / 360.0
        h = (h + hue_shift) % 1.0
        
        # Apply saturation adjustment
        sat_adj = self._adjustments['saturate'] / 100.0
        s = max(0.0, min(1.0, s + sat_adj))
        
        # Apply lightness/value adjustment
        light_adj = self._adjustments['lighten'] / 100.0
        v = max(0.0, min(1.0, v + light_adj))
        
        # Convert back to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        # Apply temperature adjustment (shift towards warm/cool)
        temp = self._adjustments['temperature']
        if temp != 0:
            # Warm = add red/yellow, reduce blue
            # Cool = add blue, reduce red/yellow
            temp_factor = temp / 100.0
            if temp > 0:  # Warm
                r = min(255, int(r + temp_factor * 30))
                g = min(255, int(g + temp_factor * 15))
                b = max(0, int(b - temp_factor * 20))
            else:  # Cool
                r = max(0, int(r + temp_factor * 20))
                g = min(255, int(g - temp_factor * 5))
                b = min(255, int(b - temp_factor * 30))
        
        # Apply tint/shade (mix with white or black)
        tint_shade = self._adjustments['tint_shade']
        if tint_shade != 0:
            factor = abs(tint_shade) / 100.0
            if tint_shade > 0:  # Tint (add white)
                r = int(r + (255 - r) * factor)
                g = int(g + (255 - g) * factor)
                b = int(b + (255 - b) * factor)
            else:  # Shade (add black)
                r = int(r * (1 - factor))
                g = int(g * (1 - factor))
                b = int(b * (1 - factor))
        
        # Clamp values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return (r, g, b)
    
    def _update_preview(self) -> None:
        """Update the color preview displays."""
        # Original color preview
        orig_pixmap = self._create_color_swatch(self.original_color, 80, 80)
        self.original_preview.setPixmap(orig_pixmap)
        orig_hex = "#{:02x}{:02x}{:02x}".format(*self.original_color)
        self.original_hex_label.setText(orig_hex.upper())
        
        # Adjusted color preview
        self.current_color = self._calculate_adjusted_color()
        adj_pixmap = self._create_color_swatch(self.current_color, 80, 80)
        self.adjusted_preview.setPixmap(adj_pixmap)
        adj_hex = "#{:02x}{:02x}{:02x}".format(*self.current_color)
        self.adjusted_hex_label.setText(adj_hex.upper())
    
    def _create_color_swatch(self, color: tuple, width: int, height: int) -> QPixmap:
        """Create a color swatch pixmap with border."""
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw color fill
        brush = QBrush(QColor(*color))
        painter.setBrush(brush)
        
        # Draw border
        _t = config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME
        border_color = _t['slot_border']
        pen = QPen(QColor(border_color))
        pen.setWidth(2)
        painter.setPen(pen)
        
        painter.drawRoundedRect(1, 1, width - 2, height - 2, 6, 6)
        painter.end()
        
        return pixmap
    
    def _reset_all(self) -> None:
        """Reset all sliders to their default values."""
        for key, slider in self.sliders.items():
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
            self._adjustments[key] = 0
            self.value_labels[key].setText("0")
        
        self._update_preview()
        
        if logger:
            logger.info("All adjustments reset")
    
    def _apply_changes(self) -> None:
        """Apply the adjusted color and close dialog."""
        self.color_applied.emit(self.current_color)
        
        if logger:
            orig_hex = "#{:02x}{:02x}{:02x}".format(*self.original_color)
            new_hex = "#{:02x}{:02x}{:02x}".format(*self.current_color)
            logger.success(f"Color adjusted: {orig_hex} → {new_hex}")
        
        self.accept()
    
    def get_adjusted_color(self) -> tuple:
        """Get the current adjusted color."""
        return self.current_color
    
    def set_theme(self, is_dark: bool) -> None:
        """Set the dialog theme."""
        self._is_dark = is_dark
        self._apply_theme()
        self._update_preview()
    
    def _apply_theme(self) -> None:
        """Apply the current theme to the dialog."""
        if self._is_dark:
            _d = config.ThemeManager.DARK_THEME
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {_d['panel_bg']};
                    color: {_d['text_color']};
                }}
                QFrame {{
                    background-color: {_d['panel_secondary']};
                    border: 1px solid {_d['border_color']};
                    border-radius: 6px;
                }}
                QLabel {{
                    color: {_d['text_color']};
                    background-color: transparent;
                    border: none;
                }}
                QSlider::groove:horizontal {{
                    border: 1px solid {_d['border_color']};
                    height: 8px;
                    background: {_d['panel_bg']};
                    border-radius: 4px;
                }}
                QSlider::handle:horizontal {{
                    background: {_d['slider_handle']};
                    border: 1px solid {_d['border_color']};
                    width: 16px;
                    border-radius: 8px;
                    margin: -4px 0;
                }}
                QSlider::handle:horizontal:hover {{
                    background: {_d['accent']};
                }}
                QSlider::sub-page:horizontal {{
                    background: {_d['accent']};
                    border-radius: 4px;
                }}
                QPushButton {{
                    background-color: {_d['panel_secondary']};
                    color: {_d['text_color']};
                    border: 1px solid {_d['border_color']};
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {_d['panel_hover']};
                    border-color: {_d['accent']};
                    color: {_d['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {_d['accent']};
                    border-color: {_d['accent']};
                    color: {_d['accent_on']};
                }}
            """)
        else:
            _l = config.ThemeManager.LIGHT_THEME
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {_l['window_bg']};
                    color: {_l['text_color']};
                }}
                QFrame {{
                    background-color: {_l['panel_secondary']};
                    border: 1px solid {_l['border_color']};
                    border-radius: 6px;
                }}
                QLabel {{
                    color: {_l['text_color']};
                    background-color: transparent;
                    border: none;
                }}
                QSlider::groove:horizontal {{
                    border: 1px solid {_l['border_color']};
                    height: 8px;
                    background: {_l['hover_color']};
                    border-radius: 4px;
                }}
                QSlider::handle:horizontal {{
                    background: {_l['slider_handle']};
                    border: 1px solid {_l['border_color']};
                    width: 16px;
                    border-radius: 8px;
                    margin: -4px 0;
                }}
                QSlider::handle:horizontal:hover {{
                    background: {_l['accent']};
                }}
                QSlider::sub-page:horizontal {{
                    background: {_l['accent']};
                    border-radius: 4px;
                }}
                QPushButton {{
                    background-color: {_l['button_bg']};
                    color: {_l['text_color']};
                    border: 1px solid {_l['border_color']};
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {_l['panel_hover']};
                    border-color: {_l['accent']};
                    color: {_l['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {_l['accent']};
                    border-color: {_l['accent']};
                    color: {_l['accent_on']};
                }}
            """)
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
        Clears references to free memory.
        """
        try:
            self._original_color = None
            self._current_color = None
            self._sliders.clear()
            
            if logger:
                logger.debug("ColorFineTuneDialog cleanup complete")
                
        except Exception as e:
            if logger:
                logger.error(f"Error during ColorFineTuneDialog cleanup: {e}")