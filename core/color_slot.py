"""
Individual color slot widget with weight controls and theme-aware styling.

Each slot owns an RGB color, a weight slider that contributes to the mix,
overlay controls (remove, copy, edit), and a right-click context menu for
fine-tuning. Slots emit signals when their color or weight changes so the
main application can recompute the mixed output.
"""

from typing import Callable, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
    QLineEdit, QSlider, QColorDialog, QMessageBox, QFrame, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QFont, QIcon, QAction, QContextMenuEvent

if TYPE_CHECKING:
    from ui.ui_handler import UIHandler
from core.color_math import ColorMath
from ui.debug_button import DebugButton
import os
import traceback
from utils import config

# Import ColorFineTuneDialog
try:
    from core.color_fine_tune import ColorFineTuneDialog
except ImportError:
    ColorFineTuneDialog = None

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("ColorSlot")
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


class ColorSlot(QWidget, SignalMixin):
    """Individual color slot with weight controls and theme-aware styling."""
    
    # Signals
    color_changed = pyqtSignal()
    weight_changed = pyqtSignal()
    remove_requested = pyqtSignal(object)
    
    # Maximum history size for undo/redo
    MAX_HISTORY_SIZE = 33
    
    def __init__(self, index: int, on_change_callback: Callable | None = None):
        super().__init__()
        
        # Initialize signal tracking
        self.init_signal_tracking()
        
        self.index = index
        self.on_change = on_change_callback
        self.color = (200, 200, 200)
        self._weight = 0
        self.is_dark = True
        self.is_image_mode = False  # Track if in image mode
        
        # Color history for undo/redo (stores up to 33 entries)
        self._color_history = [(200, 200, 200)]  # Initial color
        self._history_index = 0  # Current position in history
        self._skip_history = False  # Flag to skip adding to history during undo/redo
        
        self._build_ui()
        self._connect_signals()
        self._update_display()

    def _build_ui(self) -> None:
        """Build the UI components for this color slot."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 2)
        main_layout.setSpacing(6)
        
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Color swatch button with professional border
        self.swatch_btn = QPushButton()
        self.swatch_btn.setFixedSize(60, 40)
        self.swatch_btn.setStyleSheet("border: none; padding: 0px;")
        main_layout.addWidget(self.swatch_btn)
        
        # Info section
        info_widget = QWidget()
        info_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Color label and hex entry
        label_hex_layout = QHBoxLayout()
        label_hex_layout.setContentsMargins(0, 0, 0, 0)
        
        # Store as instance attribute for efficient updates (avoids findChildren)
        self.color_label = QLabel(f"Color {self.index + 1}")
        self.color_label.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['normal']}px;")
        label_hex_layout.addWidget(self.color_label)
        
        self.hex_entry = QLineEdit()
        self.hex_entry.setFixedWidth(80)
        self.hex_entry.setPlaceholderText("#RRGGBB")
        label_hex_layout.addWidget(self.hex_entry)
        label_hex_layout.addStretch()
        
        info_layout.addLayout(label_hex_layout)
        
        # Weight controls
        weight_layout = QHBoxLayout()
        weight_layout.setContentsMargins(0, 0, 0, 0)
        
        weight_layout.addWidget(QLabel("Weight:"))
        
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setRange(0, 100)
        self.weight_slider.setValue(0)
        self.weight_slider.setMinimumWidth(80)
        self.weight_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        weight_layout.addWidget(self.weight_slider)
        
        self.weight_label = QLabel("0")
        self.weight_label.setFixedWidth(30)
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weight_label.setStyleSheet(f"font-size: {config.FONT_SIZES['normal']}px; font-weight: bold;")
        weight_layout.addWidget(self.weight_label)
        
        info_layout.addLayout(weight_layout)
        
        main_layout.addWidget(info_widget)
        
        # Remove button - FIXED at 80x50
        # Load button images first
        file_name = "remove"
        base_path = os.path.join(config.BUTTON_IMAGES_DIR, f"{file_name}_base.png")
        hover_path = os.path.join(config.BUTTON_IMAGES_DIR, f"{file_name}_hover.png")
        pressed_path = os.path.join(config.BUTTON_IMAGES_DIR, f"{file_name}_pressed.png")
        
        # Create DebugButton with images if they exist
        if os.path.exists(base_path):
            self.clear_btn = DebugButton(
                text="Remove",
                base_img=base_path,
                hover_img=hover_path if os.path.exists(hover_path) else base_path,
                pressed_img=pressed_path if os.path.exists(pressed_path) else base_path
            )
        else:
            self.clear_btn = DebugButton(text="Remove")
        
        self.clear_btn.setFixedSize(80, 50)  # Remove button: 80px wide, 50px tall
        self.clear_btn.setToolTip("Remove this color slot")
        self.clear_btn.setProperty("button_name", "Remove")
        
        main_layout.addWidget(self.clear_btn)

    def _connect_signals(self) -> None:
        """Connect widget signals with tracking for proper cleanup."""
        # Track all signal connections for proper cleanup
        self.track_connection(self.swatch_btn, self.swatch_btn.clicked, self._pick_color, "swatch_clicked")
        self.track_connection(self.hex_entry, self.hex_entry.textChanged, self._on_hex_changed, "hex_changed")
        self.track_connection(self.hex_entry, self.hex_entry.returnPressed, self._on_hex_entered, "hex_entered")
        self.track_connection(self.weight_slider, self.weight_slider.valueChanged, self._on_weight_changed, "weight_changed")
        self.track_connection(self.clear_btn, self.clear_btn.clicked, self._request_removal, "clear_clicked")
        
        if self.on_change:
            self.track_connection(self, self.color_changed, self.on_change, "color_callback")
            self.track_connection(self, self.weight_changed, self.on_change, "weight_callback")

    def _request_removal(self) -> None:
        """Request removal of this slot."""
        logger.debug(f"ColorSlot {self.index}: Remove button clicked, emitting signal...")
        try:
            self.remove_requested.emit(self)
            logger.info(f"ColorSlot {self.index}: Signal emitted successfully")
        except Exception as e:
            logger.error(f"ColorSlot {self.index}: Error emitting signal: {e}")
            traceback.print_exc()

    def update_index_label(self, new_index: int) -> None:
        """
        Update the slot's index and label efficiently.
        
        Direct attribute access instead of findChildren().
        
        Args:
            new_index: The new index for this slot
        """
        self.index = new_index
        if hasattr(self, 'color_label'):
            self.color_label.setText(f"Color {new_index + 1}")

    def _update_display(self) -> None:
        """Update the color swatch display and hex entry."""
        hex_color = ColorMath.rgb_to_hex(self.color)
        
        # Update swatch button with professional border
        self._update_swatch_display()
        
        # Update hex entry (without triggering signal)
        self.hex_entry.blockSignals(True)
        self.hex_entry.setText(hex_color)
        self.hex_entry.blockSignals(False)
        
        # Update weight label
        self.weight_label.setText(str(self._weight))

    def _update_swatch_display(self) -> None:
        """Update swatch with professional styling."""
        hex_color = ColorMath.rgb_to_hex(self.color)
        
        # Get border styling based on theme
        theme = config.ThemeManager().get_current_theme()
        if theme:
            border_width = theme.get('slot_border_width', 2)
            border_color = theme.get('slot_border', config.ThemeManager.DARK_THEME['slot_border'])
        else:
            border_width = 2
            border_color = config.ThemeManager.DARK_THEME['slot_border']
        
        # Get brand accent color for hover/pressed border
        accent_color = theme.get('accent', config.ThemeManager.DARK_THEME['accent']) if theme else config.ThemeManager.DARK_THEME['accent']

        self.swatch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: {border_width}px solid {border_color};
                border-radius: 3px;
                padding: 0px;
            }}
            QPushButton:hover {{
                border: {border_width}px solid {accent_color};
            }}
            QPushButton:pressed {{
                border: {border_width}px solid {accent_color};
            }}
        """)


    def _update_remove_button_display(self, ui_handler: "UIHandler | None" = None) -> None:
        """Update remove button to show image in Image Mode or text in other modes."""
        try:
            # Check if we're in Image Mode
            is_image_mode = False
            if ui_handler and hasattr(ui_handler, 'is_image_mode'):
                is_image_mode = ui_handler.is_image_mode()
            
            self.is_image_mode = is_image_mode
            
            if is_image_mode and hasattr(self.clear_btn, 'base_img') and self.clear_btn.base_img:
                # Image Mode - show image, hide text (DebugButton handles state changes)
                self.clear_btn.setText("")
                self.clear_btn.setIcon(QIcon(self.clear_btn.base_img))
                self.clear_btn.setIconSize(self.clear_btn.size())
            else:
                # Dark/Light Mode - show text, no icon
                if self.clear_btn.text() == "":
                    self.clear_btn.setText("Remove")
                self.clear_btn.setIcon(QIcon())
                
        except Exception as e:
            logger.error(f"Error updating remove button display: {e}")

    def _pick_color(self) -> None:
        """Open color picker dialog with brand palette and stylesheet applied."""
        from PyQt6.QtGui import QPalette

        current_color = QColor(*self.color)
        dialog = QColorDialog(current_color, self)
        dialog.setWindowTitle("Choose Color")

        # Image Mode shares dark styling
        use_dark = self.is_dark or self.is_image_mode
        _ct = config.ThemeManager.DARK_THEME if use_dark else config.ThemeManager.LIGHT_THEME
        accent      = _ct['accent']
        accent_text = _ct['accent_on']
        base_hex    = _ct['input_bg']
        text_hex    = _ct['text_color']
        window_hex  = _ct['window_bg']    # dialog/panel bg
        button_hex  = _ct['button_bg']    # button surface bg
        border_hex  = _ct['border_color']

        # 1. Stylesheet — forces focus rings, spinbox borders, input selection
        #    on ALL child widgets (QProxyStyle ignores dialog palette for these)
        dialog.setStyleSheet(f"""
            QWidget {{
                background-color: {window_hex};
                color: {text_hex};
            }}
            QSpinBox, QLineEdit {{
                background-color: {base_hex};
                color: {text_hex};
                border: 1px solid {border_hex};
                selection-background-color: {accent};
                selection-color: {accent_text};
            }}
            QSpinBox:focus, QLineEdit:focus {{
                border: 1px solid {accent};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {window_hex};
                border: 1px solid {border_hex};
            }}
            QPushButton {{
                background-color: {button_hex};
                color: {text_hex};
                border: 1px solid {border_hex};
                padding: 4px 12px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {_ct['panel_hover']};
                border-color: {accent};
                color: {accent if use_dark else accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: {accent_text};
                border-color: {accent};
            }}
            QLabel {{
                color: {text_hex};
                background-color: transparent;
            }}
        """)

        # 2. Palette — covers roles that stylesheet cannot reach
        palette = dialog.palette()
        for group in (QPalette.ColorGroup.Active,
                      QPalette.ColorGroup.Inactive,
                      QPalette.ColorGroup.Normal):
            palette.setColor(group, QPalette.ColorRole.Highlight,       QColor(accent))
            palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor(accent_text))
            palette.setColor(group, QPalette.ColorRole.Base,            QColor(base_hex))
            palette.setColor(group, QPalette.ColorRole.Text,            QColor(text_hex))
            palette.setColor(group, QPalette.ColorRole.Window,          QColor(window_hex))
            palette.setColor(group, QPalette.ColorRole.WindowText,      QColor(text_hex))
            palette.setColor(group, QPalette.ColorRole.Button,          QColor(button_hex))
            palette.setColor(group, QPalette.ColorRole.ButtonText,      QColor(text_hex))
        dialog.setPalette(palette)

        if dialog.exec() == QColorDialog.DialogCode.Accepted:
            color = dialog.selectedColor()
            if color.isValid():
                rgb = (color.red(), color.green(), color.blue())
                self.set_color(rgb)

    def _on_hex_changed(self) -> None:
        """Handle hex color entry changes (real-time)."""
        hex_text = self.hex_entry.text().strip()
        if self._is_valid_hex(hex_text):
            try:
                rgb = ColorMath.hex_to_rgb(hex_text)
                self.color = rgb
                self._update_swatch_display()
            except Exception:
                pass

    def _on_hex_entered(self) -> None:
        """Handle hex color entry completion (Enter pressed)."""
        hex_text = self.hex_entry.text().strip()
        if self._is_valid_hex(hex_text):
            try:
                rgb = ColorMath.hex_to_rgb(hex_text)
                self.set_color(rgb)
            except Exception as ex:
                QMessageBox.warning(self, "Invalid Color", 
                                  f"Could not parse color: {hex_text}\n{ex}")
                self._update_display()

    def _is_valid_hex(self, hex_text: str) -> bool:
        """Check if hex text is valid."""
        hex_text = hex_text.lstrip("#")
        if len(hex_text) == 3:
            hex_text = ''.join(ch * 2 for ch in hex_text)
        return len(hex_text) == 6 and all(c in '0123456789abcdefABCDEF' for c in hex_text)

    def _on_weight_changed(self, value: int) -> None:
        """Handle weight slider changes."""
        self._weight = value
        self.weight_label.setText(str(value))
        self.weight_changed.emit()

    def set_color(self, rgb: tuple[int, int, int]) -> None:
        """Set the color and update display."""
        new_color = tuple(int(max(0, min(255, v))) for v in rgb)
        
        # Add to history if not during undo/redo operation
        if not self._skip_history and new_color != self.color:
            self._add_to_history(new_color)
        
        self.color = new_color
        self._update_display()
        self.color_changed.emit()
    
    def _add_to_history(self, color: tuple) -> None:
        """Add a color to the history stack."""
        # If we're not at the end of history, truncate future entries
        if self._history_index < len(self._color_history) - 1:
            self._color_history = self._color_history[:self._history_index + 1]
        
        # Add new color
        self._color_history.append(color)
        
        # Trim history if it exceeds max size
        if len(self._color_history) > self.MAX_HISTORY_SIZE:
            self._color_history = self._color_history[-self.MAX_HISTORY_SIZE:]
        
        # Update index to point to the latest entry
        self._history_index = len(self._color_history) - 1
        
        if logger:
            logger.debug(f"History added: {ColorMath.rgb_to_hex(color)} (index {self._history_index}/{len(self._color_history)-1})")
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._history_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._history_index < len(self._color_history) - 1
    
    def undo_color(self) -> None:
        """Undo to the previous color in history."""
        if not self.can_undo():
            if logger:
                logger.warning("Cannot undo: at beginning of history")
            return
        
        self._history_index -= 1
        previous_color = self._color_history[self._history_index]
        
        # Set color without adding to history
        self._skip_history = True
        self.set_color(previous_color)
        self._skip_history = False
        
        if logger:
            logger.info(f"Undo: {ColorMath.rgb_to_hex(previous_color)} (index {self._history_index}/{len(self._color_history)-1})")
    
    def redo_color(self) -> None:
        """Redo to the next color in history."""
        if not self.can_redo():
            if logger:
                logger.warning("Cannot redo: at end of history")
            return
        
        self._history_index += 1
        next_color = self._color_history[self._history_index]
        
        # Set color without adding to history
        self._skip_history = True
        self.set_color(next_color)
        self._skip_history = False
        
        if logger:
            logger.info(f"Redo: {ColorMath.rgb_to_hex(next_color)} (index {self._history_index}/{len(self._color_history)-1})")
    
    def get_history_info(self) -> tuple:
        """Get history status info for display."""
        return (self._history_index, len(self._color_history) - 1)

    def set_weight(self, weight: int) -> None:
        """Set the weight value."""
        weight = max(0, min(100, weight))
        self._weight = weight
        self.weight_slider.setValue(weight)
        self.weight_label.setText(str(weight))

    def get_color(self) -> tuple[int, int, int]:
        """Get the current color."""
        return self.color

    def get_weight(self) -> int:
        """Get the current weight."""
        return self._weight

    def clear(self) -> None:
        """Clear the color slot and reset history."""
        self.color = (200, 200, 200)
        self._weight = 0
        self.weight_slider.setValue(0)
        
        # Reset history
        self._color_history = [(200, 200, 200)]
        self._history_index = 0
        
        self._update_display()
        self.color_changed.emit()
        self.weight_changed.emit()

    def get_color_data(self) -> dict:
        """Get color and weight data for export."""
        return {
            "color": self.color,
            "weight": self._weight,
            "hex": ColorMath.rgb_to_hex(self.color)
        }

    def set_color_data(self, data: dict) -> None:
        """Set color data from import."""
        if "color" in data:
            self.set_color(data["color"])
        if "weight" in data:
            self.set_weight(data["weight"])

    def set_theme(self, is_dark: bool, ui_handler: "UIHandler | None" = None) -> None:
        """Apply theme to the color slot."""
        self.is_dark = is_dark
        
        # Get the actual current theme (handles Image Mode correctly)
        if ui_handler and hasattr(ui_handler, 'theme_manager'):
            theme = ui_handler.theme_manager.get_current_theme()
        else:
            # Fallback: create theme manager and set based on is_dark
            theme_manager = config.ThemeManager()
            theme_manager.current_theme = 'dark' if is_dark else 'light'
            theme = theme_manager.get_current_theme()
        
        if theme:
            # Use transparent background for color slots in Image Mode
            widget_bg = 'transparent' if (ui_handler and hasattr(ui_handler, 'is_image_mode') and ui_handler.is_image_mode()) else theme['window_bg']
            
            stylesheet = f"""
                QWidget {{
                    background-color: {widget_bg};
                    color: {theme['text_color']};
                    font-family: "{config.FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
                }}
                QLabel {{
                    color: {theme['text_color']};
                    font-family: "{config.FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
                }}
                QLineEdit {{
                    background-color: {theme['input_bg']};
                    color: {theme['input_text']};
                    border: 1px solid {theme['border_color']};
                    padding: 2px;
                    border-radius: 3px;
                    font-family: "{config.FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
                    font-size: {config.FONT_SIZES["normal"]}px;
                }}
                QPushButton {{
                    background-color: {theme['button_bg']};
                    color: {theme['button_text']};
                    border: 1px solid {theme['border_color']};
                    padding: 4px;
                    border-radius: 3px;
                    font-family: "{config.FONT_FAMILY}", "Arial Black", "Arial", sans-serif;
                    font-size: {config.FONT_SIZES["normal"]}px;
                }}
                QPushButton:hover {{
                    background-color: {theme['button_hover_bg']};
                    color: {theme['button_text']};
                }}
                QPushButton:pressed {{
                    background-color: {theme['button_hover_bg']};
                    color: {theme['button_pressed_text']};
                    border-color: {theme['border_color']};
                }}
                QSlider::groove:horizontal {{
                    border: 1px solid {theme['border_color']};
                    height: 8px;
                    background: {theme['input_bg']};
                    border-radius: 4px;
                }}
                QSlider::handle:horizontal {{
                    background: {theme['text_color']};
                    border: 1px solid {theme['border_color']};
                    width: 18px;
                    border-radius: 9px;
                    margin: -5px 0;
                }}
            """
            self.setStyleSheet(stylesheet)
        
        # Update swatch border colors
        self._update_swatch_display()
        
        # Set theme manager for remove button if it's a DebugButton
        if ui_handler and hasattr(ui_handler, 'theme_manager'):
            if isinstance(self.clear_btn, DebugButton):
                self.clear_btn.set_theme_manager(ui_handler.theme_manager)
        
        # Handle remove button images based on mode
        self._update_remove_button_display(ui_handler)
    
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Handle right-click context menu for color fine-tuning."""
        menu = QMenu(self)
        
        # Apply theme to menu - Dark and Image Mode use dark style
        use_dark_style = self.is_dark or self.is_image_mode
        
        if use_dark_style:
            _m = config.ThemeManager.DARK_THEME
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {_m['panel_secondary']};
                    color: {_m['text_color']};
                    border: 1px solid {_m['hover_color']};
                    border-radius: 4px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 6px 20px;
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: {_m['accent']};
                    color: {_m['accent_on']};
                }}
                QMenu::item:disabled {{
                    color: {_m['menu_disabled']};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {_m['hover_color']};
                    margin: 4px 8px;
                }}
            """)
        else:
            _m = config.ThemeManager.LIGHT_THEME
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {_m['panel_secondary']};
                    color: {_m['text_color']};
                    border: 1px solid {_m['border_color']};
                    border-radius: 4px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 6px 20px;
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: {_m['accent']};
                    color: {_m['accent_on']};
                }}
                QMenu::item:disabled {{
                    color: {_m['menu_disabled']};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {_m['border_color']};
                    margin: 4px 8px;
                }}
            """)
        
        # Undo/Redo actions at the top
        history_idx, history_max = self.get_history_info()
        
        undo_action = QAction(f"↩️ Undo ({history_idx} available)", self)
        undo_action.triggered.connect(self.undo_color)
        undo_action.setEnabled(self.can_undo())
        menu.addAction(undo_action)
        
        redo_action = QAction(f"↪️ Redo ({history_max - history_idx} available)", self)
        redo_action.triggered.connect(self.redo_color)
        redo_action.setEnabled(self.can_redo())
        menu.addAction(redo_action)
        
        menu.addSeparator()
        
        # Fine-tune action
        fine_tune_action = QAction("🎨 Fine-Tune Color...", self)
        fine_tune_action.triggered.connect(self._open_fine_tune_dialog)
        menu.addAction(fine_tune_action)
        
        menu.addSeparator()
        
        # Quick adjustments submenu
        quick_menu = menu.addMenu("⚡ Quick Adjustments")
        
        # Apply same style to submenu
        if use_dark_style:
            quick_menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {_m['panel_secondary']};
                    color: {_m['text_color']};
                    border: 1px solid {_m['hover_color']};
                    border-radius: 4px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 6px 20px;
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: {_m['accent']};
                    color: {_m['accent_on']};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {_m['hover_color']};
                    margin: 4px 8px;
                }}
            """)
        else:
            quick_menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {_m['panel_secondary']};
                    color: {_m['text_color']};
                    border: 1px solid {_m['border_color']};
                    border-radius: 4px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 6px 20px;
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: {_m['accent']};
                    color: {_m['accent_on']};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {_m['border_color']};
                    margin: 4px 8px;
                }}
            """)
        
        lighten_action = QAction("☀️ Lighten 10%", self)
        lighten_action.triggered.connect(lambda: self._quick_adjust('lighten', 10))
        quick_menu.addAction(lighten_action)
        
        darken_action = QAction("🌙 Darken 10%", self)
        darken_action.triggered.connect(lambda: self._quick_adjust('darken', 10))
        quick_menu.addAction(darken_action)
        
        quick_menu.addSeparator()
        
        saturate_action = QAction("🎯 Saturate 10%", self)
        saturate_action.triggered.connect(lambda: self._quick_adjust('saturate', 10))
        quick_menu.addAction(saturate_action)
        
        desaturate_action = QAction("⚪ Desaturate 10%", self)
        desaturate_action.triggered.connect(lambda: self._quick_adjust('desaturate', 10))
        quick_menu.addAction(desaturate_action)
        
        quick_menu.addSeparator()
        
        warm_action = QAction("🔥 Warmer", self)
        warm_action.triggered.connect(lambda: self._quick_adjust('warm', 15))
        quick_menu.addAction(warm_action)
        
        cool_action = QAction("❄️ Cooler", self)
        cool_action.triggered.connect(lambda: self._quick_adjust('cool', 15))
        quick_menu.addAction(cool_action)
        
        menu.addSeparator()
        
        # Color picker action
        pick_color_action = QAction("🎨 Pick New Color...", self)
        pick_color_action.triggered.connect(self._pick_color)
        menu.addAction(pick_color_action)
        
        # Copy hex action
        copy_hex_action = QAction("📋 Copy Hex Code", self)
        copy_hex_action.triggered.connect(self._copy_hex_to_clipboard)
        menu.addAction(copy_hex_action)
        
        menu.addSeparator()
        
        # Reset action
        reset_action = QAction("🔄 Reset Color", self)
        reset_action.triggered.connect(self._reset_color)
        menu.addAction(reset_action)
        
        menu.exec(event.globalPos())
    
    def _open_fine_tune_dialog(self) -> None:
        """Open the color fine-tune dialog."""
        if ColorFineTuneDialog is None:
            QMessageBox.warning(self, "Not Available", 
                              "Color Fine-Tune feature is not available.")
            return
        
        # Image Mode uses dark theme — treat it as dark for the fine-tune dialog
        dialog = ColorFineTuneDialog(self, self.color, self.is_dark or self.is_image_mode)
        dialog.color_applied.connect(self._apply_fine_tuned_color)
        dialog.exec()
    
    def _apply_fine_tuned_color(self, new_color: tuple) -> None:
        """Apply the fine-tuned color from the dialog."""
        self.set_color(new_color)
        if logger:
            hex_color = ColorMath.rgb_to_hex(new_color)
            logger.success(f"Fine-tuned color applied: {hex_color}")
    
    def _quick_adjust(self, adjustment_type: str, amount: int) -> None:
        """Apply a quick color adjustment."""
        import colorsys
        
        r, g, b = self.color
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        
        if adjustment_type == 'lighten':
            v = min(1.0, v + amount / 100.0)
        elif adjustment_type == 'darken':
            v = max(0.0, v - amount / 100.0)
        elif adjustment_type == 'saturate':
            s = min(1.0, s + amount / 100.0)
        elif adjustment_type == 'desaturate':
            s = max(0.0, s - amount / 100.0)
        elif adjustment_type == 'warm':
            # Shift hue towards orange/red and increase saturation slightly
            h = (h - 0.02) % 1.0  # Shift towards red
            r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s, v)
            r = min(255, int(r_new * 255) + amount)
            g = int(g_new * 255)
            b = max(0, int(b_new * 255) - amount // 2)
            self.set_color((r, g, b))
            return
        elif adjustment_type == 'cool':
            # Shift hue towards blue and adjust
            h = (h + 0.02) % 1.0  # Shift towards blue
            r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s, v)
            r = max(0, int(r_new * 255) - amount // 2)
            g = int(g_new * 255)
            b = min(255, int(b_new * 255) + amount)
            self.set_color((r, g, b))
            return
        
        # Convert back to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.set_color((int(r * 255), int(g * 255), int(b * 255)))
        
        if logger:
            logger.info(f"Quick adjustment: {adjustment_type} by {amount}%")
    
    def _copy_hex_to_clipboard(self) -> None:
        """Copy the current hex color to clipboard."""
        from PyQt6.QtWidgets import QApplication
        hex_color = ColorMath.rgb_to_hex(self.color)
        clipboard = QApplication.clipboard()
        clipboard.setText(hex_color)
        
        if logger:
            logger.info(f"Copied to clipboard: {hex_color}")
    
    def _reset_color(self) -> None:
        """Reset the color to default gray."""
        self.set_color((200, 200, 200))
        if logger:
            logger.info("Color reset to default")
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
        Properly disconnects all tracked signals
        to prevent memory leaks when slots are removed.
        """
        if logger:
            logger.debug(f"ColorSlot {self.index}: Cleaning up signals...")
        
        # Disconnect all tracked signals
        self.cleanup_signals()
        
        # Clear references
        self.on_change = None
        
        if logger:
            logger.debug(f"ColorSlot {self.index}: Cleanup complete")