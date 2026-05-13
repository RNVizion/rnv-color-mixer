"""
Package D Control Panel - Features & Settings Dialog
Contains 5 tabs: History, Presets, Harmony, Sessions, Settings
"""

from datetime import datetime
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QFileDialog, QLineEdit, QComboBox, QScrollArea, QCheckBox, QSlider, QSizePolicy,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QModelIndex, QSize
from PyQt6.QtGui import QColor, QPixmap, QPainter, QBrush, QIcon, QShortcut, QKeySequence, QResizeEvent, QShowEvent, QCloseEvent
from utils import config
import os
import traceback
from ui.debug_overlay import DebugOverlay
from utils.settings_manager import get_settings_manager

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("PackageDPanel")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False


# Type checking imports (for type hints only)
if TYPE_CHECKING:
    from core.color_history import ColorHistory, ColorHistoryEntry
    from core.preset_palettes import PresetPalettes, PresetPalette
    from core.color_harmony import ColorHarmony, HarmonyType
    from utils.settings_manager import SettingsManager

# Runtime imports
try:
    from core.color_history import ColorHistory, ColorHistoryEntry
    logger.info("[OK] Color History module loaded")
except ImportError as e:
    logger.warning(f"Warning: Color History not available: {e}")
    ColorHistory = None  # type: ignore
    ColorHistoryEntry = None  # type: ignore

# Import preset palettes
try:
    from core.preset_palettes import PresetPalettes, PresetPalette
    logger.info("[OK] Preset Palettes module loaded")
except ImportError as e:
    logger.warning(f"Warning: Preset Palettes not available: {e}")
    PresetPalettes = None  # type: ignore
    PresetPalette = None  # type: ignore

# Import color harmony
try:
    from core.color_harmony import ColorHarmony, HarmonyType  # type: ignore
    logger.info("[OK] Color Harmony module loaded")
except ImportError as e:
    logger.warning(f"Warning: Color Harmony not available: {e}")
    ColorHarmony = None  # type: ignore
    HarmonyType = None  # type: ignore

# Import session manager
try:
    from utils.session_manager import SessionManager
    logger.info("[OK] Session Manager module loaded")
except ImportError as e:
    logger.warning(f"Warning: Session Manager not available: {e}")
    SessionManager = None  # type: ignore




class _BrandComboDelegate(QStyledItemDelegate):
    """Custom item delegate for QComboBox dropdowns.
    
    Qt Fusion style on Windows ignores QAbstractItemView::item:hover in
    stylesheets entirely — the native delegate overpaints it. This delegate
    bypasses that by painting hover and selection states directly in Python
    using brand colors, making it immune to the native style system.
    """

    @staticmethod
    def _get_colors(is_dark: bool) -> dict:
        """Colors sourced from ThemeManager — no hardcoding."""
        t = _theme_colors(is_dark)
        return {
            'bg':       t['panel_secondary'],
            'text':     t['text_color'],
            'hover_bg': t['panel_hover'],
            'hover_fg': t['accent'],
            'sel_bg':   t['accent'],
            'sel_fg':   t['accent_on'],
        }

    def __init__(self, parent: QWidget | None = None, is_dark: bool = True) -> None:
        super().__init__(parent)
        self._colors = self._get_colors(is_dark)

    def set_dark(self, is_dark: bool) -> None:
        self._colors = self._get_colors(is_dark)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        from PyQt6.QtGui import QColor, QPen, QBrush
        from PyQt6.QtCore import Qt

        c = self._colors
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered  = bool(option.state & QStyle.StateFlag.State_MouseOver)

        painter.save()

        # Background fill
        if is_selected:
            bg = QColor(c['sel_bg'])
        elif is_hovered:
            bg = QColor(c['hover_bg'])
        else:
            bg = QColor(c['bg'])
        painter.fillRect(option.rect, QBrush(bg))

        # Text color
        if is_selected:
            fg = QColor(c['sel_fg'])
        elif is_hovered:
            fg = QColor(c['hover_fg'])
        else:
            fg = QColor(c['text'])

        painter.setPen(QPen(fg))

        # Draw text with left padding
        text_rect = option.rect.adjusted(8, 0, -4, 0)
        text = index.data()
        if text:
            painter.drawText(
                text_rect,
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                str(text)
            )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        hint = super().sizeHint(option, index)
        return hint.__class__(hint.width(), max(hint.height(), 26))


def _theme_colors(is_dark: bool) -> dict:
    """Return the current theme color dict from ThemeManager.
    Single source of truth for all colors used in PackageDPanel.
    """
    from utils import config as _cfg
    _tm = _cfg.ThemeManager()
    _tm.current_theme = 'dark' if is_dark else 'light'
    return _tm.get_current_theme()


