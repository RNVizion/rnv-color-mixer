"""
About Dialog - Application Information and Help
Accessible via Ctrl+/ keyboard shortcut

Displays:
- Application name, version, description
- Feature list
- Keyboard shortcuts reference
- System information
- Credits
"""

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QCloseEvent

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("AboutDialog")
except ImportError:
    logger = None

# Import config for app info
try:
    from utils import config
except ImportError:
    config = None


class AboutDialog(QDialog):
    """About dialog with application information, features, and keyboard shortcuts."""
    
    def __init__(self, parent: QWidget | None = None, is_dark: bool = True) -> None:
        # Don't pass parent to avoid stylesheet inheritance issues
        super().__init__(None)
        
        self._is_dark = is_dark
        
        self.setWindowTitle("About RNV Color Mixer")
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.MSWindowsFixedSizeDialogHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setFixedSize(500, 680)
        
        self._build_ui()
        self._apply_theme()
        
        if logger:
            logger.success("About dialog initialized")
    
    def _build_ui(self) -> None:
        """Build the about dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header section with app name and version
        header = self._create_header()
        layout.addWidget(header)
        
        # Tab widget for organized content
        self.tabs = QTabWidget()
        
        # Create tabs
        about_tab = self._create_about_tab()
        features_tab = self._create_features_tab()
        shortcuts_tab = self._create_shortcuts_tab()
        credits_tab = self._create_credits_tab()
        
        self.tabs.addTab(about_tab, "About")
        self.tabs.addTab(features_tab, "Features")
        self.tabs.addTab(shortcuts_tab, "Shortcuts")
        self.tabs.addTab(credits_tab, "Credits")
        
        layout.addWidget(self.tabs, 1)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 35)
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_header(self) -> QWidget:
        """Create the header section with app name and logo."""
        header = QFrame()
        header.setObjectName("header_frame")  # For custom styling without border
        header.setFrameShape(QFrame.Shape.NoFrame)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        # App icon (if available)
        icon_label = QLabel()
        icon_label.setStyleSheet("border: none; background: transparent;")
        if config:
            icon_path = os.path.join(config.BASE_DIR, "resources", "icons", "icon.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, 
                                                   Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
        icon_label.setFixedSize(70, 70)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # App name and version
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        app_info = self._get_app_info()
        
        name_label = QLabel(app_info['name'])
        name_label.setStyleSheet("font-size: 24px; font-weight: bold; border: none; background: transparent;")
        text_layout.addWidget(name_label)
        
        _t = config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME
        version_label = QLabel(f"Version {app_info['version']}")
        version_label.setStyleSheet(f"font-size: 14px; color: {_t['accent']}; border: none; background: transparent;")
        text_layout.addWidget(version_label)
        
        desc_label = QLabel(app_info['description'])
        desc_label.setStyleSheet("font-size: 12px; border: none; background: transparent;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        text_layout.addStretch()
        header_layout.addLayout(text_layout, 1)
        
        return header
    
    def _create_about_tab(self) -> QWidget:
        """Create the About tab with application description."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Description
        desc_text = """
<h3>Professional Color Mixing Application</h3>

<p>RNV Color Mixer is a desktop application for simulating real-world paint mixing 
behavior. It uses advanced color algorithms to help artists, designers, and color 
enthusiasts create precise color combinations.</p>

<h4>Core Capabilities:</h4>
<ul>
<li><b>Realistic Paint Mixing</b> - Kubelka-Munk theory simulation</li>
<li><b>Multiple Color Spaces</b> - RGB, LAB, RYB, HSV support</li>
<li><b>Image Color Sampling</b> - Pick colors from any loaded image</li>
<li><b>Screen Color Picker</b> - Sample colors from anywhere on screen</li>
<li><b>Palette Management</b> - 16+ professional export formats</li>
<li><b>Color Harmonies</b> - Generate complementary, analogous, triadic palettes</li>
<li><b>Session Management</b> - Save and restore your work</li>
</ul>

<h4>System Information:</h4>
"""
        
        # Add system info
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        try:
            from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
            qt_version = QT_VERSION_STR
            pyqt_version = PYQT_VERSION_STR
        except ImportError:
            qt_version = "Unknown"
            pyqt_version = "Unknown"
        
        desc_text += f"""
<table>
<tr><td><b>Python:</b></td><td>{python_version}</td></tr>
<tr><td><b>PyQt6:</b></td><td>{pyqt_version}</td></tr>
<tr><td><b>Qt:</b></td><td>{qt_version}</td></tr>
<tr><td><b>Platform:</b></td><td>{sys.platform}</td></tr>
</table>
"""
        
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setTextFormat(Qt.TextFormat.RichText)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(desc_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_features_tab(self) -> QWidget:
        """Create the Features tab with feature list."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        features_text = """
<h3>Feature Overview</h3>

<h4>🎨 Color Mixing</h4>
<ul>
<li><b>Weighted Color Mixing</b> - Adjust individual color weights with sliders</li>
<li><b>Up to 12 Color Slots</b> - Mix multiple colors simultaneously</li>
<li><b>Real-time Preview</b> - See mixed results instantly</li>
<li><b>Multiple Algorithms</b> - RGB, LAB, RYB, Kubelka-Munk mixing modes</li>
</ul>

<h4>🖼️ Image Sampling</h4>
<ul>
<li><b>Drag & Drop Support</b> - Load images by dropping them on the canvas</li>
<li><b>Click to Sample</b> - Pick colors directly from loaded images</li>
<li><b>Region Averaging</b> - Double-click to average colors in an area</li>
<li><b>Zoom & Pan</b> - Navigate large images with scroll wheel</li>
</ul>

<h4>🌈 Color Harmonies</h4>
<ul>
<li><b>Complementary</b> - Opposite colors on the color wheel</li>
<li><b>Analogous</b> - Adjacent colors for smooth transitions</li>
<li><b>Triadic</b> - Three evenly spaced colors</li>
<li><b>Split-Complementary</b> - Variation of complementary scheme</li>
<li><b>Tetradic</b> - Four colors forming a rectangle</li>
<li><b>Square</b> - Four evenly spaced colors</li>
</ul>

<h4>💾 Session & Palette Management</h4>
<ul>
<li><b>Auto-Save</b> - Never lose your work with automatic session saving</li>
<li><b>Crash Recovery</b> - Restore sessions after unexpected closures</li>
<li><b>Export Formats</b> - ASE, ACO, GPL, PAL, ACT, GIMP, CSS, SCSS, and more</li>
<li><b>Preset Palettes</b> - Built-in color schemes to get started quickly</li>
<li><b>Color History</b> - Track recently used colors</li>
</ul>

<h4>🎯 Screen Color Picker</h4>
<ul>
<li><b>Global Picking</b> - Sample colors from any application</li>
<li><b>Multi-Monitor Support</b> - Works across all connected displays</li>
<li><b>Magnified Preview</b> - See exact pixel under cursor</li>
<li><b>One-Click Add</b> - Picked colors are added to slots automatically</li>
</ul>

<h4>🎭 Themes</h4>
<ul>
<li><b>Dark Mode</b> - Easy on the eyes for long sessions</li>
<li><b>Light Mode</b> - High contrast for bright environments</li>
<li><b>Image Mode</b> - Custom button graphics and backgrounds</li>
</ul>
"""
        
        features_label = QLabel(features_text)
        features_label.setWordWrap(True)
        features_label.setTextFormat(Qt.TextFormat.RichText)
        features_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(features_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_shortcuts_tab(self) -> QWidget:
        """Create the Shortcuts tab with keyboard shortcuts reference."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        shortcuts_text = """
<h3>Keyboard Shortcuts</h3>

<h4>File Operations</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+O</b></td><td>Open/Upload Image</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save Color Swatch</td></tr>
</table>

<h4>Color Operations</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+N</b></td><td>Add New Color Slot</td></tr>
<tr><td><b>Ctrl+C</b></td><td>Copy Hex Color to Clipboard</td></tr>
<tr><td><b>Ctrl+Shift+C</b></td><td>Screen Color Picker</td></tr>
</table>

<h4>Application</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+,</b></td><td>Open Settings & Features Panel</td></tr>
<tr><td><b>Ctrl+P</b></td><td>Open Settings & Features Panel (Alt)</td></tr>
<tr><td><b>Ctrl+/</b></td><td>Open About Dialog (This Window)</td></tr>
</table>

<h4>Debug & Display</h4>
<table width="100%">
<tr><td width="40%"><b>F11</b></td><td>Toggle Tooltips On/Off</td></tr>
<tr><td><b>F12</b></td><td>Toggle Debug Overlays</td></tr>
</table>

<h4>Canvas Navigation</h4>
<table width="100%">
<tr><td width="40%"><b>Mouse Wheel</b></td><td>Zoom In/Out</td></tr>
<tr><td><b>Click & Drag</b></td><td>Pan Image</td></tr>
<tr><td><b>Single Click</b></td><td>Sample Pixel Color</td></tr>
<tr><td><b>Double Click</b></td><td>Sample Region Average</td></tr>
</table>

<h4>Color Slots</h4>
<table width="100%">
<tr><td width="40%"><b>Slider Drag</b></td><td>Adjust Color Weight</td></tr>
<tr><td><b>Color Well Click</b></td><td>Open Color Picker</td></tr>
<tr><td><b>X Button</b></td><td>Remove Color Slot</td></tr>
</table>
"""
        
        shortcuts_label = QLabel(shortcuts_text)
        shortcuts_label.setWordWrap(True)
        shortcuts_label.setTextFormat(Qt.TextFormat.RichText)
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(shortcuts_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _create_credits_tab(self) -> QWidget:
        """Create the Credits tab with acknowledgments."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        _t = config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME
        credits_text = f"""
<h3>Credits & Acknowledgments</h3>

<h4>Development</h4>
<p>RNV Color Mixer was created with passion for color science and 
practical tools for artists and designers.</p>

<h4>Technologies</h4>
<table width="100%">
<tr><td width="40%"><b>Framework</b></td><td>PyQt6</td></tr>
<tr><td><b>Language</b></td><td>Python 3</td></tr>
<tr><td><b>Image Processing</b></td><td>Pillow (PIL)</td></tr>
<tr><td><b>Color Science</b></td><td>Custom Kubelka-Munk Implementation</td></tr>
</table>

<h4>Color Science References</h4>
<ul>
<li><b>Kubelka-Munk Theory</b> - Paint mixing simulation</li>
<li><b>CIE LAB Color Space</b> - Perceptually uniform color mixing</li>
<li><b>RYB Color Model</b> - Traditional artist color wheel</li>
</ul>

<h4>Special Thanks</h4>
<ul>
<li>The PyQt community for excellent documentation</li>
<li>Color science researchers and educators</li>
<li>Beta testers and early adopters</li>
<li>Everyone who provided feedback and suggestions</li>
</ul>

<hr>

<p style="text-align: center; color: {_t['accent']};">
<b>RNV Color Mixer</b><br>
Bringing real-world paint mixing to the digital palette<br>
© 2026 RNV Development. All rights reserved.
</p>
"""
        
        credits_label = QLabel(credits_text)
        credits_label.setWordWrap(True)
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidget(credits_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _get_app_info(self) -> dict:
        """Get application information from config or defaults."""
        if config and hasattr(config, 'get_app_info'):
            return config.get_app_info()
        
        # Fallback when config module is unavailable
        return {
            "name": "RNV Color Mixer",
            "version": "Unknown",
            "description": "Professional Color Mixing Application",
            "author": "RNV Development",
            "framework": "PyQt6"
        }
    
    def set_theme(self, is_dark: bool) -> None:
        """Set the dialog theme (dark or light)."""
        self._is_dark = is_dark
        self._apply_theme()
    
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
                    border-radius: 8px;
                }}
                QFrame#header_frame {{
                    background-color: transparent;
                    border: none;
                    border-radius: 0px;
                }}
                QTabWidget::pane {{
                    background-color: {_d['panel_bg']};
                    border: 1px solid {_d['border_color']};
                    border-radius: 4px;
                }}
                QTabBar::tab {{
                    background-color: {_d['panel_secondary']};
                    color: {_d['text_color']};
                    padding: 8px 16px;
                    border: 1px solid {_d['border_color']};
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }}
                QTabBar::tab:selected {{
                    background-color: {_d['panel_bg']};
                    color: {_d['accent']};
                    border-bottom: 2px solid {_d['accent']};
                }}
                QTabBar::tab:hover:!selected {{
                    background-color: {_d['button_hover_bg']};
                    color: {_d['accent']};
                }}
                QLabel {{
                    color: {_d['text_color']};
                    background-color: transparent;
                }}
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background-color: {_d['panel_secondary']};
                    width: 12px;
                    border-radius: 6px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {_d['hover_color']};
                    border-radius: 5px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {_d['scrollbar_hover']};
                }}
                QPushButton {{
                    background-color: {_d['panel_secondary']};
                    color: {_d['text_color']};
                    border: 1px solid {_d['border_color']};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {_d['panel_hover']};
                    border-color: {_d['accent']};
                    color: {_d['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {_d['accent']};
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
                    border-radius: 8px;
                }}
                QFrame#header_frame {{
                    background-color: transparent;
                    border: none;
                    border-radius: 0px;
                }}
                QTabWidget::pane {{
                    background-color: {_l['window_bg']};
                    border: 1px solid {_l['border_color']};
                    border-radius: 4px;
                }}
                QTabBar::tab {{
                    background-color: {_l['panel_secondary']};
                    color: {_l['text_color']};
                    padding: 8px 16px;
                    border: 1px solid {_l['border_color']};
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }}
                QTabBar::tab:selected {{
                    background-color: {_l['window_bg']};
                    color: {_l['accent']};
                    border-bottom: 2px solid {_l['accent']};
                }}
                QTabBar::tab:hover:!selected {{
                    background-color: {_l['hover_color']};
                    color: {_l['accent']};
                }}
                QLabel {{
                    color: {_l['text_color']};
                    background-color: transparent;
                }}
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background-color: {_l['hover_color']};
                    width: 12px;
                    border-radius: 6px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {_l['text_disabled']};
                    border-radius: 5px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {_l['scrollbar_hover']};
                }}
                QPushButton {{
                    background-color: {_l['button_bg']};
                    color: {_l['text_color']};
                    border: 1px solid {_l['border_color']};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {_l['panel_hover']};
                    border-color: {_l['accent']};
                    color: {_l['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {_l['accent']};
                    color: {_l['accent_on']};
                }}
            """)
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
        Clears pixmaps to free memory.
        """
        try:
            # Clear any pixmaps to free memory
            for child in self.findChildren(QLabel):
                if child.pixmap() and not child.pixmap().isNull():
                    child.clear()
            
            if logger:
                logger.debug("AboutDialog cleanup complete")
                
        except Exception as e:
            if logger:
                logger.error(f"Error during AboutDialog cleanup: {e}")
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle dialog close - ensure cleanup runs."""
        self.cleanup()
        super().closeEvent(event)