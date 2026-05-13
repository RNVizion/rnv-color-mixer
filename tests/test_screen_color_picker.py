"""
RNV Color Mixer — ScreenColorPicker Tests  (Phase 8.4 deliverable)
=====================================================================

`screen_color_picker.ScreenColorPicker` is a fullscreen overlay widget
that captures all screens, displays a magnifier, and emits the RGB tuple
under the cursor when clicked. It depends on real hardware:
  - QApplication.screens() returns the connected monitors
  - QScreen.grabWindow() captures pixels off the screen
  - QCursor.pos() reports global cursor position

In the offscreen Qt test environment, QApplication.screens() returns a
fake screen with no real pixels, so `_capture_all_screens` produces
mostly-empty pixmaps and the picker can't actually pick colors.

Strategy: monkeypatch `QApplication.screens` in the picker's module
namespace (same module-replacement pattern from Phase 7.9) and provide
fake screen objects that return predictable geometries and pixmaps.

This lets us drive every code path without touching real hardware.
"""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPixmap, QColor

from screen_color_picker import ScreenColorPicker


# ═══════════════════════════════════════════════════════════════════════════
# Hardware mock infrastructure
# ═══════════════════════════════════════════════════════════════════════════

class _FakeScreen:
    """Stand-in for QScreen — returns canned geometry and a solid-color
    pixmap from grabWindow."""

    def __init__(self, x=0, y=0, w=1920, h=1080, color=(255, 0, 0)):
        self._geo = QRect(x, y, w, h)
        self._color = color

    def geometry(self):
        return self._geo

    def grabWindow(self, wid, *args, **kwargs):
        """Return a solid-color QPixmap matching this screen's geometry.
        Some Qt versions call grabWindow with positional args (x, y, w, h),
        others without — accept everything via *args."""
        pm = QPixmap(self._geo.width(), self._geo.height())
        pm.fill(QColor(*self._color))
        return pm


