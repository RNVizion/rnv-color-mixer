"""White on the dark gold, black on the bright gold.

RNV-RULINGS-2026-10-13, item 32. Ruled 2026-10-13: "A". It holds item 4,
ruled 2026-10-11: "Keep this is a core look identity for my brand."

WHAT IS RULED. Text on the gold fill is white on the dark gold, #8c7337,
and black on the bright gold, #d2bc93. On the dark gold white reads 4.54:1
and black 4.62:1: both clear the 4.5 floor, and the arithmetic of which is
better would pick black. The ink is a decision, not a measurement, and it
is the brand's look in all five apps. The picker has held it since
2026-09-02, in its tests/test_ink_rule.py. Until this guard nothing held it
here, though the application painted it in every rule measured on
2026-10-05.

WHAT THIS GUARD HOLDS, in every mode the theme button reaches, through the
main window and every window its own openers show:

1. Every stylesheet rule that fills with a gold and sets an ink sets that
   gold's ink: `color` on a fill, `selection-color` on a selection.
2. A rule that fills with a gold and sets no ink fills a part that holds no
   text: a check box's indicator, a handle, a progress bar's chunk. A
   selection that sets no ink takes the palette's, which 3 holds.
3. The application's palette and each window's, where a selection takes
   its ink when no rule sets one: if it highlights in a gold, it gives the
   highlighted text that gold's ink.
4. The reader is looking: in each mode it reads every window, and finds at
   least as many rules putting an ink on a gold as it found on 2026-10-13;
   and it reads a sample sheet as Qt reads it.

The theme button is pressed round to the mode it started in, so a run
leaves the saved mode as it found it.
"""
from __future__ import annotations

import re

import pytest
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QWidget

@pytest.fixture
def window(app_window):
    """The main window, its home kept apart (tests/conftest.py)."""
    return app_window

#: The windows the main window's own openers show.
OPENERS = ('open_package_d_panel', 'open_about_dialog')

#: Rules that put an ink on a gold, found in each mode on 2026-10-13. Fewer
#: and the reader has gone blind.
MIN_INKED = {'dark': 6, 'light': 6, 'image': 6}

#: The modes the theme button must reach here. A mode it reaches beyond them
#: is read as well.
MODES = ('dark', 'light', 'image')

#: What was found against the ruling and is held as found while a ruling is
#: asked on it, -> why: ("rule", mode, selector, gold, ink) for a rule of a
#: sheet, ("palette", mode, gold, ink) for a palette. One that is no longer
#: found fails: take it out.
HELD = {}


def _mode(win) -> str:
    tm = getattr(win, "theme_manager", None) or win.ui_handler.theme_manager
    return "image" if tm.is_image_mode() else str(tm.current_theme)


def _prepare(win) -> None:
    """What the windows need before every opener shows one."""
    return None

#: The ruled ink for text on each gold fill: white on the dark gold, black on
#: the bright gold.
GOLD_INK = {"#8c7337": "#ffffff", "#d2bc93": "#000000"}
GOLD_NAME = {"#8c7337": "the dark gold", "#d2bc93": "the bright gold"}

HEX = re.compile(r"#[0-9a-fA-F]{6}(?![0-9a-fA-F])")
RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
DECL = re.compile(r"([a-zA-Z-]+)\s*:\s*([^;]+);?")
#: A part of a widget that holds no text. A gold fill there needs no ink.
TEXT_FREE = re.compile(r"::(?:indicator|handle|chunk|sub-page|add-page|up-button|down-button|groove|"
                       r"add-line|sub-line|up-arrow|down-arrow|branch)\b")
#: The palettes' two colour groups text is drawn in.
GROUPS = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive)


def _rules(sheet: str):
    """(selector, {property: value}) for each rule of a sheet, as Qt reads it.
    A sheet with no braces is a list of declarations set on one widget."""
    sheet = re.sub(r"/\*.*?\*/", "", sheet, flags=re.S)
    if "{" not in sheet:
        yield "(the widget itself)", {k.lower(): v.strip() for k, v in DECL.findall(sheet)}
        return
    for selector, body in RULE.findall(sheet):
        yield " ".join(selector.split()), {k.lower(): v.strip() for k, v in DECL.findall(body)}


