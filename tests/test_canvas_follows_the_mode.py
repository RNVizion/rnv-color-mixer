"""The canvas draws its selection and its preview for the mode the app is in.

RNV-RULINGS-2026-10-05, item 3. Ruled 2026-10-05: "Yes, also i think the
comment meant see through gold."

WHAT WAS THERE. Three faults in one paint.

  The canvas asked a ThemeManager it made itself for the mode, and a new one
  always answers dark. So in light mode a dragged selection and the colour
  preview were drawn as in dark: dark's gold, a black plate, white figures.
  The slots had the same fault until 2026-09-26.

  The selection was filled with SOLID gold, under a comment that said
  semi-transparent. The area being selected could not be seen.

  The branches asked whether the theme was NAMED Dark. Had the canvas been
  handed the app's theme, image mode, whose palette is the dark one under
  its own name, would have taken light's black figures and grey plate.

WHAT IS THERE NOW. The canvas hands its label the theme the app is in, as
each slot is handed it. The fill is the mode's accent at
CANVAS_SELECTION_ALPHA, the byte of this application's other see-through
gold. Dark and image draw the dark look; only light draws the light one.
The light plate, which was written as numbers and never drawn, has a name.

WHAT THIS GUARD HOLDS.

1. The label holds the theme the app is in, after every switch.
2. Dark and image take the dark look. Light takes the light one.
3. A dragged selection is see-through gold: inside it the image shows
   through the mode's accent at CANVAS_SELECTION_ALPHA, and its edge is the
   accent, solid. Read back from the label's own pixels, and from the
   string the paint is handed.
4. The size label and the colour preview are drawn for the mode: light
   figures on a dark plate in dark and image, dark figures on a light plate
   in light.
5. Without a handler, the label takes the theme `is_dark` names.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import QApplication

from utils import config

pytestmark = pytest.mark.integration

GROUND = (90, 120, 150)                     # the image under the selection
SIZE = (420, 300)
SELECTION = QRect(60, 50, 240, 150)
INSIDE = (80, 70)                           # in the selection, clear of its edge, corners and size label
EDGE = (60, 125)                            # on its left edge, half way down
LABEL = QRect(165, 119, 30, 12)             # on the size label's plate, at the selection's centre
THEMES = {"dark": "DARK_THEME", "light": "LIGHT_THEME", "image": "IMAGE_THEME"}


def _mode(app_window) -> str:
    return app_window.ui_handler.theme_manager.current_theme


def _switch(app_window) -> str:
    """One press of the theme button."""
    app_window._on_theme_button_clicked()
    QApplication.processEvents()
    return _mode(app_window)


def _every_mode(app_window):
    seen = []
    for _ in range(3):
        mode = _mode(app_window)
        if mode not in seen:
            seen.append(mode)
            yield mode
        _switch(app_window)
    assert {"dark", "light", "image"} <= set(seen), seen


def _over(under: tuple, colour: str, alpha: int) -> tuple:
    """`colour` at `alpha` painted over `under`: what a painter leaves."""
    c = QColor(colour)
    return tuple(round(top * alpha / 255 + bottom * (255 - alpha) / 255)
                 for top, bottom in zip((c.red(), c.green(), c.blue()), under))


def _near(pixel: QColor, want: tuple, slack: int = 3) -> bool:
    return all(abs(got - w) <= slack for got, w in zip((pixel.red(), pixel.green(), pixel.blue()), want))


def _rgb(pixel: QColor) -> tuple:
    return pixel.red(), pixel.green(), pixel.blue()


def _lum(pixel: QColor) -> float:
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(pixel.red()) + 0.7152 * lin(pixel.green()) + 0.0722 * lin(pixel.blue())


def _label(app_window):
    label = app_window.canvas_view.image_label
    ground = QPixmap(*SIZE)
    ground.fill(QColor(*GROUND))
    label.setPixmap(ground)
    label.resize(*SIZE)
    label.crosshair_pos = None
    return label


def _dragging(app_window) -> QImage:
    label = _label(app_window)
    label.show_preview = False
    label.is_dragging, label.selection_rect = True, QRect(SELECTION)
    image = label.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
    label.is_dragging, label.selection_rect = False, None
    return image


def _previewing(app_window) -> QImage:
    label = _label(app_window)
    label.is_dragging, label.selection_rect = False, None
    label.show_preview, label.preview_color = True, (210, 188, 147)
    image = label.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
    label.show_preview = False
    return image


def _plate_and_figures(image: QImage, rect: QRect) -> tuple:
    """(the darkest, the middle, the lightest) luminance of a region that
    holds figures on a plate. The middle is the plate: most of the region."""
    lums = sorted(_lum(image.pixelColor(x, y)) for y in range(rect.top(), rect.bottom() + 1)
                  for x in range(rect.left(), rect.right() + 1))
    return lums[0], lums[len(lums) // 2], lums[-1]


def test_the_label_holds_the_theme_the_app_is_in(app_window):
    label = app_window.canvas_view.image_label
    for mode in _every_mode(app_window):
        want = getattr(config.ThemeManager, THEMES[mode])
        assert label._theme is want, f"{mode}: the canvas label holds {label._theme and label._theme['name']}"
        assert label._canvas_theme() is want


def test_dark_and_image_take_the_dark_look_and_light_the_light_one():
    from ui.canvas_view import ImageDisplayLabel
    assert ImageDisplayLabel._draws_dark(config.ThemeManager.DARK_THEME) is True
    assert ImageDisplayLabel._draws_dark(config.ThemeManager.IMAGE_THEME) is True, \
        "image mode would draw light's black figures and grey plate"
    assert ImageDisplayLabel._draws_dark(config.ThemeManager.LIGHT_THEME) is False
    assert ImageDisplayLabel._draws_dark(None) is False
    assert config.ThemeManager.IMAGE_THEME["accent"] == config.ThemeManager.DARK_THEME["accent"]


def test_the_fill_is_the_accent_at_the_named_alpha():
    """In the string the paint is handed: each palette's accent at
    CANVAS_SELECTION_ALPHA, and dark's when there is no theme to ask."""
    from ui.canvas_view import ImageDisplayLabel
    manager = config.ThemeManager
    assert config.CANVAS_SELECTION_ALPHA == 0x32 == config.SCREEN_GRID_ALPHA
    for palette in THEMES.values():
        theme = getattr(manager, palette)
        fill = ImageDisplayLabel._selection_fill(theme)
        assert fill == config.translucent(theme["accent"], config.CANVAS_SELECTION_ALPHA), (palette, fill)
        assert fill == "#32" + theme["accent"][1:].lower(), (palette, fill)
    assert ImageDisplayLabel._selection_fill(None) == ImageDisplayLabel._selection_fill(manager.DARK_THEME)
    assert ImageDisplayLabel._selection_fill(manager.LIGHT_THEME) != ImageDisplayLabel._selection_fill(manager.DARK_THEME), \
        "light and dark share an accent: the test of the mode above would pass with either"


