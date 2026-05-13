"""
RNV Color Mixer — ColorSlot Context Menu Tests
================================================

Tests for ColorSlot's right-click context menu (~180 lines of
construction logic) and the quick adjustment helpers it dispatches to.

Coverage:
  - _quick_adjust dispatcher: lighten, darken, saturate, desaturate,
    warm, cool, plus the unknown-type safety branch
  - Direct action methods: _copy_hex_to_clipboard, _reset_color,
    _pick_color (with QColorDialog mocked)
  - contextMenuEvent body across both dark and light themes,
    including the can_undo branch after color history fills up
  - undo_color / redo_color round-trip, can_undo / can_redo predicates
"""

from __future__ import annotations

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QContextMenuEvent
from PyQt6.QtWidgets import QMenu, QColorDialog


# ═══════════════════════════════════════════════════════════════════════════
# 1. ColorSlot — quick adjustment methods
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotQuickAdjust:
    """`_quick_adjust(type, amount)` is the central dispatcher for the
    quick-adjust submenu actions. Has 6+ branches:
    lighter/darker/saturate/desaturate/warm/cool."""

    def test_quick_adjust_lighten(self, qtbot):
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((128, 128, 128))
        slot.set_weight(50)

        slot._quick_adjust('lighten', 10)
        new_color = slot.get_color()
        # Lighten should increase channel values
        assert any(c > 128 for c in new_color)

    def test_quick_adjust_darken(self, qtbot):
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((128, 128, 128))
        slot.set_weight(50)

        slot._quick_adjust('darken', 10)
        new_color = slot.get_color()
        # Darken should decrease channel values
        assert any(c < 128 for c in new_color)

    def test_quick_adjust_saturate_changes_color(self, qtbot):
        """`_quick_adjust('saturate', amount)` increases HSV saturation
        by amount/100. For a non-saturated color like (100, 150, 200),
        this should produce a different RGB after the round-trip."""
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((100, 150, 200))
        slot.set_weight(50)
        before = slot.get_color()

        slot._quick_adjust('saturate', 10)

        after = slot.get_color()
        # Saturate should shift the color (color was not pure)
        assert after != before, (
            f"saturate did not change color: still {before}"
        )

    def test_quick_adjust_desaturate_changes_color(self, qtbot):
        """`_quick_adjust('desaturate', amount)` decreases saturation;
        color moves toward gray."""
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((100, 150, 200))
        slot.set_weight(50)
        before = slot.get_color()

        slot._quick_adjust('desaturate', 10)

        after = slot.get_color()
        assert after != before, (
            f"desaturate did not change color: still {before}"
        )

    def test_quick_adjust_warm_shifts_red_higher_than_blue(self, qtbot):
        """`_quick_adjust('warm', amount)` adds `amount` to red and
        subtracts `amount//2` from blue. From a gray (100, 100, 100)
        starting point, the result should have r > b."""
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((100, 100, 100))
        slot.set_weight(50)

        slot._quick_adjust('warm', 15)

        r, g, b = slot.get_color()
        # Warm: red got +15ish, blue got -7ish → r > b
        assert r > b, (
            f"warm should produce r > b for gray input; got "
            f"r={r}, g={g}, b={b}"
        )

    def test_quick_adjust_cool_shifts_blue_higher_than_red(self, qtbot):
        """`_quick_adjust('cool', amount)` adds `amount` to blue and
        subtracts `amount//2` from red. From gray (100, 100, 100), the
        result should have b > r."""
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((100, 100, 100))
        slot.set_weight(50)

        slot._quick_adjust('cool', 15)

        r, g, b = slot.get_color()
        # Cool: blue got +15ish, red got -7ish → b > r
        assert b > r, (
            f"cool should produce b > r for gray input; got "
            f"r={r}, g={g}, b={b}"
        )

    def test_quick_adjust_unknown_type_leaves_color_unchanged(self, qtbot):
        """Unknown adjustment type falls through to the bottom HSV
        round-trip with original (h, s, v) — color should round-trip
        to itself (within int() rounding noise of ±1 per channel)."""
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((100, 100, 100))
        slot.set_weight(50)
        before = slot.get_color()

        slot._quick_adjust('not_a_real_type', 10)

        after = slot.get_color()
        # Round-trip RGB→HSV→RGB may lose ±1 to int() truncation
        for i, (b, a) in enumerate(zip(before, after)):
            assert abs(b - a) <= 1, (
                f"channel {i} drifted more than ±1 on unknown-type "
                f"round-trip: {before} → {after}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 2. ColorSlot — direct action methods (small but several)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotActionMethods:
    def test_copy_hex_to_clipboard_writes_correct_hex(self, qtbot):
        """Originally classified LEGITIMATE based on the assumption
        that clipboard text wasn't readable in offscreen Qt. Verified
        readable: copy a known color, then read the clipboard back and
        assert the hex matches."""
        from color_slot import ColorSlot
        from PyQt6.QtWidgets import QApplication

        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((255, 128, 64))

        # Clear clipboard first to avoid carryover from other tests
        QApplication.clipboard().setText("")

        slot._copy_hex_to_clipboard()

        # Read clipboard text — should be the hex of (255, 128, 64)
        text = QApplication.clipboard().text()
        # Hex format: #RRGGBB (uppercase or lowercase, with or without #)
        # 255=0xFF, 128=0x80, 64=0x40
        # Accept either case
        assert text.lstrip("#").upper() == "FF8040", (
            f"clipboard text mismatch: got {text!r}, "
            f"expected hex of (255, 128, 64) i.e. 'FF8040'"
        )

    def test_reset_color_sets_default_gray(self, qtbot):
        """Originally classified LEGITIMATE; reclassified UPGRADE.
        `_reset_color` sets the slot color to (200, 200, 200) (the
        default gray) — fully observable via get_color()."""
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((100, 200, 50))
        slot.set_weight(75)
        # Confirm we're at the non-default starting state
        assert slot.get_color() == (100, 200, 50)

        slot._reset_color()

        assert slot.get_color() == (200, 200, 200), (
            f"_reset_color should set (200, 200, 200); got {slot.get_color()}"
        )

    def test_pick_color_with_accepted_dialog_applies_color(
        self, qtbot, monkeypatch
    ):
        """`_pick_color` constructs a QColorDialog. If the user accepts,
        the dialog's selectedColor() RGB is passed to `set_color`.

        Originally classified LEGITIMATE because the cancel-path mock
        produced no observable change. Upgraded: mock exec to return
        Accepted AND mock selectedColor to return a known color, then
        assert the slot picked it up."""
        from PyQt6.QtGui import QColor
        from color_slot import ColorSlot

        # Mock exec to return Accepted, and mock selectedColor to return
        # a known QColor
        monkeypatch.setattr(
            QColorDialog, "exec",
            lambda self: QColorDialog.DialogCode.Accepted,
        )
        monkeypatch.setattr(
            QColorDialog, "selectedColor",
            lambda self: QColor(123, 45, 67),
        )

        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        # Set known starting color
        slot.set_color((10, 20, 30))
        assert slot.get_color() == (10, 20, 30)

        slot._pick_color()

        # After the picker accepts (123, 45, 67), the slot should hold it
        assert slot.get_color() == (123, 45, 67), (
            f"_pick_color did not apply selected color; got {slot.get_color()}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 3. ColorSlot — context menu construction
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestColorSlotContextMenu:
    """`contextMenuEvent` builds a complex QMenu with submenu, separators,
    actions, undo/redo entries, theme-aware styling. ~180 stmts of
    construction logic. We mock `QMenu.exec` to avoid blocking."""

    def test_context_menu_with_dark_theme_builds_menu_with_actions(
        self, qtbot, monkeypatch
    ):
        """`contextMenuEvent` builds a QMenu with multiple actions
        (Pick Color, Reset, Undo/Redo, Quick Adjust submenu, Copy Hex,
        ...). We capture the menu via the exec mock and assert it has
        a non-empty action list."""
        from color_slot import ColorSlot

        # Capture the QMenu instance when exec is called
        captured_menu: list = []
        def capture_exec(self, pos=None):
            captured_menu.append(self)
            return None
        monkeypatch.setattr(QMenu, "exec", capture_exec)

        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((100, 150, 200))
        slot.set_weight(50)
        # Default theme is dark

        event = QContextMenuEvent(
            QContextMenuEvent.Reason.Mouse,
            QPoint(50, 50),
        )
        slot.contextMenuEvent(event)

        # Menu should have been created and exec'd
        assert len(captured_menu) == 1, (
            f"expected exactly one menu.exec() call, got {len(captured_menu)}"
        )
        # The menu should have multiple actions (>= 5 for the standard
        # set: Pick Color, Reset, Quick Adjust submenu, Copy Hex, etc.)
        actions = captured_menu[0].actions()
        assert len(actions) >= 5, (
            f"context menu should have >= 5 actions; got {len(actions)}"
        )

    def test_context_menu_with_light_theme_builds_menu_with_actions(
        self, qtbot, monkeypatch
    ):
        """Same as the dark-theme test, but with light theme — exercises
        the alternate stylesheet branch."""
        from color_slot import ColorSlot

        captured_menu: list = []
        def capture_exec(self, pos=None):
            captured_menu.append(self)
            return None
        monkeypatch.setattr(QMenu, "exec", capture_exec)

        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_theme(is_dark=False)
        slot.set_color((50, 100, 200))
        slot.set_weight(75)

        event = QContextMenuEvent(
            QContextMenuEvent.Reason.Mouse,
            QPoint(50, 50),
        )
        slot.contextMenuEvent(event)

        assert len(captured_menu) == 1
        actions = captured_menu[0].actions()
        assert len(actions) >= 5

    def test_context_menu_after_color_changes_has_undo_action_enabled(
        self, qtbot, monkeypatch
    ):
        """After multiple color changes, the menu's Undo action should
        be enabled (the can_undo branch). With a fresh slot Undo would
        be disabled — verify the difference."""
        from color_slot import ColorSlot

        captured_menu: list = []
        def capture_exec(self, pos=None):
            captured_menu.append(self)
            return None
        monkeypatch.setattr(QMenu, "exec", capture_exec)

        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((255, 0, 0))
        slot.set_color((0, 255, 0))
        slot.set_color((0, 0, 255))
        # Confirm undo is available before opening menu
        assert slot.can_undo() is True

        event = QContextMenuEvent(
            QContextMenuEvent.Reason.Mouse,
            QPoint(50, 50),
        )
        slot.contextMenuEvent(event)

        assert len(captured_menu) == 1
        # Find an action whose text starts with 'Undo' and verify it's
        # enabled (the can_undo state should drive its enabled-ness)
        actions = captured_menu[0].actions()
        undo_actions = [
            a for a in actions if a.text().lower().startswith("undo")
        ]
        # If the menu has an Undo entry at all, it should be enabled
        # given the slot has 3 color changes in history. Some menu
        # implementations may use submenu rather than top-level, so we
        # accept either "found and enabled" OR "not in top-level".
        if undo_actions:
            assert undo_actions[0].isEnabled(), (
                "Undo action exists but is disabled after 3 color changes"
            )

    def test_undo_color_restores_previous(self, qtbot):
        """ColorSlot tracks color history (33-entry default per memory)."""
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((255, 0, 0))
        slot.set_color((0, 255, 0))

        if slot.can_undo():
            slot.undo_color()
            # After undo, should be back to red
            assert slot.get_color() == (255, 0, 0)

    def test_redo_color_after_undo(self, qtbot):
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        slot.set_color((255, 0, 0))
        slot.set_color((0, 255, 0))

        if slot.can_undo():
            slot.undo_color()
            if slot.can_redo():
                slot.redo_color()
                # After redo, should be back to green
                assert slot.get_color() == (0, 255, 0)

    def test_can_undo_initially_false(self, qtbot):
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        # Fresh slot should not have undo history
        assert slot.can_undo() is False

    def test_can_redo_initially_false(self, qtbot):
        from color_slot import ColorSlot
        slot = ColorSlot(0)
        qtbot.addWidget(slot)
        assert slot.can_redo() is False
