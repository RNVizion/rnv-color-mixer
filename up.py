#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: give every palette value a name, split the two colours that
carry two roles, and give the slider groove one key instead of three.

    python up.py             # apply, then verify
    python up.py --check     # rehearse: compose every edit, run every guard,
                             #           write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT MOVES. Three sites, all of them the same widget part:

    core/color_fine_tune.py:413   dark slider groove   #1a1a1a -> #444444
    core/color_slot.py:577        slider groove        #1a1a1a -> #444444  (dark)
                                                       #ffffff -> #e0e0e0  (light)
    core/package_d_panel.py:2622  slider groove        same as above

In dark and image the groove was the SAME COLOUR as the panel the slider sits
on -- 1.00:1 -- so there was no channel at all; the track read as a handle
floating on the panel with only its 1px edge to suggest a recess. In light the
two candidate keys pulled opposite ways: #ffffff is brighter than the #f5f5f5
panel, so the groove read as raised, while #e0e0e0 is darker, so it reads as
recessed, which is what a groove is. #e0e0e0 is what the light fine-tune
slider already painted, so one of the four sites does not move at all.

Everything else in this script is spelling. 32 literals become names; three
keys are added holding what their sites already paint.

WHAT IS NOT TOUCHED, DELIBERATELY:

  * APP_HANDLE_HOVER_DARK and APP_ITEM_HOVER_LIGHT. Both are #eeeeee and both
    stay. utils/config.py documents them as a deliberate split -- a dark
    ink-grid step and a light register plate meeting at grey(14) -- and
    tests/test_ladder_and_plate.py asserts it in both directions.

  * The _DARK / _LIGHT naming convention. utils/config.py rules it explicitly:
    "THE NAME STAYS AS IT IS ... the mirror is what carries the ownership, not
    the spelling." So the four names added below follow THIS application's
    convention, not the fleet's GREY_* spelling.

  * The main button's hover label. claude/ruling-interaction-contrast.md rules
    the transient states exempt from the 4.5 floor: the label dims on purpose.
    This script adds the key that STATES that value; it does not change it.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
SENTINEL_FILE = "utils/config.py"
SENTINEL = "RNV-MIXER-WIRING"
GUARD = "tests/test_mixer_wiring.py"
DESCRIPTION = "name every mixer palette value; one key for the slider groove"
_LOCKED_IMAGE_TEST = ("test_rnv_color_mixer.py::TestImageHandler::"
                      "test_load_real_image_if_available")
SUITES = [("pytest tests/",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          # The LOCKED file, run through pytest rather than through the command
          # CI uses. TWO REASONS, and both are worth knowing:
          #
          #   1. CI runs `unittest test_rnv_color_mixer -k "not test_load_..."`.
          #      unittest's -k is a SUBSTRING pattern, not a pytest expression,
          #      so "not test_load_real_image_if_available" matches no test
          #      name and the suite runs ZERO of its 356 tests, reporting OK.
          #      A verification step that inherits that command proves nothing.
          #   2. Plain `unittest test_rnv_color_mixer` does not finish here --
          #      it was still running after ten minutes. Under pytest the same
          #      file collects 356, deselects the one image test by node id,
          #      and passes 355 in about nineteen seconds.
          #
          # Same file, same tests, a command that actually runs them.
          ("the LOCKED file, 355 tests",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120",
            "--deselect", _LOCKED_IMAGE_TEST])]

PALETTES = ["DARK_THEME", "LIGHT_THEME", "IMAGE_THEME"]

#: Basenames this script must never be run AS -- copying it over one of these
#: would shadow the module it is meant to edit, and the import it then breaks
#: is the file it was supposed to fix.
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-MIXER-WIRING-GUARD -- every palette value has a name, and the splits hold.

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
'''

CONSTANTS = r'''
# ---- RNV-MIXER-WIRING (2026-09-06): four names for values the palettes
# ---- already carried as literals. Nothing here is a new colour.

