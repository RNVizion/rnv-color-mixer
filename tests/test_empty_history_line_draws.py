"""The History tab's empty line is drawn in the muted text.

RNV-RULINGS-2026-10-05, item 2. Ruled 2026-10-05: "Yes".

WHAT WAS THERE. With no history, the tab shows one line: "No color history
yet. Mix some colors to get started!". The code gave it CSS gray, #808080,
and it was never drawn in it: the list's sheet coloured every item
(`QListWidget::item { color: ... }`), and a sheet wins over an item's own
colour. The line was drawn like an entry: #dddddd in dark and image, black
in light. Shown on 2026-10-04 with a magenta control.

WHAT IS THERE NOW. The History list's item rule sets no colour, so an item's
own colour is drawn; an item that has none takes the list's, which is the
colour the rule gave it. And the line holds `text_hint`, the muted text the
panel's ten descriptions take: 4.91:1 in dark and image, 5.27:1 in light.

THE OTHER THREE LISTS keep the sheet they had. Two more lines in this panel
set a colour of their own, both in the Presets list, whose sheet colours
every item as this one's did. They were found while this was built, and a
ruling is asked on them.

WHAT THIS GUARD HOLDS.

1. The empty line holds the mode's muted text.
2. It is DRAWN in it, and an entry is drawn in the list's own text colour
   as it always was. Read back from the list's own pixels, as a comparison:
   how far the empty line's text stands from the row's ground, against how
   far an entry's does. Text is drawn with soft edges, more or less so from
   one machine to the next, and the comparison does not care how soft. This
   is the test the old line would have failed.
3. It follows the mode: a switch made with the panel open, or while it was
   closed, leaves the line in the new mode's muted text.
4. The History list's item rule sets no colour, and the other three lists'
   rules still do.
5. An entry holds no colour of its own, as filled and after each mode's
   theme has been applied over it.
6. The muted text can be read on the list's ground: 4.5:1 or better.

Each test drives the app the way a person does: the theme button and the
panel's opener.
"""
from __future__ import annotations

import re

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication, QTabWidget

pytestmark = pytest.mark.integration

EMPTY = "No color history yet"
LISTS = ("history_list", "presets_list", "sessions_list", "harmony_preview_list")


def _far(a: QColor, b: QColor) -> int:
    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())


def _lum(colour: str) -> float:
    c = QColor(colour)

    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c.red()) + 0.7152 * lin(c.green()) + 0.0722 * lin(c.blue())


