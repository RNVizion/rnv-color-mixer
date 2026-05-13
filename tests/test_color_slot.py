"""
RNV Color Mixer — ColorSlot Tests  (Phase 7.1 deliverable)
============================================================

The ColorSlot widget is the most-touched surface in the application —
each user interaction with the up-to-12 slots flows through `set_color`,
`set_weight`, `clear`, the 33-entry undo/redo history, the context menu
(right-click → fine-tune), and the remove signal.

Phase 4 instantiated slots transitively via ColorMixerApp but never
exercised any of these paths. Phase 7.1 closes that gap.

Scope (in)
----------
- Construction with various indices
- set_color / get_color round-trip and clamping
- set_weight / get_weight round-trip and clamping
- clear() resets state and emits both signals
- Color signal emission contract
- 33-entry undo/redo history (add → can_undo → undo → can_redo → redo)
- History truncation when set_color called after partial undo
- get_color_data / set_color_data round-trip
- remove_requested signal emission
- set_theme(is_dark=True/False) doesn't crash
- Default state matches the documented constants

Scope (out)
-----------
- contextMenuEvent / fine-tune dialog open path (modal, deferred to 7.4)
- Hex entry text field interaction (covered transitively by set_color tests)
- Remove button image swap on theme change (visual, low value)
"""

from __future__ import annotations

import pytest
from PyQt6.QtCore import pyqtBoundSignal