def _gold(value: str):
    """The gold a value fills with, or None."""
    for found in HEX.findall(value or ""):
        if found.lower() in GOLD_INK:
            return found.lower()
    return None


def _ink(value):
    """A colour written in a rule, as #rrggbb: None when the rule sets none."""
    if not value:
        return None
    found = HEX.findall(value)
    if found:
        return found[0].lower()
    return QColor(value.strip()).name() if QColor.isValidColorName(value.strip()) else value.strip().lower()


def _fills(top: QWidget, where: str) -> list:
    """(where, holder, selector, kind, gold, ink) for each rule of every sheet
    the window and the application hold that fills with a gold."""
    sheets = [("(application)", QApplication.instance().styleSheet())]
    sheets += [(type(w).__name__, w.styleSheet()) for w in [top] + top.findChildren(QWidget) if w.styleSheet()]
    out = []
    for holder, sheet in sheets:
        for selector, decl in _rules(sheet):
            gold = _gold(decl.get("background-color", "")) or _gold(decl.get("background", ""))
            if gold:
                out.append((where, holder, selector, "fill", gold, _ink(decl.get("color"))))
            gold = _gold(decl.get("selection-background-color", ""))
            if gold:
                out.append((where, holder, selector, "selection", gold, _ink(decl.get("selection-color"))))
    return out


def _palettes(top: QWidget, where: str) -> list:
    """(where, holder, highlight, highlighted text) for the application's
    palette and the window's, in each group text is drawn in: the ink a
    selection takes where no rule of a sheet sets one. A palette a widget is
    given for itself is not read: what it would draw, a sheet's rule draws
    over (a combo box's list in image mode, read back from its pixels on
    2026-10-13), and 1 holds the rules."""
    held = [("(application)", QApplication.instance().palette()), (type(top).__name__, top.palette())]
    out = set()
    for holder, palette in held:
        for group in GROUPS:
            out.add((where, holder, palette.color(group, QPalette.ColorRole.Highlight).name(),
                     palette.color(group, QPalette.ColorRole.HighlightedText).name()))
    return sorted(out)


def _settle(ms: int = 150) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    QApplication.processEvents()


def _shown(self, *_a, **_k):
    """A modal dialog's exec(), shown and returned from at once."""
    _KEEP.append(self)
    self.show()
    QApplication.processEvents()
    return 0


_KEEP: list = []
_TOUR: dict = {}


def _tour(win, monkeypatch) -> dict:
    """mode -> (fills, palettes), the main window and every window its
    openers show, in each mode the theme button reaches. Taken once; the
    theme button is pressed round to where it started."""
    if _TOUR:
        return _TOUR
    monkeypatch.setattr(QDialog, "exec", _shown)
    monkeypatch.setattr(QMessageBox, "exec", _shown)
    for name in ("warning", "information", "critical", "question"):
        monkeypatch.setattr(QMessageBox, name, staticmethod(lambda *a, **k: QMessageBox.StandardButton.No))
    for name in ("getOpenFileName", "getOpenFileNames", "getSaveFileName"):
        monkeypatch.setattr(QFileDialog, name, staticmethod(lambda *a, **k: ("", "")))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: ""))
    _prepare(win)
    tour, start = {}, _mode(win)
    for _ in range(4):
        mode = _mode(win)
        if mode in tour:
            break
        fills, palettes = _fills(win, "main window"), _palettes(win, "main window")
        for opener in OPENERS:
            before = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}
            getattr(win, opener)()
            _settle()
            for shown in [w for w in QApplication.topLevelWidgets()
                          if w.isVisible() and id(w) not in before and w is not win]:
                fills += _fills(shown, opener)
                palettes += _palettes(shown, opener)
                shown.close()
            _settle(50)
        tour[mode] = (fills, palettes)
        win.theme_button.click()
        _settle()
    assert _mode(win) == start, f"the theme button did not come back round to {start}"
    _TOUR.update(tour)
    return _TOUR


