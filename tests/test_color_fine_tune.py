"""
RNV Color Mixer — ColorFineTuneDialog Tests  (Phase 7.4 deliverable)
======================================================================

Drives the right-click fine-tune dialog. Five sliders adjust HSV space:
  - lighten:     -100 to +100 (negative darkens)
  - saturate:    -100 to +100 (negative desaturates)
  - hue_shift:   -180 to +180 degrees
  - temperature: -100 to +100 (negative cool, positive warm)
  - tint_shade:  -100 to +100 (negative tint, positive shade — TBD per impl)

The dialog is non-modal in the sense that `__init__` doesn't block — but
`_apply_changes` calls `self.accept()` which is a `QDialog` method, not
inherently blocking unless `exec()` is called. We never call `exec()` in
tests; we just construct, mutate sliders, and read state.

Per the Phase 7 plan, direction-of-change is asserted (e.g. "warmer means
more red, less blue"), not exact pixel values — the underlying HSV math
has rounding behaviour we don't want to overspecify.
"""

from __future__ import annotations

import pytest
from PyQt6.QtCore import pyqtBoundSignal

from core.color_fine_tune import ColorFineTuneDialog


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def dialog(qtbot):
    """Fresh ColorFineTuneDialog with mid-gray as starting color.

    Mid-gray is a useful default because most adjustments produce
    visible, predictable changes from it (e.g. lighten brightens
    monotonically, temperature shifts toward warm/cool symmetrically).
    """
    d = ColorFineTuneDialog(parent=None, original_color=(128, 128, 128))
    qtbot.addWidget(d)
    return d


@pytest.fixture
def red_dialog(qtbot):
    """ColorFineTuneDialog with pure red as starting color — useful for
    saturation tests since red has full saturation already (s=1)."""
    d = ColorFineTuneDialog(parent=None, original_color=(255, 0, 0))
    qtbot.addWidget(d)
    return d


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorFineTuneConstruction:
    def test_default_state_after_construction(self, dialog):
        """Construction with original_color=(128,128,128) starts with all
        adjustments at 0 and current_color matching original."""
        assert dialog.original_color == (128, 128, 128)
        assert dialog.current_color == (128, 128, 128)
        for key in ("lighten", "saturate", "hue_shift", "temperature"):
            assert dialog._adjustments[key] == 0, (
                f"adjustment {key!r} should default to 0; got "
                f"{dialog._adjustments[key]}"
            )

    def test_color_applied_signal_is_real(self, dialog):
        """Signal must be a real pyqtBoundSignal — catches rename/shadow."""
        assert isinstance(dialog.color_applied, pyqtBoundSignal)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Slider behaviour (5 tests, one per slider)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorFineTuneSliders:
    """Direction-of-change assertions per the Phase 5 lesson: asserting
    exact pixel values overspecifies the HSV math; what matters is that
    each slider moves the color in the documented direction."""

    def test_lighten_positive_brightens_toward_white(self, dialog):
        dialog._on_slider_changed("lighten", 80)
        r, g, b = dialog.current_color
        # Each channel must increase (gray → lighter)
        assert r > 128 and g > 128 and b > 128, (
            f"lighten +80 from gray produced {(r, g, b)} — expected all "
            f"channels > 128"
        )

    def test_lighten_negative_darkens_toward_black(self, dialog):
        dialog._on_slider_changed("lighten", -80)
        r, g, b = dialog.current_color
        assert r < 128 and g < 128 and b < 128, (
            f"lighten -80 from gray produced {(r, g, b)} — expected all "
            f"channels < 128"
        )

    def test_saturate_negative_desaturates_toward_gray(self, red_dialog):
        """From pure red, desaturation must reduce the gap between channels."""
        red_dialog._on_slider_changed("saturate", -100)
        r, g, b = red_dialog.current_color
        # Maximum gap between channels should shrink
        max_gap = max(r, g, b) - min(r, g, b)
        assert max_gap < 255, (
            f"Desaturating red gave {(r, g, b)} — channel gap {max_gap} "
            f"should be less than the original 255"
        )

    def test_hue_shift_changes_color_for_saturated_input(self, red_dialog):
        """Hue shifts on saturated colors produce visible color changes.
        From red, a 120° shift should land near green or somewhere
        non-red."""
        before = red_dialog.current_color
        red_dialog._on_slider_changed("hue_shift", 120)
        after = red_dialog.current_color
        assert before != after, (
            f"hue_shift 120° on red did not change the color: still {after}"
        )

    def test_temperature_warm_increases_red_and_decreases_blue(self, dialog):
        """Warm temperature: more red, less blue."""
        dialog._on_slider_changed("temperature", 80)
        r, g, b = dialog.current_color
        orig_r, orig_g, orig_b = dialog.original_color
        assert r > orig_r, f"warm did not increase red: {orig_r} → {r}"
        assert b < orig_b, f"warm did not decrease blue: {orig_b} → {b}"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Reset all (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorFineTuneReset:
    def test_reset_all_returns_to_default_state(self, dialog):
        """Mutate everything, then `_reset_all` must clear all adjustments
        AND restore current_color to original."""
        dialog._on_slider_changed("lighten", 50)
        dialog._on_slider_changed("temperature", -30)
        dialog._on_slider_changed("hue_shift", 90)
        # Non-default state confirmed
        assert dialog.current_color != dialog.original_color

        dialog._reset_all()

        for key in ("lighten", "saturate", "hue_shift", "temperature"):
            assert dialog._adjustments[key] == 0, (
                f"adjustment {key!r} not reset; still "
                f"{dialog._adjustments[key]}"
            )
        # Slider widgets must also be at 0
        for key, slider in dialog.sliders.items():
            assert slider.value() == 0, (
                f"slider {key!r} not reset; still at {slider.value()}"
            )
        assert dialog.current_color == dialog.original_color


# ═══════════════════════════════════════════════════════════════════════════
# 4. Apply changes signal (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorFineTuneApply:
    """`_apply_changes` emits `color_applied(rgb)` and closes the dialog
    via `self.accept()`."""

    def test_apply_changes_emits_color_applied_with_current_color(
        self, dialog, qtbot
    ):
        dialog._on_slider_changed("lighten", 50)
        target = dialog.current_color

        with qtbot.waitSignal(dialog.color_applied, timeout=1000) as blocker:
            dialog._apply_changes()
        assert blocker.args == [target], (
            f"color_applied emitted {blocker.args}, expected [{target}]"
        )

    def test_apply_changes_with_no_adjustments_emits_original(
        self, dialog, qtbot
    ):
        """Pressing Apply without moving any slider emits the original
        color unchanged."""
        with qtbot.waitSignal(dialog.color_applied, timeout=1000) as blocker:
            dialog._apply_changes()
        assert blocker.args == [(128, 128, 128)]


# ═══════════════════════════════════════════════════════════════════════════
# 5. Public API (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorFineTuneGetAdjustedColor:
    def test_get_adjusted_color_reflects_slider_state(self, dialog):
        """`get_adjusted_color` is the public read that callers use to
        sample the current state without committing."""
        assert dialog.get_adjusted_color() == (128, 128, 128)
        dialog._on_slider_changed("lighten", 50)
        assert dialog.get_adjusted_color() == dialog.current_color
        assert dialog.get_adjusted_color() != (128, 128, 128)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Theme (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorFineTuneTheme:
    def test_set_theme_both_directions_does_not_crash(self, dialog):
        dialog.set_theme(is_dark=False)
        dialog.set_theme(is_dark=True)
        dialog.set_theme(is_dark=False)
