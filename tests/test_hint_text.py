"""
The muted text, measured against the grounds it actually sits on.

`text_hint` has two consumers. The fine-tune hint in core/color_fine_tune.py
is a 10px QLabel under each slider, added into the QFrame built by
`_create_sliders_section`, so its ground is `panel_secondary` -- NOT
`panel_bg`, which paints the QDialog behind that frame. Measuring against the
dialog would have said light was fine when it was not. The control panel's
ten descriptions in core/package_d_panel.py sit on its tab pages, measured
in the running app at TRUE_BLACK in dark, APP_SURFACE_DARK in image and
APP_WINDOW_LIGHT in light. `panel_bg` is APP_SURFACE_DARK in dark -- the
lighter, so the harder, ground for a light ink -- and APP_WINDOW_LIGHT in
light, so holding the hint on `panel_bg` below covers them.

RNV-MUTED-DESCRIPTIONS, 2026-09-27 (ruling 1): the descriptions were
`color: gray`, DATA_CSS_GRAY in every mode, until they joined this key -- the
muted text all five applications paint, APP_HINT_DARK in dark and image and
APP_HINT_LIGHT in light.

Light was RETIRED_LIGHT_HINT on WHITE = 3.5407:1 for 10px text. It is now
APP_HINT_LIGHT, which clears 4.5 on every light ground in this app.

Dark and image are a smaller miss and are carried below rather than quietly
fixed: moving them would break the value they share with the muted text in
three other apps, and that is a ruling rather than a repair.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from color_values import RETIRED_LIGHT_HINT
from utils import colors
from utils.config import ThemeManager

#: RNV-COLOR-SYNC, #52 A (2026-10-17). Where each color comes from, as
#: brand_map.json says. The values are held by tests/test_colors_in_sync.py,
#: against the map; what this file holds is the name each one takes.
BRAND_MAP = json.loads((pathlib.Path(__file__).resolve().parents[1] / "brand_map.json")
                       .read_text(encoding="utf-8"))["colors"]

TEXT_FLOOR = 4.5

THEMES = {
    "DARK": ThemeManager.DARK_THEME,
    "LIGHT": ThemeManager.LIGHT_THEME,
    "IMAGE": ThemeManager.IMAGE_THEME,
}

# The ground the label really renders on, and the ground behind it. Both are
# checked, because a frame that stopped being painted would drop the label onto
# the dialog and the figures would change without any color moving.
GROUNDS = ("panel_secondary", "panel_bg")

# (theme, ground key) -> why it may sit below the floor.
ACCEPTED = {
    ("DARK", "panel_secondary"):
        f"{colors.APP_HINT_DARK} on {colors.APP_CARD_DARK} = 4.0490 -- the same value "
        "the muted text uses in "
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


def test_the_hint_key_has_exactly_its_two_consumers():
    """Guard the guard, and guard the docstring with it.

    Every figure here assumes the two consumers above and their two grounds.
    A third consumer on a different ground would make this file measure the
    wrong pair while still passing.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    sites = []
    for path in root.rglob("*.py"):
        if any(p in path.parts for p in ("tests", ".git", "__pycache__")):
            continue
        # The palettes, which define the key, are in utils/colors.py (#63 A).
        if path.name.startswith("test_") or path.name == "colors.py":
            continue
        # A delivery script sitting at the root mentions the key it moves.
        # Sweeping it makes the guard fail on the very run that installs it --
        # the same trap the repos' placement guards already exempt `up*.py` for.
        if path.parent == root and path.name.startswith("up"):
            continue
        if "text_hint" in path.read_text(encoding="utf-8", errors="replace"):
            sites.append(path.relative_to(root).as_posix())
    assert sorted(sites) == ["core/color_fine_tune.py", "core/package_d_panel.py"], (
        f"text_hint is read in {sites}. The grounds in this file were derived "
        f"from color_fine_tune and the control panel; re-derive them before "
        f"trusting these figures.")


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("ground", GROUNDS)
def test_the_hint_clears_aa_on_the_ground_it_sits_on(theme, ground):
    palette = THEMES[theme]
    if (theme, ground) in ACCEPTED:
        pytest.skip(ACCEPTED[(theme, ground)])
    ink, bg = palette["text_hint"], palette[ground]
    if not bg.startswith("#"):
        pytest.skip(f"{theme} {ground} is {bg}, not a flat color")
    ratio = contrast(ink, bg)
    assert ratio >= TEXT_FLOOR, (
        f"{theme}: hint {ink} on {ground} {bg} = {ratio:.4f}:1, below "
        f"{TEXT_FLOOR} for 10px text")


