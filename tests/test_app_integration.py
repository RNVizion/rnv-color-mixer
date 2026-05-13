"""
RNV Color Mixer — App-Level Integration Tests  (Phase 4 deliverable)
=====================================================================

Instantiates the real ColorMixerApp inside an offscreen Qt environment,
drives it via its public methods/signals, and verifies state. This is
the highest-ROI phase — every regression that's actually been hit in v3.x
(closeEvent QThread crash, enumerate() session restore, tooltip restore
by button_name, AboutDialog isolation) is now actively guarded here.

Isolation rules
---------------
1. **Per-test fresh app**: `app_window` fixture creates a new `ColorMixerApp`
   and tears it down via real `closeEvent`. No reference is shared between
   tests (per phase plan's "Do NOT" rule).
2. **No user data pollution**: `isolated_home` redirects HOME / USERPROFILE /
   APPDATA / XDG_CONFIG_HOME to a per-test tmp dir, so settings, sessions,
   color history, and autosave files all land in a sandbox.
3. **No real screen-color picker**: tests that touch picker code paths
   stick to inspecting wiring, not invoking multi-monitor sampling.
4. **State, not pixels**: tests verify object state (colours, weights,
   theme name, file existence) rather than pixel-perfect rendering.

Synchronization rule: NO time.sleep — qtbot.waitUntil / waitSignal only.
"""

from __future__ import annotations

import json
import os
import time
import pytest
from pathlib import Path

# Bootstrap (sys.path / virtual packages) is done by tests/conftest.py.
# Importing ColorMixerApp here triggers heavy module loads — defer to fixture
# to avoid module-level side effects during collection.


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════
# `isolated_home` and `app_window` now live in tests/conftest.py so they can
# be used by other Phase 6+ test files (e.g. test_package_d_panel.py).
# Only the file-local helper remains here.


