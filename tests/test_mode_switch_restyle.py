"""RNV-CHART-RULINGS, ruling 3 of 2026-09-26: every widget follows a mode switch.

WHAT THE CHART FOUND. Reading back every stylesheet and palette the app sets,
mode by mode, found widgets in light mode carrying dark mode's colours:

  * the preview's border               stale: only _update_preview() writes it,
                                       and a mode switch did not call it, so the
                                       border waited for the next colour mixed;
  * the colour slots' swatch borders,  always dark: _update_swatch_display()
    and their gold hover and press     asked a FRESH ThemeManager, whose mode is
                                       always dark, however often set_theme() ran;
  * the control panel's nine shortcut  always dark: styled while the panel was
    key badges                         built, before set_theme() had run, and
                                       set_theme() never reached them;
  * the About dialog's gold text, the  always dark: written once, when the
    version line and the credits       dialog was built -- and the app passes
    footer                             its ui_handler where the dark flag
                                       belongs, which is truthy.

Each test below drives the app the way a person does -- the theme button for
the main window and the panel, the About opener for the About dialog, which
the app restyles each time it opens it -- and asks every widget, in every mode
the cycle offers, for the mode's own values. Dark and image draw the panel and
the About dialog from the dark palette, as the app has always done.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QLabel

from utils.config import ThemeManager

pytestmark = pytest.mark.integration

#: The Quick Actions tab's shortcut badges, by the text each one shows.
SHORTCUT_KEYS = ("Ctrl+O", "Ctrl+S", "Ctrl+C", "Ctrl+N", "Ctrl+P or Ctrl+,",
                 "Ctrl+/", "Ctrl+Shift+C", "F11", "F12")


def _cycle(app_window):
    """Click the theme button until the cycle comes back round to where it
    started, yielding the mode after each click. Dark, light and image when
    the image assets are present; dark and light when they are not."""
    start = app_window.ui_handler.theme_manager.current_theme
    for _ in range(4):
        app_window._on_theme_button_clicked()
        QApplication.processEvents()
        mode = app_window.ui_handler.theme_manager.current_theme
        yield mode
        if mode == start:
            return
    raise AssertionError("the theme cycle never came back round to its start")


def _dialog_palette(mode: str) -> dict:
    """The panel and the About dialog draw dark and image from DARK_THEME."""
    return ThemeManager.LIGHT_THEME if mode == "light" else ThemeManager.DARK_THEME


def test_the_cycle_reaches_light_mode(app_window):
    """Every test here would pass vacuously if the cycle never left dark."""
    assert "light" in list(_cycle(app_window))


def test_the_preview_border_follows_every_mode(app_window):
    for mode in _cycle(app_window):
        theme = app_window.ui_handler.get_current_theme_dict()
        sheet = app_window.preview_label.styleSheet()
        assert f"solid {theme['border_color']};" in sheet, (
            f"{mode}: the preview's border is not {theme['border_color']}:\n{sheet}")


def _assert_swatch(slot, theme: dict, where: str) -> None:
    sheet = slot.swatch_btn.styleSheet()
    plate, _, rest = sheet.partition("QPushButton:hover")
    hover, _, pressed = rest.partition("QPushButton:pressed")
    edge = f"{theme['slot_border_width']}px solid"
    assert f"{edge} {theme['slot_border']};" in plate, f"{where}: border\n{sheet}"
    assert f"{edge} {theme['accent']};" in hover, f"{where}: hover\n{sheet}"
    assert f"{edge} {theme['accent']};" in pressed, f"{where}: pressed\n{sheet}"


def test_the_slot_swatches_follow_every_mode(app_window):
    assert app_window.slots, "the app starts with no slots, so this sees nothing"
    for mode in _cycle(app_window):
        theme = app_window.ui_handler.get_current_theme_dict()
        for i, slot in enumerate(app_window.slots):
            _assert_swatch(slot, theme, f"{mode}, slot {i}")


def test_a_swatch_keeps_its_mode_through_a_colour_change_and_a_new_slot(app_window):
    """A colour change repaints the swatch without being told the mode, and
    a slot added in light mode is built there: both must stay in the mode."""
    for mode in _cycle(app_window):
        if mode == "light":
            break
    theme = app_window.ui_handler.get_current_theme_dict()
    app_window.slots[0].set_color((12, 120, 200))
    _assert_swatch(app_window.slots[0], theme, "light, after a colour change")
    app_window.add_color_slot()
    _assert_swatch(app_window.slots[-1], theme, "light, a slot added there")


def test_the_panel_key_badges_follow_every_mode(app_window):
    app_window.open_package_d_panel()
    panel = app_window._package_d_panel
    badges = [w for w in panel.findChildren(QLabel) if w.text() in SHORTCUT_KEYS]
    assert len(badges) == len(SHORTCUT_KEYS), [w.text() for w in badges]
    try:
        for mode in _cycle(app_window):
            t = _dialog_palette(mode)
            for badge in badges:
                sheet = badge.styleSheet()
                assert f"background-color: {t['accent']};" in sheet, (
                    f"{mode}: {badge.text()!r} plate\n{sheet}")
                assert f"color: {t['accent_text']};" in sheet, (
                    f"{mode}: {badge.text()!r} text\n{sheet}")
    finally:
        panel.close()


def test_the_about_dialog_gold_follows_every_mode(app_window):
    app_window.open_about_dialog()
    about = app_window._about_dialog
    labels = about.findChildren(QLabel)
    version = [w for w in labels if w.text().startswith("Version ")]
    credits = [w for w in labels if "Credits &amp; Acknowledgments" in w.text()
               or "Credits & Acknowledgments" in w.text()]
    assert len(version) == 1 and len(credits) == 1, (len(version), len(credits))
    about.close()
    try:
        for mode in _cycle(app_window):
            app_window.open_about_dialog()
            assert app_window._about_dialog is about, "the About dialog was rebuilt"
            ink = _dialog_palette(mode)["accent_ink"]
            assert f"color: {ink};" in version[0].styleSheet(), (
                f"{mode}: the version line\n{version[0].styleSheet()}")
            assert f"color: {ink};" in credits[0].text(), f"{mode}: the credits footer"
            about.close()
    finally:
        about.close()