APP_CHROME_DARK: Final[str] = "#444444"
"""grey(4). The structural grey of a control in dark and image: the slider
groove, and the border and separator of a menu.

SPLIT, NOT RENAMED. APP_BTN_PRESSED is the same hex and stays exactly as it
is. That one is a button in its PRESSED state; this one is a resting trough
and a resting edge. Wiring a groove through the pressed name would claim an
interaction state for a piece of chrome on the strength of a shared byte --
the same reasoning this file already gives for APP_HANDLE_HOVER_DARK sharing
grey(14) with APP_ITEM_HOVER_LIGHT."""

APP_CHROME_LIGHT: Final[str] = "#e0e0e0"
"""The same job in light: the slider groove. Darker than the #f5f5f5 panel, so
the groove reads as recessed rather than raised -- which is why it is this
value and not input_bg's #ffffff.

Soft on its own at 1.21:1 against the panel; the groove's 1px APP_BORDER_LIGHT
edge does most of the defining. That is the appearance the light fine-tune
slider already had, and this pass gives it to the other two sliders as well."""

APP_DIM_LIGHT: Final[str] = "#aaaaaa"
"""grey(10). Disabled text in light. The mirror of APP_CONTROL_DIM's grey(5)
by the ink grid's own rule -- invert(n) = 15 - n, and 5 + 10 = 15 -- which is
why the pair is exact and nobody planned it."""

APP_MENU_DIM_DARK: Final[str] = "#666666"
"""grey(6). The disabled menu label in dark and image.

SPLIT, NOT RENAMED. APP_HANDLE_LIGHT is the same hex and keeps its own job.
Wiring this through that name would have put a _LIGHT-suffixed constant in the
DARK palette, and named a menu label after a slider handle. Two wrongs out of
one shared byte."""

'''

LIGHT_TEST_NEW = r'''def test_the_light_palette_names_its_own_greys():
    """RNV-MIXER-WIRING (2026-09-06). This REPLACES
    test_the_light_palette_was_left_alone, which asserted the light palette
    referenced no substituted constant at all and said in its own docstring
    that a later pass wiring light would have to delete it on purpose. This is
    that pass, and this is that deliberate act.

    What the old test protected is still protected, and more tightly. The
    concern was never that light must stay unwired -- it was that light must
    not be wired to the DARK names, which is how a value ends up true by value
    and false by name. The old form could not express that: it swept
    SUBSTITUTE.values(), which contains TRUE_BLACK, an anchor belonging to
    neither mode, so the only way to pass was to name nothing.

    So the successor asserts the positive. The two greys the old test was
    holding back -- #aaaaaa and #e0e0e0 -- now have names, and every name the
    light palette reads is a light one, an anchor, or the one dark name it
    borrows on purpose.
    """
    #: TRUE_BLACK and WHITE belong to no mode. APP_BTN_HOVER_INVERSE is the
    #: dark border step used in light DELIBERATELY -- the basic button's
    #: scheme inverts on hover, and utils/config.py assigns the alias from
    #: APP_BORDER_DARK rather than repeating the value so the two cannot drift.
    ALLOWED_IN_LIGHT = {"TRUE_BLACK", "WHITE", "APP_BTN_HOVER_INVERSE"}

    d = _dicts(("LIGHT_THEME",))["LIGHT_THEME"]
    leaked = []
    for key, value in zip(d.keys, d.values):
        if key is None or not isinstance(value, ast.Name):
            continue
        name = value.id
        if name in ALLOWED_IN_LIGHT or not name.endswith("_DARK"):
            continue
        leaked.append(f"LIGHT_THEME[{key.value!r}] -> {name}")
    assert not leaked, (
        "a dark name is being read from the light palette, which makes the "
        "value true and the name false:\n  " + "\n  ".join(leaked)
        + "\n\nIf the borrow is deliberate, add it to ALLOWED_IN_LIGHT with "
          "the reason, the way APP_BTN_HOVER_INVERSE is.")


