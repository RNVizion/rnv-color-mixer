"""RNV-THEME-BOX, 2026-09-27: the control panel's Default Theme box follows
the mode the app is in.

WHAT THE SWEEP FOUND. The control panel is non-modal and kept: closed, it
hides, and the same panel is shown again. Its Default Theme box was set when
the panel was built and never again. Measured with the app's own buttons:

  * opened in dark, switched to light with the panel open: the box still
    said Dark Mode;
  * closed, switched, reopened: still Dark Mode;
  * the panel's Save writes the box's mode to the settings file.

So a switch with the panel open, then Save, filed the old mode, and the next
launch opened in it. When this was written the theme button did not write
the mode itself, so the panel's Save was the one thing that did; since
RNV-THEME-SAVE (2026-09-30) the button files it too, and
test_theme_button_saves.py holds that.

Each test drives the app the way a person does: the theme button, the
panel's opener, the panel's Close and Save.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton

pytestmark = pytest.mark.integration

#: What the box says for each mode the app can be in.
SAYS = {"dark": "Dark Mode", "light": "Light Mode", "image": "Image Mode"}


def _mode(app_window) -> str:
    return app_window.ui_handler.theme_manager.current_theme


def _switch(app_window) -> str:
    """One press of the theme button."""
    app_window._on_theme_button_clicked()
    QApplication.processEvents()
    return _mode(app_window)


def _panel(app_window):
    """The panel, opened with the app's own opener."""
    app_window.open_package_d_panel()
    QApplication.processEvents()
    panel = app_window._package_d_panel
    assert panel is not None and panel.isVisible()
    return panel


def test_the_box_follows_a_switch_made_with_the_panel_open(app_window):
    panel = _panel(app_window)
    assert panel.theme_combo.currentText() == SAYS[_mode(app_window)]
    seen = []
    for _ in range(3):                                  # every mode, and back
        mode = _switch(app_window)
        seen.append(mode)
        assert panel.theme_combo.currentText() == SAYS[mode], (mode, panel.theme_combo.currentText())
    assert {"dark", "light"} <= set(seen), seen


def test_the_box_follows_a_switch_made_while_the_panel_was_closed(app_window):
    panel = _panel(app_window)
    for _ in range(3):
        panel.close()
        QApplication.processEvents()
        assert not panel.isVisible()
        mode = _switch(app_window)
        again = _panel(app_window)
        assert again is panel, "the app no longer keeps the panel -- this test's premise moved"
        assert panel.theme_combo.currentText() == SAYS[mode], (mode, panel.theme_combo.currentText())


def test_save_after_a_switch_files_the_mode_the_app_is_in(app_window, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: 0)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: 0)
    panel = _panel(app_window)
    save = [b for b in panel.findChildren(QPushButton) if b.text().strip() == "Save"]
    assert len(save) == 1
    for _ in range(3):
        mode = _switch(app_window)
        save[0].click()
        QApplication.processEvents()
        assert app_window.settings_manager.get("preferences.theme") == mode, mode


def test_a_choice_made_in_the_box_stays_until_the_mode_moves(app_window):
    """The box is set when the app's mode moves, and at no other time. A
    choice made in it and not saved stays -- across a close, as the panel's
    other unsaved choices do -- until the next switch."""
    panel = _panel(app_window)
    other = "Auto (follow system)"          # never the mode the app is in
    panel.theme_combo.setCurrentText(other)
    QApplication.processEvents()
    assert panel.theme_combo.currentText() == other
    panel.close()
    QApplication.processEvents()
    _panel(app_window)
    assert panel.theme_combo.currentText() == other
    mode = _switch(app_window)
    assert panel.theme_combo.currentText() == SAYS[mode]
