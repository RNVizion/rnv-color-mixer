"""THE COLOR SLOT'S CONTROLS AND THE ABOUT DIALOG'S SCROLLBAR (#79 A, #80 B, #81 A, 2026-10-22).

Three things Chris ruled from a render on 2026-10-22, each read back here from
the pixels the real widgets draw, not from the source that asks for them.

#79 A. THE WEIGHT SLIDER. The slot sets its own sheet, which overrides the main
window's slider rules, so its handle never lit up, and in light mode it was
black where every other slider handle is the palette's `slider_handle`. Its
handle now reads `slider_handle`, and on hover `accent`, as the window's
sliders do.

#80 B. THE ABOUT DIALOG'S LIGHT SCROLLBAR. Its handle was painted from a TEXT
key, `text_disabled`, on `hover_color`. It reads the palette's
`scrollbar_handle` on `scrollbar_bg`, as the window's light scrollbar does.
Dark is left as it was: there the scrollbar keys would draw the handle at
1.14:1 on the page, fainter than today's 1.47.

#81 A. THE REMOVE BUTTON'S PRESS. It pressed to its hover plate,
`main_btn_hover_bg`, so pressing changed only the label, and in dark the press
read black on that plate, 1.66:1, under the ruled 2.16. Every other
main-style button in the mixer presses to APP_BTN_PRESSED. The palettes gain
`main_btn_pressed_bg`, which the other four apps already name, and the Remove
button reads it.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QApplication, QScrollBar, QStyle, QStyleOptionSlider, QTabWidget
from PyQt6.QtTest import QTest

from utils import colors as C


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _hex(img, x, y) -> str:
    return img.pixelColor(x, y).name()


def _slot(qapp, dark: bool):
    from core.color_slot import ColorSlot
    slot = ColorSlot(0)
    slot.set_theme(dark)
    slot.resize(520, 90)
    slot.show()
    QTest.qWaitForWindowExposed(slot)
    return slot


def _move_off(widget) -> None:
    QTest.mouseMove(widget.window(), QPoint(1, 1))
    QTest.qWait(30)


def _handle_center(slider) -> QPoint:
    opt = QStyleOptionSlider()
    opt.initFrom(slider)
    opt.subControls = QStyle.SubControl.SC_All
    opt.orientation = slider.orientation()
    opt.minimum, opt.maximum = slider.minimum(), slider.maximum()
    opt.sliderPosition = opt.sliderValue = slider.value()
    opt.singleStep, opt.pageStep = slider.singleStep(), slider.pageStep()
    cc = (QStyle.ComplexControl.CC_ScrollBar if isinstance(slider, QScrollBar)
          else QStyle.ComplexControl.CC_Slider)
    sc = (QStyle.SubControl.SC_ScrollBarSlider if isinstance(slider, QScrollBar)
          else QStyle.SubControl.SC_SliderHandle)
    return slider.style().subControlRect(cc, opt, sc, slider).center()


def test_every_palette_names_the_press_plate() -> None:
    for name in ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME"):
        palette = getattr(C, name)
        assert palette.get("main_btn_pressed_bg") == C.APP_BTN_PRESSED, (
            f"{name}['main_btn_pressed_bg'] is {palette.get('main_btn_pressed_bg')}, not "
            f"APP_BTN_PRESSED {C.APP_BTN_PRESSED} (#81 A)")


@pytest.mark.parametrize("dark", [True, False], ids=["dark", "light"])
def test_the_remove_button_presses_to_the_press_plate(qapp, dark) -> None:
    slot = _slot(qapp, dark)
    btn = slot.clear_btn
    try:
        _move_off(btn)
        QTest.mouseMove(btn, QPoint(btn.width() // 2, btn.height() // 2))
        QTest.qWait(40)
        hover = _hex(btn.grab().toImage(), 4, btn.height() // 2)
        btn.setDown(True)
        QTest.qWait(30)
        pressed = _hex(btn.grab().toImage(), 4, btn.height() // 2)
    finally:
        btn.setDown(False)
        slot.close()
    palette = C.DARK_THEME if dark else C.LIGHT_THEME
    assert hover == palette["main_btn_hover_bg"].lower(), f"hover draws {hover}"
    assert pressed == C.APP_BTN_PRESSED.lower(), (
        f"the Remove button presses to {pressed}, not APP_BTN_PRESSED {C.APP_BTN_PRESSED} (#81 A)")
    assert pressed != hover, "pressing must change the plate, not only the label"


@pytest.mark.parametrize("dark", [True, False], ids=["dark", "light"])
def test_the_weight_slider_draws_as_the_window_sliders(qapp, dark) -> None:
    slot = _slot(qapp, dark)
    sl = slot.weight_slider
    try:
        sl.setValue(40)
        _move_off(sl)
        c = _handle_center(sl)
        rest = _hex(sl.grab().toImage(), c.x(), c.y())
        QTest.mouseMove(sl, c)
        QTest.qWait(40)
        hovered = _hex(sl.grab().toImage(), c.x(), c.y())
    finally:
        slot.close()
    palette = C.DARK_THEME if dark else C.LIGHT_THEME
    assert rest == palette["slider_handle"].lower(), (
        f"the weight handle draws {rest}, not the palette's slider_handle {palette['slider_handle']} (#79 A)")
    assert hovered == palette["accent"].lower(), (
        f"the weight handle hovered draws {hovered}, not the accent {palette['accent']} (#79 A)")


def _about_scrollbar(qapp, dark: bool):
    from ui.about_dialog import AboutDialog
    dlg = AboutDialog(None, is_dark=dark)
    dlg.set_theme(dark)
    dlg.show()
    QTest.qWaitForWindowExposed(dlg)
    for tabs in dlg.findChildren(QTabWidget):
        for i in range(tabs.count()):
            tabs.setCurrentIndex(i)
            QTest.qWait(30)
            bars = [b for b in dlg.findChildren(QScrollBar) if b.isVisible()
                    and b.orientation() == Qt.Orientation.Vertical and b.maximum() > 0]
            if bars:
                return dlg, bars[0]
    dlg.close()
    pytest.fail("no About page scrolls, so the scrollbar cannot be read; the check would pass by looking at nothing")


def test_the_about_light_scrollbar_reads_the_scrollbar_keys(qapp) -> None:
    dlg, sb = _about_scrollbar(qapp, dark=False)
    try:
        sb.setValue(0)
        QTest.qWait(30)
        img = sb.grab().toImage()
        c = _handle_center(sb)
        handle = _hex(img, c.x(), c.y())
        track = _hex(img, sb.width() // 2, sb.height() - 3)
    finally:
        dlg.close()
    assert handle == C.LIGHT_THEME["scrollbar_handle"].lower(), (
        f"the About light scrollbar handle draws {handle}, not scrollbar_handle "
        f"{C.LIGHT_THEME['scrollbar_handle']}; text_disabled is a text color (#80 B)")
    assert track == C.LIGHT_THEME["scrollbar_bg"].lower(), (
        f"the About light scrollbar track draws {track}, not scrollbar_bg {C.LIGHT_THEME['scrollbar_bg']} (#80 B)")


def test_the_about_dark_scrollbar_is_left_as_it_was(qapp) -> None:
    dlg, sb = _about_scrollbar(qapp, dark=True)
    try:
        sb.setValue(0)
        QTest.qWait(30)
        c = _handle_center(sb)
        handle = _hex(sb.grab().toImage(), c.x(), c.y())
    finally:
        dlg.close()
    assert handle == C.DARK_THEME["hover_color"].lower(), (
        f"the About dark scrollbar handle draws {handle}; #80 B left dark as it was, "
        f"{C.DARK_THEME['hover_color']}")
