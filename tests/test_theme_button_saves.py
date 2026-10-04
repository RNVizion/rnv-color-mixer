"""RNV-THEME-SAVE, 2026-09-30: the theme button files the mode it set.

WHAT WAS WRONG. The button changed the mode for the session only. Only the
control panel's Save wrote preferences.theme, so a switch made with the
button was lost at the next launch, which opened in whatever the file held.
The picker's and the transformer's buttons file the mode on every press;
ruled 2026-09-30 that the mixer's should too.

Each test drives the app the way a person does: the theme button, the
panel's opener, the panel's Save, a second launch. What is asserted is read
back from the settings FILE on disk, not from memory, because the file is
what the next launch reads.
"""
from __future__ import annotations

import json

import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton

pytestmark = pytest.mark.integration


def _mode(app_window) -> str:
    return app_window.ui_handler.theme_manager.current_theme


def _switch(app_window) -> str:
    """One press of the theme button."""
    app_window._on_theme_button_clicked()
    QApplication.processEvents()
    return _mode(app_window)


def _on_disk(app_window) -> dict:
    """The settings file as it is now, re-read from disk."""
    with open(app_window.settings_manager.settings_file, encoding="utf-8") as f:
        return json.load(f)


def _without_theme(settings: dict) -> dict:
    prefs = {k: v for k, v in settings.get("preferences", {}).items() if k != "theme"}
    rest = {k: v for k, v in settings.items() if k != "preferences"}
    return {**rest, "preferences": prefs}


def test_the_button_files_the_mode_it_set(app_window):
    seen = []
    for _ in range(3):                                  # every mode, and back
        mode = _switch(app_window)
        seen.append(mode)
        assert _on_disk(app_window)["preferences"]["theme"] == mode, mode
    assert {"dark", "light", "image"} <= set(seen), seen


def test_the_button_writes_the_mode_and_nothing_else(app_window):
    before = _without_theme(_on_disk(app_window))
    for _ in range(3):
        _switch(app_window)
        assert _without_theme(_on_disk(app_window)) == before, \
            "a press of the theme button changed a setting other than the mode on disk"


def test_the_next_launch_opens_in_the_mode_the_button_set(app_window, main_module, qtbot):
    for _ in range(2):
        mode = _switch(app_window)
        again = main_module.ColorMixerApp()
        qtbot.addWidget(again)
        try:
            QApplication.processEvents()
            assert _mode(again) == mode, (mode, _mode(again))
            assert again.theme_button.text() == app_window.theme_button.text()
        finally:
            again.close()
            QApplication.processEvents()


def test_a_saved_auto_gives_way_to_the_mode_the_button_set(app_window):
    """The panel can save Auto (follow system). The app starts in dark for it
    and follows no system scheme. A press of the button files the mode the
    app is in, as the picker's does, so the next launch opens in that mode."""
    app_window.settings_manager.set("preferences.theme", "auto")
    assert app_window.settings_manager.save_settings()
    assert _on_disk(app_window)["preferences"]["theme"] == "auto"
    mode = _switch(app_window)
    assert _on_disk(app_window)["preferences"]["theme"] == mode


def test_save_still_files_the_mode_and_the_panel_s_other_choices(app_window, monkeypatch):
    """The panel's Save is unchanged: it writes the box's mode with the rest
    of the panel, and after a switch the box names the mode the app is in
    (RNV-THEME-BOX), so Save and the button agree."""
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: 0)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: 0)
    app_window.open_package_d_panel()
    QApplication.processEvents()
    panel = app_window._package_d_panel
    save = [b for b in panel.findChildren(QPushButton) if b.text().strip() == "Save"]
    assert len(save) == 1
    mode = _switch(app_window)
    panel.tooltips_check.setChecked(not panel.tooltips_check.isChecked())
    save[0].click()
    QApplication.processEvents()
    disk = _on_disk(app_window)
    assert disk["preferences"]["theme"] == mode
    assert disk["preferences"]["show_tooltips"] == panel.tooltips_check.isChecked()
