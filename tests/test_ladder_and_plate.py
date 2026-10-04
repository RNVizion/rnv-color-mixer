"""Three neutrals reclassified from app-owned to mirrored.

WHAT THIS PASS DID. This app already NAMED these values -- the 2026-08-29 pass
did that. What it could not do was classify them, because the register had not
ruled. rnv-brand rev 22 registered APP["canvas"] #0a0a0a and
APP["panel-hover"] #3a3a3a; rev 23 registered APP["hover-light"] #eeeeee. So
the change is provenance, and the docstrings that argued the other way.

    BRAND_BLACK + n * 0x10,  n in -1..+2
    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover

WHY THE LADDER LOOKED INCOMPLETE. The register had called it "two-thirds
specified" because APP["border"] #333333 is not #3a3a3a, treating the border as
a missing rung. It is not a rung: #333333 is grey(3) on the INK grid, which
governs inks and EDGES. Two families compared to each other.

THE COINCIDENCE THAT WENT. Until RNV-NAMED-AND-USED, 2026-10-04, a second
name held #eeeeee here: the dark slider handle's hover, grey(14) on the ink
grid, kept apart from APP["hover-light"] by a table and three tests in this
file. No sheet painted that name -- a hovered handle takes the accent -- so
it went, and the plate's hex has one name again. With nothing left to keep
apart, the table and its tests went with it.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from utils import config
from utils.config import ThemeManager

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'utils' / 'config.py'

GRID_STEP = 0x11
LADDER_STEP = 0x10
TEXT_FLOOR = 4.5

#: Constant -> (register dict, key, the value both hold). This app names its
#: neutrals by role AND mode because it registers a light set beside the dark
#: one, so the APP_<KEY> convention the other apps resolve by does not apply --
#: the map is explicit, exactly as tests/test_app_mirror.py does it.
NEW = {
    'APP_CANVAS_DARK': ('canvas', '#0a0a0a'),
    'APP_PANEL_HOVER_DARK': ('panel-hover', '#3a3a3a'),
    'APP_ITEM_HOVER_LIGHT': ('hover-light', '#eeeeee'),
}

#: dict NAME -> the live palette.
PALETTES = {'DARK_THEME': ThemeManager.DARK_THEME,
            'LIGHT_THEME': ThemeManager.LIGHT_THEME,
            'IMAGE_THEME': ThemeManager.IMAGE_THEME}

#: The value the plate is NOT, and the reason the distinction is worth a test.
FLOOR = '#e8e8e8'


def grey(n: int) -> str:
    v = n * GRID_STEP
    return '#%02x%02x%02x' % (v, v, v)


def _luminance(value: str) -> float:
    channels = [int(value.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _palette_node(name: str) -> ast.Dict:
    tree = ast.parse(SRC.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(target, 'id', None) == name and isinstance(node.value, ast.Dict):
                return node.value
    raise AssertionError(f'{name} is not a dict literal in utils/config.py')


def _entry(node: ast.Dict, key: str):
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


# ------------------------------------------------------------- guard the guard

def test_everything_this_file_reads_still_exists():
    """Renaming a constant must fail loudly here rather than let the rest of
    this file pass quietly over nothing."""
    for name in NEW:
        assert hasattr(config, name), f'utils.config has no {name}'
    for dict_name, live in PALETTES.items():
        assert live, f'{dict_name} is empty'


# ------------------------------------------------------------------ the values

def test_the_reclassified_constants_still_hold_their_values():
    """This pass changes what is SAID about three constants. If it moved one of
    them, that would be the worst possible outcome of a provenance pass."""
    drift = {n: getattr(config, n) for n, (_, v) in NEW.items()
             if getattr(config, n) != v}
    assert not drift, f'values moved during a reclassification: {drift}'


def test_the_reclassified_constants_match_rnv_brand():
    """The upstream half. Skips where rnv-brand is not importable, which is why
    tests/test_app_mirror.py pins the same three locally."""
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; the local pin is doing the work')
    drift = []
    for name, (key, _) in NEW.items():
        theirs, mine = brand.APP[key], getattr(config, name)
        if mine.lower() != theirs.lower():
            drift.append(f'{name}: ours {mine}, theirs APP[{key!r}] {theirs}')
    assert not drift, 'drift from rnv-brand:\n  ' + '\n  '.join(drift)


def test_all_three_are_pinned_and_mirrored():
    """The reclassification IS the two tables. A docstring saying a value is
    mirrored, with no entry making it so, is the failure this pass is fixing in
    the opposite direction."""
    mirror = pathlib.Path(__file__).with_name('test_app_mirror.py')
    source = mirror.read_text(encoding='utf-8')
    for name in NEW:
        assert f"'{name}':" in source, (
            f'{name} is not in tests/test_app_mirror.py. It is declared '
            f'mirrored in its docstring; without a PINNED and a MIRRORS entry '
            f'that claim is decorative.')


# ------------------------------------------------------------------ the ladder

def test_the_dark_rungs_are_exact_steps_on_the_ladder():
    """BRAND_BLACK + n * 0x10. Two of these were app-owned on the argument that
    the ladder might not be real. It is, and this is what says so."""
    base = int(config.APP_SURFACE_DARK.lstrip('#'), 16)
    for n, name in ((-1, 'APP_CANVAS_DARK'), (0, 'APP_SURFACE_DARK'),
                    (1, 'APP_CARD_DARK'), (2, 'APP_PANEL_HOVER_DARK')):
        want = base + n * (LADDER_STEP * 0x010101)
        assert int(getattr(config, name).lstrip('#'), 16) == want, (
            f'{name} is {getattr(config, name)}, not rung n={n} of '
            f'APP_SURFACE_DARK + n*0x10')


def test_the_border_is_an_edge_and_not_a_rung():
    """The distinction that made the ladder look incomplete for a week."""
    assert config.APP_BORDER_DARK == grey(3)
    base = int(config.APP_SURFACE_DARK.lstrip('#'), 16)
    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}
    assert int(config.APP_BORDER_DARK.lstrip('#'), 16) not in rungs


def test_the_canvas_is_not_the_web_ground():
    """One byte apart, deliberately. The docstring used to say #0a0a0a was
    app-owned BECAUSE the register's canvas was WEB_BLACK. The first half is
    now wrong and the second half was always the part that mattered."""
    r, g, b = (int(config.APP_CANVAS_DARK.lstrip('#')[i:i + 2], 16)
               for i in (0, 2, 4))
    assert r == g == b, f'{config.APP_CANVAS_DARK} is not a pure grey'
    brand = pytest.importorskip('engine.brand', reason='rnv-brand not importable')
    assert config.APP_CANVAS_DARK.lower() != brand.WEB_BLACK.lower()


# ------------------------------------------------------------------- the plate

def test_the_plate_is_a_step_on_the_ink_grid():
    assert config.APP_ITEM_HOVER_LIGHT == grey(14) == '#eeeeee'


def test_the_plate_is_not_the_gold_text_floor():
    """Both clear the 4.5 floor. Only one clears it by enough to survive the
    gold moving, and the other is the value the gold is calibrated against."""
    gold = config.BRAND_DARK_GOLD_DEEP
    here = _contrast(gold, config.APP_ITEM_HOVER_LIGHT)
    edge = _contrast(gold, FLOOR)
    assert config.APP_ITEM_HOVER_LIGHT.lower() != FLOOR
    assert here - TEXT_FLOOR >= 0.2, (
        f'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The '
        f'register moved APP["hover-light"] here for margin, not for a pass.')
    assert edge - TEXT_FLOOR < 0.05, (
        f'{FLOOR} now clears by {edge - TEXT_FLOOR:.4f}, so it is no longer the '
        f'knife-edge this ruling was about. Either the gold moved or the floor '
        f'did; re-derive before trusting the value above.')


def test_the_light_panel_hover_names_the_plate():
    """The last literal in the light palette that spelled the plate out. A
    literal cannot follow its base."""
    node = _palette_node('LIGHT_THEME')
    value = _entry(node, 'panel_hover')
    assert isinstance(value, ast.Name) and value.id == 'APP_ITEM_HOVER_LIGHT', (
        f'LIGHT_THEME["panel_hover"] is '
        f'{ast.unparse(value) if value else "missing"}, not the plate constant')
    assert ThemeManager.LIGHT_THEME['panel_hover'] == config.APP_ITEM_HOVER_LIGHT