def test_a_dragged_selection_is_see_through_gold(app_window):
    """Read back from the pixels: the image shows through the mode's accent."""
    for mode in _every_mode(app_window):
        accent = getattr(config.ThemeManager, THEMES[mode])["accent"]
        image = _dragging(app_window)
        assert _near(image.pixelColor(5, 5), GROUND, 0), f"{mode}: the image itself is not what the test laid down"
        inside = image.pixelColor(*INSIDE)
        want = _over(GROUND, accent, config.CANVAS_SELECTION_ALPHA)
        assert _near(inside, want), (
            f"{mode}: inside the selection the canvas draws {_rgb(inside)}, not the image under "
            f"{accent} at alpha {config.CANVAS_SELECTION_ALPHA}, which is {want}")
        solid = QColor(accent)
        assert not _near(inside, _rgb(solid), 12), f"{mode}: the selection is filled solid: the image cannot be seen"
        assert not _near(inside, GROUND, 6), f"{mode}: the selection has no fill at all"
        edge = image.pixelColor(*EDGE)
        assert _near(edge, _rgb(solid)), f"{mode}: the selection's edge is {_rgb(edge)}, not the accent {accent}"


def test_the_size_label_is_drawn_for_the_mode(app_window):
    """Light figures on a dark plate, or dark figures on a light one. The
    plate is a fill and is read exactly; the figures are text, with soft
    edges, and are only asked to stand clear of it on the right side."""
    for mode in _every_mode(app_window):
        accent = getattr(config.ThemeManager, THEMES[mode])["accent"]
        under = _over(GROUND, accent, config.CANVAS_SELECTION_ALPHA)
        darkest, plate, lightest = _plate_and_figures(_dragging(app_window), LABEL)
        if mode == "light":
            want = _over(under, config.CANVAS_LABEL_PLATE_LIGHT, config.CANVAS_LABEL_ALPHA)
            assert abs(plate - _lum(QColor(*want))) < 0.03, f"light: the size is not on the light plate {want}"
            assert plate - darkest > 0.2, "light: the size is not in dark figures"
        else:
            want = _over(under, config.TRUE_BLACK, config.CANVAS_LABEL_ALPHA)
            assert abs(plate - _lum(QColor(*want))) < 0.03, f"{mode}: the size is not on the dark plate {want}"
            assert lightest - plate > 0.3, f"{mode}: the size is not in light figures"


def test_the_preview_is_drawn_for_the_mode(app_window):
    half = 60                                # the preview is 120 square, at the label's centre
    corner = (SIZE[0] // 2 - half + 3, SIZE[1] // 2 - half + 3)      # on its plate, outside the colour square
    for mode in _every_mode(app_window):
        plate = _previewing(app_window).pixelColor(*corner)
        ink = config.WHITE if mode == "light" else config.TRUE_BLACK
        want = _over(GROUND, ink, config.CANVAS_PREVIEW_ALPHA)
        assert _near(plate, want), (
            f"{mode}: the preview's plate is {_rgb(plate)}, not {ink} at alpha "
            f"{config.CANVAS_PREVIEW_ALPHA} over the image, which is {want}")


def test_without_a_handler_the_label_takes_the_theme_is_dark_names(app_window):
    canvas = app_window.canvas_view
    canvas.set_theme(False)
    assert canvas.image_label._theme is config.ThemeManager.LIGHT_THEME
    canvas.set_theme(True)
    assert canvas.image_label._theme is config.ThemeManager.DARK_THEME
    canvas.set_theme(app_window.ui_handler.is_dark_mode(), app_window.ui_handler)      # as the app left it