def test_the_accepted_entries_are_still_real():
    """An exemption that no longer describes anything is a license waiting for
    a future defect. Each one must still be below the floor."""
    stale = []
    for (theme, ground), _why in ACCEPTED.items():
        palette = THEMES[theme]
        ratio = contrast(palette["text_hint"], palette[ground])
        if ratio >= TEXT_FLOOR:
            stale.append(f"{theme}/{ground} now reads {ratio:.4f} -- delete it")
    assert not stale, "; ".join(stale)


def test_light_is_the_one_that_was_fixed():
    """The specific regression: 10px RETIRED_LIGHT_HINT on white."""
    light = THEMES["LIGHT"]
    assert light["text_hint"] != RETIRED_LIGHT_HINT, (
        f"the light hint is back to {RETIRED_LIGHT_HINT}, which reads 3.5407:1 on this "
        "app's white frame")
    assert contrast(light["text_hint"], light["panel_secondary"]) >= TEXT_FLOOR


# RNV-MUTED-DESCRIPTIONS
# -------------------------------------------------- the descriptions (ruling 1)

def test_the_muted_values_are_the_ones_the_fleet_already_uses():
    """Ruling 1 was conditional: two values are fine if every app splits it by
    mode, and only with values already in use. Both halves, held here."""
    assert THEMES["DARK"]["text_hint"] == THEMES["IMAGE"]["text_hint"] == colors.APP_HINT_DARK
    assert THEMES["LIGHT"]["text_hint"] == colors.APP_HINT_LIGHT


def test_the_light_hint_has_its_own_name():
    """Not the slider handle's: APP_HANDLE_LIGHT holds the same hex for
    another job, and wired through it, text would move with the handle."""
    import ast
    import pathlib
    from utils import colors
    src = pathlib.Path(colors.__file__).read_text(encoding="utf-8-sig")
    light = next(n.value for n in ast.parse(src).body
                 if isinstance(n, (ast.Assign, ast.AnnAssign))
                 and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target,
                             "id", None) == "LIGHT_THEME")
    value = next(v for k, v in zip(light.keys, light.values)
                 if isinstance(k, ast.Constant) and k.value == "text_hint")
    assert isinstance(value, ast.Name) and value.id == "APP_HINT_LIGHT", ast.unparse(value)
    assert colors.APP_HINT_LIGHT == colors.APP_HANDLE_LIGHT
    # #52 A, 2026-10-17: the value both hold is the application's own, by the
    # map; tests/test_colors_in_sync.py holds it there.
    assert isinstance(BRAND_MAP["APP_HINT_LIGHT"], dict)
    assert isinstance(BRAND_MAP["APP_HANDLE_LIGHT"], dict)


def test_no_label_is_written_in_a_css_gray():
    """The literal the ruling retired, anywhere the application EVALUATES a
    string. Docstrings and comments may still name it; code may not."""
    import ast
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parent.parent
    css_gray = re.compile(r"color\s*:\s*(gray|grey)\b", re.I)
    found, files = [], 0
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(p in {"tests", ".git", "__pycache__", "build", "dist", ".venv", "snapshots"}
               for p in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        files += 1
        tree = ast.parse(text)
        docs = {id(st.value) for node in ast.walk(tree)
                for st in (node.body if isinstance(getattr(node, "body", None), list) else [])
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)}
        found += [f"{rel}:{node.lineno}" for node in ast.walk(tree)
                  if isinstance(node, ast.Constant) and isinstance(node.value, str)
                  and id(node) not in docs and css_gray.search(node.value)]
    assert files >= 20, f"only {files} files swept -- the walk has gone blind"
    assert not found, "CSS gray still written as a color:\n  " + "\n  ".join(found)
