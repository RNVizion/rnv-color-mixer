"""RNV-MIXER-WIRING-GUARD -- every palette value has a name, and the splits hold.

Installed 2026-09-06. What it pins:

  * no value in any of the three palettes is a bare hex -- a literal cannot
    follow the register, so one appearing here is a value that will be
    orphaned the first time the brand moves;
  * the two SPLITS: #444444 and #666666 each carry two constants, because each
    plays two roles, and the guard states which name goes with which role;
  * `slider_groove` is the ONLY key any QSlider groove reads, in every file;
  * `main_btn_hover_text` states the ruled dimming rather than inheriting it;
  * every name a palette uses is assigned ABOVE the palette that uses it.

The palettes here are CLASS ATTRIBUTES of ThemeManager, not module-level
dicts, so everything below descends into the ClassDef. A sweep written for the
other four applications finds nothing in this one and passes for the wrong
reason -- which is what `test_this_guard_can_see_the_palettes` is for.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from utils import config as C

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'utils/config.py'
PALETTES = ['DARK_THEME', 'LIGHT_THEME', 'IMAGE_THEME']
HEX = re.compile(r"#[0-9a-fA-F]{3,8}$")

#: hex -> the two constants that share it, and the role each one plays. A
#: second name for one colour is either a split with a stated role or a
#: defect; these two are splits, ruled 2026-09-06.
SPLITS = {
    '#444444': {'APP_BTN_PRESSED': 'the pressed plate of the basic button',
                'APP_CHROME_DARK': 'the dark control trough and menu edge'},
    '#666666': {'APP_HANDLE_LIGHT': 'the light slider handle at rest',
                'APP_MENU_DIM_DARK': 'the disabled menu label in dark and image'},
    '#eeeeee': {'APP_HANDLE_HOVER_DARK': 'a dark ink-grid step, app-owned',
                'APP_ITEM_HOVER_LIGHT': 'the light register plate APP["hover-light"]'},
}

#: The four names this pass introduced, with the value each must hold.
ADDED = {
    'APP_CHROME_DARK': '#444444',
    'APP_CHROME_LIGHT': '#e0e0e0',
    'APP_DIM_LIGHT': '#aaaaaa',
    'APP_MENU_DIM_DARK': '#666666',
}


def _class_body():
    mod = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    for node in mod.body:
        if isinstance(node, ast.ClassDef) and node.name == 'ThemeManager':
            return node
    raise AssertionError('ThemeManager is no longer a class in utils/config.py')


def _palette_dicts():
    out = {}
    for node in _class_body().body:
        target = value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            target, value = node.targets[0].id, node.value
        if target in PALETTES and isinstance(value, ast.Dict):
            out[target] = value
    return out


def _entries(d):
    """(key, value) for the literal entries of a dict node, skipping any
    `**OTHER` expansion, which ast records as a key of None."""
    for k, v in zip(d.keys, d.values):
        if k is None:
            continue
        yield ast.literal_eval(k), v


# ------------------------------------------------------------- guard the guard

def test_this_guard_can_see_the_palettes():
    """These palettes are class attributes. A sweep written for the other four
    applications looks at module level, finds nothing, and passes on an empty
    set -- so the first thing to assert is that the sweep has a subject."""
    found = _palette_dicts()
    assert set(found) == set(PALETTES), (
        f'palettes not found as dict literals inside ThemeManager: '
        f'{set(PALETTES) - set(found)}')
    for name, d in found.items():
        assert len(list(_entries(d))) > 20, (
            f'{name} has {len(list(_entries(d)))} entries; the sweep below '
            f'would pass on almost nothing')


# --------------------------------------------------------------- the wiring

@pytest.mark.parametrize('palette', PALETTES)
def test_no_palette_value_is_a_bare_hex(palette):
    """Read from SOURCE rather than from the imported dict, because the
    imported dict cannot tell a literal from a constant -- both are plain
    strings by the time they are values."""
    bad = [(key, v.value) for key, v in _entries(_palette_dicts()[palette])
           if isinstance(v, ast.Constant) and isinstance(v.value, str)
           and HEX.match(v.value)]
    assert not bad, (
        f'{palette} writes these as literals; a literal cannot follow the '
        f'register and will be orphaned the first time it moves: {bad}')


def test_every_name_a_palette_uses_is_defined_above_it():
    """Wiring gives constants callers they did not have. A constant assigned
    below the palette that reads it is a NameError at import, which surfaces as
    a collection error naming one symbol and explaining nothing. Read from the
    source, because by the time the module imports this has either worked or
    taken the whole suite down with it."""
    mod = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    assigned = {}
    for node in mod.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
        if target:
            assigned.setdefault(target, node.lineno)
    late = set()
    for name, d in _palette_dicts().items():
        for sub in ast.walk(d):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                at = assigned.get(sub.id)
                if at is not None and at > d.lineno:
                    late.add((name, sub.id, at))
    assert not late, (
        f'assigned below the palette that reads them, which is a NameError at '
        f'import, not a style point: {sorted(late)}')


@pytest.mark.parametrize('name,value', sorted(ADDED.items()))
def test_the_names_this_pass_added_hold_what_they_say(name, value):
    assert getattr(C, name) == value


# ---------------------------------------------------------------- the splits

@pytest.mark.parametrize('hexv', sorted(SPLITS))
def test_a_declared_split_keeps_both_names(hexv):
    """Both halves must exist and both must still hold the shared value. If a
    later pass 'tidies' one away, the role it carried is silently merged into
    the other -- which is exactly what naming them was meant to prevent."""
    for name in SPLITS[hexv]:
        assert hasattr(C, name), (
            f'{name} is gone. It is half of a declared split on {hexv}, and '
            f'the role it names -- {SPLITS[hexv][name]} -- has nowhere to go.')
        assert getattr(C, name) == hexv


def test_no_undeclared_second_name_for_one_colour():
    """The other direction. A colour with two names is a split with a stated
    role, or a defect. This is what stops a third name appearing for #444444
    with nobody having decided that it should."""
    src = SOURCE.read_text(encoding='utf-8-sig')
    pat = re.compile(r"^([A-Z][A-Z0-9_]+)\s*:\s*Final\[str\]\s*=\s*"
                     r"['\"](#[0-9a-fA-F]{6})['\"]", re.M)
    by_hex = {}
    for name, hexv in pat.findall(src):
        by_hex.setdefault(hexv.lower(), []).append(name)
    for hexv, names in sorted(by_hex.items()):
        if len(names) < 2:
            continue
        declared = set(SPLITS.get(hexv, {}))
        extra = set(names) - declared - {'INITIAL_COLOR_HEX'}
        assert not extra or set(names) <= declared | {'INITIAL_COLOR_HEX'}, (
            f'{hexv} has the names {sorted(names)}. Declared for it: '
            f'{sorted(declared) or "none"}. Either one is a duplicate, or a '
            f'split needs declaring in SPLITS with the role each name plays.')


# ------------------------------------------------------------ the split keys

@pytest.mark.parametrize('key', ['slider_groove', 'menu_edge', 'main_btn_hover_text'])
def test_the_keys_this_pass_added_exist_in_every_mode(key):
    for palette in PALETTES:
        keys = {k for k, _ in _entries(_palette_dicts()[palette])}
        assert key in keys, f'{palette} has no {key!r}'


def test_the_slider_groove_is_read_from_one_key_everywhere():
    """Before this pass the same widget part was painted from three different
    keys in three files -- panel_bg, hover_color and input_bg -- and in dark
    two of them resolved to the panel's own colour, so the groove did not
    exist. One key now, and this asserts nothing has drifted back."""
    offenders = []
    for path in sorted(ROOT.rglob('*.py')):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(('tests/', 'build/', '.venv/')) or rel == 'up.py':
            continue
        lines = path.read_text(encoding='utf-8-sig', errors='ignore').splitlines()
        selector = None
        for i, line in enumerate(lines):
            s = line.strip()
            if s.endswith('{{'):
                selector = s.rstrip('{ ') if 'QSlider::groove' in s else None
            elif selector and 'background' in s and '[' in s:
                m = re.search(r"\['([a-z_0-9]+)'\]", s)
                if m and m.group(1) != 'slider_groove':
                    offenders.append(f'{rel}:{i + 1} groove reads {m.group(1)!r}')
    assert not offenders, (
        'a QSlider groove is painted from something other than slider_groove:'
        '\n  ' + '\n  '.join(offenders))


def test_the_hover_label_states_the_ruled_dimming():
    """rnv-brand / claude/ruling-interaction-contrast.md: the main button's
    transient states are exempt from the 4.5 floor and the label DIMS on
    purpose. Two files disagreed about whether to say so -- one set the hover
    colour explicitly, the other let Qt inherit it -- so the ruled behaviour
    was half stated and half accidental.

    It is one key now, holding what each mode already painted. This test
    asserts the value did NOT change: hover keeps the resting label."""
    for palette in PALETTES:
        d = dict(_entries(_palette_dicts()[palette]))
        resolved = getattr(C.ThemeManager, palette)
        assert resolved['main_btn_hover_text'] == resolved['main_btn_text'], (
            f'{palette}: the hover label is no longer the resting label. That '
            f'is a change to a RULED transition -- see '
            f'claude/ruling-interaction-contrast.md -- not a wiring fix.')


def test_the_light_button_hover_uses_the_alias_that_exists_for_it():
    """APP_BTN_HOVER_INVERSE was defined for exactly this and the light palette
    wrote the value out by hand instead. Assigned from APP_BORDER_DARK rather
    than repeating #333333, so the two cannot drift apart."""
    d = dict(_entries(_palette_dicts()['LIGHT_THEME']))
    for key in ('main_btn_hover_bg', 'dialog_btn_hover_bg'):
        v = d[key]
        assert isinstance(v, ast.Name) and v.id == 'APP_BTN_HOVER_INVERSE', (
            f'LIGHT {key} does not read APP_BTN_HOVER_INVERSE')
    assert C.APP_BTN_HOVER_INVERSE == C.APP_BORDER_DARK == '#333333'