def test_every_ink_on_a_gold_is_the_ruled_one(window, monkeypatch):
    seen, wrong = set(), []
    for mode, (fills, _p) in _tour(window, monkeypatch).items():
        for where, holder, selector, _kind, gold, ink in fills:
            if ink and ink != GOLD_INK[gold]:
                if ("rule", mode, selector, gold, ink) in HELD:
                    seen.add(("rule", mode, selector, gold, ink))
                    continue
                wrong.append(f"{mode}, {where} ({holder}): {selector} puts {ink} on {GOLD_NAME[gold]}, "
                             f"not {GOLD_INK[gold]}")
    assert not wrong, ("text on the gold fill is ruled: white on the dark gold, black on the bright "
                       "gold (2026-10-11, item 4):\n  " + "\n  ".join(sorted(set(wrong))))
    stale = sorted(k for k in set(HELD) - seen if k[0] == "rule")
    assert not stale, f"held as found and no longer found: {stale}. Take it out of HELD."


def test_a_gold_fill_without_an_ink_holds_no_text(window, monkeypatch):
    """A selection that sets no ink takes the palette's, which the next test holds."""
    bare = [f"{mode}, {where} ({holder}): {selector}"
            for mode, (fills, _p) in _tour(window, monkeypatch).items()
            for where, holder, selector, kind, _gold, ink in fills
            if ink is None and kind == "fill" and not TEXT_FREE.search(selector)]
    assert not bare, ("a rule fills with a gold under text and leaves the ink to whatever the "
                      "widget inherits:\n  " + "\n  ".join(sorted(set(bare))))


def test_every_window_palette_that_highlights_in_a_gold_gives_its_ink(window, monkeypatch):
    seen, wrong = set(), []
    for mode, (_f, palettes) in _tour(window, monkeypatch).items():
        for where, holder, highlight, text in palettes:
            if highlight in GOLD_INK and text != GOLD_INK[highlight]:
                if ("palette", mode, highlight, text) in HELD:
                    seen.add(("palette", mode, highlight, text))
                    continue
                wrong.append(f"{mode}, {where} ({holder}): highlighted text {text} on {GOLD_NAME[highlight]}")
    assert not wrong, ("a palette highlights in a gold and gives the highlighted text another ink "
                       "than the ruled one:\n  " + "\n  ".join(sorted(set(wrong))))
    stale = sorted(k for k in set(HELD) - seen if k[0] == "palette")
    assert not stale, f"held as found and no longer found: {stale}. Take it out of HELD."


def test_the_reader_is_looking(window, monkeypatch):
    """A reader that finds nothing passes every test above."""
    tour = _tour(window, monkeypatch)
    assert set(MODES) <= set(tour), f"the theme button reached {sorted(tour)}, not {sorted(MODES)}"
    for mode, (fills, palettes) in tour.items():
        inked = {(selector, kind, gold) for _w, _h, selector, kind, gold, ink in fills if ink}
        assert len(inked) >= MIN_INKED.get(mode, 1), (
            f"{mode}: the reader finds {len(inked)} rules that put an ink on a gold, not {MIN_INKED.get(mode, 1)}")
        reached = {where for where, *_rest in fills} | {where for where, *_rest in palettes}
        assert set(OPENERS) <= reached, f"{mode}: no window was read from {sorted(set(OPENERS) - reached)}"
    sample = ("/* a comment { } */ QPushButton:pressed { background-color: #8C7337; color: white; }\n"
              "QLineEdit, QSpinBox { selection-background-color: #d2bc93; selection-color: #000; }\n"
              "QSlider::handle:horizontal { background: #8c7337; }\n"
              "QComboBox QAbstractItemView { selection-background-color: #d2bc93; }\n"
              "QLabel { background-color: #8c73370a; color: #ffffff; }\n")
    probe = QWidget()
    probe.setStyleSheet(sample)
    try:
        found = [f[2:] for f in _fills(probe, "sample") if f[1] == "QWidget"]
    finally:
        probe.deleteLater()
    assert found == [("QPushButton:pressed", "fill", "#8c7337", "#ffffff"),
                     ("QLineEdit, QSpinBox", "selection", "#d2bc93", "#000000"),
                     ("QSlider::handle:horizontal", "fill", "#8c7337", None),
                     ("QComboBox QAbstractItemView", "selection", "#d2bc93", None)], found
    assert TEXT_FREE.search("QSlider::handle:horizontal") and not TEXT_FREE.search("QPushButton:pressed")