def _ratio(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _mode(app_window) -> str:
    return app_window.ui_handler.theme_manager.current_theme


def _switch(app_window) -> str:
    """One press of the theme button."""
    app_window._on_theme_button_clicked()
    QApplication.processEvents()
    return _mode(app_window)


def _palette(panel) -> dict:
    from core.package_d_panel import _theme_colors
    return _theme_colors(bool(panel._is_dark))


def _history_tab(app_window, entries=()):
    """The panel, opened with the app's own opener, on its History tab, with
    the history holding `entries`."""
    app_window.open_package_d_panel()
    QApplication.processEvents()
    panel = app_window._package_d_panel
    assert panel is not None and panel.isVisible()
    panel.color_history.clear()
    for colour in entries:
        panel.color_history.add_color(colour)
    panel.refresh_history()
    for tabs in panel.findChildren(QTabWidget):
        for index in range(tabs.count()):
            if tabs.widget(index).isAncestorOf(panel.history_list):
                tabs.setCurrentIndex(index)
    panel.history_list.clearSelection()
    panel.history_list.setCurrentRow(-1)
    panel.history_list.clearFocus()
    QApplication.processEvents()
    return panel


def _reach(list_widget, row: int = 0, skip_left: int = 0) -> tuple:
    """(the row's ground, how far its text stands from that ground): the
    distance of the pixel furthest from the ground. `skip_left` leaves out
    an entry's colour square."""
    image = list_widget.viewport().grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
    rect = list_widget.visualItemRect(list_widget.item(row))
    ground = image.pixelColor(rect.right() - 4, rect.top() + 4)
    far = max(_far(image.pixelColor(x, y), ground)
              for y in range(rect.top() + 3, rect.bottom() - 3)
              for x in range(rect.left() + 3 + skip_left, rect.right() - 3))
    assert far > 60, f"no text was found in row {row}"
    return ground, far


def _every_mode(app_window):
    """Each mode the theme button reaches, once: (mode, the panel on its History tab)."""
    seen = []
    for _ in range(3):
        mode = _mode(app_window)
        if mode not in seen:
            seen.append(mode)
            yield mode
        _switch(app_window)
    assert {"dark", "light", "image"} <= set(seen), seen


def test_the_empty_line_holds_the_modes_muted_text(app_window):
    for mode in _every_mode(app_window):
        panel = _history_tab(app_window)
        item = panel.history_list.item(0)
        assert panel.history_list.count() == 1 and item.text().startswith(EMPTY), (mode, item.text())
        muted = _palette(panel)["text_hint"]
        assert item.foreground().color().name() == QColor(muted).name(), \
            f"{mode}: the empty line holds {item.foreground().color().name()}, not text_hint ({muted})"
        panel.close()


def test_the_empty_line_is_drawn_in_the_muted_text_and_an_entry_in_the_lists(app_window):
    """Read back from the pixels. Setting a colour on an item is not drawing it."""
    for mode in _every_mode(app_window):
        panel = _history_tab(app_window)
        palette = _palette(panel)
        assert panel.history_list.item(0).text().startswith(EMPTY)
        ground, empty = _reach(panel.history_list)
        panel = _history_tab(app_window, entries=[(40, 90, 200)])
        assert not panel.history_list.item(0).text().startswith(EMPTY)
        entry_ground, entry = _reach(panel.history_list, skip_left=40)
        assert ground == entry_ground, f"{mode}: the two rows are not on one ground"
        want = _far(QColor(palette["text_hint"]), ground) / _far(QColor(palette["text_color"]), ground)
        assert 0.4 < want < 0.75, f"{mode}: the two inks are too alike for this test to tell them apart ({want:.2f})"
        got = empty / entry
        assert abs(got - want) < 0.12, (
            f"{mode}: the empty line's text stands {got:.2f} as far from the ground as an entry's. In the "
            f"muted text it stands {want:.2f} as far; at 1.00 it is drawn like an entry, which is what a "
            f"sheet that colours every item does")
        panel.color_history.clear()
        panel.close()


def test_it_follows_a_switch_made_with_the_panel_open(app_window):
    panel = _history_tab(app_window)
    for _ in range(3):
        mode = _switch(app_window)
        palette = _palette(panel)
        item = panel.history_list.item(0)
        assert item.foreground().color().name() == QColor(palette["text_hint"]).name(), \
            f"a switch to {mode} left the empty line in the old mode's colour"


def test_it_follows_a_switch_made_while_the_panel_was_closed(app_window):
    panel = _history_tab(app_window)
    for _ in range(3):
        panel.close()
        QApplication.processEvents()
        mode = _switch(app_window)
        app_window.open_package_d_panel()
        QApplication.processEvents()
        item = panel.history_list.item(0)
        assert item.text().startswith(EMPTY)
        assert item.foreground().color().name() == QColor(_palette(panel)["text_hint"]).name(), \
            f"a switch to {mode} with the panel closed left the empty line in the old mode's colour"


def test_the_history_lists_item_rule_sets_no_colour_and_the_others_still_do(app_window):
    for mode in _every_mode(app_window):
        panel = _history_tab(app_window)
        text = _palette(panel)["text_color"]
        for name in LISTS:
            sheet = getattr(panel, name).styleSheet()
            rules = re.findall(r"QListWidget::item \{([^}]*)\}", sheet)
            assert len(rules) == 1, f"{mode}: {name} has {len(rules)} plain item rules"
            properties = {line.split(":")[0].strip(): line.split(":", 1)[1].strip()
                          for line in rules[0].split(";") if ":" in line}
            if name == "history_list":
                assert "color" not in properties, (
                    f"{mode}: the History list's item rule sets a colour again. A sheet wins over an "
                    f"item's own colour, so the empty line would stop being drawn in the muted text.")
            else:
                assert properties.get("color") == text, \
                    f"{mode}: {name}'s item rule no longer colours its items {text}: {properties}"
            list_rule = re.search(r"QListWidget \{([^}]*)\}", sheet)
            assert list_rule and re.search(r"(?<![a-z-])color:\s*" + re.escape(text), list_rule.group(1)), \
                f"{mode}: {name} no longer gives its items the list's text colour"
        panel.close()


def test_an_entry_holds_no_colour_of_its_own(app_window):
    """Not when the list is filled, and not when a theme is applied over it:
    the pass that colours the empty line runs then too, and has to leave
    every entry alone."""
    panel = _history_tab(app_window, entries=[(40, 90, 200), (200, 90, 40)])
    assert panel.history_list.count() == 2

    def entries_hold_none(when: str) -> None:
        for row in range(2):
            item = panel.history_list.item(row)
            assert item.data(Qt.ItemDataRole.UserRole) is not None and not item.text().startswith(EMPTY)
            assert item.data(Qt.ItemDataRole.ForegroundRole) is None, \
                f"an entry was given a colour of its own {when}"
    entries_hold_none("when the list was filled")
    for _ in range(3):
        mode = _switch(app_window)
        entries_hold_none(f"when {mode}'s theme was applied")
    panel.color_history.clear()


@pytest.mark.parametrize("is_dark", [True, False])
def test_the_muted_text_can_be_read_on_the_lists_ground(is_dark):
    from core.package_d_panel import _theme_colors
    palette = _theme_colors(is_dark)
    ground = palette.get("scroll_bg", palette["panel_bg"])
    ratio = _ratio(palette["text_hint"], ground)
    assert ratio >= 4.5, f"text_hint on the list's ground is {ratio:.2f}:1, under 4.5"
