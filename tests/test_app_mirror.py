"""
The APP register, mirrored -- and the ink move that made mirroring necessary.

WHY THIS FILE EXISTS. Until 2026-08-28 this app carried #e0e0e0, #1a1a1a,
#2a2a2a and #333333 as bare hex literals with no constant and no provenance.
Every one of them is a REGISTERED value in RNVizion/rnv-brand. A registered
value could have moved upstream and this app would have kept the old one
silently -- the same failure #c4a458 had, one level down.

It nearly happened. `APP["text"]` moved from #e0e0e0 to #dddddd in
rnv-brand@68d195e, and nothing here would have noticed.

THE INK GRID, published in the brand beside that move:

    grey(n) = n * 0x11, n in 0..15.   TRUE_BLACK -> WHITE in fifteen steps.

It governs INKS AND EDGES and deliberately does not govern surfaces --
BRAND_BLACK sits at n = 1.53 and APP_CARD at n = 2.47, and BRAND_BLACK is a
permanent that will not move to fit a ladder.

TWO GUARDS, NOT ONE. rnv-text-transformer's mirror test guards with
`pytest.importorskip('engine.brand')`, so where rnv-brand is not importable it
reports clean and drift hides. Every register value here is therefore pinned
LOCALLY as well as mirrored UPSTREAM: the pin catches drift when the brand is
absent, the mirror catches the brand moving. Neither alone is enough.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from utils import config as colors
from utils.config import ThemeManager

DARK = ThemeManager.DARK_THEME
LIGHT = ThemeManager.LIGHT_THEME
IMAGE = ThemeManager.IMAGE_THEME

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'utils' / 'config.py'

GRID_STEP = 0x11

#: What the brand register held on 2026-08-28, written down so this file still
#: has an opinion when engine.brand cannot be imported.
PINNED = {
    'TRUE_BLACK': '#000000',
    'WHITE': '#ffffff',
    'APP_SURFACE_DARK': '#1a1a1a',
    'APP_BORDER_DARK': '#333333',
    'APP_TEXT_DARK': '#dddddd',
}

#: This app names its neutrals by ROLE AND MODE -- APP_SURFACE_DARK, not
#: APP_CARD -- because it registers a light set beside the dark one. The brand's
#: APP dict is the dark palette only, so the APP_<KEY> convention the other four
#: apps resolve by cannot be used here. Mapped explicitly rather than renaming
#: eleven constants to fit a convention that would then be wrong within this
#: file.
MIRRORS = {
    'TRUE_BLACK': ('module', 'TRUE_BLACK'),
    'WHITE': ('module', 'WHITE'),
    'APP_SURFACE_DARK': ('APP', 'panel'),
    'APP_BORDER_DARK': ('APP', 'border'),
    'APP_TEXT_DARK': ('APP', 'text'),
}

#: Dark-mode ink and edge. These carry APP_TEXT and must reference it by name.
INK_KEYS = ('text_color', 'button_text', 'input_text', 'slot_border',
            'slider_handle')

#: The other half of #e0e0e0's old double life: a LIGHT surface, which the
#: grid does not govern and which did not move.
LIGHT_SURFACE_KEYS = ('hover_color',)


def grey(n: int) -> str:
    v = n * GRID_STEP
    return '#%02x%02x%02x' % (v, v, v)


def _dict_node(name: str) -> ast.Dict:
    tree = ast.parse(SRC.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(target, 'id', None) == name and isinstance(node.value, ast.Dict):
                return node.value
    raise AssertionError(f'{name} is not a dict literal in utils/config.py')


def _entry(node: ast.Dict, key: str) -> ast.AST | None:
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


# ------------------------------------------------------------- guard the guard

def test_the_keys_this_file_reads_still_exist():
    """Every assertion below reads these. If a key is renamed, this fails
    loudly instead of the rest quietly passing over nothing."""
    for key in INK_KEYS:
        assert key in DARK, f'DARK has no {key}'
    for key in LIGHT_SURFACE_KEYS:
        assert key in LIGHT, f'LIGHT has no {key}'
    for name in PINNED:
        assert hasattr(colors, name), f'utils.config has no {name}'


# ------------------------------------------------------------------- the value

def test_the_ink_is_a_step_on_the_grid():
    assert colors.APP_TEXT_DARK == grey(13) == '#dddddd', (
        f'APP_TEXT is {colors.APP_TEXT_DARK}, not grey(13). The ink grid admits no '
        f'exceptions -- see rnv-brand engine/brand.py APP.')


def test_every_pinned_neutral_is_what_the_register_held():
    """The local half of the mirror. Runs everywhere, including where
    engine.brand is not importable."""
    drift = {n: getattr(colors, n) for n, v in PINNED.items()
             if getattr(colors, n) != v}
    assert not drift, (
        f'these constants no longer hold their registered values: {drift}\n'
        f'If the brand moved, update PINNED here in the same commit that '
        f'updates utils/config.py -- never one without the other.')


def test_register_values_match_rnv_brand():
    """The upstream half. Skips where rnv-brand is not importable, which is
    exactly why the pin above is not optional."""
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; the local pin is doing the work')
    drift = []
    for name in PINNED:
        where, key = MIRRORS[name]
        theirs = brand.APP[key] if where == 'APP' else getattr(brand, key)
        mine = getattr(colors, name)
        if mine.lower() != theirs.lower():
            drift.append(f'{name}: ours {mine}, theirs {theirs}')
    assert not drift, 'drift from rnv-brand:\n  ' + '\n  '.join(drift)


# --------------------------------------------------- the ink references the name

def test_every_dark_ink_reads_the_constant_not_a_literal():
    """A literal cannot follow its base. This is the whole point of the pass:
    if APP_TEXT moves again, these move with it or this test fails."""
    node = _dict_node('DARK_THEME')
    literals = []
    for key in INK_KEYS:
        value = _entry(node, key)
        if not (isinstance(value, ast.Name) and value.id == 'APP_TEXT_DARK'):
            literals.append(f'{key} = {ast.unparse(value) if value else "missing"}')
    assert not literals, (
        'dark ink entries still written as literals:\n  ' + '\n  '.join(literals))


def test_the_resolved_ink_is_the_constant():
    """The AST check above proves the spelling; this proves the value."""
    for key in INK_KEYS:
        assert DARK[key] == colors.APP_TEXT_DARK, f'DARK[{key!r}] is {DARK[key]}'


def test_image_mode_carries_the_same_ink():
    """IMAGE_THEME is a separate literal block here, not a spread of DARK, so
    the move has to be made twice and asserted twice."""
    node = _dict_node('IMAGE_THEME')
    literals = []
    for key in INK_KEYS:
        value = _entry(node, key)
        if not (isinstance(value, ast.Name) and value.id == 'APP_TEXT_DARK'):
            literals.append(
                f'{key} = {ast.unparse(value) if value is not None else "missing"}')
    assert not literals, ('image ink still written as literals:\n  '
                          + '\n  '.join(literals))
    for key in INK_KEYS:
        assert IMAGE[key] == colors.APP_TEXT_DARK, f'IMAGE[{key!r}]'


def test_the_handle_hover_is_still_one_step_above_the_text():
    """APP_HANDLE_HOVER_DARK is documented as 'one step above the text'. That
    sentence was true of #f0f0f0 above #e0e0e0 only by accident -- the gap was
    0x10, not a grid step. Both are on the grid now and the relationship is
    asserted rather than described."""
    assert colors.APP_HANDLE_HOVER_DARK == grey(14) == '#eeeeee'
    assert colors.APP_HANDLE_HOVER_DARK == grey(
        (int(colors.APP_TEXT_DARK[1:3], 16) // GRID_STEP) + 1)


def test_the_light_surface_did_not_follow_the_ink():
    """#e0e0e0's other half. LIGHT hover_color is a SURFACE, and the grid does
    not govern surfaces."""
    assert LIGHT['hover_color'] == '#e0e0e0'


# ------------------------------------------------------------- what did NOT move

def test_the_light_ink_is_true_black():
    """Primary text is one role with two mode values: dark is a grey on the
    grid, light is TRUE_BLACK."""
    assert LIGHT['text_color'] == colors.TRUE_BLACK == '#000000'


# ---------------------------------------------------------------- what it costs

def _luminance(value: str) -> float:
    channels = [int(value.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_the_ink_clears_the_text_floor_on_every_dark_ground_it_touches():
    """Measured, not assumed. The darkest ground the ink is drawn on is the
    pressed plate; everything else has more room."""
    grounds = ('#000000', '#1a1a1a', '#2a2a2a', '#333333', '#3a3a3a', '#444444')
    worst = min((_contrast(colors.APP_TEXT_DARK, g), g) for g in grounds)
    assert worst[0] >= 4.5, (
        f'the ink falls to {worst[0]:.2f}:1 on {worst[1]}, under the 4.5 floor')