def test_the_two_held_back_greys_now_have_light_names():
    """The other half: the old test's subject, asserted as done rather than as
    forbidden. An allowlist that permits everything and a wiring that names
    nothing look identical from the outside, so this states what landed."""
    assert config.APP_DIM_LIGHT == "#aaaaaa"
    assert config.APP_CHROME_LIGHT == "#e0e0e0"
    resolved = ThemeManager.LIGHT_THEME
    assert resolved["text_disabled"] == config.APP_DIM_LIGHT
    assert resolved["slider_groove"] == config.APP_CHROME_LIGHT
'''


# --------------------------------------------------------------- the constants
# Four names, in this application's role+mode convention. Two of them are the
# second half of a split: the colour already had a name, playing a different
# role, and wiring through that name would have claimed the role along with
# the value.
# name -> the line it is inserted after (the last line of APP_BTN_PRESSED's
# docstring). Anchored on text rather than a line number so a shifted file
# refuses rather than lands in the wrong place.
CONST_ANCHOR = ('flips instead -- TRUE_BLACK on dark, WHITE on light."""\n')

PROVENANCE_ANCHOR = '    "APP_BTN_HOVER_INVERSE": "alias",\n}\n'
PROVENANCE_ADD = ('    "APP_CHROME_DARK": "step",\n'
                  '    "APP_CHROME_LIGHT": "step",\n'
                  '    "APP_DIM_LIGHT": "step",\n'
                  '    "APP_MENU_DIM_DARK": "step",\n')

# ---------------------------------------------------------------- the palettes
# hex -> constant, per palette. Written per palette rather than per hex because
# this application's names carry the mode, so the same byte takes a different
# name on each side.
WIRE = {
    "DARK_THEME": {"#444444": "APP_CHROME_DARK", "#555555": "APP_CONTROL_DIM",
                   "#666666": "APP_MENU_DIM_DARK"},
    "IMAGE_THEME": {"#444444": "APP_CHROME_DARK", "#555555": "APP_CONTROL_DIM",
                    "#666666": "APP_MENU_DIM_DARK"},
    "LIGHT_THEME": {"#f5f5f5": "APP_WINDOW_LIGHT", "#000000": "TRUE_BLACK",
                    "#cccccc": "APP_BORDER_LIGHT", "#e0e0e0": "APP_CHROME_LIGHT",
                    "#ffffff": "WHITE", "#aaaaaa": "APP_DIM_LIGHT",
                    "#666666": "APP_HANDLE_LIGHT", "#999999": "APP_HANDLE_EDGE_LIGHT",
                    "#333333": "APP_BTN_HOVER_INVERSE"},
}
# (palette, key) -> constant, where the key plays a role the default name would
# misdescribe. #333333 in light is the inverse button scheme, and the alias for
# it already exists; every other light #333333 would be a plain dark border.
EXPECTED = {"DARK_THEME": 3, "LIGHT_THEME": 26, "IMAGE_THEME": 3}

# key -> (dark, light, image) constant, appended to each palette. Every one
# holds what its call sites already paint.
NEW_KEYS = [
    ("slider_groove", "APP_CHROME_DARK", "APP_CHROME_LIGHT", "APP_CHROME_DARK",
     "# One key for the slider groove. Before this pass three files painted\n"
     "# it from three different keys -- panel_bg, hover_color and input_bg --\n"
     "# and in dark two of those resolved to the panel's own colour, so the\n"
     "# groove did not exist. RNV-MIXER-WIRING (2026-09-06)."),
    ("menu_edge", "APP_CHROME_DARK", "APP_BORDER_LIGHT", "APP_CHROME_DARK",
     "# The menu's border and separator. The dark and light branches of\n"
     "# core/color_slot.py painted these from different keys -- hover_color\n"
     "# and border_color -- so the same two parts had no shared name. Values\n"
     "# unchanged; the difference between the modes is now a value, not a key."),
    ("main_btn_hover_text", "APP_TEXT_DARK", "TRUE_BLACK", "APP_TEXT_DARK",
     "# The label while the main button is hovered. RULED, not chosen: see\n"
     "# claude/ruling-interaction-contrast.md -- the transient states of this\n"
     "# button are exempt from the 4.5 floor and the label dims on purpose.\n"
     "# It held the resting label by inheritance in one file and by an\n"
     "# explicit line in another; this states it once, at the same value."),
]

# ------------------------------------------------------- the deliberate delete
# tests/test_register_wiring.py pins the light palette as UNWIRED and says in
# its own docstring: "If a later pass wires light, this test has to be deleted
# on purpose." This is that pass and this is that purpose. It is REPLACED
# rather than deleted, because the ruling it protected -- light must not read
# the dark names -- is still live and the successor states it directly.
LIGHT_TEST_OLD = (
    'def test_the_light_palette_was_left_alone():\n'
    '    """The light ladder is unruled. Two of its greys -- #aaaaaa and #e0e0e0 --\n'
    '    are deliberately still unnamed. If a later pass wires light, this test has\n'
    '    to be deleted on purpose."""\n'
    '    named = []\n'
    '    for key, value in zip(*(lambda n: (n.keys, n.values))(_dicts(("LIGHT_THEME",))["LIGHT_THEME"])):\n'
    '        if isinstance(value, ast.Name) and value.id in SUBSTITUTE.values():\n'
    '            named.append(f"LIGHT_THEME[{key.value!r}] -> {value.id}")\n'
    '    assert not named, ("the light palette now references the dark names:\\n  "\n'
    '                       + "\\n  ".join(named))\n')

# ------------------------------------------------------------------- the QSS
# (file, old, new, times). Every one of these is anchored on enough context to
# be unique or to state its count -- `border_color` alone appears in a dozen
# rules that are not menus.
QSS_EDITS = [
    # --- the slider groove, three files. THIS IS WHERE PIXELS MOVE.
    ("core/color_fine_tune.py",
     "                QSlider::groove:horizontal {{\n"
     "                    border: 1px solid {_d['border_color']};\n"
     "                    height: 8px;\n"
     "                    background: {_d['panel_bg']};\n",
     "                QSlider::groove:horizontal {{\n"
     "                    border: 1px solid {_d['border_color']};\n"
     "                    height: 8px;\n"
     "                    background: {_d['slider_groove']};\n", 1),
    ("core/color_fine_tune.py",
     "                    background: {_l['hover_color']};\n",
     "                    background: {_l['slider_groove']};\n", 1),
    ("core/color_slot.py",
     "                QSlider::groove:horizontal {{\n"
     "                    border: 1px solid {theme['border_color']};\n"
     "                    height: 8px;\n"
     "                    background: {theme['input_bg']};\n",
     "                QSlider::groove:horizontal {{\n"
     "                    border: 1px solid {theme['border_color']};\n"
     "                    height: 8px;\n"
     "                    background: {theme['slider_groove']};\n", 1),
    ("core/package_d_panel.py",
     "            QSlider::groove:horizontal {{\n"
     "                background: {t['input_bg']};\n",
     "            QSlider::groove:horizontal {{\n"
     "                background: {t['slider_groove']};\n", 1),
    # --- the menu edge, four blocks in one file: two dark, two light.
    ("core/color_slot.py",
     "                    border: 1px solid {_m['hover_color']};\n",
     "                    border: 1px solid {_m['menu_edge']};\n", 2),
    ("core/color_slot.py",
     "                QMenu::separator {{\n"
     "                    height: 1px;\n"
     "                    background-color: {_m['hover_color']};\n",
     "                QMenu::separator {{\n"
     "                    height: 1px;\n"
     "                    background-color: {_m['menu_edge']};\n", 2),
    ("core/color_slot.py",
     "                QMenu {{\n"
     "                    background-color: {_m['panel_secondary']};\n"
     "                    color: {_m['text_color']};\n"
     "                    border: 1px solid {_m['border_color']};\n",
     "                QMenu {{\n"
     "                    background-color: {_m['panel_secondary']};\n"
     "                    color: {_m['text_color']};\n"
     "                    border: 1px solid {_m['menu_edge']};\n", 2),
    ("core/color_slot.py",
     "                QMenu::separator {{\n"
     "                    height: 1px;\n"
     "                    background-color: {_m['border_color']};\n",
     "                QMenu::separator {{\n"
     "                    height: 1px;\n"
     "                    background-color: {_m['menu_edge']};\n", 2),
    # --- the hover label, stated in both files that paint it.
    ("ui/ui_handler.py",
     "                    QPushButton:hover {{\n"
     "                        background-color: {theme['main_btn_hover_bg']};\n"
     "                    }}\n",
     "                    QPushButton:hover {{\n"
     "                        background-color: {theme['main_btn_hover_bg']};\n"
     "                        color: {theme['main_btn_hover_text']};\n"
     "                    }}\n", 1),
    ("core/color_slot.py",
     "                QPushButton:hover {{\n"
     "                    background-color: {theme['main_btn_hover_bg']};\n"
     "                    color: {theme['main_btn_text']};\n",
     "                QPushButton:hover {{\n"
     "                    background-color: {theme['main_btn_hover_bg']};\n"
     "                    color: {theme['main_btn_hover_text']};\n", 1),
]

LINE = re.compile(r"^(\s+)'([a-z_0-9]+)':(\s+)'(#[0-9a-fA-F]{3,8})'(,.*)$")


def _palette_span(src: str, name: str):
    """(start, end) of the dict assigned to `name` -- a CLASS ATTRIBUTE here,
    indented four spaces, not a module-level assignment."""
    m = re.search(r"^    %s\s*=\s*\{\n" % re.escape(name), src, re.M)
    if not m:
        raise SystemExit(f"{SENTINEL_FILE}: no palette named {name}. These are "
                         f"class attributes of ThemeManager in this repo; a "
                         f"module-level search finds nothing.")
    start = m.end()
    end = src.index("\n    }\n", start)
    return start, end


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)

    # --- 1. the four constants, after the pressed plate they split from.
    if src.count(CONST_ANCHOR) != 1:
        raise SystemExit(f"{SENTINEL_FILE}: the APP_BTN_PRESSED anchor is not "
                         f"where this script expects it")
    for name in ("APP_CHROME_DARK", "APP_CHROME_LIGHT", "APP_DIM_LIGHT",
                 "APP_MENU_DIM_DARK"):
        if re.search(r"^%s\b" % name, src, re.M):
            raise SystemExit(f"{name} already exists in {SENTINEL_FILE}")
    src = src.replace(CONST_ANCHOR, CONST_ANCHOR + CONSTANTS, 1)

    # --- 2. the palettes: every literal to its constant, per mode.
    rewired = []
    for pal in PALETTES:
        table = WIRE[pal]
        start, end = _palette_span(src, pal)
        out = []
        for line in src[start:end].split("\n"):
            m = LINE.match(line)
            if not m:
                out.append(line)
                continue
            indent, key, gap, hexv, rest = m.groups()
            const = table.get(hexv.lower())
            if const is None:
                raise SystemExit(f"{pal}: {key!r} holds {hexv}, which this "
                                 f"script has no name for in this mode")
            pad = gap if len(gap) > 1 else " "
            out.append(f"{indent}'{key}':{pad}{const}{rest}")
            rewired.append((pal, key, hexv, const))
        src = src[:start] + "\n".join(out) + src[end:]
        got = sum(1 for r in rewired if r[0] == pal)
        if got != EXPECTED[pal]:
            raise SystemExit(f"{pal}: rewired {got}, expected {EXPECTED[pal]}. "
                             f"The palette has changed shape since this script "
                             f"was derived; re-derive rather than trust it.")

    # --- 3. the three new keys, appended to each palette.
    for key, dark, light, image, note in NEW_KEYS:
        for pal, const in (("DARK_THEME", dark), ("LIGHT_THEME", light),
                           ("IMAGE_THEME", image)):
            start, end = _palette_span(src, pal)
            body = src[start:end]
            if f"'{key}'" in body:
                raise SystemExit(f"{pal} already has a {key!r} key")
            block = "".join(f"        {l}\n" for l in note.split("\n"))
            src = src[:end] + "\n" + block + f"        '{key}': {const}," + src[end:]

    tree.write(SENTINEL_FILE, src)

    # --- 4. NEUTRAL_PROVENANCE, which tests/test_neutral_ramp.py reads. A
    # classification that lives only in a test drifts from what it classifies.
    tree.sub(SENTINEL_FILE, PROVENANCE_ANCHOR,
             PROVENANCE_ANCHOR.replace("}\n", PROVENANCE_ADD + "}\n"), 1)

    # --- 5. the deliberate replacement in tests/test_register_wiring.py.
    tree.sub("tests/test_register_wiring.py", LIGHT_TEST_OLD, LIGHT_TEST_NEW, 1)

    # --- 6. the stylesheets.
    for rel, old, new, times in QSS_EDITS:
        tree.sub(rel, old, new, times)

    print(f"  4 constants added, {len(rewired)} palette entries wired, "
          f"3 keys added to each of {len(PALETTES)} palettes")
    for pal, key, hexv, const in rewired:
        print(f"     {pal[:5]:5} {key:26} {hexv:9} -> {const}")


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    mod = ast.parse(src.lstrip("﻿"))

    cls = next((n for n in mod.body
                if isinstance(n, ast.ClassDef) and n.name == "ThemeManager"), None)
    if cls is None:
        raise SystemExit("ThemeManager is no longer a class")

    dicts = {}
    for node in cls.body:
        target = value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            target, value = node.targets[0].id, node.value
        if target in PALETTES and isinstance(value, ast.Dict):
            dicts[target] = value
    if set(dicts) != set(PALETTES):
        raise SystemExit(f"palettes not found: {set(PALETTES) - set(dicts)}")

    # no string hex survives inside a palette
    for name, d in dicts.items():
        for k, v in zip(d.keys, d.values):
            if k is None:
                continue
            if isinstance(v, ast.Constant) and isinstance(v.value, str) \
                    and re.fullmatch(r"#[0-9a-fA-F]{3,8}", v.value):
                raise SystemExit(f"{name}[{ast.literal_eval(k)!r}] is still "
                                 f"the literal {v.value}")

    # the three new keys landed in all three
    for key, *_ in NEW_KEYS:
        for name, d in dicts.items():
            keys = {ast.literal_eval(k) for k in d.keys if k is not None}
            if key not in keys:
                raise SystemExit(f"{name} has no {key!r}")

    # every name a palette reads is assigned above it -- the guard the light
    # pass was missing, which turned a module into a NameError at import.
    assigned = {}
    for node in mod.body:
        t = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            t = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            t = node.targets[0].id
        if t:
            assigned.setdefault(t, node.lineno)
    late = set()
    for name, d in dicts.items():
        for sub in ast.walk(d):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                at = assigned.get(sub.id)
                if at is not None and at > d.lineno:
                    late.add((name, sub.id, at))
    if late:
        raise SystemExit(f"assigned below the palette that reads them, which "
                         f"is a NameError at import: {sorted(late)}")

    # no QSlider groove reads anything but slider_groove
    offenders = []
    root = Path.cwd()
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(("tests/", "build/", ".venv/")) or rel in ("up.py", GUARD):
            continue
        # tree.files holds the edited copy of anything this run touched; a
        # file it did not touch is still only on disk. Reading the wrong one
        # is how a sweep passes on the pre-edit text.
        text = (tree.files[rel] if rel in tree.files
                else path.read_text(encoding="utf-8-sig", errors="ignore"))
        selector = None
        for i, line in enumerate(text.splitlines()):
            s = line.strip()
            if s.endswith("{{"):
                selector = s if "QSlider::groove" in s else None
            elif selector and "background" in s and "[" in s:
                m = re.search(r"\['([a-z_0-9]+)'\]", s)
                if m and m.group(1) != "slider_groove":
                    offenders.append(f"{rel}:{i + 1} reads {m.group(1)!r}")
    if offenders:
        raise SystemExit("a QSlider groove still reads another key:\n  "
                         + "\n  ".join(offenders))

    if SENTINEL not in src:
        raise SystemExit("the wiring note did not land")
    print(f"  guards: 0 literals left in 3 palettes, 4 constants in, "
          f"3 keys added per palette, every name defined above its use, "
          f"one key for every slider groove")


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        return "fail"
    return "env"


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""


KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