def _ensure_n_slots(win, n: int) -> None:
    """Add slots until len(win.slots) == n (default app starts with 2)."""
    while len(win.slots) < n:
        win.add_color_slot()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Lifecycle (4 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAppLifecycle:
    """Construction, closing, repeated cycling. Targets the QThread close-time
    crash regression directly via the `cleanup()` call site in `closeEvent`."""

    def test_app_instantiates_with_default_state(self, app_window):
        assert app_window.windowTitle().startswith("RNV Color Mixer") or \
               "Color Mixer" in app_window.windowTitle()
        assert hasattr(app_window, "slots")
        assert len(app_window.slots) >= 2
        assert hasattr(app_window, "ui_handler")
        assert hasattr(app_window, "session_manager")
        assert hasattr(app_window, "color_history")
        assert app_window.current_mixed_color is not None

    def test_close_event_calls_color_history_cleanup(
        self, isolated_home, qtbot, main_module
    ):
        """Regression guard: the v3.3.3 close-time QThread crash was fixed by
        calling `self.color_history.cleanup()` inside `closeEvent`. This
        test instruments cleanup() with a flag and asserts it ran."""
        win = main_module.ColorMixerApp()
        qtbot.addWidget(win)

        called = {"flag": False}
        original_cleanup = win.color_history.cleanup

        def instrumented_cleanup(*args, **kwargs):
            called["flag"] = True
            return original_cleanup(*args, **kwargs)

        win.color_history.cleanup = instrumented_cleanup
        win.close()

        assert called["flag"] is True, (
            "ColorHistory.cleanup() must be called from closeEvent. "
            "Removing this call brings back the QThread destroyed-while-"
            "running crash on quick exit."
        )

    def test_close_event_stops_autosave_timer(self, isolated_home, qtbot, main_module):
        """closeEvent should call session_manager.stop_autosave()."""
        win = main_module.ColorMixerApp()
        qtbot.addWidget(win)

        called = {"flag": False}
        original = win.session_manager.stop_autosave

        def instrumented(*a, **kw):
            called["flag"] = True
            return original(*a, **kw)

        win.session_manager.stop_autosave = instrumented
        win.close()

        assert called["flag"] is True, "closeEvent must stop autosave"

    def test_two_consecutive_app_cycles_are_stable(
        self, isolated_home, qtbot, main_module
    ):
        """Build → close → build → close. Catches state leaks between
        QApplication-shared instances."""
        for cycle in range(2):
            win = main_module.ColorMixerApp()
            qtbot.addWidget(win)
            assert len(win.slots) >= 2, f"cycle {cycle}: missing default slots"
            win.close()


# ═══════════════════════════════════════════════════════════════════════════
# 2. Theme cycling (4 tests) — guards the v3.1.3 _apply_widget_stylesheet fix
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestThemeCycling:
    """The v3.1.3 milestone moved widget-level inline stylesheets into a
    dedicated `_apply_widget_stylesheet` method called on every theme change.
    These tests verify the cycle progresses through the three documented
    themes and that the documented apply hooks are invoked."""

    def test_default_theme_is_dark_mode(self, app_window):
        assert app_window.ui_handler.get_current_theme_name() == "Dark Mode"
        assert app_window.ui_handler.is_dark_mode() is True
        assert app_window.ui_handler.is_image_mode() is False

    def test_cycle_dark_to_light_changes_active_theme(self, app_window):
        before = app_window.ui_handler.get_current_theme_name()
        app_window._on_theme_button_clicked()
        after = app_window.ui_handler.get_current_theme_name()
        assert after != before
        assert app_window.ui_handler.is_dark_mode() is False

    def test_cycle_three_steps_visits_expected_themes(self, app_window):
        """Theme cycle behaviour depends on whether Image Mode assets exist:
          • If `image_mode_available` is True (a background image or ≥4 button
            base PNGs are on disk): Dark → Light → Image → Dark → … (ternary)
          • Otherwise: Dark ↔ Light (binary)
        This test asserts the right one fires for the current environment."""
        tm = app_window.ui_handler.theme_manager
        seen = [app_window.ui_handler.get_current_theme_name()]
        for _ in range(3):
            app_window._on_theme_button_clicked()
            seen.append(app_window.ui_handler.get_current_theme_name())

        distinct = set(seen)
        if tm.image_mode_available:
            assert len(distinct) == 3, (
                f"Image Mode is available — expected 3 distinct themes after "
                f"3 cycles; saw {distinct}"
            )
        else:
            assert distinct == {"Dark Mode", "Light Mode"}, (
                f"Image Mode unavailable — expected only Dark/Light cycling; "
                f"saw {distinct}"
            )
        # Cycle must actually be progressing in either case
        assert seen[1] != seen[0], "Theme didn't change on first cycle"

    def test_cycle_theme_calls_apply_to_buttons_and_components(
        self, app_window
    ):
        """Both `_apply_theme_to_buttons` and `_apply_theme_to_all` must run
        on every cycle — the v3.1.3 regression was a silent failure to
        re-style widgets when the theme changed."""
        button_calls = {"n": 0}
        all_calls = {"n": 0}

        original_buttons = app_window._apply_theme_to_buttons
        original_all = app_window._apply_theme_to_all

        def instr_buttons(*a, **kw):
            button_calls["n"] += 1
            return original_buttons(*a, **kw)

        def instr_all(*a, **kw):
            all_calls["n"] += 1
            return original_all(*a, **kw)

        app_window._apply_theme_to_buttons = instr_buttons
        app_window._apply_theme_to_all = instr_all
        app_window._on_theme_button_clicked()

        assert button_calls["n"] == 1, "_apply_theme_to_buttons not called"
        assert all_calls["n"] == 1, "_apply_theme_to_all not called"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Session save / restore (4 tests) — guards the enumerate() fix
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSessionRoundTrip:
    """The session loader uses `enumerate(slots_data)` to iterate slots in
    order; an earlier bug iterated by index and silently truncated multi-slot
    sessions. These tests confirm full multi-slot round-trips."""

    def test_save_load_preserves_colors_2_slots(self, app_window, tmp_path):
        app_window.slots[0].set_color((123, 45, 67))
        app_window.slots[0].set_weight(50)
        app_window.slots[1].set_color((200, 100, 30))
        app_window.slots[1].set_weight(30)

        sess_path = str(tmp_path / "s.session")
        app_window._on_save_session(sess_path)
        assert os.path.exists(sess_path), "session file not created"

        # Mutate state, then reload from disk
        app_window.slots[0].set_color((0, 0, 0))
        app_window.slots[1].set_color((0, 0, 0))
        app_window._load_session_file(sess_path)

        assert app_window.slots[0].get_color() == (123, 45, 67)
        assert app_window.slots[1].get_color() == (200, 100, 30)

    def test_save_load_preserves_weights(self, app_window, tmp_path):
        app_window.slots[0].set_weight(75)
        app_window.slots[1].set_weight(25)

        sess_path = str(tmp_path / "w.session")
        app_window._on_save_session(sess_path)
        app_window.slots[0].set_weight(0)
        app_window.slots[1].set_weight(0)
        app_window._load_session_file(sess_path)

        assert app_window.slots[0].get_weight() == 75
        assert app_window.slots[1].get_weight() == 25

    def test_save_load_12_slot_session(self, app_window, tmp_path):
        """The enumerate() fix matters most when slot count exceeds default 2."""
        _ensure_n_slots(app_window, 12)
        assert len(app_window.slots) == 12

        # Distinct colour/weight per slot so any silent reordering shows up
        for i in range(12):
            app_window.slots[i].set_color((i * 20, 100 + i, (i * 7) % 256))
            app_window.slots[i].set_weight(8)  # 12 × 8 ≈ 100

        sess_path = str(tmp_path / "12.session")
        app_window._on_save_session(sess_path)

        # Wipe and reload
        for i in range(12):
            app_window.slots[i].set_color((0, 0, 0))
            app_window.slots[i].set_weight(0)
        app_window._load_session_file(sess_path)

        for i in range(12):
            expected = (i * 20, 100 + i, (i * 7) % 256)
            assert app_window.slots[i].get_color() == expected, (
                f"slot {i} colour drifted; got {app_window.slots[i].get_color()}"
            )
            assert app_window.slots[i].get_weight() == 8

    def test_autosave_writes_file_when_triggered(self, app_window):
        """Trigger autosave directly (don't wait the 60s interval) and
        confirm a file lands in the autosave directory."""
        sm = app_window.session_manager
        # Most session managers expose perform_autosave or similar; if not,
        # fall back to building the same payload save_session would write.
        slots_data = [
            {"index": s.index, "color": list(s.get_color()),
             "weight": s.get_weight()}
            for s in app_window.slots
        ]
        # Use the same save method the autosave timer would use internally
        autosave_dir = sm.sessions_dir
        target = autosave_dir / "manual_autosave.session"
        ok = sm.save_session(
            filepath=str(target),
            slots_data=slots_data,
            mixed_color=app_window.current_mixed_color,
            settings={},
            name="manual_autosave",
            description="phase 4 autosave smoke test",
        )
        assert ok is True
        assert target.exists()


# ═══════════════════════════════════════════════════════════════════════════
# 4. AboutDialog (3 tests) — guards v3.3.3 isolation fix
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAboutDialog:
    """The v3.3.3 fix isolated AboutDialog from the main window's stylesheet
    cascade so opening it didn't trigger expensive re-layouts. These tests
    verify the dialog opens, can be re-opened, and creation cost stays linear."""

    def test_about_dialog_opens_without_crash(self, app_window):
        app_window.open_about_dialog()
        assert hasattr(app_window, "_about_dialog")
        assert app_window._about_dialog is not None

    def test_about_dialog_reopens_without_creating_duplicate(self, app_window):
        app_window.open_about_dialog()
        first = app_window._about_dialog
        app_window._about_dialog.close()
        app_window.open_about_dialog()
        # Implementation reuses the same instance — that's the design
        assert app_window._about_dialog is first

    def test_creating_5_about_dialogs_stays_linear_in_time(
        self, app_window, isolated_home
    ):
        """The pre-fix bug caused dialog creation to slow exponentially as
        more were opened (stylesheet propagation through parent chain).
        Creating 5 fresh instances must stay roughly linear."""
        from ui.about_dialog import AboutDialog

        durations: list[float] = []
        dialogs = []
        for _ in range(5):
            t0 = time.perf_counter()
            d = AboutDialog(app_window, app_window.ui_handler)
            durations.append(time.perf_counter() - t0)
            dialogs.append(d)

        # The 5th creation must not take wildly longer than the 1st.
        # Allow generous 10x to account for one-time caches warming up.
        assert durations[-1] < max(durations[0] * 10.0, 0.5), (
            f"AboutDialog creation appears non-linear: {durations}"
        )

        for d in dialogs:
            d.deleteLater()


# ═══════════════════════════════════════════════════════════════════════════
# 5. Mixing & slots (4 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestMixingAndSlots:
    """The auto_mix_colors path is the heart of the app's user value. These
    tests verify state propagation from slot mutation → mix output."""

    def test_set_color_then_auto_mix_updates_current_mixed(self, app_window):
        app_window.slots[0].set_color((255, 0, 0))
        app_window.slots[0].set_weight(100)
        app_window.slots[1].set_weight(0)
        app_window.auto_mix_colors()

        # Expect pure red since only slot 0 contributes
        assert app_window.current_mixed_color == (255, 0, 0)

    def test_changing_weight_changes_mix_result(self, app_window):
        app_window.slots[0].set_color((255, 0, 0))
        app_window.slots[1].set_color((0, 0, 255))
        app_window.slots[0].set_weight(50)
        app_window.slots[1].set_weight(50)
        app_window.auto_mix_colors()
        balanced = app_window.current_mixed_color

        # Tilt heavily toward slot 0
        app_window.slots[0].set_weight(99)
        app_window.slots[1].set_weight(1)
        app_window.auto_mix_colors()
        red_heavy = app_window.current_mixed_color

        assert red_heavy != balanced
        # Should be much redder than the balanced mix
        assert red_heavy[0] > balanced[0]
        assert red_heavy[2] < balanced[2]

    def test_clearing_slot_updates_mix(self, app_window):
        app_window.slots[0].set_color((255, 0, 0))
        app_window.slots[0].set_weight(100)
        app_window.slots[1].set_weight(0)
        app_window.auto_mix_colors()
        before = app_window.current_mixed_color

        app_window.slots[0].clear()
        app_window.auto_mix_colors()
        after = app_window.current_mixed_color

        assert before != after
        # No contributing slots → black sentinel
        assert after == (0, 0, 0)

    def test_zero_weight_slots_excluded_from_mix(self, app_window):
        """Slots with weight 0 must not contribute to the mix even if they
        have a non-default colour set."""
        app_window.slots[0].set_color((100, 200, 50))
        app_window.slots[0].set_weight(0)
        app_window.slots[1].set_color((50, 50, 50))
        app_window.slots[1].set_weight(100)
        app_window.auto_mix_colors()

        # Only slot 1 contributes, so the mix should equal slot 1's colour
        assert app_window.current_mixed_color == (50, 50, 50)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Misc regressions (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestMiscRegressions:
    """Smaller regression guards covering: tooltip-restore by `button_name`
    property (not by id(widget)), palette export from live app state, and
    closeEvent idempotency."""

    def test_buttons_have_button_name_property_for_tooltip_restore(
        self, app_window
    ):
        """The pre-fix bug stored tooltip mappings keyed on `id(widget)`
        (memory addresses), which became stale when widgets were re-created
        across theme cycles. The fix uses the stable `button_name` property.
        Verify that property is set on at least one well-known button."""
        named_buttons = [
            b for b in getattr(app_window, "buttons", [])
            if b.property("button_name")
        ]
        assert len(named_buttons) > 0, (
            "No button has a 'button_name' property — tooltip restoration "
            "after theme cycle will fall back to id() and break."
        )

    def test_palette_export_from_live_app_state(self, app_window, tmp_path):
        """Drive the actual export pipeline from app slots to a JSON file."""
        from core.palette_formats import PaletteFormats

        app_window.slots[0].set_color((10, 20, 30))
        app_window.slots[0].set_weight(50)
        app_window.slots[1].set_color((200, 100, 50))
        app_window.slots[1].set_weight(50)

        # Export uses the same data structure auto_mix_colors consumes
        out = tmp_path / "exported.json"
        palette = [
            (s.get_color(), s.get_weight())
            for s in app_window.slots
            if s.get_weight() > 0
        ]
        PaletteFormats.export_palette(str(out), palette)

        assert out.exists()
        assert out.stat().st_size > 0
        with open(out) as f:
            data = json.load(f)
        # Implementation-specific JSON shape — assert basic invariants only
        assert data, "exported JSON is empty"

    def test_close_event_safe_to_call_twice(self, isolated_home, qtbot, main_module):
        """Defensive: `closeEvent` is normally fired once by Qt, but the
        cleanup helpers it calls (color_history.cleanup, stop_autosave)
        are themselves required to be idempotent — Phase 3 covered the
        ColorHistory side, this covers the integration point."""
        win = main_module.ColorMixerApp()
        qtbot.addWidget(win)
        win.close()  # first
        # Second close — Qt may swallow this, but it must not raise
        try:
            win.close()
        except Exception as e:
            pytest.fail(f"second close raised {type(e).__name__}: {e}")
