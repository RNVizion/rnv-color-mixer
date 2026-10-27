"""
tests/test_harmony_description_reads.py
=======================================
Ruling 102 A, 2026-10-26. The control panel's harmony description reads, in
every mode.

The description is the panel's accent ink on a wash of the same ink:
translucent(accent_ink, HARMONY_DESCRIPTION_ALPHA), over the panel's ground.
Brand Infrastructure measured it in BRAND_COLORS.md rev 47 as at the floor in
light mode. A render settled it: 4.49:1 at the old byte, 0x19, just under the
register's 4.5 for text on an alpha. At 0x10 it reads 4.71 in light and 8.39
in dark. Image mode styles the panel as dark (the application passes
is_dark for dark and image alike), on an opaque ground.

The test renders the panel itself, as a user sees it, and reads the wash
from the pixels inside the label: the color most of them are. A ground the
panel no longer paints, or a wash it no longer draws, fails here rather than
passing on arithmetic.
"""
from __future__ import annotations

from collections import Counter

import pytest
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QTabWidget

FLOOR = 4.5


def _luminance(rgb: tuple[int, int, int]) -> float:
    chans = [c / 255 for c in rgb]
    chans = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in chans]
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def _contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _rendered_wash(panel) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """(the wash inside the description, the ground just outside it), as drawn."""
    label = panel.harmony_description
    for tabs in panel.findChildren(QTabWidget):
        for i in range(tabs.count()):
            if tabs.widget(i).isAncestorOf(label):
                tabs.setCurrentIndex(i)
    QApplication.processEvents()
    assert label.isVisible(), "the harmony description is not shown: nothing was rendered"
    image = panel.grab().toImage()
    origin = label.mapTo(panel, label.rect().topLeft())
    seen = Counter()
    for y in range(origin.y() + 2, origin.y() + label.height() - 2):
        for x in range(origin.x() + 6, origin.x() + label.width() - 6):
            c = image.pixelColor(x, y)
            seen[(c.red(), c.green(), c.blue())] += 1
    outside = image.pixelColor(origin.x() - 3, origin.y() + label.height() // 2)
    return seen.most_common(1)[0][0], (outside.red(), outside.green(), outside.blue())


@pytest.mark.parametrize("is_dark", [True, False], ids=["dark and image", "light"])
def test_the_description_reads_on_its_wash(qapp, is_dark):
    from core.package_d_panel import PackageDPanel, _theme_colors

    panel = PackageDPanel(parent=None)
    try:
        panel.set_theme(is_dark)
        panel.harmony_description.setText("  Colors opposite on the wheel")
        panel.resize(900, 900)
        panel.show()
        QApplication.processEvents()
        wash, ground = _rendered_wash(panel)
        theme = _theme_colors(is_dark)
        ink = QColor(theme["accent_ink"])
        ink = (ink.red(), ink.green(), ink.blue())
        assert wash != ground, f"no wash drawn: the description's ground is the panel's {ground}"
        ratio = _contrast(wash, ink)
        assert ratio >= FLOOR, f"the description reads {ratio:.3f}:1 on its wash {wash}"
    finally:
        panel.close()