class PackageDPanel(QDialog):
    """Control panel for all Package D features."""
    
    # Signals
    load_history_color = pyqtSignal(tuple)  # (r, g, b)
    load_preset = pyqtSignal(list, str)  # colors list, preset name
    save_as_preset = pyqtSignal(str, str)  # preset name, description
    apply_harmony = pyqtSignal(str, tuple)  # harmony type, base color
    load_session = pyqtSignal(str)  # session file path
    save_session = pyqtSignal(str)  # session file path
    
    # Quick Actions signals
    export_current_mix = pyqtSignal()  # Export mixed color as swatch
    pick_screen_color = pyqtSignal()  # Activate global color picker
    generate_quick_palette = pyqtSignal(str)  # Generate palette (type: complementary, analogous, etc.)
    
    # Settings signals
    settings_changed = pyqtSignal(str, object)  # setting_key, value
    
    def __init__(self, parent: QWidget | None = None, color_history: "ColorHistory | None" = None, preset_palettes: "PresetPalettes | None" = None, settings_manager: "SettingsManager | None" = None) -> None:
        super().__init__(parent)
        
        self.color_history = color_history
        self.preset_palettes = preset_palettes
        
        # Initialize session manager
        self.session_manager = SessionManager() if SessionManager else None
        
        # Use provided settings manager or get global instance
        if settings_manager:
            self.settings_manager = settings_manager
            logger.debug(f"[OK] Settings manager injected from parent")
        else:
            self.settings_manager = get_settings_manager()
            logger.debug(f"[OK] Settings manager initialized")
        
        self.setWindowTitle("Color Mixer - Features & Settings")
        self.setModal(False)  # Allow interaction with main window
        self.setMinimumSize(config.PACKAGE_D_WIDTH, config.PACKAGE_D_MIN_HEIGHT)  # Minimum size (cannot resize smaller)
        self.setMaximumWidth(config.PACKAGE_D_WIDTH)  # Lock width
        self.resize(config.PACKAGE_D_WIDTH, config.PACKAGE_D_DEFAULT_HEIGHT)  # Default dimensions
        
        # Restore saved panel height if remember_size is enabled
        if self.settings_manager:
            remember_size = self.settings_manager.get('window.remember_size', True)
            if remember_size:
                saved_height = self.settings_manager.get('window.package_d_height', config.PACKAGE_D_DEFAULT_HEIGHT)
                # Enforce minimum height, width stays locked
                restored_height = max(config.PACKAGE_D_MIN_HEIGHT, saved_height)
                self.resize(config.PACKAGE_D_WIDTH, restored_height)
                if logger:
                    logger.debug(f"Restored Package D panel height: {restored_height}")
        
        self._build_ui()
        
        # Load settings into UI after UI is built
        self._load_settings_into_ui()
        
    def _build_ui(self) -> None:
        """Build the control panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab widget
        self.tabs = QTabWidget()
        # Note: Tabs at natural size, NOT expanding to fill width
        
        # Create 6 tabs
        self.history_tab = self._create_history_tab()
        self.presets_tab = self._create_presets_tab()
        self.harmony_tab = self._create_harmony_tab()
        self.sessions_tab = self._create_sessions_tab()
        self.quick_actions_tab = self._create_quick_actions_tab()
        self.settings_tab = self._create_settings_tab()
        
        # Add tabs
        self.tabs.addTab(self.history_tab, "📜 History")
        self.tabs.addTab(self.presets_tab, "🎨 Presets")
        self.tabs.addTab(self.harmony_tab, "🎵 Harmony")
        self.tabs.addTab(self.sessions_tab, "💾 Sessions")
        self.tabs.addTab(self.quick_actions_tab, "⚡ Quick Actions")
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")
        
        layout.addWidget(self.tabs)
        
        # Apply custom gold-themed stylesheet to override blue colors
        # This stylesheet ensures gold brand colors in BOTH dark and light modes
        # Widget-level stylesheet applied in set_theme() — see _apply_widget_stylesheet()

        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Apply combo view hover styles (bypasses native Windows delegate)
        self._apply_combo_view_styles(is_dark=True)
        
        # Set initial palette so QListWidget selected items use brand gold from the start
        self.set_theme(is_dark=True)
        self._apply_list_view_styles(is_dark=True)
        
        # Debug overlays - Show panel and tabs dimensions (toggle with F12)
        # Initialize as None - will be created by settings if enabled
        self.debug_overlay_panel = None
        self.debug_overlay_tabs = None
        
        # F12 keyboard shortcut to toggle debug overlays
        self.debug_shortcut = QShortcut(QKeySequence("F12"), self)
        self.debug_shortcut.activated.connect(self._toggle_debug_overlays)
        
    def _toggle_debug_overlays(self) -> None:
        """Toggle debug overlays visibility with F12."""
        try:
            # Create overlays if they don't exist
            if self.debug_overlay_panel is None or self.debug_overlay_tabs is None:
                self._create_debug_overlays()
            
            # Toggle visibility
            is_visible = self.debug_overlay_panel.isVisible()
            
            if is_visible:
                self.debug_overlay_panel.hide()
                self.debug_overlay_tabs.hide()
                logger.debug("Debug overlays hidden (F12)")
            else:
                self.debug_overlay_panel.show()
                self.debug_overlay_tabs.show()
                logger.debug("Debug overlays shown (F12)")
        except Exception as e:
            logger.error(f"Error toggling debug overlays: {e}")
        
    def _create_debug_overlays(self) -> None:
        """Create debug overlays for Package D Panel."""
        # Panel overlay - TOP-RIGHT (green)
        self.debug_overlay_panel = DebugOverlay(self, "Package D Panel", "rgba(80, 255, 80, 220)")
        
        # Tabs overlay - TOP-LEFT (orange) - custom position
        self.debug_overlay_tabs = DebugOverlay(self.tabs, "Tabs Widget", "rgba(255, 200, 80, 220)")
        
        # Override position_overlay for tabs overlay to place in TOP-LEFT
        def position_tabs_overlay() -> None:
            if self.debug_overlay_tabs.parent():
                # Position in top-left with 10px margin
                self.debug_overlay_tabs.move(10, 10)
        
        self.debug_overlay_tabs.position_overlay = position_tabs_overlay
    
    def _apply_debug_overlays_setting(self, show: bool) -> None:
        """Apply debug overlays setting."""
        try:
            if show:
                # Create and show overlays
                if self.debug_overlay_panel is None or self.debug_overlay_tabs is None:
                    self._create_debug_overlays()
                self.debug_overlay_panel.show()
                self.debug_overlay_tabs.show()
                logger.debug("Debug overlays enabled by setting")
            else:
                # Hide overlays if they exist
                if self.debug_overlay_panel:
                    self.debug_overlay_panel.hide()
                if self.debug_overlay_tabs:
                    self.debug_overlay_tabs.hide()
        except Exception as e:
            logger.error(f"Error applying debug overlays setting: {e}")
    
    def _create_history_tab(self) -> QWidget:
        """Create the Color History tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Recent Mixed Colors")
        title.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['large']}px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Click any color to load it into an empty slot")
        desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px;")
        layout.addWidget(desc)
        
        # History list
        self.history_list = QListWidget()
        # Styled via set_theme() so hover/selected colors update with theme
        layout.addWidget(self.history_list)
        
        # Populate with real or placeholder data
        self.refresh_history()
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._clear_history)
        button_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("Export History")
        export_btn.clicked.connect(self._export_history)
        button_layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_history)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return widget
        
    def _create_presets_tab(self) -> QWidget:
        """Create the Preset Palettes tab."""
        from PyQt6.QtWidgets import QComboBox, QScrollArea
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title and description
        title = QLabel("Preset Color Palettes")
        title.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['large']}px;")
        layout.addWidget(title)
        
        desc = QLabel("Click a preset to load it into your color slots")
        desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px;")
        layout.addWidget(desc)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addSpacing(5)  # Small space between label and dropdown
        
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(150)
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self.category_combo)
        filter_layout.addStretch()  # Push button to the right
        
        # Refresh button (matching harmony refresh style)
        refresh_btn = QPushButton("⟳")
        refresh_btn.setObjectName("preset_refresh_btn")
        refresh_btn.setFixedSize(46, 34)
        refresh_btn.setStyleSheet(
            "QPushButton { font-size: 22px; font-family: Arial, 'Segoe UI', sans-serif; "
            "padding-bottom: 7px; padding-left: 0px; padding-right: 0px; padding-top: 0px; border: 1px solid transparent; }"
        )
        refresh_btn.setToolTip("Refresh presets list")
        refresh_btn.clicked.connect(self.refresh_presets)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Presets list
        self.presets_list = QListWidget()
        # Styled via set_theme() so hover/selected colors update with theme
        self.presets_list.itemClicked.connect(self._on_preset_clicked)
        self.presets_list.itemDoubleClicked.connect(self._on_preset_double_clicked)
        layout.addWidget(self.presets_list)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("📥 Load Selected")
        load_btn.setFixedHeight(35)
        load_btn.clicked.connect(self._load_selected_preset)
        button_layout.addWidget(load_btn)
        
        save_btn = QPushButton("💾 Save Current as Preset")
        save_btn.setFixedHeight(35)
        save_btn.clicked.connect(self._save_current_as_preset)
        button_layout.addWidget(save_btn)
        
        # Delete button (only for user presets)
        self.delete_preset_btn = QPushButton("🗑️ Delete Selected")
        self.delete_preset_btn.setFixedHeight(35)
        self.delete_preset_btn.setEnabled(False)  # Disabled by default
        self.delete_preset_btn.setToolTip("Delete user-created preset (system presets cannot be deleted)")
        self.delete_preset_btn.clicked.connect(self._delete_selected_preset)
        button_layout.addWidget(self.delete_preset_btn)
        
        layout.addLayout(button_layout)
        
        # Info label
        info = QLabel(" Tip: Double-click to load   = User preset (can delete)")
        info.setStyleSheet(f"color: {{config.ThemeManager().DARK_THEME['accent']}}; font-size: {config.FONT_SIZES['small']}px;")
        layout.addWidget(info)
        
        # Initial population
        self.refresh_presets()
        
        return widget
        
    def _create_harmony_tab(self) -> QWidget:
        """Create the Color Harmony tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Color Harmony Generator")
        title.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['large']}px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Generate professional color schemes based on color theory")
        desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px;")
        layout.addWidget(desc)
        
        # Base color selection
        base_color_layout = QHBoxLayout()
        base_color_layout.addWidget(QLabel("Base Color:"))
        
        self.harmony_base_combo = QComboBox()
        self.harmony_base_combo.setMinimumHeight(30)
        self.harmony_base_combo.currentIndexChanged.connect(self._on_base_color_changed)
        base_color_layout.addWidget(self.harmony_base_combo, 1)
        base_color_layout.addSpacing(10)  # Add fixed 10px spacing
        
        # Add refresh button
        self.harmony_refresh_btn = QPushButton("⟳")  # Refresh symbol (U+27F3)
        self.harmony_refresh_btn.setObjectName("harmony_refresh_btn")  # For theme styling
        self.harmony_refresh_btn.setFixedSize(46, 34)
        self.harmony_refresh_btn.setStyleSheet(
            "QPushButton { font-size: 22px; font-family: Arial, 'Segoe UI', sans-serif; "
            "padding-bottom: 7px; padding-left: 0px; padding-right: 0px; padding-top: 0px; border: 1px solid transparent; }"
        )
        
        self.harmony_refresh_btn.setToolTip("Refresh base colors from current slots")
        self.harmony_refresh_btn.clicked.connect(self._refresh_base_colors)
        base_color_layout.addWidget(self.harmony_refresh_btn)
        layout.addLayout(base_color_layout)
        
        # Harmony type selection
        harmony_type_layout = QHBoxLayout()
        harmony_type_layout.addWidget(QLabel("Harmony Type:"))
        
        self.harmony_type_combo = QComboBox()
        self.harmony_type_combo.setMinimumHeight(30)
        if ColorHarmony and HarmonyType:
            for harmony in HarmonyType:
                self.harmony_type_combo.addItem(harmony.value)
        self.harmony_type_combo.currentIndexChanged.connect(self._on_harmony_type_changed)
        harmony_type_layout.addWidget(self.harmony_type_combo, 1)
        
        layout.addLayout(harmony_type_layout)
        
        # Description of selected harmony
        self.harmony_description = QLabel("")
        _acc = config.ThemeManager.DARK_THEME['accent']
        _r, _g, _b = int(_acc[1:3], 16), int(_acc[3:5], 16), int(_acc[5:7], 16)
        self.harmony_description.setStyleSheet(
            f"color: {_acc}; font-size: {config.FONT_SIZES['small']}px; "
            f"padding: 8px; background-color: rgba({_r}, {_g}, {_b}, 0.1); border-radius: 4px;"
        )
        layout.addWidget(self.harmony_description)
        
        # Preview area
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['normal']}px; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        # Color preview list - expands to fill available space
        self.harmony_preview_list = QListWidget()
        self.harmony_preview_list.setMinimumHeight(150)  # Minimum height, but can grow
        # Styling will be applied by set_theme()
        layout.addWidget(self.harmony_preview_list, 1)  # Stretch factor 1 to expand
        
        # Buttons
        button_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Generate Harmony")
        generate_btn.setFixedHeight(35)
        generate_btn.clicked.connect(self._generate_harmony)
        button_layout.addWidget(generate_btn)
        
        apply_btn = QPushButton("Apply to Slots")
        apply_btn.setFixedHeight(35)
        apply_btn.clicked.connect(self._apply_harmony_to_slots)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        # Tip
        tip = QLabel(" Tip: Select a base color, choose a harmony type, and apply!")
        tip.setStyleSheet(f"color: {{config.ThemeManager().DARK_THEME['accent']}}; font-size: {config.FONT_SIZES['small']}px;")
        layout.addWidget(tip)
        
        # No stretch at end - let the preview list take available space
        
        # Initialize with current harmony type description
        self._on_harmony_type_changed(0)
        
        return widget
        
    def _create_sessions_tab(self) -> QWidget:
        """Create the Sessions tab with save/load functionality."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Session Management")
        title.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['large']}px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Save and restore your complete mixing sessions")
        desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px;")
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        # Recent Sessions Section
        sessions_label = QLabel("Recent Sessions:")
        sessions_label.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['normal']}px;")
        layout.addWidget(sessions_label)
        
        # Sessions list
        self.sessions_list = QListWidget()
        self.sessions_list.setMinimumHeight(200)
        # Styling will be applied by set_theme method
        self.sessions_list.itemDoubleClicked.connect(self._on_session_double_click)
        layout.addWidget(self.sessions_list, 1)
        
        # Button row 1: Save and Load
        button_row_1 = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Current Session")
        save_btn.setObjectName("session_save_btn")  # For gold theme styling
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._on_save_session)
        button_row_1.addWidget(save_btn)
        
        load_btn = QPushButton("📥 Load Selected")
        load_btn.setObjectName("session_load_btn")  # For gold theme styling
        load_btn.setFixedHeight(40)
        load_btn.clicked.connect(self._on_load_session)
        button_row_1.addWidget(load_btn)
        
        layout.addLayout(button_row_1)
        
        # Button row 2: Refresh and Delete
        button_row_2 = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.setObjectName("session_refresh_btn")  # For gold theme styling
        refresh_btn.setFixedHeight(35)
        refresh_btn.clicked.connect(self._refresh_sessions_list)
        button_row_2.addWidget(refresh_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setObjectName("session_delete_btn")  # For gold theme styling
        delete_btn.setFixedHeight(35)
        delete_btn.clicked.connect(self._on_delete_session)
        button_row_2.addWidget(delete_btn)
        
        layout.addLayout(button_row_2)
        
        # Info tip
        tip = QLabel(" Tip: Double-click a session to load it quickly")
        tip.setStyleSheet(f"color: {{config.ThemeManager().DARK_THEME['accent']}}; font-size: {config.FONT_SIZES['small']}px; margin-top: 5px;")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tip)
        
        # Populate sessions list
        self._refresh_sessions_list()
        
        return widget
    
    def _create_quick_actions_tab(self) -> QWidget:
        """Create the Quick Actions tab."""
        widget = QWidget()

        # Outer layout: fixed-content container + stretch + logo overlay.
        # The stretch lives here so it CANNOT reach inside content_w.
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ── Fixed content container ──────────────────────────────────────────
        # All widgets that must not resize go in here.
        # setFixedHeight() is called on this container in showEvent() after
        # stylesheets have settled, hard-capping the height in one shot so
        # nothing inside can receive extra pixels from the outer stretch.
        content_w = QWidget()
        content_w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._qa_content_widget = content_w   # pinned in showEvent
        layout = QVBoxLayout(content_w)       # keep name 'layout' — all addWidget calls below unchanged
        layout.setContentsMargins(15, 15, 15, 15)  # Match other tabs
        layout.setSpacing(0)  # Each element controls its own margins
        
        # Title
        title = QLabel("Quick Actions & Shortcuts")
        title.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['large']}px;")
        title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Fast productivity tools and keyboard shortcuts")
        desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px;")
        desc.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(desc)
        
        # === Section 1: Keyboard Shortcuts Reference ===
        self._shortcuts_label = QLabel(" Keyboard Shortcuts")
        shortcuts_label = self._shortcuts_label
        shortcuts_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(shortcuts_label)
        
        # Shortcuts list - fixed size, doesn't stretch with panel resize
        shortcuts_widget = QWidget()
        shortcuts_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        shortcuts_layout = QVBoxLayout(shortcuts_widget)
        shortcuts_layout.setContentsMargins(10, 5, 10, 5)
        shortcuts_layout.setSpacing(3)  # 3px space between rows
        
        shortcuts_data = [
            ("Ctrl+O", "Upload Image"),
            ("Ctrl+S", "Save Color Swatch"),
            ("Ctrl+C", "Copy Hex Color"),
            ("Ctrl+N", "Add Color Slot"),
            ("Ctrl+P or Ctrl+,", "Open This Panel"),
            ("Ctrl+/", "About / Help"),
            ("Ctrl+Shift+C", "Pick Screen Color"),
            ("F11", "Toggle Tooltips"),
            ("F12", "Toggle Debug Overlays"),
        ]
        
        for shortcut, description in shortcuts_data:
            shortcut_row = QWidget()
            shortcut_row.setFixedHeight(24)  # Fixed height - prevents stretching on resize
            shortcut_layout = QHBoxLayout(shortcut_row)
            shortcut_layout.setContentsMargins(0, 2, 0, 2)
            
            key_label = QLabel(shortcut)
            _t_k = _theme_colors(True)
            key_label.setStyleSheet(f"""
                background-color: {_t_k['accent']};
                color: {_t_k['accent_on']};
                padding: 3px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: {config.FONT_SIZES['small']}px;
            """)
            key_label.setFixedWidth(150)
            shortcut_layout.addWidget(key_label)
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet(f"font-size: {config.FONT_SIZES['small']}px;")
            shortcut_layout.addWidget(desc_label)
            shortcut_layout.addStretch()
            
            shortcuts_layout.addWidget(shortcut_row)
        
        # Hard-pin the container height so the layout engine cannot assign it
        # any extra pixels when the panel grows (setSizePolicy alone is a hint,
        # setFixedHeight is a hard constraint that Qt cannot override)
        _n    = len(shortcuts_data)
        _row  = 24   # matches shortcut_row.setFixedHeight(24)
        _gap  = 3    # matches shortcuts_layout.setSpacing(3)
        _marg = 5 + 5  # top(5) + bottom(5) from setContentsMargins(10,5,10,5)
        shortcuts_widget.setFixedHeight(_n * _row + max(0, _n - 1) * _gap + _marg)
        
        layout.addWidget(shortcuts_widget)
        
        # === Section 2: Quick Export ===
        self._export_label = QLabel(" Quick Export")
        export_label = self._export_label
        export_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(export_label)
        
        export_desc = QLabel("Instantly export your current mixed color")
        export_desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px; margin-bottom: 6px;")
        export_desc.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(export_desc)
        
        export_row = QHBoxLayout()
        
        export_swatch_btn = QPushButton(" Export Current Mix as Swatch")
        export_swatch_btn.setObjectName("qa_export_btn")  # For gold theme styling
        export_swatch_btn.clicked.connect(self._on_export_current_mix)
        export_row.addWidget(export_swatch_btn)
        
        export_row.addStretch()
        layout.addLayout(export_row)
        
        # === Section 3: Quick Palette Generation ===
        self._palette_label = QLabel(" Quick Palette Generation")
        palette_label = self._palette_label
        palette_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(palette_label)
        
        palette_desc = QLabel("Generate color palettes based on your current mixed color")
        palette_desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px; margin-bottom: 6px;")
        palette_desc.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(palette_desc)
        
        # Palette generation buttons
        palette_grid = QHBoxLayout()
        
        palette_types = [
            ("Complementary", "complementary"),
            ("Analogous", "analogous"),
            ("Triadic", "triadic"),
            ("Split Complementary", "split_complementary"),
        ]
        
        for label, palette_type in palette_types:
            btn = QPushButton(label)
            # Set objectName based on palette type for gold theme styling
            btn.setObjectName(f"qa_{palette_type}_btn")
            btn.clicked.connect(lambda checked, pt=palette_type: self._on_generate_quick_palette(pt))
            palette_grid.addWidget(btn)
        
        layout.addLayout(palette_grid)
        
        # === Section 4: Screen Color Picker ===
        self._picker_label = QLabel(" Screen Color Picker")
        picker_label = self._picker_label
        picker_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(picker_label)
        
        picker_desc = QLabel("Pick any color from anywhere on your screen with magnified preview")
        picker_desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px; margin-bottom: 6px;")
        picker_desc.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(picker_desc)
        
        self.picker_btn = QPushButton(" Activate Color Picker (Ctrl+Shift+C)")
        self.picker_btn.setObjectName("screen_color_picker_btn")  # For theme-aware styling
        self.picker_btn.setEnabled(True)
        self.picker_btn.clicked.connect(lambda: self.pick_screen_color.emit())
        # Initial styling will be set by set_theme()
        self.picker_btn.setToolTip("Pick a color from anywhere on screen - shows magnified view with crosshair")
        self.picker_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.picker_btn)
        
        # Info tip — placed ABOVE the stretch so nothing sits below the logo
        tip = QLabel(" Tip: Use keyboard shortcuts for fastest workflow!")
        tip.setStyleSheet(f"color: {{config.ThemeManager().DARK_THEME['accent']}}; font-size: {config.FONT_SIZES['small']}px; margin-top: 5px;")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(tip)

        # Add content container to outer layout, then the stretch
        outer_layout.addWidget(content_w)
        outer_layout.addStretch()   # stretch lives OUTSIDE content_w — cannot touch fixed items
        
        # === CUSTOM LOGO (gradually reveals as panel grows above 666px) ===
        # Logo is an overlay child of widget — NOT in the layout.
        # setGeometry() moves/resizes it without triggering any layout recalculation,
        # which is why there is no jitter.
        self.quick_actions_logo = QLabel(widget)          # parent=widget, NOT in layout
        self.quick_actions_logo.setAlignment(
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter
        )
        logo_path = os.path.join(config.RESOURCES_DIR, "icons", "custom_logo.png")
        if os.path.exists(logo_path):
            from PyQt6.QtGui import QPixmap
            original_pixmap = QPixmap(logo_path)
            # Store original for high-quality scaling later
            self._logo_pixmap_original = original_pixmap
            # Scale to initial display size (max 200px wide, maintain aspect ratio)
            if original_pixmap.width() > 200:
                pixmap = original_pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            else:
                pixmap = original_pixmap
            self.quick_actions_logo.setPixmap(pixmap)
            self._logo_pixmap = pixmap  # Current display pixmap
            self._logo_height = pixmap.height()
            self._logo_width  = pixmap.width()
        else:
            self._logo_pixmap_original = None
            self._logo_pixmap = None
            self._logo_height = 0
            self._logo_width  = 0
        
        # Start hidden — positioned by _do_update_logo_visibility via setGeometry
        self.quick_actions_logo.hide()
        # Store tab widget reference so we can compute overlay geometry later
        self._qa_tab_widget = widget
        # === END CUSTOM LOGO ===
        
        return widget
    
    def _on_export_current_mix(self) -> None:
        """Handle export current mix button click."""
        self.export_current_mix.emit()
    
    def _on_generate_quick_palette(self, palette_type: str) -> None:
        """Handle quick palette generation button click."""
        self.generate_quick_palette.emit(palette_type)
    
    def _update_algo_description(self, index: int) -> None:
        """Update algorithm description label based on selected algorithm."""
        descriptions = {
            0: "Standard digital color mixing using weighted RGB averaging. Best for screen/digital work.",
            1: "HSV-based mixing with better hue preservation. Good for maintaining color vibrancy.",
            2: "LAB color space mixing for perceptually uniform blending. Natural-looking gradients.",
            3: "Subtractive CMY mixing like inks/dyes. Yellow + Cyan = Green, not gray.",
            4: "Artist's RYB color wheel mixing. Yellow + Blue = Green, Red + Blue = Purple.",
            5: "Kubelka-Munk paint theory. Most realistic paint/pigment simulation with natural darkening."
        }
        if hasattr(self, 'algo_desc_label'):
            self.algo_desc_label.setText(descriptions.get(index, "Select a color mixing algorithm."))
        
    def _create_settings_tab(self) -> QWidget:
        """Create the Settings tab with full preferences UI."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Application Settings")
        title.setStyleSheet(f"font-weight: bold; font-size: {config.FONT_SIZES['large']}px;")
        main_layout.addWidget(title)
        
        # Description
        desc = QLabel("Customize your Color Mixer experience")
        desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px;")
        main_layout.addWidget(desc)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)
        
        # === GENERAL PREFERENCES ===
        layout.addWidget(self._create_section_header(" General Preferences"))
        
        # Theme preference
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Default Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Mode", "Light Mode", "Image Mode", "Auto (follow system)"])
        self.theme_combo.setMinimumWidth(200)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Auto-save colors
        self.autosave_check = QCheckBox("Auto-save mixed colors to history")
        self.autosave_check.setChecked(True)
        layout.addWidget(self.autosave_check)
        
        # Auto-load last session
        self.autoload_session_check = QCheckBox("Auto-load last session on startup")
        self.autoload_session_check.setChecked(False)
        layout.addWidget(self.autoload_session_check)
        
        # Show tooltips (F11 to toggle)
        self.tooltips_check = QCheckBox("Show tooltips (F11)")
        self.tooltips_check.setChecked(True)
        layout.addWidget(self.tooltips_check)
        
        # === COLOR SLOT DEFAULTS ===
        layout.addWidget(self._create_section_header(" Color Slot Defaults"))
        
        # Default weight
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("Default Slot Weight:"))
        self.default_weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.default_weight_slider.setRange(0, 100)
        self.default_weight_slider.setValue(50)
        self.default_weight_slider.setMinimumWidth(150)
        self.default_weight_label = QLabel("50")
        self.default_weight_label.setMinimumWidth(30)
        self.default_weight_slider.valueChanged.connect(
            lambda v: self.default_weight_label.setText(str(v))
        )
        weight_layout.addWidget(self.default_weight_slider)
        weight_layout.addWidget(self.default_weight_label)
        weight_layout.addStretch()
        layout.addLayout(weight_layout)
        
        # Max slots
        max_slots_layout = QHBoxLayout()
        max_slots_layout.addWidget(QLabel("Maximum Color Slots:"))
        self.max_slots_spin = QLineEdit("12")
        self.max_slots_spin.setMaximumWidth(60)
        max_slots_layout.addWidget(self.max_slots_spin)
        max_slots_layout.addStretch()
        layout.addLayout(max_slots_layout)
        
        # === HISTORY SETTINGS ===
        layout.addWidget(self._create_section_header(" History Settings"))
        
        # Enable history
        self.history_enabled_check = QCheckBox("Enable color history")
        self.history_enabled_check.setChecked(True)
        layout.addWidget(self.history_enabled_check)
        
        # History limit
        history_limit_layout = QHBoxLayout()
        history_limit_layout.addWidget(QLabel("History Size Limit:"))
        self.history_limit_spin = QLineEdit("50")
        self.history_limit_spin.setMaximumWidth(60)
        history_limit_layout.addWidget(self.history_limit_spin)
        history_limit_layout.addWidget(QLabel("colors"))
        history_limit_layout.addStretch()
        layout.addLayout(history_limit_layout)
        
        # === EXPORT SETTINGS ===
        layout.addWidget(self._create_section_header(" Export Settings"))
        
        # Default export format
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Default Export Format:"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["PNG Image", "JPEG Image", "JSON Data", "Adobe Swatch (ASE)", "GIMP Palette (GPL)"])
        self.export_format_combo.setMinimumWidth(200)
        export_layout.addWidget(self.export_format_combo)
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        # === UI PREFERENCES ===
        layout.addWidget(self._create_section_header(" UI Preferences"))
        
        # Show debug overlays
        self.debug_overlays_check = QCheckBox("Show debug dimension overlays (F12 to toggle)")
        self.debug_overlays_check.setChecked(False)
        layout.addWidget(self.debug_overlays_check)
        
        # Enable animations
        self.animations_check = QCheckBox("Enable UI animations")
        self.animations_check.setChecked(True)
        layout.addWidget(self.animations_check)
        
        # === ADVANCED SETTINGS ===
        layout.addWidget(self._create_section_header(" Advanced Settings"))
        
        # Color mixing algorithm
        algorithm_layout = QHBoxLayout()
        algorithm_layout.addWidget(QLabel("Color Mixing Algorithm:"))
        self.mixing_algo_combo = QComboBox()
        # Realistic color mixing algorithms
        self.mixing_algo_combo.addItems([
            "Weighted RGB (Standard)",
            "Weighted HSV (Perceptual)", 
            "LAB Perceptual (Uniform)",
            "Subtractive CMY (Inks)",
            "Weighted RYB (Artist)",
            "Kubelka-Munk (Paint)"
        ])
        self.mixing_algo_combo.setMinimumWidth(250)
        self.mixing_algo_combo.setToolTip(
            "Select color mixing algorithm:\n\n"
            "• Weighted RGB - Standard digital mixing (additive light)\n"
            "• Weighted HSV - Better hue preservation\n"
            "• LAB Perceptual - Perceptually uniform blending\n"
            "• Subtractive CMY - Like inks/dyes (Yellow+Cyan=Green)\n"
            "• Weighted RYB - Artist's color wheel (Yellow+Blue=Green)\n"
            "• Kubelka-Munk - Realistic paint/pigment simulation"
        )
        algorithm_layout.addWidget(self.mixing_algo_combo)
        algorithm_layout.addStretch()
        layout.addLayout(algorithm_layout)
        
        # Algorithm description label (updates based on selection)
        self.algo_desc_label = QLabel("Standard digital color mixing using weighted RGB averaging.")
        self.algo_desc_label.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES['small']}px; margin-left: 5px;")
        self.algo_desc_label.setWordWrap(True)
        self.mixing_algo_combo.currentIndexChanged.connect(self._update_algo_description)
        layout.addWidget(self.algo_desc_label)
        
        # Show RGB values
        self.show_rgb_check = QCheckBox("Show RGB values in previews")
        self.show_rgb_check.setChecked(True)
        layout.addWidget(self.show_rgb_check)
        
        # Show HSV values
        self.show_hsv_check = QCheckBox("Show HSV values in previews")
        self.show_hsv_check.setChecked(False)
        layout.addWidget(self.show_hsv_check)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)
        
        # === FORCE GOLD CHECKBOX STYLING ===
        # Apply gold styling to each checkbox explicitly to override Qt defaults
        # Checkbox styling applied in set_theme() with correct theme colors
        self._themed_checkboxes = [
            self.autosave_check, self.autoload_session_check, self.tooltips_check,
            self.history_enabled_check, self.debug_overlays_check, self.animations_check,
            self.show_rgb_check, self.show_hsv_check
        ]
        
        # === ACTION BUTTONS ===
        button_layout = QHBoxLayout()
        
        # Load Settings button
        load_btn = QPushButton(" Load")
        load_btn.clicked.connect(self._load_settings_from_file)
        load_btn.setMinimumWidth(85)
        load_btn.setToolTip("Load settings from default location")
        button_layout.addWidget(load_btn)
        
        # Save Settings button
        save_btn = QPushButton(" Save")
        save_btn.clicked.connect(self._save_settings_to_file)
        save_btn.setMinimumWidth(85)
        save_btn.setToolTip("Save current settings to file")
        button_layout.addWidget(save_btn)
        
        # Export Settings button
        export_btn = QPushButton(" Export")
        export_btn.clicked.connect(self._export_settings)
        export_btn.setMinimumWidth(85)
        export_btn.setToolTip("Export settings to custom location")
        button_layout.addWidget(export_btn)
        
        # Import Settings button
        import_btn = QPushButton(" Import")
        import_btn.clicked.connect(self._import_settings)
        import_btn.setMinimumWidth(85)
        import_btn.setToolTip("Import settings from file")
        button_layout.addWidget(import_btn)
        
        button_layout.addStretch()
        
        # Reset to Defaults button
        reset_btn = QPushButton(" Reset to Defaults")
        reset_btn.clicked.connect(self._reset_settings_to_defaults)
        reset_btn.setMinimumWidth(125)
        reset_btn.setToolTip("Reset all settings to default values")
        button_layout.addWidget(reset_btn)
        
        main_layout.addLayout(button_layout)
        
        return widget
    
    def _create_section_header(self, text: str) -> QLabel:
        """Create a section header label."""
        header = QLabel(text)
        _t_h = _theme_colors(True)
        header.setStyleSheet(f"""
            font-weight: bold;
            font-size: {config.FONT_SIZES['medium']}px;
            color: {_t_h['accent']};
            padding-top: 10px;
            padding-bottom: 5px;
        """)
        return header
    
    def _load_settings_from_file(self) -> None:
        """Load settings from settings manager and update UI."""
        try:
            # Reload settings from file
            self.settings_manager.load_settings()
            
            # Update UI controls with loaded settings
            self._load_settings_into_ui()
            
            QMessageBox.information(self, "Load Settings", 
                "Settings loaded successfully from:\n" + 
                str(self.settings_manager.settings_file))
            logger.info("    Settings loaded and UI updated")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load settings:\n{str(e)}")
    
    def _save_settings_to_file(self) -> None:
        """Save current UI settings to file via settings manager."""
        try:
            # Read current UI values and update settings
            # CRITICAL: Skip theme signal to avoid applying theme when just saving to disk
            self._save_ui_to_settings(skip_theme=True)
            
            # Save to file
            if self.settings_manager.save_settings():
                QMessageBox.information(self, "Save Settings", 
                    "Settings saved successfully to:\n" + 
                    str(self.settings_manager.settings_file))
                logger.info("    Settings saved")
            else:
                QMessageBox.warning(self, "Save Warning", 
                    "Settings may not have saved correctly.\nCheck console for details.")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
    
    def _export_settings(self) -> None:
        """Export settings to a custom location."""
        try:
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Export Settings",
                "colormixer_settings.json",
                "JSON Files (*.json);;All Files (*)"
            )
            if filepath:
                # Save current UI to settings first
                self._save_ui_to_settings()
                
                # Export via settings manager
                if self.settings_manager.export_settings(filepath):
                    QMessageBox.information(self, "Export Settings", 
                        f"Settings exported successfully to:\n{filepath}")
                    logger.debug(f"    Settings exported to: {filepath}")
                else:
                    QMessageBox.warning(self, "Export Warning",
                        "Export may have failed.\nCheck console for details.")
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to export settings:\n{str(e)}")
    
    def _import_settings(self) -> None:
        """Import settings from a file."""
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self,
                "Import Settings",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            if filepath:
                # Import via settings manager
                if self.settings_manager.import_settings(filepath):
                    # Update UI with imported settings
                    self._load_settings_into_ui()
                    
                    QMessageBox.information(self, "Import Settings", 
                        f"Settings imported successfully from:\n{filepath}\n\n" +
                        "The imported settings have been applied.")
                    logger.debug(f"    Settings imported from: {filepath}")
                else:
                    QMessageBox.warning(self, "Import Warning",
                        "Import may have failed.\nCheck console for details.")
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to import settings:\n{str(e)}")
    
    def _reset_settings_to_defaults(self) -> None:
        """Reset all settings to default values."""
        try:
            reply = QMessageBox.question(
                self,
                "Reset Settings",
                "Are you sure you want to reset all settings to defaults?\nThis cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Reset via settings manager
                self.settings_manager.reset_to_defaults()
                self.settings_manager.save_settings()
                
                # Update UI with default values
                self._load_settings_into_ui()
                
                QMessageBox.information(self, "Reset Complete", 
                    "All settings have been reset to defaults and saved.")
                logger.debug("    Settings reset to defaults")
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to reset settings:\n{str(e)}")
    
    def _load_settings_into_ui(self) -> None:
        """Load settings from settings manager into UI controls."""
        try:
            # General Preferences
            # CRITICAL FIX: Read theme from current theme_manager, not from settings file!
            # Settings file can be outdated if user switched themes using theme button
            if self.parent() and hasattr(self.parent(), 'ui_handler') and self.parent().ui_handler:
                current_theme = self.parent().ui_handler.theme_manager.current_theme
                theme_index = {"dark": 0, "light": 1, "image": 2, "auto": 3}.get(current_theme, 0)
                self.theme_combo.setCurrentIndex(theme_index)
                logger.debug(f"     Theme combo set to match CURRENT theme: '{current_theme}' (index {theme_index})")
            else:
                # Fallback to settings file if can't access theme manager
                theme = self.settings_manager.get("preferences.theme", "dark")
                theme_index = {"dark": 0, "light": 1, "image": 2, "auto": 3}.get(theme, 0)
                self.theme_combo.setCurrentIndex(theme_index)
                logger.debug(f"       Theme combo set from settings file: '{theme}' (index {theme_index})")
            
            self.autosave_check.setChecked(
                self.settings_manager.get("preferences.auto_save_colors", True))
            self.autoload_session_check.setChecked(
                self.settings_manager.get("preferences.auto_load_last_session", False))
            self.tooltips_check.setChecked(
                self.settings_manager.get("preferences.show_tooltips", True))
            
            # Color Slot Defaults
            default_weight = self.settings_manager.get("preferences.default_slot_weight", 50)
            self.default_weight_slider.setValue(default_weight)
            self.default_weight_label.setText(str(default_weight))
            
            max_slots = self.settings_manager.get("preferences.max_color_slots", 12)
            self.max_slots_spin.setText(str(max_slots))
            
            # History Settings
            self.history_enabled_check.setChecked(
                self.settings_manager.get("preferences.history_enabled", True))
            
            history_limit = self.settings_manager.get("preferences.history_size_limit", 50)
            self.history_limit_spin.setText(str(history_limit))
            
            # Export Settings
            export_format = self.settings_manager.get("preferences.default_export_format", "png")
            format_index = {"png": 0, "jpeg": 1, "json": 2, "ase": 3, "gpl": 4}.get(export_format, 0)
            self.export_format_combo.setCurrentIndex(format_index)
            
            # UI Preferences
            self.debug_overlays_check.setChecked(
                self.settings_manager.get("preferences.show_debug_overlays", False))
            # Apply the debug overlays setting immediately
            show_debug = self.settings_manager.get("preferences.show_debug_overlays", False)
            self._apply_debug_overlays_setting(show_debug)
            
            self.animations_check.setChecked(
                self.settings_manager.get("advanced.enable_animations", True))
            
            # Advanced Settings
            mixing_algo = self.settings_manager.get("advanced.color_mixing_algorithm", "weighted_rgb")
            # Map all mixing algorithms to combo box index
            algo_index_map = {
                "weighted_rgb": 0,
                "weighted_hsv": 1,
                "lab_perceptual": 2,
                "subtractive_cmy": 3,
                "weighted_ryb": 4,
                "kubelka_munk": 5
            }
            algo_index = algo_index_map.get(mixing_algo, 0)
            self.mixing_algo_combo.setCurrentIndex(algo_index)
            # Update the description label
            self._update_algo_description(algo_index)
            
            self.show_rgb_check.setChecked(
                self.settings_manager.get("advanced.show_rgb_values", True))
            self.show_hsv_check.setChecked(
                self.settings_manager.get("advanced.show_hsv_values", False))
            
            logger.info("    Settings loaded into UI")
            
        except Exception as e:
            logger.error(f"Error loading settings into UI: {e}")
            traceback.print_exc()
    
    def _save_ui_to_settings(self, skip_theme: bool = False) -> None:
        """Save UI control values to settings manager and emit change signals.
        
        Args:
            skip_theme: If True, don't emit theme signal (used when saving to file)
        """
        try:
            # General Preferences
            theme_map = {0: "dark", 1: "light", 2: "image", 3: "auto"}
            theme = theme_map.get(self.theme_combo.currentIndex(), "dark")
            logger.debug(f"     Saving theme: combo index={self.theme_combo.currentIndex()}, theme='{theme}'")
            self.settings_manager.set("preferences.theme", theme)
            
            # CRITICAL: Only emit theme signal if not skipping (i.e., Apply/OK, not Save)
            if not skip_theme:
                self.settings_changed.emit("theme", theme)  # Signal main app
            else:
                logger.debug("          Skipping theme signal emission (Save button)")
            
            auto_save = self.autosave_check.isChecked()
            self.settings_manager.set("preferences.auto_save_colors", auto_save)
            self.settings_changed.emit("auto_save_colors", auto_save)
            
            auto_load = self.autoload_session_check.isChecked()
            self.settings_manager.set("preferences.auto_load_last_session", auto_load)
            self.settings_changed.emit("auto_load_last_session", auto_load)
            
            show_tooltips = self.tooltips_check.isChecked()
            self.settings_manager.set("preferences.show_tooltips", show_tooltips)
            self.settings_changed.emit("show_tooltips", show_tooltips)
            
            # Color Slot Defaults
            default_weight = self.default_weight_slider.value()
            self.settings_manager.set("preferences.default_slot_weight", default_weight)
            self.settings_changed.emit("default_slot_weight", default_weight)
            
            try:
                max_slots = int(self.max_slots_spin.text())
                self.settings_manager.set("preferences.max_color_slots", max_slots)
                self.settings_changed.emit("max_color_slots", max_slots)
            except ValueError:
                pass  # Keep existing value if invalid
            
            # History Settings
            history_enabled = self.history_enabled_check.isChecked()
            self.settings_manager.set("preferences.history_enabled", history_enabled)
            self.settings_changed.emit("history_enabled", history_enabled)
            
            try:
                history_limit = int(self.history_limit_spin.text())
                self.settings_manager.set("preferences.history_size_limit", history_limit)
                self.settings_changed.emit("history_size_limit", history_limit)
            except ValueError:
                pass  # Keep existing value if invalid
            
            # Export Settings
            format_map = {0: "png", 1: "jpeg", 2: "json", 3: "ase", 4: "gpl"}
            export_format = format_map.get(self.export_format_combo.currentIndex(), "png")
            self.settings_manager.set("preferences.default_export_format", export_format)
            self.settings_changed.emit("default_export_format", export_format)
            
            # UI Preferences
            show_debug = self.debug_overlays_check.isChecked()
            self.settings_manager.set("preferences.show_debug_overlays", show_debug)
            self.settings_changed.emit("show_debug_overlays", show_debug)
            
            animations = self.animations_check.isChecked()
            self.settings_manager.set("advanced.enable_animations", animations)
            self.settings_changed.emit("enable_animations", animations)
            
            # Advanced Settings
            # Map all mixing algorithms from combo box index
            algo_map = {
                0: "weighted_rgb",
                1: "weighted_hsv",
                2: "lab_perceptual",
                3: "subtractive_cmy",
                4: "weighted_ryb",
                5: "kubelka_munk"
            }
            mixing_algo = algo_map.get(self.mixing_algo_combo.currentIndex(), "weighted_rgb")
            self.settings_manager.set("advanced.color_mixing_algorithm", mixing_algo)
            self.settings_changed.emit("color_mixing_algorithm", mixing_algo)
            
            show_rgb = self.show_rgb_check.isChecked()
            self.settings_manager.set("advanced.show_rgb_values", show_rgb)
            self.settings_changed.emit("show_rgb_values", show_rgb)
            
            show_hsv = self.show_hsv_check.isChecked()
            self.settings_manager.set("advanced.show_hsv_values", show_hsv)
            self.settings_changed.emit("show_hsv_values", show_hsv)
            
            logger.info("    UI values saved to settings + signals emitted")
            
        except Exception as e:
            logger.error(f"Error saving UI to settings: {e}")
            traceback.print_exc()
        
    def refresh_history(self) -> None:
        """
        Refresh history list with current data.
        
        Uses setUpdatesEnabled for batch updates (10-50x faster).
        """
        # Disable updates during batch operation
        self.history_list.setUpdatesEnabled(False)
        try:
            self.history_list.clear()
            
            if not self.color_history or not ColorHistory:
                # Show placeholder if no history available
                self._populate_history_placeholder()
                return
            
            entries = self.color_history.get_entries()
            
            if not entries:
                # Show empty state
                empty_item = QListWidgetItem("No color history yet. Mix some colors to get started!")
                empty_item.setForeground(QColor(128, 128, 128))
                self.history_list.addItem(empty_item)
                return
            
            # Import once outside loop for efficiency
            from core.color_math import ColorMath
            
            # Populate with real history
            for entry in entries:
                hex_color = ColorMath.rgb_to_hex(entry.color)
                display_time = entry.get_display_time()
                
                # Create colored square icon
                pixmap = QPixmap(20, 20)
                pixmap.fill(QColor(*entry.color))
                
                # Create list item
                item = QListWidgetItem(f"  {hex_color}  -  {display_time}")
                item.setIcon(QIcon(pixmap))
                item.setData(Qt.ItemDataRole.UserRole, entry.color)
                self.history_list.addItem(item)
            
            # Connect click event
            try:
                self.history_list.itemClicked.disconnect()
            except Exception:
                pass
            self.history_list.itemClicked.connect(self._on_history_item_clicked)
        finally:
            # Re-enable updates - triggers single repaint
            self.history_list.setUpdatesEnabled(True)
        
    def _populate_history_placeholder(self) -> None:
        """
        Populate history with placeholder items (fallback).
        
        Uses setUpdatesEnabled for batch updates.
        """
        placeholder_colors = [
            "#FF5733", "#33FF57", "#3357FF", "#FF33F5", "#F5FF33"
        ]
        
        # Disable updates during batch operation
        self.history_list.setUpdatesEnabled(False)
        try:
            from core.color_math import ColorMath
            
            for i, color_hex in enumerate(placeholder_colors):
                try:
                    color_rgb = ColorMath.hex_to_rgb(color_hex)
                    
                    # Create colored square icon
                    pixmap = QPixmap(20, 20)
                    pixmap.fill(QColor(*color_rgb))
                    
                    item = QListWidgetItem(f"  {color_hex}  -  Sample {i+1}")
                    item.setIcon(QIcon(pixmap))
                    item.setData(Qt.ItemDataRole.UserRole, color_rgb)
                    self.history_list.addItem(item)
                except Exception:
                    item = QListWidgetItem(f" {color_hex}  -  Sample {i+1}")
                    item.setData(Qt.ItemDataRole.UserRole, color_hex)
                    self.history_list.addItem(item)
                
            # Connect click event
            try:
                self.history_list.itemClicked.disconnect()
            except Exception:
                pass
            self.history_list.itemClicked.connect(self._on_history_item_clicked)
        finally:
            self.history_list.setUpdatesEnabled(True)
        
    def refresh_presets(self) -> None:
        """
        Refresh the presets list.
        
        Uses setUpdatesEnabled for batch updates.
        """
        # Disable updates during batch operation
        self.presets_list.setUpdatesEnabled(False)
        try:
            self.presets_list.clear()
            
            if not self.preset_palettes:
                self._populate_presets_placeholder()
                return
            
            # Get all presets
            all_presets = self.preset_palettes.get_all_presets()
            
            # Get selected category
            selected_category = self.category_combo.currentText()
            
            # Filter by category
            if selected_category == " User Presets":
                # Show only user-created presets
                presets = [p for p in all_presets if self._is_user_preset(p)]
                
                # === EMPTY STATE HANDLING ===
                if not presets:
                    item = QListWidgetItem(
                        " No user presets yet\n\n"
                        "Click ' Save Current as Preset' to create\n"
                        "your first custom color palette!"
                    )
                    item.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable
                    item.setForeground(QColor(_theme_colors(True)['accent']))  # Gold text
                    self.presets_list.addItem(item)
                    self.delete_preset_btn.setEnabled(False)
                    
                    # Populate categories combo if empty
                    if self.category_combo.count() == 0:
                        categories = ["All", " User Presets"] + self.preset_palettes.get_categories()
                        self.category_combo.blockSignals(True)
                        self.category_combo.addItems(categories)
                        self.category_combo.blockSignals(False)
                    return
                # === END EMPTY STATE ===
                
            elif selected_category and selected_category != "All":
                # Show presets from specific category
                presets = [p for p in all_presets if p.category == selected_category]
                
                # === EMPTY STATE FOR CATEGORIES ===
                if not presets:
                    item = QListWidgetItem(
                        f" No presets in '{selected_category}' category\n\n"
                        "Select 'All' to see all available presets."
                    )
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(QColor(_theme_colors(True).get('text_disabled', config.ThemeManager.DARK_THEME['text_disabled'])))
                    self.presets_list.addItem(item)
                    self.delete_preset_btn.setEnabled(False)
                    
                    if self.category_combo.count() == 0:
                        categories = ["All", " User Presets"] + self.preset_palettes.get_categories()
                        self.category_combo.blockSignals(True)
                        self.category_combo.addItems(categories)
                        self.category_combo.blockSignals(False)
                    return
                # === END EMPTY STATE ===
            else:
                # Show all presets
                presets = all_presets
            
            # Populate categories combo if empty
            if self.category_combo.count() == 0:
                        categories = ["All", " User Presets"] + self.preset_palettes.get_categories()
                        self.category_combo.blockSignals(True)
                        self.category_combo.addItems(categories)
                        self.category_combo.blockSignals(False)
            
            # Add each preset
            for preset in presets:
                item = self._create_preset_list_item(preset)
                self.presets_list.addItem(item)
            
            logger.info(f"    Loaded {len(presets)} presets")
            
        except Exception as e:
            logger.error(f"Error refreshing presets: {e}")
            traceback.print_exc()
            self._populate_presets_placeholder()
        finally:
            # Re-enable updates - triggers single repaint
            self.presets_list.setUpdatesEnabled(True)
    
    def _create_preset_list_item(self, preset: 'PresetPalette') -> QListWidgetItem:
        """Create a list item for a preset with color preview."""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout
        
        # Check if user preset
        is_user = self._is_user_preset(preset)
        user_indicator = " " if is_user else ""
        
        # Create item text with user indicator
        text = f"{user_indicator}{preset.icon} {preset.name}\n{preset.description}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, preset)
        
        # Create color preview pixmap (shows first 6 colors)
        preview_colors = preset.colors[:6]
        swatch_size = 20
        pixmap = QPixmap(swatch_size * len(preview_colors), swatch_size)
        painter = QPainter(pixmap)
        
        for i, color in enumerate(preview_colors):
            painter.fillRect(i * swatch_size, 0, swatch_size, swatch_size, QColor(*color))
        
        painter.end()
        
        # Set icon
        item.setIcon(QIcon(pixmap))
        
        return item
    
    def _populate_presets_placeholder(self) -> None:
        """Populate presets with placeholder items (fallback)."""
        presets = [
            (" Rainbow", "7 vibrant colors"),
            (" Earth Tones", "Natural browns and greens"),
            (" Pastels", "Soft, delicate colors"),
            (" Grayscale", "Black to white spectrum"),
            (" Neon", "Bright, electric colors"),
            (" Ocean", "Blues and teals"),
            (" Fire", "Reds, oranges, yellows"),
        ]
        
        for name, desc in presets:
            item = QListWidgetItem(f"{name}\n{desc}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.presets_list.addItem(item)
    
    def _on_category_changed(self, category: str) -> None:
        """Handle category filter change."""
        self.refresh_presets()
    
    def _on_preset_clicked(self, item: QListWidgetItem) -> None:
        """Handle single click on preset."""
        try:
            # Get preset from item data
            preset = item.data(Qt.ItemDataRole.UserRole)
            
            if preset and self.preset_palettes:
                # Check if this is a user preset (not built-in)
                is_user_preset = self._is_user_preset(preset)
                self.delete_preset_btn.setEnabled(is_user_preset)
                
                # Update tooltip based on preset type
                if is_user_preset:
                    self.delete_preset_btn.setToolTip(f"Delete '{preset.name}' preset")
                else:
                    self.delete_preset_btn.setToolTip("Cannot delete system presets")
            else:
                self.delete_preset_btn.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Error handling preset click: {e}")
            self.delete_preset_btn.setEnabled(False)
    
    def _on_preset_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double click on preset - load immediately."""
        self._load_selected_preset()
    
    def _load_selected_preset(self) -> None:
        """Load the selected preset."""
        try:
            selected_items = self.presets_list.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "No Selection", "Please select a preset to load")
                return
            
            item = selected_items[0]
            preset_data = item.data(Qt.ItemDataRole.UserRole)
            
            if not preset_data:
                return
            
            # If it's a PresetPalette object
            if hasattr(preset_data, 'colors'):
                colors = preset_data.colors
                preset_name = preset_data.name
            else:
                # Fallback when preset data is unavailable
                QMessageBox.information(self, "Preset Unavailable", 
                    "This preset cannot be loaded at this time.")
                return
            
            # Emit signal to load preset
            self.load_preset.emit(colors, preset_name)
            
            # Show confirmation
            self.parent().status_updated.emit(f"Loaded preset: {preset_name}")
            
        except Exception as e:
            logger.error(f"Error loading preset: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load preset:\n{str(e)}")
    
    def _save_current_as_preset(self) -> None:
        """Save current colors as a new preset."""
        from PyQt6.QtWidgets import QInputDialog, QComboBox
        import re
        
        try:
            # Get preset name from user
            name, ok = QInputDialog.getText(
                self, 
                "Save as Preset",
                "Enter preset name:",
                QLineEdit.EchoMode.Normal,
                "My Custom Palette"
            )
            
            if not ok or not name:
                return
            
            # === INPUT VALIDATION ===
            # Sanitize input
            name = name.strip()
            
            # Check for empty name
            if len(name) == 0:
                QMessageBox.warning(self, "Invalid Name", "Preset name cannot be empty.")
                return
            
            # Length check
            if len(name) > 100:
                QMessageBox.warning(self, "Name Too Long", 
                    "Preset name must be 100 characters or less.")
                return
            
            # Character validation (alphanumeric, spaces, hyphens, underscores, periods)
            if not re.match(r'^[\w\s\-\.]+$', name):
                QMessageBox.warning(self, "Invalid Characters", 
                    "Preset name can only contain letters, numbers, spaces, hyphens, underscores, and periods.")
                return
            
            # === DUPLICATE CHECK ===
            if self.preset_palettes and self.preset_palettes.get_preset_by_name(name):
                # Check if it's a system preset (can't overwrite)
                if not self._is_user_preset(self.preset_palettes.get_preset_by_name(name)):
                    QMessageBox.warning(self, "Cannot Overwrite", 
                        f"'{name}' is a system preset and cannot be overwritten.\n\n"
                        "Please choose a different name.")
                    return
                
                # User preset - offer to overwrite
                reply = QMessageBox.question(
                    self,
                    "Preset Exists",
                    f"A preset named '{name}' already exists.\n\n"
                    "Overwrite existing preset?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Delete old preset first
                    self.preset_palettes.remove_custom_preset(name)
                else:
                    # User chose not to overwrite
                    return
            
            # Get description
            description, ok = QInputDialog.getText(
                self, 
                "Preset Description",
                "Enter description (optional):",
                QLineEdit.EchoMode.Normal,
                ""
            )
            
            if not ok:
                description = ""
            
            # Emit signal to save current colors
            self.save_as_preset.emit(name, description)
            
        except Exception as e:
            logger.error(f"Error saving preset: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save preset:\n{str(e)}")
    
    def _is_user_preset(self, preset: 'PresetPalette') -> bool:
        """
        Check if a preset is user-created (not a built-in system preset).
        
        Args:
            preset: Preset to check
            
        Returns:
            True if user-created, False if system preset
        """
        try:
            if not self.preset_palettes:
                return False
            
            # Check if preset name matches any built-in preset
            built_in_names = [p.name for p in self.preset_palettes.BUILT_IN_PRESETS]
            return preset.name not in built_in_names
            
        except Exception as e:
            logger.error(f"Error checking if preset is user-created: {e}")
            return False
    
    def _delete_selected_preset(self) -> None:
        """Delete the currently selected user preset."""
        try:
            # Get selected item
            selected_item = self.presets_list.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "No Selection", "Please select a preset to delete.")
                return
            
            # Get preset from item
            preset = selected_item.data(Qt.ItemDataRole.UserRole)
            if not preset:
                return
            
            # Verify it's a user preset
            if not self._is_user_preset(preset):
                QMessageBox.warning(
                    self, 
                    "Cannot Delete", 
                    f"'{preset.name}' is a system preset and cannot be deleted."
                )
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the preset '{preset.name}'?\n\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Delete the preset
            if self.preset_palettes and self.preset_palettes.remove_custom_preset(preset.name):
                QMessageBox.information(
                    self,
                    "Preset Deleted",
                    f"Preset '{preset.name}' has been deleted successfully."
                )
                
                # Refresh the list
                self.refresh_presets()
                
                # Disable delete button since nothing is selected
                self.delete_preset_btn.setEnabled(False)
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete preset '{preset.name}'."
                )
                
        except Exception as e:
            logger.error(f"Error deleting preset: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to delete preset:\n{str(e)}")
    
    # ===== Harmony Tab Methods =====
    
    def update_base_color_options(self, current_colors: list) -> None:
        """
        Update the base color dropdown with current slot colors.
        
        Args:
            current_colors: List of (color, weight) tuples from current slots
        """
        try:
            self.harmony_base_combo.clear()
            
            if not current_colors:
                self.harmony_base_combo.addItem("No colors in slots", None)
                return
            
            for i, (color, weight) in enumerate(current_colors):
                if weight > 0:  # Only include colors with non-zero weight
                    from core.color_math import ColorMath
                    hex_color = ColorMath.rgb_to_hex(color)
                    
                    # Create color preview icon
                    pixmap = QPixmap(20, 20)
                    pixmap.fill(QColor(*color))
                    icon = QIcon(pixmap)
                    
                    self.harmony_base_combo.addItem(icon, f"Color {i+1}: {hex_color}", color)
            
            # If no colors with weight, show message
            if self.harmony_base_combo.count() == 0:
                self.harmony_base_combo.addItem("No colors with weight > 0", None)
                
        except Exception as e:
            logger.error(f"Error updating base color options: {e}")
    
    def _on_base_color_changed(self, index: int) -> None:
        """Handle base color selection change."""
        try:
            # Regenerate harmony if we have a valid color selected
            if index >= 0:
                self._generate_harmony()
        except Exception as e:
            logger.error(f"Error in base color change: {e}")
    
    def _refresh_base_colors(self) -> None:
        """Refresh base color dropdown from main app slots."""
        try:
            # Get parent window (main app)
            parent = self.parent()
            if parent and hasattr(parent, 'slots'):
                # Get current colors from slots
                current_colors = [(slot.get_color(), slot.get_weight()) for slot in parent.slots]
                self.update_base_color_options(current_colors)
                logger.debug("    Refreshed base color options from slots")
            else:
                QMessageBox.warning(self, "Refresh Failed", 
                    "Could not access slot colors. Please reopen the panel.")
        except Exception as e:
            logger.error(f"Error refreshing base colors: {e}")
            traceback.print_exc()
    
    def _on_harmony_type_changed(self, index: int) -> None:
        """Handle harmony type selection change."""
        try:
            if not ColorHarmony or not HarmonyType:
                return
            
            harmony_name = self.harmony_type_combo.currentText()
            
            # Find matching HarmonyType
            harmony_type = None
            for ht in HarmonyType:
                if ht.value == harmony_name:
                    harmony_type = ht
                    break
            
            if harmony_type:
                description = ColorHarmony.get_harmony_description(harmony_type)
                self.harmony_description.setText(f"  {description}")
            
            # Regenerate harmony with new type
            self._generate_harmony()
            
        except Exception as e:
            logger.error(f"Error in harmony type change: {e}")
    
    def _generate_harmony(self) -> None:
        """
        Generate and display harmony colors.
        
        Uses setUpdatesEnabled for batch updates.
        """
        # Disable updates during batch operation
        self.harmony_preview_list.setUpdatesEnabled(False)
        try:
            if not ColorHarmony or not HarmonyType:
                self.harmony_preview_list.clear()
                item = QListWidgetItem("  Color Harmony module not available")
                self.harmony_preview_list.addItem(item)
                return
            
            # Get base color
            base_color = self.harmony_base_combo.currentData()
            if not base_color:
                self.harmony_preview_list.clear()
                item = QListWidgetItem("  Please select a base color first")
                self.harmony_preview_list.addItem(item)
                return
            
            # Get harmony type
            harmony_name = self.harmony_type_combo.currentText()
            harmony_type = None
            for ht in HarmonyType:
                if ht.value == harmony_name:
                    harmony_type = ht
                    break
            
            if not harmony_type:
                return
            
            # Generate harmony
            harmony_colors = ColorHarmony.generate_harmony(base_color, harmony_type)
            
            # Display in preview list
            self.harmony_preview_list.clear()
            
            from core.color_math import ColorMath
            for i, color in enumerate(harmony_colors):
                hex_color = ColorMath.rgb_to_hex(color)
                
                # Create color swatch
                pixmap = QPixmap(40, 40)
                pixmap.fill(QColor(*color))
                icon = QIcon(pixmap)
                
                # Create list item
                item = QListWidgetItem(icon, f"  {hex_color}  rgb{color}")
                item.setData(Qt.ItemDataRole.UserRole, color)
                self.harmony_preview_list.addItem(item)
            
            logger.debug(f"    Generated {len(harmony_colors)} colors for {harmony_name} harmony")
            
        except Exception as e:
            logger.error(f"Error generating harmony: {e}")
            traceback.print_exc()
            
            self.harmony_preview_list.clear()
            item = QListWidgetItem(f" Error: {str(e)}")
            self.harmony_preview_list.addItem(item)
        finally:
            # Re-enable updates - triggers single repaint
            self.harmony_preview_list.setUpdatesEnabled(True)
    
    def _apply_harmony_to_slots(self) -> None:
        """Apply generated harmony colors to color slots."""
        try:
            # Get colors from preview list
            harmony_colors = []
            for i in range(self.harmony_preview_list.count()):
                item = self.harmony_preview_list.item(i)
                color = item.data(Qt.ItemDataRole.UserRole)
                if color:
                    harmony_colors.append(color)
            
            if not harmony_colors:
                QMessageBox.warning(self, "No Colors", "Please generate a harmony first.")
                return
            
            # Get base color and harmony type for signal
            base_color = self.harmony_base_combo.currentData()
            harmony_type_name = self.harmony_type_combo.currentText()
            
            if not base_color:
                QMessageBox.warning(self, "No Base Color", "Please select a base color.")
                return
            
            # Emit signal with harmony colors
            # The main app will handle loading these into slots
            self.apply_harmony.emit(harmony_type_name, base_color)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Harmony Applied", 
                f"Applied {len(harmony_colors)} colors from {harmony_type_name} harmony to slots!"
            )
            
        except Exception as e:
            logger.error(f"Error applying harmony: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to apply harmony:\n{str(e)}")
        

    def _on_history_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle history item click."""
        color_data = item.data(Qt.ItemDataRole.UserRole)
        
        if color_data:
            # If it's a hex string, convert to RGB
            if isinstance(color_data, str):
                try:
                    from core.color_math import ColorMath
                    color_rgb = ColorMath.hex_to_rgb(color_data)
                except Exception:
                    QMessageBox.warning(self, "Invalid Color", f"Could not parse color: {color_data}")
                    return
            else:
                color_rgb = color_data
            
            # Emit signal to load color
            self.load_history_color.emit(color_rgb)
            
            # Show confirmation
            from core.color_math import ColorMath
            hex_color = ColorMath.rgb_to_hex(color_rgb)
            self.parent().status_updated.emit(f"Loaded {hex_color} from history")
        
    def _on_preset_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle preset item click."""
        preset_name = item.data(Qt.ItemDataRole.UserRole)
        QMessageBox.information(self, "Presets", 
                              f"Preset '{preset_name}' selected.\n\n" +
                              f"Double-click to load into slots.")
        
    def _clear_history(self) -> None:
        """Clear color history."""
        if not self.color_history:
            QMessageBox.information(self, "Clear History", 
                                  "No color history available.")
            return
        
        # Confirm
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all color history?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.color_history.clear()
            self.refresh_history()
            QMessageBox.information(self, "History Cleared", "Color history has been cleared.")
        
    def _export_history(self) -> None:
        """Export color history."""
        if not self.color_history:
            QMessageBox.information(self, "Export History", 
                                  "No color history available.")
            return
        
        entries = self.color_history.get_entries()
        if not entries:
            QMessageBox.information(self, "Export History", 
                                  "No colors in history to export.")
            return
        
        # File dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Color History",
            "",
            "JSON File (*.json);;HTML File (*.html);;Text File (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            success = self.color_history.export_to_file(file_path)
            
            if success:
                import os
                filename = os.path.basename(file_path)
                QMessageBox.information(self, "Export Successful", 
                                      f"History exported to:\n{filename}")
            else:
                QMessageBox.critical(self, "Export Failed", 
                                   "Failed to export color history.")
    
    # =========================================================================
    # SESSION MANAGEMENT METHODS
    # =========================================================================
    
    def _refresh_sessions_list(self) -> None:
        """Refresh the sessions list from disk."""
        self.sessions_list.clear()
        
        if not self.session_manager or not SessionManager:
            # Show placeholder
            item = QListWidgetItem("Session Manager not available")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.sessions_list.addItem(item)
            return
        
        # Get recent sessions
        sessions = self.session_manager.get_recent_sessions()
        
        if not sessions:
            item = QListWidgetItem("No recent sessions\n\nClick 'Save Current Session' to get started!")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.sessions_list.addItem(item)
            return
        
        # Populate list
        for session_info in sessions:
            # Format: "Session Name\n   Date - 5 colors"
            name = session_info.get('name', 'Unnamed')
            modified = session_info.get('modified', '')
            color_count = session_info.get('color_count', 0)
            
            # Parse date nicely
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(modified)
                date_str = dt.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                date_str = modified[:10] if modified else "Unknown"
            
            item_text = f" {name}\n   {date_str} - {color_count} colors"
            item = QListWidgetItem(item_text)
            
            # Store filepath in item data
            item.setData(Qt.ItemDataRole.UserRole, session_info.get('filepath'))
            
            self.sessions_list.addItem(item)
        
        logger.info(f"    Loaded {len(sessions)} recent sessions")
    
    def _on_save_session(self) -> None:
        """Handle Save Session button click."""
        if not self.session_manager or not SessionManager:
            QMessageBox.warning(self, "Not Available", 
                              "Session Manager is not available.")
            return
        
        # Ask for session name
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self,
            "Save Session",
            "Enter a name for this session:",
            QLineEdit.EchoMode.Normal,
            f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if not ok or not name:
            return
        
        # Generate filename
        filepath = self.session_manager.generate_session_filename(name)
        
        # Emit signal to main app to save
        self.save_session.emit(filepath)
        
        # Refresh list
        self._refresh_sessions_list()
        
        # Success message
        QMessageBox.information(self, "Session Saved", 
                              f"Session '{name}' saved successfully!")
    
    def _on_load_session(self) -> None:
        """Handle Load Session button click."""
        selected_items = self.sessions_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", 
                              "Please select a session to load.")
            return
        
        self._load_selected_session()
    
    def _on_session_double_click(self, item: QListWidgetItem) -> None:
        """Handle double-click on session item."""
        self._load_selected_session()
    
    def _load_selected_session(self) -> None:
        """Load the currently selected session."""
        selected_items = self.sessions_list.selectedItems()
        
        if not selected_items:
            return
        
        item = selected_items[0]
        filepath = item.data(Qt.ItemDataRole.UserRole)
        
        if not filepath:
            return
        
        # Emit signal to main app to load
        self.load_session.emit(filepath)
        
        # Close dialog
        self.accept()
    
    def _on_delete_session(self) -> None:
        """Handle Delete Session button click."""
        selected_items = self.sessions_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", 
                              "Please select a session to delete.")
            return
        
        if not self.session_manager or not SessionManager:
            return
        
        item = selected_items[0]
        filepath = item.data(Qt.ItemDataRole.UserRole)
        
        if not filepath:
            return
        
        # Get session name
        name = self.session_manager.get_session_info(filepath).get('name', 'this session')
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{name}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.session_manager.delete_session(filepath)
            
            if success:
                self._refresh_sessions_list()
                QMessageBox.information(self, "Deleted", 
                                      f"Session '{name}' deleted successfully.")
            else:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to delete session '{name}'.")
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize — update logo overlay position each frame."""
        super().resizeEvent(event)
        self._do_update_logo_visibility()
    
    def showEvent(self, event: QShowEvent) -> None:
        """Handle show event — pin content height and update logo overlay."""
        super().showEvent(event)
        # Hard-pin the Quick Actions content container on first show.
        # By showEvent, all stylesheets (including section-label margins) have
        # been applied, so sizeHint() is accurate.  setFixedHeight() is a hard
        # constraint the layout engine cannot override, unlike setSizePolicy(Fixed).
        if not getattr(self, '_qa_heights_pinned', False):
            cw = getattr(self, '_qa_content_widget', None)
            if cw:
                h = cw.sizeHint().height()
                if h > 0:
                    cw.setFixedHeight(h)
            self._qa_heights_pinned = True
        self._update_logo_visibility()
    
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle close event with proper cleanup.
        
        Final Optimization: Ensures resources are released when dialog closes.
        """
        try:
            # Save panel height if remember_size is enabled (width is locked)
            if hasattr(self, 'settings_manager') and self.settings_manager:
                remember_size = self.settings_manager.get('window.remember_size', True)
                if remember_size:
                    self.settings_manager.set('window.package_d_height', self.height())
                    if logger:
                        logger.debug(f"Saved Package D panel height: {self.height()}")
            
            # Clear list widgets to release item references
            if hasattr(self, 'history_list') and self.history_list:
                self.history_list.clear()
            if hasattr(self, 'presets_list') and self.presets_list:
                self.presets_list.clear()
            if hasattr(self, 'sessions_list') and self.sessions_list:
                self.sessions_list.clear()
            if hasattr(self, 'harmony_preview_list') and self.harmony_preview_list:
                self.harmony_preview_list.clear()
            
            # Clear logo pixmap reference
            if hasattr(self, 'quick_actions_logo') and self.quick_actions_logo:
                self.quick_actions_logo.setPixmap(QPixmap())  # Release pixmap
            
            if logger:
                logger.debug("PackageDPanel closed with cleanup")
                
        except Exception as e:
            if logger:
                logger.error(f"Error in PackageDPanel closeEvent: {e}")
        
        super().closeEvent(event)
    
    def _update_logo_visibility(self) -> None:
        """Update logo overlay — called from showEvent."""
        self._do_update_logo_visibility()

    def _do_update_logo_visibility(self) -> None:
        """Position the logo using setGeometry (absolute overlay, not in layout).

        Because the logo is a child of the tab widget but NOT part of its
        QVBoxLayout, calling setGeometry here does NOT invalidate the parent
        layout.  Qt just schedules a repaint of that region — no second layout
        pass, no jitter, smooth pixel-perfect reveal on every resize event.

        Phase 1: panel grows beyond threshold → reveal bottom of logo upward.
                 AlignBottom means Qt clips the TOP of the pixmap, so the
                 bottom of the image appears first as the widget grows.
        Phase 2: extra space exceeds logo height → scale the pixmap to fill.
        """
        if not (hasattr(self, 'quick_actions_logo') and self.quick_actions_logo
                and hasattr(self, '_logo_height') and self._logo_height > 0):
            return
        if not hasattr(self, '_qa_tab_widget'):
            return

        extra_space = self.height() - config.PACKAGE_D_MIN_HEIGHT
        tab         = self._qa_tab_widget
        tab_w       = tab.width()
        tab_h       = tab.height()
        max_w       = tab_w - 60

        if extra_space <= 0:
            self.quick_actions_logo.hide()
            return

        if extra_space <= self._logo_height:
            # Phase 1: reveal — restore original (unscaled) pixmap
            if hasattr(self, '_logo_pixmap') and self._logo_pixmap:
                self.quick_actions_logo.setPixmap(self._logo_pixmap)
            reveal_h = extra_space
            logo_w   = min(self._logo_width, max_w)
        else:
            # Phase 2: fully revealed — scale pixmap to fill extra space
            scale_h = extra_space
            source  = (getattr(self, '_logo_pixmap_original', None)
                       or getattr(self, '_logo_pixmap', None))
            if source:
                scaled = source.scaledToHeight(
                    int(scale_h), Qt.TransformationMode.SmoothTransformation
                )
                if scaled.width() > max_w:
                    scaled = source.scaledToWidth(
                        int(max_w), Qt.TransformationMode.SmoothTransformation
                    )
                    scale_h = scaled.height()
                self.quick_actions_logo.setPixmap(scaled)
            pm       = self.quick_actions_logo.pixmap()
            logo_w   = min(pm.width() if pm and not pm.isNull() else self._logo_width, max_w)
            reveal_h = int(scale_h)

        logo_x = (tab_w - logo_w) // 2
        logo_y = tab_h - reveal_h

        # setGeometry on a widget outside its parent's layout = pure paint op, no layout pass
        self.quick_actions_logo.setGeometry(logo_x, logo_y, logo_w, reveal_h)
        self.quick_actions_logo.raise_()   # paint above the stretch area
        self.quick_actions_logo.show()

        
    def _apply_widget_stylesheet(self, t: dict) -> None:
        """Apply theme colors to individual widgets that can't be covered
        by the dialog-level setStyleSheet (labels, checkboxes, key badges).
        Called from set_theme() on every theme change.
        """
        accent      = t['accent']
        bg          = t['panel_bg']
        border      = t['border_color']
        text        = t['text_color']
        bg2         = t['panel_secondary']
        bg_hover    = t['panel_hover']
        accent_on   = t['accent_on']
        accent_hov  = t['accent_hover']
        pressed_bg  = t['button_pressed_bg']
        disabled    = t['text_disabled']

        label_style = (
            f"font-weight: bold; font-size: {config.FONT_SIZES['medium']}px; "
            f"color: {accent}; margin-top: 15px; margin-bottom: 5px;"
        )
        for attr in ('_shortcuts_label', '_export_label', '_palette_label', '_picker_label'):
            widget = getattr(self, attr, None)
            if widget:
                widget.setStyleSheet(label_style)

        # Checkbox indicators — needs per-widget setStyleSheet because
        # QCheckBox::indicator rules only apply from direct widget stylesheet
        cb_style = f"""
            QCheckBox::indicator {{
                width: 13px; height: 13px; border-radius: 2px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {bg};
                border: 1px solid {disabled};
            }}
            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid {accent};
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border: 1px solid {accent};
                image: none;
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {accent_hov};
                border: 1px solid {accent_hov};
            }}
        """
        for checkbox in getattr(self, '_themed_checkboxes', []):
            if checkbox:
                checkbox.setStyleSheet(cb_style)

        # Dialog-level widget stylesheet — buttons, inputs, lists, sliders
        # Using {{ }} to escape CSS braces inside the f-string
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QTabWidget::pane {{
                border: 1px solid {border};
                background-color: {bg};
            }}
            QTabBar::tab {{
                background-color: {bg2};
                color: {text};
                padding: 8px 16px;
                border: 1px solid {border};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {t.get('tab_selected_bg', bg)};
                color: {accent};
                border-bottom: 2px solid {accent};
            }}
            QTabBar::tab:hover {{
                background-color: {bg_hover};
                color: {accent};
            }}
            QPushButton {{
                background-color: {bg2};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
                border-color: {accent};
                color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
                border-color: {pressed_bg};
                color: {accent_on};
            }}
            QPushButton:disabled {{
                background-color: {border};
                color: {disabled};
                border-color: {border};
            }}
            QLineEdit, QSpinBox {{
                background-color: {t['input_bg']};
                color: {t['input_text']};
                border: 1px solid {border};
                padding: 4px;
                border-radius: 3px;
                selection-background-color: {accent};
                selection-color: {accent_on};
            }}
            QLineEdit:focus, QSpinBox:focus {{
                border-color: {accent};
            }}
            QComboBox {{
                background-color: {bg2};
                color: {text};
                border: 1px solid {border};
                padding: 4px 8px;
                border-radius: 3px;
            }}
            QComboBox:hover {{
                border-color: {accent};
            }}
            QComboBox::drop-down {{
                border-left: 1px solid {border};
            }}
            QSlider::groove:horizontal {{
                background: {t['input_bg']};
                border: 1px solid {border};
                height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: 1px solid {accent};
                width: 14px; height: 14px;
                margin: -5px 0; border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {accent_hov};
            }}
            QScrollBar:vertical {{
                background: {t.get('scrollbar_bg', bg)};
                width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.get('scrollbar_handle', border)};
                border-radius: 4px; min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t.get('scrollbar_hover', accent)};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QLabel[class="section-header"] {{
                color: {accent}; font-weight: bold;
            }}
            /* Primary action buttons inherit standard QPushButton styling */
        """)

    def _apply_list_view_styles(self, is_dark: bool = True) -> None:
        """Apply brand selection/hover colors directly to all list widgets.

        Same problem as combo popups — QListWidget selected items on Windows
        Fusion read QPalette.Highlight for the focused selection fill, ignoring
        the parent dialog's cascaded stylesheet. Setting stylesheet AND palette
        directly on each QListWidget is the only reliable fix.
        """
        from PyQt6.QtGui import QPalette, QColor

        t             = _theme_colors(is_dark)
        bg_col        = t.get('scroll_bg',    t['panel_bg'])
        text_col      = t['text_color']
        border_col    = t['border_color']
        hover_bg      = t['panel_hover']
        accent_col    = t['accent']
        accent_on_col = t['accent_on']

        list_ss = f"""
                QListWidget {{
                    background-color: {bg_col};
                    color: {text_col};
                    border: 1px solid {border_col};
                    outline: 0;
                }}
                QListWidget::item {{
                    padding: 8px 10px;
                    border-bottom: 1px solid {border_col};
                    color: {text_col};
                }}
                QListWidget::item:hover {{
                    background-color: {hover_bg};
                    color: {accent_col};
                }}
                QListWidget::item:selected,
                QListWidget::item:selected:active,
                QListWidget::item:selected:!active {{
                    background-color: {accent_col};
                    color: {accent_on_col};
                }}
            """
        highlight      = QColor(accent_col)
        highlight_text = QColor(accent_on_col)
        base           = QColor(bg_col)
        text           = QColor(text_col)

        lists = [
            getattr(self, 'history_list', None),
            getattr(self, 'presets_list', None),
            getattr(self, 'sessions_list', None),
            getattr(self, 'harmony_preview_list', None),
        ]
        for widget in lists:
            if widget is None:
                continue
            widget.setStyleSheet(list_ss)

            # Set palette on each widget for all color groups — Qt reads
            # QPalette.Highlight for focused AND inactive selected items
            palette = widget.palette()
            for group in (QPalette.ColorGroup.Active,
                          QPalette.ColorGroup.Inactive,
                          QPalette.ColorGroup.Normal):
                palette.setColor(group, QPalette.ColorRole.Highlight,       highlight)
                palette.setColor(group, QPalette.ColorRole.HighlightedText, highlight_text)
                palette.setColor(group, QPalette.ColorRole.Base,            base)
                palette.setColor(group, QPalette.ColorRole.Text,            text)
            widget.setPalette(palette)

    def _apply_combo_view_styles(self, is_dark: bool = True) -> None:
        """Apply brand hover/selection colors to all combo box dropdowns.

        Uses _BrandComboDelegate which paints directly in Python, bypassing
        Qt Fusion's native item delegate that ignores stylesheet hover rules
        on Windows.
        """
        from PyQt6.QtGui import QPalette, QColor

        combos = [
            getattr(self, 'harmony_type_combo', None),
            getattr(self, 'harmony_base_combo', None),
            getattr(self, 'category_combo', None),
            getattr(self, 'theme_combo', None),
            getattr(self, 'export_format_combo', None),
            getattr(self, 'mixing_algo_combo', None),
        ]

        t               = _theme_colors(is_dark)
        highlight_color = QColor(t['accent'])
        highlight_text  = QColor(t['accent_on'])
        base_color      = QColor(t['panel_secondary'])
        text_color      = QColor(t['text_color'])

        for combo in combos:
            if combo is None:
                continue

            view = combo.view()

            # Install or update the custom delegate
            existing = view.itemDelegate()
            if isinstance(existing, _BrandComboDelegate):
                existing.set_dark(is_dark)
            else:
                delegate = _BrandComboDelegate(view, is_dark=is_dark)
                view.setItemDelegate(delegate)

            # Enable mouse tracking so hover events reach the delegate
            view.setMouseTracking(True)

            # Set palette so the combobox border/bg also uses brand colors
            palette = view.palette()
            palette.setColor(QPalette.ColorRole.Base,            base_color)
            palette.setColor(QPalette.ColorRole.Text,            text_color)
            palette.setColor(QPalette.ColorRole.Highlight,       highlight_color)
            palette.setColor(QPalette.ColorRole.HighlightedText, highlight_text)
            view.setPalette(palette)


    def set_theme(self, is_dark: bool) -> None:
        """Apply theme to the dialog — all colors sourced from ThemeManager."""
        t = _theme_colors(is_dark)

        # Apply all widget-level theme styles (labels, checkboxes, buttons, stylesheet)
        self._apply_widget_stylesheet(t)
        # Re-apply combo view hover styles after theme change
        self._apply_combo_view_styles(is_dark=is_dark)
        # Re-apply list view selection styles after theme change
        self._apply_list_view_styles(is_dark=is_dark)

        # Set dialog palette so QListWidget focused-selection uses brand gold,
        # not the system blue. Qt reads QPalette.Highlight for focused items
        # regardless of stylesheet — dialog must have its own palette set.
        from PyQt6.QtGui import QPalette, QColor
        t2 = _theme_colors(is_dark)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Highlight,       QColor(t2['accent']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(t2['accent_on']))
        palette.setColor(QPalette.ColorRole.Base,            QColor(t2['input_bg']))
        palette.setColor(QPalette.ColorRole.Text,            QColor(t2['text_color']))
        palette.setColor(QPalette.ColorRole.Window,          QColor(t2['panel_bg']))
        palette.setColor(QPalette.ColorRole.WindowText,      QColor(t2['text_color']))
        self.setPalette(palette)