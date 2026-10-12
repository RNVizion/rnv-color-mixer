"""The Presets list's two empty lines are drawn in the muted text.

RNV-RULINGS-2026-10-11, item 20. Ruled 2026-10-11: "B".

WHAT WAS THERE. Two lines stand in the Presets list when it has nothing to
show. "No user presets yet", with User Presets chosen and none saved, was
given the gold text; the line a category shows when it holds no preset was
given dark's disabled grey, in every mode. Neither was drawn in it: the
list's sheet coloured every item (`QListWidget::item { color: ... }`), and a
sheet wins over an item's own colour. Both were drawn like a preset: #dddddd
in dark and image, black in light. Rendered on 2026-10-05.

WHAT IS THERE NOW. The list's item rule sets no colour, as the History
list's has not since 2026-10-05, and both lines hold text_hint, the muted
text the History tab's empty line takes: #888888 in dark and image, #666666
in light.

WHAT THIS GUARD HOLDS.

1. Each empty line holds the mode's muted text.
2. It is DRAWN in it. Read back from the list's own pixels, as a
   comparison: the line as it is drawn, against the same line given the
   list's text colour for a moment. How far its text stands from the row's
   ground in the one, against the other, is how far the two inks stand from
   it. A sheet that coloured every item would draw the two alike.
3. It follows the mode: a switch made with the panel open, or while it was
   closed, leaves each line in the new mode's muted text.
4. A preset holds no colour of its own, as the list is filled and after
   each mode's theme has been applied over it.

That the list's item rule sets no colour is held with the History list's,
in tests/test_empty_history_line_draws.py. Each test drives the app the way
a person does: the theme button, the panel's opener and the category box.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication, QTabWidget

pytestmark = pytest.mark.integration

NO_USER_PRESETS = " No user presets yet"
EMPTY_CATEGORY = "A category with nothing in it"
USER_PRESETS = " User Presets"


def _far(a: QColor, b: QColor) -> int:
    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())


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


def _presets_tab(app_window, category: str):
    """The panel, opened with the app's own opener, on its Presets tab, with
    `category` chosen in the category box."""
    app_window.open_package_d_panel()
    QApplication.processEvents()
    panel = app_window._package_d_panel
    assert panel is not None and panel.isVisible()
    for tabs in panel.findChildren(QTabWidget):
        for index in range(tabs.count()):
            if tabs.widget(index).isAncestorOf(panel.presets_list):
                tabs.setCurrentIndex(index)
    combo = panel.category_combo
    if combo.findText(category) < 0:
        combo.addItem(category)
    combo.setCurrentIndex(combo.findText(category))
    panel.refresh_presets()
    panel.presets_list.clearSelection()
    panel.presets_list.setCurrentRow(-1)
    panel.presets_list.clearFocus()
    QApplication.processEvents()
    return panel


def _empty_line(panel, starts: str):
    lst = panel.presets_list
    assert lst.count() == 1 and lst.item(0).text().startswith(starts), \
        f"the list does not hold the one empty line {starts!r}: {[lst.item(r).text()[:30] for r in range(lst.count())]}"
    return lst.item(0)


def _reach(list_widget, row: int = 0) -> tuple:
    """(the row's ground, how far its text stands from that ground): the
    distance of the pixel furthest from the ground."""
    image = list_widget.viewport().grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
    rect = list_widget.visualItemRect(list_widget.item(row))
    ground = image.pixelColor(rect.right() - 4, rect.top() + 4)
    far = max(_far(image.pixelColor(x, y), ground)
              for y in range(rect.top() + 3, rect.bottom() - 3)
              for x in range(rect.left() + 3, rect.right() - 3))
    assert far > 60, f"no text was found in row {row}"
    return ground, far


def _every_mode(app_window):
    seen = []
    for _ in range(3):
        mode = _mode(app_window)
        if mode not in seen:
            seen.append(mode)
            yield mode
        _switch(app_window)
    assert {"dark", "light", "image"} <= set(seen), seen


LINES = ((USER_PRESETS, NO_USER_PRESETS), (EMPTY_CATEGORY, f" No presets in '{EMPTY_CATEGORY}' category"))


@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))
def test_each_empty_line_holds_the_modes_muted_text(app_window, category, starts):
    for mode in _every_mode(app_window):
        panel = _presets_tab(app_window, category)
        item = _empty_line(panel, starts)
        muted = _palette(panel)["text_hint"]
        assert item.foreground().color().name() == QColor(muted).name(), \
            f"{mode}: {starts.strip()!r} holds {item.foreground().color().name()}, not text_hint ({muted})"
        panel.close()


@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))
def test_each_empty_line_is_drawn_in_the_muted_text(app_window, category, starts):
    """Read back from the pixels. Setting a colour on an item is not drawing it."""
    for mode in _every_mode(app_window):
        panel = _presets_tab(app_window, category)
        palette = _palette(panel)
        item = _empty_line(panel, starts)
        ground, drawn = _reach(panel.presets_list)
        held = item.foreground()
        item.setForeground(QColor(palette["text_color"]))
        QApplication.processEvents()
        control_ground, control = _reach(panel.presets_list)
        item.setForeground(held)
        QApplication.processEvents()
        assert ground == control_ground, f"{mode}: the line's ground moved between the two grabs"
        want = _far(QColor(palette["text_hint"]), ground) / _far(QColor(palette["text_color"]), ground)
        assert 0.4 < want < 0.75, f"{mode}: the two inks are too alike for this test to tell them apart ({want:.2f})"
        got = drawn / control
        assert abs(got - want) < 0.12, (
            f"{mode}: {starts.strip()!r} stands {got:.2f} as far from the ground as it does in the list's text "
            f"colour. In the muted text it stands {want:.2f} as far; at 1.00 the two are drawn alike, which is "
            f"what a sheet that colours every item does")
        panel.close()


@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))
def test_each_follows_a_switch_made_with_the_panel_open(app_window, category, starts):
    panel = _presets_tab(app_window, category)
    for _ in range(3):
        mode = _switch(app_window)
        item = _empty_line(panel, starts)
        assert item.foreground().color().name() == QColor(_palette(panel)["text_hint"]).name(), \
            f"a switch to {mode} left {starts.strip()!r} in the old mode's colour"


@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))
def test_each_follows_a_switch_made_while_the_panel_was_closed(app_window, category, starts):
    panel = _presets_tab(app_window, category)
    for _ in range(3):
        panel.close()
        QApplication.processEvents()
        mode = _switch(app_window)
        app_window.open_package_d_panel()
        QApplication.processEvents()
        item = _empty_line(panel, starts)
        assert item.foreground().color().name() == QColor(_palette(panel)["text_hint"]).name(), \
            f"a switch to {mode} with the panel closed left {starts.strip()!r} in the old mode's colour"


def test_a_preset_holds_no_colour_of_its_own(app_window):
    """Not when the list is filled, and not when a theme is applied over it:
    the pass that colours the empty lines runs then too, and has to leave
    every preset alone."""
    panel = _presets_tab(app_window, "All")
    lst = panel.presets_list
    assert lst.count() > 3, f"the list holds {lst.count()} presets"

    def presets_hold_none(when: str) -> None:
        for row in range(lst.count()):
            item = lst.item(row)
            assert item.data(Qt.ItemDataRole.UserRole) is not None
            assert item.data(Qt.ItemDataRole.ForegroundRole) is None, \
                f"{item.text().splitlines()[0].strip()!r} was given a colour of its own {when}"
    presets_hold_none("when the list was filled")
    for _ in range(3):
        mode = _switch(app_window)
        presets_hold_none(f"when {mode}'s theme was applied")
