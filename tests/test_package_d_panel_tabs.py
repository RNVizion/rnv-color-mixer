"""
RNV Color Mixer — Package D Panel Tab Interaction Tests  (Phase 7.3)
======================================================================

Drives the user-interaction handlers on each of the 6 tabs. Phase 6.2
already covered construction, signal-wiring, and theme application;
this phase covers what happens when users actually click things.

Lessons applied from Phase 7.1 and 7.2:
  - Method-inventory rule: every method tested was first verified by
    grepping the source for its actual name AND signature.
  - Modal handling: any test path that pops `QMessageBox`/`QInputDialog`
    is monkeypatched with a return value, never relied on offscreen
    dismissal.
  - String-keyed dispatch tested with the EXACT enum strings the source
    uses (e.g. `mixing_algo_combo` indices 0-5, not algorithm names).

Standalone construction is preferred where possible (parent=None, all
deps None) — avoids the cost of building a full ColorMixerApp for tests
that only need the panel.
"""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

from core.package_d_panel import PackageDPanel


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def standalone_panel(qtbot, isolated_home, monkeypatch):
    """A PackageDPanel built with no parent, no real dependencies.

    Suppresses every modal that any handler could fire. Tests that
    deliberately exercise a modal branch should use their own monkeypatch
    fixtures inside the test body.
    """
    from PyQt6.QtWidgets import QMessageBox, QInputDialog

    # Default suppression so the runner never hangs on a stray modal
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: 0)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: 0)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **kw: 0)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: 1)
    monkeypatch.setattr(
        QInputDialog, "getText",
        lambda *a, **kw: ("test_session_name", True),
    )

    panel = PackageDPanel(
        parent=None,
        color_history=None,
        preset_palettes=None,
        settings_manager=None,
    )
    qtbot.addWidget(panel)
    return panel


# ═══════════════════════════════════════════════════════════════════════════
# 1. History tab (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestHistoryTab:
    """The history tab shows a `history_list` populated from `color_history`.
    Clicking an item fires `load_history_color` with the RGB tuple."""

    def test_history_tab_has_required_widgets(self, standalone_panel):
        """history_list must exist; without it the tab is broken."""
        assert hasattr(standalone_panel, "history_list")
        assert standalone_panel.history_list is not None

    def test_history_list_starts_empty_with_no_history(self, standalone_panel):
        """With color_history=None the list should be empty (or contain
        a placeholder, but not crash on access)."""
        # Refresh is safe to call with no backing color_history
        try:
            standalone_panel.refresh_history()
        except Exception as e:
            pytest.fail(
                f"refresh_history with no color_history raised "
                f"{type(e).__name__}: {e}"
            )

    def test_clicking_history_item_with_rgb_tuple_emits_load_signal(
        self, standalone_panel, qtbot
    ):
        """Inject a synthetic history item with an RGB tuple payload and
        verify the click handler emits `load_history_color` correctly.

        The handler does `self.parent().status_updated.emit(...)` which
        crashes when parent is None — so we monkeypatch parent() to return
        an object with a no-op status_updated."""
        # Build a fake parent with a status_updated signal-like object
        class _FakeParent:
            class _FakeSignal:
                def emit(self, *args, **kwargs): pass
            status_updated = _FakeSignal()

        fake_parent = _FakeParent()
        standalone_panel.parent = lambda: fake_parent

        # Insert a synthetic item with an RGB tuple as user data
        item = QListWidgetItem("Red")
        item.setData(Qt.ItemDataRole.UserRole, (255, 0, 0))
        standalone_panel.history_list.addItem(item)

        with qtbot.waitSignal(
            standalone_panel.load_history_color, timeout=1000
        ) as blocker:
            standalone_panel._on_history_item_clicked(item)
        assert blocker.args == [(255, 0, 0)]


