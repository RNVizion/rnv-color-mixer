"""
RNV Color Mixer — CanvasView Tests  (Phase 8.3 deliverable)
=============================================================

Phase 8.3 covers `ui.canvas_view.CanvasView` — the image canvas widget
that handles pan/zoom and color sampling. Per the Phase 8 plan, this is
the highest-risk phase: paint events on offscreen Qt are unreliable.

Strategy (per plan):
  - Tier 1: state queries + direct method calls — LOW RISK
  - Tier 2: zoom in/out via direct calls — LOW RISK
  - Tier 3+: mouse/wheel event synthesis — MEDIUM/HIGH RISK, deferred

This file implements Tiers 1-2 only. Event-synthesis tests would be
Phase 8.3.b in a future iteration if Tier 1-2 lands cleanly and
demand exists.
"""

from __future__ import annotations

import pytest
from PyQt6.QtCore import pyqtBoundSignal

from core.image_handler import ImageHandler
from ui.canvas_view import CanvasView


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def image_handler():
    """Fresh ImageHandler — CanvasView's required dependency."""
    return ImageHandler()


@pytest.fixture
def canvas(qtbot, image_handler):
    """Fresh CanvasView with isolated ImageHandler."""
    cv = CanvasView(image_handler)
    qtbot.addWidget(cv)
    return cv


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCanvasViewConstruction:
    def test_construction_with_real_image_handler(self, canvas, image_handler):
        """CanvasView wires its signals to ImageHandler at init. The
        smoke-test confirms everything connected without crashing."""
        assert canvas is not None
        assert canvas.image_handler is image_handler

    def test_signals_are_real_pyqt_bound_signals(self, canvas):
        """Catches accidental signal-shadow regressions."""
        for sig_name in ("pixel_hovered", "pixel_sampled",
                         "region_sampled", "zoom_changed"):
            sig = getattr(canvas, sig_name)
            assert isinstance(sig, pyqtBoundSignal), (
                f"{sig_name} is {type(sig).__name__}, not a pyqtBoundSignal"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Zoom queries + direct calls (3 tests — TIER 2)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCanvasViewZoom:
    """Zoom state is owned by `image_handler`; `CanvasView.get_current_zoom`
    delegates. We test the delegation contract."""

    def test_get_current_zoom_returns_float(self, canvas):
        """At construction, no image loaded, zoom should still return a
        sensible float (likely 1.0)."""
        z = canvas.get_current_zoom()
        assert isinstance(z, float), (
            f"get_current_zoom returned {type(z).__name__}, expected float"
        )

    def test_zoom_in_with_no_image_does_not_change_zoom(self, canvas):
        """Contract: when no image is loaded, `zoom_in` is a graceful
        no-op (early-return). Zoom level should not change."""
        before = canvas.image_handler.zoom_level
        # Confirm setup: no image loaded
        assert canvas.image_handler.is_loaded() is False

        canvas.zoom_in()

        # Zoom level unchanged
        assert canvas.image_handler.zoom_level == before, (
            f"zoom_in changed zoom_level {before} -> "
            f"{canvas.image_handler.zoom_level} despite no image loaded"
        )

    def test_zoom_out_with_no_image_does_not_change_zoom(self, canvas):
        """Same contract: zoom_out is no-op without a loaded image."""
        before = canvas.image_handler.zoom_level
        assert canvas.image_handler.is_loaded() is False

        canvas.zoom_out()

        assert canvas.image_handler.zoom_level == before


# ═══════════════════════════════════════════════════════════════════════════
# 3. Reset zoom / fit / actual size (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCanvasViewZoomReset:
    def test_reset_zoom_with_no_image_does_not_change_zoom(self, canvas):
        """`reset_zoom` early-returns when no image is loaded."""
        before = canvas.image_handler.zoom_level
        assert canvas.image_handler.is_loaded() is False

        canvas.reset_zoom()

        assert canvas.image_handler.zoom_level == before

    def test_fit_image_with_no_image_does_not_change_zoom(self, canvas):
        """`fit_image` delegates to `reset_zoom`, which early-returns
        without an image."""
        before = canvas.image_handler.zoom_level
        assert canvas.image_handler.is_loaded() is False

        canvas.fit_image()

        assert canvas.image_handler.zoom_level == before

    def test_actual_size_with_no_image_does_not_change_zoom(self, canvas):
        """`actual_size` early-returns when no image is loaded."""
        before = canvas.image_handler.zoom_level
        assert canvas.image_handler.is_loaded() is False

        canvas.actual_size()

        assert canvas.image_handler.zoom_level == before


# ═══════════════════════════════════════════════════════════════════════════
# 4. Theme application (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCanvasViewTheme:
    def test_set_theme_dark_then_light_does_not_crash(self, canvas):
        canvas.set_theme(is_dark=True)
        canvas.set_theme(is_dark=False)
        canvas.set_theme(is_dark=True)  # back to dark

    def test_set_theme_with_ui_handler_param(self, canvas):
        """`set_theme(is_dark, ui_handler)` accepts an optional ui_handler
        for image-mode background. Drive with None to verify it's optional."""
        canvas.set_theme(is_dark=True, ui_handler=None)
        canvas.set_theme(is_dark=False, ui_handler=None)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Preview color (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCanvasViewPreview:
    """`set_preview_color` and `hide_preview` are forwarded to the inner
    `ImageDisplayLabel`."""

    def test_set_preview_color_show_true_sets_label_state(self, canvas):
        """`canvas.set_preview_color(rgb, show=True)` forwards to
        `image_label.set_preview_color(rgb, show)` which sets
        `preview_color` and `show_preview = True` on the inner label."""
        # Fixture canvas has an image_label
        assert canvas.image_label is not None

        canvas.set_preview_color((255, 0, 0), show=True)

        assert canvas.image_label.preview_color == (255, 0, 0)
        assert canvas.image_label.show_preview is True

    def test_set_preview_color_show_false_sets_label_hidden(self, canvas):
        """show=False should set `image_label.show_preview = False` even
        though the color is still recorded."""
        assert canvas.image_label is not None

        canvas.set_preview_color((0, 255, 0), show=False)

        assert canvas.image_label.preview_color == (0, 255, 0)
        assert canvas.image_label.show_preview is False

    def test_hide_preview_clears_label_show_state(self, canvas):
        """Originally LEGITIMATE; reclassified UPGRADE because
        `image_label.show_preview` is fully observable.

        After set_preview_color(show=True) then hide_preview(), the
        label should report show_preview=False."""
        assert canvas.image_label is not None
        canvas.set_preview_color((255, 0, 0), show=True)
        # Confirm pre-condition
        assert canvas.image_label.show_preview is True

        canvas.hide_preview()

        assert canvas.image_label.show_preview is False


# ═══════════════════════════════════════════════════════════════════════════
# 6. Display / clear (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCanvasViewDisplayClear:
    def test_clear_canvas_does_not_crash(self, canvas):
        """LEGITIMATE smoke test: `clear_canvas` clears the inner label's
        pixmap and triggers a paint update. The pixmap state on
        ImageDisplayLabel isn't reliably observable offscreen (Qt's
        internal pixmap is abstracted away), so the strongest check is
        "doesn't raise"."""
        try:
            canvas.clear_canvas()
        except Exception as e:
            pytest.fail(f"clear_canvas raised {type(e).__name__}: {e}")

    def test_display_image_with_no_image_does_not_crash(self, canvas):
        """LEGITIMATE smoke test: `display_image` early-returns and
        calls `clear_canvas` when no image is loaded. The clear-canvas
        side effect is what we'd assert on, but per above, that isn't
        cleanly observable. This test verifies the "called by external
        listeners on lifecycle events" path is graceful."""
        try:
            canvas.display_image()
        except Exception as e:
            pytest.fail(
                f"display_image (no image) raised {type(e).__name__}: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 7. Cleanup (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCanvasViewCleanup:
    def test_cleanup_does_not_crash(self, canvas):
        """LEGITIMATE smoke test: `cleanup()` disconnects signals from
        the image_handler. The disconnections themselves are internal
        to the SignalConnectionManager — observable as
        `signal_manager.get_connection_count()` going to 0, but only
        for the connections this canvas owned, which the test fixture
        doesn't track. Strongest check: "doesn't raise"."""
        try:
            canvas.cleanup()
        except Exception as e:
            pytest.fail(f"cleanup raised {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# 8. ImageDisplayLabel (the inner widget) — 3 tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageDisplayLabel:
    """The CanvasView's inner widget. Construct directly to test its
    set_preview_color / hide_preview / set_preview_size / set_theme
    paths in isolation."""

    @pytest.fixture
    def label(self, qtbot):
        from ui.canvas_view import ImageDisplayLabel
        lbl = ImageDisplayLabel()
        qtbot.addWidget(lbl)
        return lbl

    def test_set_preview_color_then_hide_updates_label_state(self, label):
        """The inner ImageDisplayLabel exposes preview_color and
        show_preview directly — verify both changes."""
        label.set_preview_color((100, 200, 50), show=True)
        assert label.preview_color == (100, 200, 50)
        assert label.show_preview is True

        label.hide_preview()
        # show_preview flipped; preview_color preserved
        assert label.show_preview is False
        assert label.preview_color == (100, 200, 50)

    def test_set_preview_size_clamps_and_stores(self, label):
        """Originally LEGITIMATE; upgraded.

        `set_preview_size(size)` clamps to [80, 200] and stores in
        `preview_size`. We test both within-range and clamping cases."""
        # Within range
        label.set_preview_size(150)
        assert label.preview_size == 150

        # Below min — should clamp UP to 80
        label.set_preview_size(40)
        assert label.preview_size == 80

        # Above max — should clamp DOWN to 200
        label.set_preview_size(500)
        assert label.preview_size == 200

    def test_label_set_theme_both_directions(self, label):
        label.set_theme(is_dark=True)
        label.set_theme(is_dark=False)
        label.set_theme(is_dark=True)
