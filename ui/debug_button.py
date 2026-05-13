"""
Custom QPushButton with full support for Image Mode theming.

DebugButton extends QPushButton with per-state image rendering (normal,
hover, pressed) driven by an event filter, and an optional
`always_show_images` flag for toolbar buttons that should retain their
custom artwork even when the user switches to a flat theme.
"""


import os
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import QSize, QEvent
from PyQt6.QtGui import QIcon, QPainter, QPaintEvent, QEnterEvent, QMouseEvent

if TYPE_CHECKING:
    from utils.config import ThemeManager

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("DebugButton")
except ImportError:
    logger = None


class DebugButton(QPushButton):
    """QPushButton that fully fills the button area with icon in Image Mode (or always if specified)."""

    def __init__(self, text: str = "", base_img: str | None = None, hover_img: str | None = None, pressed_img: str | None = None, parent: QWidget | None = None, always_show_images: bool = False) -> None:
        super().__init__(text, parent)
        
        # Store image paths directly on the button
        self.base_img = base_img
        self.hover_img = hover_img
        self.pressed_img = pressed_img
        self.theme_manager = None
        self.always_show_images = always_show_images  # NEW: Force images in all modes
        
        self._icon = None
        self._is_pressed = False  # Track if button is currently pressed
        
        # Enable mouse tracking to detect when mouse leaves during press
        self.setMouseTracking(True)
        
        # If always_show_images is True and we have a base image, set it immediately
        if self.always_show_images and self.base_img and os.path.exists(self.base_img):
            self.setIcon(QIcon(self.base_img))
            self.setIconSize(QSize(self.width(), self.height()))

    def set_theme_manager(self, theme_manager: "ThemeManager") -> None:
        """Set theme manager reference"""
        self.theme_manager = theme_manager

    def setIcon(self, icon: QIcon) -> None:
        """Store icon and repaint."""
        self._icon = icon
        super().setIcon(icon)
        self.update()

    def _should_show_images(self) -> bool:
        """Determine if images should be shown based on mode."""
        if self.always_show_images:
            return True
        return self.theme_manager and self.theme_manager.is_image_mode()

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._should_show_images() and self._icon:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            rect = self.rect()
            # Get pixmap and scale it to full rect
            pixmap = self._icon.pixmap(QSize(rect.width(), rect.height()))
            painter.drawPixmap(rect, pixmap)
        else:
            super().paintEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - show hover image"""
        if self._should_show_images():
            # If we're re-entering while pressed, show pressed image
            if self._is_pressed:
                if self.pressed_img and os.path.exists(self.pressed_img):
                    self.setIcon(QIcon(self.pressed_img))
            else:
                # Otherwise show hover image
                if self.hover_img and os.path.exists(self.hover_img):
                    self.setIcon(QIcon(self.hover_img))
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Handle mouse leave - show base image"""
        if self._should_show_images():
            # Only reset to base if NOT currently pressed
            # If pressed, mouseMoveEvent will handle the state
            if not self._is_pressed:
                if self.base_img and os.path.exists(self.base_img):
                    self.setIcon(QIcon(self.base_img))
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - show pressed image"""
        self._is_pressed = True  # Track press state regardless of mode
        if self._should_show_images():
            if self.pressed_img and os.path.exists(self.pressed_img):
                self.setIcon(QIcon(self.pressed_img))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release - show appropriate image"""
        self._is_pressed = False  # Reset press state regardless of mode
        if self._should_show_images():
            # Check if mouse is still over the button
            if self.rect().contains(event.pos()):
                # Mouse is still over button, show hover image
                if self.hover_img and os.path.exists(self.hover_img):
                    self.setIcon(QIcon(self.hover_img))
            else:
                # Mouse is not over button, show base image
                if self.base_img and os.path.exists(self.base_img):
                    self.setIcon(QIcon(self.base_img))
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse movement"""
        if self._should_show_images() and self._is_pressed:
            # Check if mouse is still within button bounds
            if not self.rect().contains(event.pos()):
                # Mouse left button area while pressed, reset to base
                if self.base_img and os.path.exists(self.base_img):
                    self.setIcon(QIcon(self.base_img))
            else:
                # Mouse is still within bounds and pressed, show pressed image
                if self.pressed_img and os.path.exists(self.pressed_img):
                    self.setIcon(QIcon(self.pressed_img))
        super().mouseMoveEvent(event)