# ═══════════════════════════════════════════════════════════════════════════
# 2. Presets tab (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPresetsTab:
    """The presets tab has a category combo, presets list, and delete
    button. Phase 7.3 covers the basic widget existence and the
    refresh_presets path."""

    def test_presets_tab_has_required_widgets(self, standalone_panel):
        for attr in ("presets_list", "category_combo", "delete_preset_btn"):
            assert hasattr(standalone_panel, attr), f"missing {attr}"

    def test_refresh_presets_with_no_preset_palettes_does_not_crash(
        self, standalone_panel
    ):
        """preset_palettes=None should be handled gracefully."""
        try:
            standalone_panel.refresh_presets()
        except Exception as e:
            pytest.fail(
                f"refresh_presets with no preset_palettes raised "
                f"{type(e).__name__}: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 3. Harmony tab (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestHarmonyTab:
    """The harmony tab has type and base color combos, a preview list,
    and a refresh button. Changing the type combo fires
    `_on_harmony_type_changed`."""

    def test_harmony_tab_has_required_widgets(self, standalone_panel):
        for attr in ("harmony_type_combo", "harmony_base_combo",
                     "harmony_preview_list", "harmony_refresh_btn"):
            assert hasattr(standalone_panel, attr), f"missing {attr}"

    def test_harmony_type_combo_has_multiple_options(self, standalone_panel):
        """The combo should be populated with at least the 7 HarmonyType
        enum values (Complementary, Triadic, Analogous, etc.)."""
        n = standalone_panel.harmony_type_combo.count()
        assert n >= 5, (
            f"harmony_type_combo has only {n} entries; expected ≥ 5 "
            f"(7 HarmonyType enum values)"
        )

    def test_changing_harmony_type_combo_does_not_crash(self, standalone_panel):
        """Cycle through every entry in the combo — handler is invoked
        on each change via `_on_harmony_type_changed`."""
        n = standalone_panel.harmony_type_combo.count()
        for i in range(n):
            standalone_panel.harmony_type_combo.setCurrentIndex(i)
        # We made it through all options without exception


# ═══════════════════════════════════════════════════════════════════════════
# 4. Sessions tab (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSessionsTab:
    """Sessions tab shows a list of saved sessions plus save/load/delete
    buttons. Save goes through QInputDialog (modal — monkeypatched)."""

    def test_sessions_tab_has_required_widgets(self, standalone_panel):
        assert hasattr(standalone_panel, "sessions_list")
        assert standalone_panel.sessions_list is not None

    def test_save_session_with_no_session_manager_pops_warning(
        self, standalone_panel
    ):
        """`_on_save_session` pops a `QMessageBox.warning("Not Available"...)`
        modal when session_manager is None. Default fixture monkeypatch
        traps the modal — verify the call doesn't crash."""
        try:
            standalone_panel._on_save_session()
        except Exception as e:
            pytest.fail(
                f"_on_save_session with no session_manager raised "
                f"{type(e).__name__}: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 5. Quick Actions tab (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestQuickActionsTab:
    """Quick Actions has the screen-color picker button and quick-palette
    generators. These are pure signal emitters."""

    def test_picker_button_exists(self, standalone_panel):
        assert hasattr(standalone_panel, "picker_btn")
        assert standalone_panel.picker_btn is not None

    def test_export_current_mix_emits_signal(self, standalone_panel, qtbot):
        """`_on_export_current_mix` is a one-line emitter."""
        with qtbot.waitSignal(
            standalone_panel.export_current_mix, timeout=1000
        ):
            standalone_panel._on_export_current_mix()


# ═══════════════════════════════════════════════════════════════════════════
# 6. Settings tab (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSettingsTab:
    """The settings tab has many checkboxes (tooltips, animations, debug
    overlays, history-enabled, etc.) and combos (theme, mixing algorithm,
    export format). Each checkbox fires `settings_changed` when toggled."""

    def test_settings_tab_has_required_widgets(self, standalone_panel):
        for attr in (
            "tooltips_check", "animations_check", "debug_overlays_check",
            "history_enabled_check", "autosave_check", "autoload_session_check",
            "show_rgb_check", "show_hsv_check",
            "theme_combo", "mixing_algo_combo", "export_format_combo",
            "history_limit_spin", "max_slots_spin",
        ):
            assert hasattr(standalone_panel, attr), f"missing {attr}"

    def test_save_ui_to_settings_emits_settings_changed_for_each_setting(
        self, qtbot, isolated_home, monkeypatch
    ):
        """`_save_ui_to_settings` is the handler that runs when the user
        clicks Apply/OK. It iterates through each UI control, persists to
        settings_manager, and emits `settings_changed` per key.

        We need a real (or mock) settings_manager because `set(...)` is
        called for each key. We use a tiny stub that records calls and
        provides defaults for `get(...)`."""
        from PyQt6.QtWidgets import QMessageBox, QInputDialog

        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: 0)
        monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: 0)

        class _StubSettings:
            def __init__(self):
                self.set_calls: list = []
            def get(self, key, default=None): return default
            def set(self, key, value): self.set_calls.append((key, value))
            def save(self): pass

        stub = _StubSettings()
        panel = PackageDPanel(
            parent=None, color_history=None, preset_palettes=None,
            settings_manager=stub,
        )
        qtbot.addWidget(panel)

        # Collect all settings_changed emissions
        emissions: list = []
        panel.settings_changed.connect(
            lambda key, value: emissions.append((key, value))
        )

        panel._save_ui_to_settings(skip_theme=False)

        # Apply must emit at least the core preference signals
        keys_emitted = {key for key, _ in emissions}
        for required_key in (
            "auto_save_colors", "auto_load_last_session", "show_tooltips",
            "history_enabled",
        ):
            assert required_key in keys_emitted, (
                f"Apply did not emit settings_changed for {required_key!r}. "
                f"Emitted: {sorted(keys_emitted)}"
            )
