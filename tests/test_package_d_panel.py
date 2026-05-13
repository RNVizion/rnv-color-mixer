"""
RNV Color Mixer — Package D Panel Tests  (Phase 6.2)
======================================================

Exercises `core/package_d_panel.py` — the largest unexercised module after
Phase 5 (1,443 statements at 6.1% coverage). Construction alone fires
`_build_ui()` and the six `_create_*_tab()` methods, lifting coverage
substantially.

Approach
--------
Two access paths, both tested:

  1. **Via main app**: `app_window.open_package_d_panel()` constructs the
     panel with all real dependencies wired up. This is the path users hit.

  2. **Standalone**: `PackageDPanel(parent=None, ...)` with `None` defaults
     for color_history / preset_palettes / settings_manager. This validates
     the panel handles missing deps gracefully — a contract relevant for
     plugin/embedding scenarios.

What's NOT tested here
----------------------
Driving individual tab interactions (clicking history entries, applying
harmonies, etc.) is deferred. Each tab has its own signal handlers that
would need ~5–10 tests; total cost would balloon the file. Phase 6.3 (if
ever pursued) is where tab interaction tests would live.
"""

from __future__ import annotations

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

EXPECTED_TAB_TITLES = [
    "📜 History",
    "🎨 Presets",
    "🎵 Harmony",
    "💾 Sessions",
    "⚡ Quick Actions",
    "⚙️ Settings",
]