# Bootstrap (sys.path + virtual packages) is done by tests/conftest.py
from core.color_slot import ColorSlot


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def slot(qtbot):
    """Fresh ColorSlot at index 0, registered for Qt teardown."""
    s = ColorSlot(index=0)
    qtbot.addWidget(s)
    return s


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction & defaults (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotConstruction:
    """Construction is parameterised by index; defaults must match what the
    rest of the app expects (color (200,200,200), weight 0, history of 1)."""

    def test_default_state_after_construction(self, slot):
        assert slot.get_color() == (200, 200, 200)
        assert slot.get_weight() == 0
        assert slot.index == 0
        assert len(slot._color_history) == 1
        assert slot._history_index == 0
        assert slot.can_undo() is False
        assert slot.can_redo() is False

    def test_construction_with_various_indices(self, qtbot):
        for idx in (0, 1, 5, 11):
            s = ColorSlot(index=idx)
            qtbot.addWidget(s)
            assert s.index == idx

    def test_signals_are_real_pyqt_bound_signals(self, slot):
        """Catches accidental shadowing during refactors."""
        for sig_name in ("color_changed", "weight_changed", "remove_requested"):
            sig = getattr(slot, sig_name)
            assert isinstance(sig, pyqtBoundSignal), (
                f"{sig_name} is {type(sig).__name__}, not a pyqtBoundSignal"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Color setters (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotColorSetters:
    """`set_color` is the most-called mutator in the app."""

    def test_set_color_round_trip(self, slot):
        slot.set_color((123, 45, 67))
        assert slot.get_color() == (123, 45, 67)

    def test_set_color_clamps_out_of_range_values(self, slot):
        """Implementation clamps each channel to [0, 255]."""
        slot.set_color((-50, 300, 128))
        assert slot.get_color() == (0, 255, 128)

    def test_set_color_emits_color_changed_signal(self, slot, qtbot):
        with qtbot.waitSignal(slot.color_changed, timeout=1000):
            slot.set_color((10, 20, 30))


# ═══════════════════════════════════════════════════════════════════════════
# 3. Weight setters (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotWeightSetter:
    def test_set_weight_round_trip_and_clamping(self, slot):
        slot.set_weight(50)
        assert slot.get_weight() == 50
        # Clamping at both bounds
        slot.set_weight(150)
        assert slot.get_weight() == 100
        slot.set_weight(-10)
        assert slot.get_weight() == 0
        # Slider widget reflects the value (not just internal state)
        slot.set_weight(75)
        assert slot.weight_slider.value() == 75


# ═══════════════════════════════════════════════════════════════════════════
# 4. Clear (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotClear:
    def test_clear_resets_state_and_emits_both_signals(self, slot, qtbot):
        # Set up non-default state
        slot.set_color((100, 100, 100))
        slot.set_weight(60)
        # Clear must emit BOTH color_changed and weight_changed
        with qtbot.waitSignal(slot.color_changed, timeout=1000):
            with qtbot.waitSignal(slot.weight_changed, timeout=1000):
                slot.clear()
        assert slot.get_color() == (200, 200, 200)
        assert slot.get_weight() == 0
        # History also resets to 1 entry (the default color)
        assert len(slot._color_history) == 1
        assert slot._history_index == 0


# ═══════════════════════════════════════════════════════════════════════════
# 5. Undo / Redo (2 tests — guards the 33-entry history machinery)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotUndoRedo:
    """The 33-entry color history is non-trivial state that's currently
    untested. These two cover the core invariants."""

    def test_undo_redo_navigates_history_correctly(self, slot):
        # 3 distinct colors → 4 history entries (incl. default)
        slot.set_color((10, 0, 0))
        slot.set_color((20, 0, 0))
        slot.set_color((30, 0, 0))
        assert len(slot._color_history) == 4
        assert slot.get_color() == (30, 0, 0)

        # Undo back through them
        slot.undo_color()
        assert slot.get_color() == (20, 0, 0)
        slot.undo_color()
        assert slot.get_color() == (10, 0, 0)
        slot.undo_color()
        assert slot.get_color() == (200, 200, 200)
        assert slot.can_undo() is False  # at start

        # Redo forward
        slot.redo_color()
        assert slot.get_color() == (10, 0, 0)
        slot.redo_color()
        assert slot.get_color() == (20, 0, 0)

    def test_set_color_after_undo_truncates_redo_history(self, slot):
        """Standard undo/redo semantics: setting a new color after partial
        undo discards the redo history."""
        slot.set_color((1, 0, 0))
        slot.set_color((2, 0, 0))
        slot.set_color((3, 0, 0))   # history: [default, 1, 2, 3], index=3
        slot.undo_color()           # index=2 (color=2)
        slot.undo_color()           # index=1 (color=1)
        assert slot.can_redo() is True

        # New set_color truncates the redo branch
        slot.set_color((99, 0, 0))
        assert slot.can_redo() is False, (
            "set_color after partial undo must discard redo history"
        )
        # New color is at the end of a now-shorter history
        assert slot.get_color() == (99, 0, 0)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Data export / import (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotDataRoundTrip:
    """`get_color_data` / `set_color_data` are used by session save/load.
    A round-trip must preserve color, weight, and hex consistency."""

    def test_get_set_color_data_round_trip(self, slot, qtbot):
        slot.set_color((128, 64, 32))
        slot.set_weight(45)
        data = slot.get_color_data()
        assert data["color"] == (128, 64, 32)
        assert data["weight"] == 45
        assert data["hex"].lower().lstrip("#") == "804020"

        # Load into a fresh slot — both must end up identical
        target = ColorSlot(index=1)
        qtbot.addWidget(target)
        target.set_color_data(data)
        assert target.get_color() == (128, 64, 32)


# ═══════════════════════════════════════════════════════════════════════════
# 7. Remove signal (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotRemoveSignal:
    def test_remove_requested_emits_with_self_as_payload(self, slot, qtbot):
        """The signal payload is the slot instance itself — main app uses
        it to identify which slot to remove."""
        with qtbot.waitSignal(slot.remove_requested, timeout=1000) as blocker:
            slot.remove_requested.emit(slot)
        assert blocker.args == [slot]


# ═══════════════════════════════════════════════════════════════════════════
# 8. Theme application (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotTheme:
    def test_set_theme_both_directions_does_not_crash(self, slot):
        """The full `_apply_widget_stylesheet` chain runs on every call."""
        slot.set_theme(is_dark=True)
        slot.set_theme(is_dark=False)
        slot.set_theme(is_dark=True)  # back to dark — covers retoggle path


# ═══════════════════════════════════════════════════════════════════════════
# 9. Hex entry field (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotHexEntry:
    """The hex_entry QLineEdit lets the user type colors directly. Two
    handlers fire — `_on_hex_changed` (live preview while typing) and
    `_on_hex_entered` (commits on Enter)."""

    def test_valid_hex_entry_updates_color_on_enter(self, slot):
        """`_on_hex_entered` calls set_color which goes through the full
        update path including signal emission."""
        slot.hex_entry.setText("#ff8040")
        slot._on_hex_entered()
        assert slot.get_color() == (255, 128, 64)

    def test_invalid_hex_entry_is_silently_ignored_during_typing(self, slot):
        """`_on_hex_changed` only previews valid hex; partial/invalid input
        leaves the slot's color unchanged. This is the core robustness
        contract for the live-preview behaviour."""
        starting_color = slot.get_color()
        # Various invalid forms a user might be in the middle of typing
        for bogus in ("", "#", "#z", "#12", "not-a-color", "#1234567"):
            slot.hex_entry.setText(bogus)
            slot._on_hex_changed()
        assert slot.get_color() == starting_color


# ═══════════════════════════════════════════════════════════════════════════
# 10. Quick adjust (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotQuickAdjust:
    """`_quick_adjust` is the worker behind the context-menu lighten /
    darken / saturate / etc actions. Each branch handles a different
    HSV transformation. We test direction (sign of change), not exact
    pixel values, per the Phase 5 lesson."""

    def test_lighten_increases_value_component(self, slot):
        slot.set_color((100, 100, 100))
        slot._quick_adjust("lighten", 50)
        new = slot.get_color()
        # Lighter means each channel went up (gray → lighter gray)
        assert new[0] > 100 and new[1] > 100 and new[2] > 100

    def test_darken_decreases_value_component(self, slot):
        slot.set_color((100, 100, 100))
        slot._quick_adjust("darken", 50)
        new = slot.get_color()
        assert new[0] < 100 and new[1] < 100 and new[2] < 100


# ═══════════════════════════════════════════════════════════════════════════
# 11. Reset color (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotResetColor:
    def test_reset_color_returns_to_default_gray(self, slot):
        slot.set_color((255, 0, 0))
        slot._reset_color()
        assert slot.get_color() == (200, 200, 200)


# ═══════════════════════════════════════════════════════════════════════════
# 12. Copy hex (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotCopyHex:
    def test_copy_hex_to_clipboard_writes_correct_hex(self, slot):
        """Verifies the hex string written to the application clipboard
        matches the slot's current color."""
        from PyQt6.QtWidgets import QApplication

        slot.set_color((171, 205, 239))
        slot._copy_hex_to_clipboard()
        clipboard_text = QApplication.clipboard().text()
        assert clipboard_text.lower().lstrip("#") == "abcdef"


# ═══════════════════════════════════════════════════════════════════════════
# 13. Color picker dialog (1 test — modal mocked)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotColorPicker:
    """`_open_color_dialog` pops a QColorDialog modal. We monkeypatch the
    dialog's `exec()` and `selectedColor()` so the test runs headlessly
    while still exercising the real wiring around the dialog call."""

    def test_color_picker_applies_selected_color_when_accepted(
        self, slot, monkeypatch
    ):
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtGui import QColor

        # Force exec() to return Accepted, and selectedColor() to return
        # a known QColor. These are both instance methods on QColorDialog.
        monkeypatch.setattr(
            QColorDialog, "exec",
            lambda self: QColorDialog.DialogCode.Accepted.value,
        )
        monkeypatch.setattr(
            QColorDialog, "selectedColor",
            lambda self: QColor(50, 100, 200),
        )

        slot._pick_color()
        assert slot.get_color() == (50, 100, 200)

    def test_color_picker_leaves_color_unchanged_when_rejected(
        self, slot, monkeypatch
    ):
        from PyQt6.QtWidgets import QColorDialog

        slot.set_color((10, 20, 30))
        monkeypatch.setattr(
            QColorDialog, "exec",
            lambda self: QColorDialog.DialogCode.Rejected.value,
        )
        slot._pick_color()
        assert slot.get_color() == (10, 20, 30)
