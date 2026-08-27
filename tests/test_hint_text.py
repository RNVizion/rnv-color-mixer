"""
The fine-tune hint label, measured against the ground it actually sits on.

`text_hint` has exactly one consumer: core/color_fine_tune.py, a 10px QLabel
under each slider. It is added into the QFrame built by
`_create_sliders_section`, so its ground is `panel_secondary` -- NOT
`panel_bg`, which paints the QDialog behind that frame. Measuring against the
dialog would have said light was fine when it was not.

Light was #888888 on #ffffff = 3.5407:1 for 10px text. It is now #666666,
which clears 4.5 on every light ground in this app.

Dark and image are a smaller miss and are carried below rather than quietly
fixed: moving them would break the value they share with the muted text in
three other apps, and that is a ruling rather than a repair.
"""
from __future__ import annotations

import pathlib

import pytest

from utils.config import ThemeManager

TEXT_FLOOR = 4.5

THEMES = {
    "DARK": ThemeManager.DARK_THEME,
    "LIGHT": ThemeManager.LIGHT_THEME,
    "IMAGE": ThemeManager.IMAGE_THEME,
}

# The ground the label really renders on, and the ground behind it. Both are
# checked, because a frame that stopped being painted would drop the label onto
# the dialog and the figures would change without any colour moving.
GROUNDS = ("panel_secondary", "panel_bg")

# (theme, ground key) -> why it may sit below the floor.
ACCEPTED = {
    ("DARK", "panel_secondary"):
        "#888888 on #2a2a2a = 4.0490 -- the same value the muted text uses in "
        "three other apps; lifting it here alone is a ruling, not a repair",
    ("IMAGE", "panel_secondary"):
        "same pair as DARK -- image mode reuses the dark surfaces",
}


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:                      # Qt #AARRGGBB
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def test_the_hint_key_still_has_exactly_one_consumer():
    """Guard the guard, and guard the docstring with it.

    Every figure here assumes the label is the one in color_fine_tune. A second
    consumer on a different ground would make this file measure the wrong pair
    while still passing.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    sites = []
    for path in root.rglob("*.py"):
        if any(p in path.parts for p in ("tests", ".git", "__pycache__")):
            continue
        if path.name.startswith("test_") or path.name == "config.py":
            continue
        # A delivery script sitting at the root mentions the key it moves.
        # Sweeping it makes the guard fail on the very run that installs it --
        # the same trap the repos' placement guards already exempt `up*.py` for.
        if path.parent == root and path.name.startswith("up"):
            continue
        if "text_hint" in path.read_text(encoding="utf-8", errors="replace"):
            sites.append(path.relative_to(root).as_posix())
    assert sites == ["core/color_fine_tune.py"], (
        f"text_hint is read in {sites}. The grounds in this file were derived "
        f"from color_fine_tune alone; re-derive them before trusting these "
        f"figures.")


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("ground", GROUNDS)
def test_the_hint_clears_aa_on_the_ground_it_sits_on(theme, ground):
    palette = THEMES[theme]
    if (theme, ground) in ACCEPTED:
        pytest.skip(ACCEPTED[(theme, ground)])
    ink, bg = palette["text_hint"], palette[ground]
    if not bg.startswith("#"):
        pytest.skip(f"{theme} {ground} is {bg}, not a flat colour")
    ratio = contrast(ink, bg)
    assert ratio >= TEXT_FLOOR, (
        f"{theme}: hint {ink} on {ground} {bg} = {ratio:.4f}:1, below "
        f"{TEXT_FLOOR} for 10px text")


def test_the_accepted_entries_are_still_real():
    """An exemption that no longer describes anything is a licence waiting for
    a future defect. Each one must still be below the floor."""
    stale = []
    for (theme, ground), _why in ACCEPTED.items():
        palette = THEMES[theme]
        ratio = contrast(palette["text_hint"], palette[ground])
        if ratio >= TEXT_FLOOR:
            stale.append(f"{theme}/{ground} now reads {ratio:.4f} -- delete it")
    assert not stale, "; ".join(stale)


def test_light_is_the_one_that_was_fixed():
    """The specific regression: 10px #888888 on white."""
    light = THEMES["LIGHT"]
    assert light["text_hint"] != "#888888", (
        "the light hint is back to #888888, which reads 3.5407:1 on this "
        "app's white frame")
    assert contrast(light["text_hint"], light["panel_secondary"]) >= TEXT_FLOOR