EXPECTED_SIGNALS = [
    "load_history_color",
    "load_preset",
    "save_as_preset",
    "apply_harmony",
    "load_session",
    "save_session",
    "export_current_mix",
    "pick_screen_color",
    "generate_quick_palette",
    "settings_changed",
]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction via main app — the user-visible path
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPackageDPanelViaMainApp:
    """The main app exposes `open_package_d_panel()` (Ctrl+,) which lazily
    constructs the panel with real dependencies. These tests verify the
    panel comes up correctly and stays consistent across opens."""

    def test_open_package_d_panel_creates_instance(self, app_window):
        assert not hasattr(app_window, "_package_d_panel") or \
               app_window._package_d_panel is None
        app_window.open_package_d_panel()
        assert app_window._package_d_panel is not None

    def test_panel_has_six_tabs_with_expected_titles(self, app_window):
        app_window.open_package_d_panel()
        panel = app_window._package_d_panel
        assert hasattr(panel, "tabs")
        assert panel.tabs.count() == 6

        actual_titles = [panel.tabs.tabText(i) for i in range(panel.tabs.count())]
        assert actual_titles == EXPECTED_TAB_TITLES, (
            f"Tab titles drifted from spec.\n"
            f"  expected: {EXPECTED_TAB_TITLES}\n"
            f"  actual:   {actual_titles}"
        )

    def test_panel_has_six_named_tab_widgets(self, app_window):
        """Each tab widget is stored on the panel as `<name>_tab` for
        downstream access. Verify all six are present and not None."""
        app_window.open_package_d_panel()
        panel = app_window._package_d_panel
        for name in ("history_tab", "presets_tab", "harmony_tab",
                     "sessions_tab", "quick_actions_tab", "settings_tab"):
            assert hasattr(panel, name), f"missing {name} attribute"
            assert getattr(panel, name) is not None, f"{name} is None"

    def test_panel_can_switch_active_tab(self, app_window):
        app_window.open_package_d_panel()
        panel = app_window._package_d_panel
        for i in range(panel.tabs.count()):
            panel.tabs.setCurrentIndex(i)
            assert panel.tabs.currentIndex() == i

    def test_panel_has_all_public_signals(self, app_window):
        """The panel publishes signals for the main app to react to. If a
        signal is renamed without updating both ends, this catches it."""
        app_window.open_package_d_panel()
        panel = app_window._package_d_panel
        for sig_name in EXPECTED_SIGNALS:
            assert hasattr(panel, sig_name), (
                f"Panel is missing signal: {sig_name!r}"
            )

    def test_set_theme_dark_applies_without_crash(self, app_window):
        app_window.open_package_d_panel()
        panel = app_window._package_d_panel
        panel.set_theme(True)   # dark
        panel.set_theme(False)  # light
        panel.set_theme(True)   # back to dark

    def test_reopen_does_not_create_new_instance(self, app_window):
        """The panel is cached on the app — re-opening must reuse, not
        re-create. Catches a re-instantiation regression that would leak
        signal connections."""
        app_window.open_package_d_panel()
        first = app_window._package_d_panel
        app_window.open_package_d_panel()
        second = app_window._package_d_panel
        assert first is second, (
            "Panel was re-instantiated on reopen — would leak the prior "
            "instance's signal connections."
        )

    def test_panel_set_theme_propagates_after_main_theme_cycle(
        self, app_window
    ):
        """Theme cycle on the main window re-applies theme to a live
        panel via `set_theme(is_dark or is_image)`. Verify the call site
        in `_on_theme_button_clicked` actually fires when panel is open."""
        app_window.open_package_d_panel()
        panel = app_window._package_d_panel

        calls: list[bool] = []
        original_set_theme = panel.set_theme

        def instrumented(is_dark):
            calls.append(is_dark)
            return original_set_theme(is_dark)

        panel.set_theme = instrumented
        app_window._on_theme_button_clicked()

        assert len(calls) == 1, (
            f"Expected panel.set_theme to be called once on theme cycle; "
            f"saw {len(calls)} calls"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Standalone construction — robustness contract
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPackageDPanelStandalone:
    """Construction outside the main-app context. Catches regressions where
    the panel becomes coupled to specific parent state."""

    def test_panel_constructs_with_all_none_dependencies(
        self, isolated_home, qtbot
    ):
        """No parent, no color_history, no preset_palettes, no settings
        manager — the panel must still build all 6 tabs without crashing."""
        from core.package_d_panel import PackageDPanel

        panel = PackageDPanel(
            parent=None,
            color_history=None,
            preset_palettes=None,
            settings_manager=None,
        )
        qtbot.addWidget(panel)
        assert panel.tabs.count() == 6

    def test_panel_constructs_with_only_color_history(
        self, isolated_home, qtbot
    ):
        from core.package_d_panel import PackageDPanel
        from core.color_history import ColorHistory

        ch = ColorHistory()
        panel = PackageDPanel(parent=None, color_history=ch)
        qtbot.addWidget(panel)
        assert panel.tabs.count() == 6

    def test_panel_constructs_with_only_preset_palettes(
        self, isolated_home, qtbot
    ):
        from core.package_d_panel import PackageDPanel
        from core.preset_palettes import PresetPalettes

        pp = PresetPalettes()
        panel = PackageDPanel(parent=None, preset_palettes=pp)
        qtbot.addWidget(panel)
        assert panel.tabs.count() == 6

    def test_panel_set_theme_works_standalone(self, isolated_home, qtbot):
        """`set_theme` must not depend on parent or settings_manager being
        present — the panel can be embedded in a test harness or third-
        party container."""
        from core.package_d_panel import PackageDPanel

        panel = PackageDPanel(
            parent=None,
            color_history=None,
            preset_palettes=None,
            settings_manager=None,
        )
        qtbot.addWidget(panel)
        # Both directions exercise the full _apply_widget_stylesheet path
        panel.set_theme(True)
        panel.set_theme(False)
        panel.set_theme(True)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Main-app integration: panel signals are wired correctly
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPackageDPanelSignalWiring:
    """The main app connects ~10 signals from the panel to its own slots.
    Each connection point has a `track_as=` label in `signal_manager.connect`
    — this section verifies those wires are made on first open."""

    def test_panel_signals_increase_signal_manager_count(self, app_window):
        sm = app_window.signal_manager
        if sm is None:
            pytest.skip("SignalConnectionManager not available")

        before = sm.get_stats().get("active", 0)
        app_window.open_package_d_panel()
        after = sm.get_stats().get("active", 0)

        # The main app connects multiple panel signals on first open.
        # Exact count depends on which optional features compile in, but
        # at least the core load/save signals must be wired.
        assert after >= before + 4, (
            f"Expected ≥4 new signal connections after opening panel; "
            f"saw {after - before}"
        )

    def test_panel_signals_have_correct_pyqt_signal_type(self, app_window):
        """Each declared signal must be a real `pyqtBoundSignal`, not just
        any attribute. Catches accidental shadowing or rename-without-emit
        regressions on the panel side."""
        from PyQt6.QtCore import pyqtBoundSignal

        app_window.open_package_d_panel()
        panel = app_window._package_d_panel
        for sig_name in EXPECTED_SIGNALS:
            sig = getattr(panel, sig_name)
            assert isinstance(sig, pyqtBoundSignal), (
                f"{sig_name} is {type(sig).__name__}, not a pyqtBoundSignal"
            )