def _patch_screens(monkeypatch, screens):
    """Replace `QApplication.screens` in the screen_color_picker module
    namespace. Returns nothing — call from inside the test."""
    import screen_color_picker as scp

    # The picker's `_capture_all_screens` method calls
    # `QApplication.screens()`. We patch the QApplication symbol in
    # the picker's module namespace.
    class _FakeQApp:
        @staticmethod
        def screens():
            return list(screens)
        @staticmethod
        def primaryScreen():
            return screens[0] if screens else None

    monkeypatch.setattr(scp, "QApplication", _FakeQApp)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestScreenColorPickerConstruction:
    """Construction sets up window flags, attributes, and timer."""

    def test_construction_sets_initial_state(self, qtbot):
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)

        assert picker.current_color == (0, 0, 0)
        assert picker._is_active == False
        assert picker.screenshot is None
        assert picker._screenshot_image is None

    def test_magnifier_dimensions_invariants(self, qtbot):
        """Hard-coded UI invariants — sentinel against accidental edits."""
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        assert picker.magnifier_size == 140
        assert picker.zoom_factor == 8
        assert picker._pixel_size == 140 // 8

    def test_color_picked_signal_is_pyqt_bound(self, qtbot):
        from PyQt6.QtCore import pyqtBoundSignal
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        assert isinstance(picker.color_picked, pyqtBoundSignal)
        assert isinstance(picker.picker_cancelled, pyqtBoundSignal)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Single-monitor capture (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSingleMonitorCapture:
    """`_capture_all_screens` has a fast path for the single-screen case."""

    def test_capture_with_single_screen_sets_screenshot(
        self, qtbot, monkeypatch
    ):
        red_screen = _FakeScreen(0, 0, 800, 600, color=(255, 0, 0))
        _patch_screens(monkeypatch, [red_screen])

        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        picker._capture_all_screens()

        assert picker.screenshot is not None
        assert picker._screenshot_image is not None
        assert picker.screenshot.width() == 800
        assert picker.screenshot.height() == 600

    def test_capture_with_single_screen_pixel_color_matches(
        self, qtbot, monkeypatch
    ):
        """Verify the captured QImage actually has the fake screen's
        color at a known coordinate."""
        green_screen = _FakeScreen(0, 0, 800, 600, color=(0, 255, 0))
        _patch_screens(monkeypatch, [green_screen])

        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        picker._capture_all_screens()

        # Sample pixel at (10, 10) — should be green
        pixel = picker._screenshot_image.pixelColor(10, 10)
        assert pixel.red() == 0
        assert pixel.green() == 255
        assert pixel.blue() == 0


# ═══════════════════════════════════════════════════════════════════════════
# 3. Multi-monitor capture (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestMultiMonitorCapture:
    """The multi-monitor path is a separate code branch (~40 stmts) that
    composites multiple screens into a single virtual desktop pixmap."""

    def test_capture_with_two_screens_creates_composite(
        self, qtbot, monkeypatch
    ):
        # Two monitors side by side
        screen1 = _FakeScreen(0, 0, 800, 600, color=(255, 0, 0))
        screen2 = _FakeScreen(800, 0, 800, 600, color=(0, 0, 255))
        _patch_screens(monkeypatch, [screen1, screen2])

        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        picker._capture_all_screens()

        assert picker.screenshot is not None
        # Composite should span both screens horizontally
        assert picker.screenshot.width() == 1600  # 800 + 800
        assert picker.screenshot.height() == 600
        # Virtual geometry covers both
        assert picker._virtual_geometry.width() == 1600
        assert picker._virtual_geometry.height() == 600

    def test_capture_with_negative_coord_screens(
        self, qtbot, monkeypatch
    ):
        """Real multi-monitor setups often have a screen at negative
        coordinates (e.g., laptop-left + external-right)."""
        # Left screen at (-1024, 0), right at (0, 0)
        left = _FakeScreen(-1024, 0, 1024, 768, color=(255, 100, 100))
        right = _FakeScreen(0, 0, 1920, 1080, color=(100, 100, 255))
        _patch_screens(monkeypatch, [left, right])

        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        picker._capture_all_screens()

        # Virtual desktop spans from -1024 to 1920+1 = 1920
        # min_x = -1024, so screen_offset.x() should be -1024
        assert picker._screen_offset.x() == -1024
        assert picker._screen_offset.y() == 0
        # Virtual width = max_x - min_x + 1 = 1919 - (-1024) + 1 = 2944
        assert picker._virtual_geometry.width() == 2944


# ═══════════════════════════════════════════════════════════════════════════
# 4. Empty screen list — error path (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestEmptyScreensErrorPath:
    """If `QApplication.screens()` returns empty (theoretically impossible
    on real hardware), the capture method logs an error and returns
    without setting screenshot."""

    def test_capture_with_no_screens_returns_safely(
        self, qtbot, monkeypatch
    ):
        _patch_screens(monkeypatch, [])

        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        try:
            picker._capture_all_screens()
        except Exception as e:
            pytest.fail(
                f"_capture_all_screens with no screens raised "
                f"{type(e).__name__}: {e}"
            )
        assert picker.screenshot is None


# ═══════════════════════════════════════════════════════════════════════════
# 5. Color string updates (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorStringUpdates:
    """`_update_color_strings` formats the current_color into the
    hex/rgb/qcolor display strings."""

    def test_update_color_strings_with_known_rgb(self, qtbot):
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)

        picker.current_color = (255, 128, 64)
        picker._update_color_strings()

        assert picker._hex_text == "#FF8040"
        assert picker._rgb_text == "RGB: 255, 128, 64"
        assert picker._current_color_qcolor.red() == 255
        assert picker._current_color_qcolor.green() == 128
        assert picker._current_color_qcolor.blue() == 64

    def test_update_color_strings_with_zero_pads_correctly(self, qtbot):
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)

        picker.current_color = (5, 0, 250)
        picker._update_color_strings()

        # Hex should zero-pad each channel to 2 digits
        assert picker._hex_text == "#0500FA"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Mouse click → color_picked emission (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestMouseClickHandling:
    """`mousePressEvent` with LeftButton emits color_picked when active.
    We construct a synthetic QMouseEvent and call the handler directly."""

    def test_left_click_when_active_emits_color_picked(
        self, qtbot, monkeypatch
    ):
        red_screen = _FakeScreen(0, 0, 800, 600, color=(255, 0, 0))
        _patch_screens(monkeypatch, [red_screen])

        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        picker._is_active = True
        picker.current_color = (123, 45, 67)

        # Synthesize a left-button mouse press event
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import QPointF, QEvent
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(50.0, 50.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        with qtbot.waitSignal(picker.color_picked, timeout=1000) as blocker:
            picker.mousePressEvent(event)
        assert blocker.args[0] == (123, 45, 67)

    def test_left_click_when_inactive_does_not_emit(
        self, qtbot, monkeypatch
    ):
        """If picker hasn't started (still _is_active=False), the click
        should be ignored."""
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        # Stay inactive

        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import QPointF, QEvent
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(0.0, 0.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        emitted: list = []
        picker.color_picked.connect(lambda c: emitted.append(c))
        picker.mousePressEvent(event)

        assert len(emitted) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 7. Escape key → picker_cancelled (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestEscapeKeyCancellation:
    def test_escape_when_active_emits_cancelled(self, qtbot):
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        picker._is_active = True

        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            int(Qt.Key.Key_Escape),
            Qt.KeyboardModifier.NoModifier,
        )

        with qtbot.waitSignal(picker.picker_cancelled, timeout=1000):
            picker.keyPressEvent(event)

    def test_escape_when_inactive_does_not_emit(self, qtbot):
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        # Stay inactive

        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            int(Qt.Key.Key_Escape),
            Qt.KeyboardModifier.NoModifier,
        )

        emitted: list = []
        picker.picker_cancelled.connect(lambda: emitted.append(True))
        picker.keyPressEvent(event)

        assert len(emitted) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 8. Cleanup paths (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCleanupPaths:
    def test_cleanup_and_close_clears_resources_and_marks_inactive(
        self, qtbot, monkeypatch
    ):
        # Set up with screenshot present
        red = _FakeScreen(0, 0, 800, 600, color=(255, 0, 0))
        _patch_screens(monkeypatch, [red])

        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        picker._capture_all_screens()
        picker._is_active = True
        assert picker.screenshot is not None

        picker._cleanup_and_close()

        assert picker._is_active == False
        assert picker.screenshot is None
        assert picker._screenshot_image is None

    def test_cleanup_when_already_inactive_does_not_crash(self, qtbot):
        picker = ScreenColorPicker()
        qtbot.addWidget(picker)
        # Already inactive
        try:
            picker._cleanup_and_close()
        except Exception as e:
            pytest.fail(
                f"_cleanup_and_close raised {type(e).__name__}: {e}"
            )
