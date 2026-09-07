#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: four resolver fixes for the gold-as-text guard

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT THE GUARD DOES. It reads every f-string in the source, pulls `color:` and
`background-color:` out of each QSS rule, resolves the placeholders through
this application's own palettes, and measures. Gold drawn as TEXT below 4.5 on
its ground fails; a label on a gold FILL below 4.5 fails. It has run in three
of the five applications since the gold alignment round.

FOUR RESOLVER DEFECTS, FOUND BY PORTING IT. rnv-color-palette-manager builds
its two dialog stylesheets in two separate functions -- _get_style_dark() and
_get_style_light() -- where the other applications use one function with an
if/else. That difference exposed four blind spots that had been in the sweep
since it was written:

  1. THE MODULE SCOPE CLAIMED EVERY F-STRING. `ast.walk` yields the Module
     before the functions inside it, and walking the Module collects
     assignments from every function in the file -- last one wins. So the dark
     block's `pressed_text = TRUE_BLACK` resolved as the light block's
     `pressed_text = WHITE`, and the sweep reported white-on-gold at 1.85 in
     DARK: a pairing that cannot render. Scopes are now sorted deepest first.

  2. AN ALIASED IMPORT IS A BINDING. That application binds its palette with a
     lazy `from ui.colors import LIGHT_THEME_COLORS as colors` inside each
     function, to break a circular import. Only Assign was read, so the mode
     marker -- which was sitting on the import line -- was invisible, the mode
     reader fell back to all three modes, and a light-only stylesheet was
     scored against the dark palette.

  3. THE TWO READERS DISAGREED. The value resolver expanded a bare local
     through the bindings; the mode reader did not, and returned all modes for
     anything that was not literally a subscript. The value then came from one
     palette and the mode from another.

  4. A DECLARED COLOUR THAT CANNOT BE PARSED IS NOT AN ABSENT ONE. The pressed
     gold button is written `color: {WHITE if is_light else TRUE_BLACK}` --
     correct in both modes, 6.03:1 in dark. The resolver does not read
     conditionals, returned None, and the code fell through to the CONTAINER
     rule's label, reporting black text as #dddddd at 1.36 in two files.
     Inheriting is only right where the rule declares nothing.

WHAT THIS MEANS FOR THE THREE THAT ALREADY HAD IT. All three were re-run with
the fixed sweep and all three are still clean -- the blind spots were hiding
nothing here. They would have started hiding things the first time a
stylesheet was split into two functions, which is a refactor nobody would
think to check a contrast guard against.

NO SOURCE FILE IS TOUCHED except for one pointer comment. This round changes
what is checked, not what is painted.
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
SENTINEL = "RNV-GOLD-GUARD"
GUARD = "tests/test_gold_as_text.py"
DESCRIPTION = "four resolver fixes for the gold-as-text guard"
SUITES = [("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py",
           "dialog_styles.py"}

IS_NEW = False

GUARD_SOURCE = r'''"""Gold drawn as TEXT must clear the text floor on the ground it is drawn on.

WHY THIS EXISTS. The gold family has two members that look interchangeable and
are not. BRAND_DARK_GOLD #8c7337 fills and bounds correctly on light surfaces
and FAILS as text on them; BRAND_DARK_GOLD_DEEP #7e6529 is the derivative that
exists for text, and the palettes name it `accent_ink` -- "Accent when it
carries text". In DARK MODE THE TWO ARE THE SAME VALUE, so every check written
where they coincide is blind to the case where they diverge, and that is
exactly what happened: gold-as-text sites shipped in light mode at 3.71 and
4.17 against a 4.5 floor, in more than one application, for as long as the
dialogs have existed.

WHAT IT DOES. Reads every f-string in the source, pulls `color:` and
`background-color:` out of each QSS rule, resolves the placeholders through
this app's own palettes, and measures. A declaration whose foreground is a
gold-family value and whose contrast falls below the floor fails.

WHAT IT CANNOT SEE, stated because a sweep that reports only what it found
looks identical to one that found nothing:

  - a placeholder that is not a palette lookup, a module constant or a local
    bound to one is UNRESOLVED and skipped
  - a rule with no background-color of its own INHERITS, and the ground is
    taken from the palette's window or panel value, which is a guess

Both counts are asserted rather than printed: if the resolved count collapses,
the sweep has gone blind and says so instead of passing.

READING THE MODE. A block written inside `if self._is_dark:` and bound with
`_d = ThemeManager.DARK_THEME` is dark-only, and scoring it against the light
palette invents a pairing that never renders. Declarations are restricted to
the mode their variable came from. The first version of this sweep, without
that, reported five impossible failures including gold on #333333 at 2.78.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

from utils import config as colors
from utils.config import ThemeManager

ROOT = pathlib.Path(__file__).resolve().parents[1]

TEXT_FLOOR = 4.5
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')
BLOCK = re.compile(r'([^{}\n][^{}]*?)\{\{(.*?)\}\}', re.S)
DECL = re.compile(r'(?<!-)\bcolor\s*:\s*([^;\n]+)')
BGDECL = re.compile(r'background-color\s*:\s*([^;\n]+)')
LOOKUP = re.compile(r"^\{\s*([A-Za-z_][A-Za-z_0-9]*)\s*\[\s*['\"]([a-z_0-9]+)['\"]\s*\]\s*\}$")
#: `{t.get('tab_selected_bg', bg)}` is a lookup wearing a fallback. Reading it
#: as unresolvable made the sweep guess the ground from the palette and score
#: rnv-color-mixer's selected tab at 4.1670 when it actually sits on #ffffff
#: and clears at 4.5429 -- a failure that does not exist.
GETLOOKUP = re.compile(
    r"^\{\s*([A-Za-z_][A-Za-z_0-9]*)\s*\.get\(\s*['\"]([a-z_0-9]+)['\"]\s*(?:,.*)?\)\s*\}$",
    re.S)
BARE = re.compile(r'^\{\s*([A-Za-z_][A-Za-z_0-9]*)\s*\}$')

MODE_MARKERS = (('DARK', ('DARK_THEME', '.DARK', 'DARK_THEME_COLORS')),
                ('LIGHT', ('LIGHT_THEME', '.LIGHT', 'LIGHT_THEME_COLORS')),
                ('IMAGE', ('IMAGE_THEME', '.IMAGE', 'IMAGE_MODE_COLORS')))

#: mode -> the live palette.
PALETTES = {'DARK': ThemeManager.DARK_THEME,
            'LIGHT': ThemeManager.LIGHT_THEME,
            'IMAGE': ThemeManager.IMAGE_THEME}

#: Keys tried, in order, when a rule inherits its ground.
GROUND_KEYS = ('panel_bg', 'window_bg', 'panel_secondary')

#: Declarations that are below the floor and are CORRECT ANYWAY, keyed by the
#: declaration text rather than by line number -- an edit above a site shifts
#: its line and would silently un-review it, while the declaration itself is
#: stable. Same form as REVIEWED in tests/test_brand_contrast.py.
#:
#: An entry here is an exemption, so it has to earn its place twice: the
#: reason must be true, and test_no_exemption_has_outlived_its_reason below
#: fails when the site it names has stopped failing, so a fix cannot leave a
#: licence standing behind it.
ACCEPTED: dict[str, str] = {}

#: Below this, the sweep has stopped finding things and is passing for the
#: wrong reason.
#:
#: 8, not the 20 that rnv-color-picker and rnv-icon-builder use. This is the
#: smallest of the five applications for gold: it resolves 14 gold-as-text
#: pairs and 2 gold fills, where the picker resolves 63 and 48 and the icon
#: builder 91 and 47. 8 is what rnv-text-transformer and rnv-color-mixer
#: already use, and it leaves this app six sites of headroom -- enough that
#: ordinary editing does not trip it, low enough that a collapse to nothing
#: still does.
MIN_RESOLVED = 8


def _luminance(value: str) -> float:
    channels = [int(value.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


#: Names that contain GOLD and are not a gold. GOLD_TEXT_GROUND_FLOOR is the
#: light GROUND the gold family is calibrated against -- #e8e8e8 -- and a
#: name-based sweep swept it into the family, after which every disabled
#: control drawn on it was reported as gold-on-gold at 1.8960. Those pairs are
#: real and already exempt as WCAG-exempt disabled text; they are not gold.
#: Match what the name CLAIMS, not the substring it contains.
NOT_A_GOLD = ('GROUND', 'FLOOR', 'RGB')


def _golds() -> set:
    """Every gold-family value this app holds, by name rather than by list."""
    out = set()
    for name in dir(colors):
        if 'GOLD' not in name or any(w in name for w in NOT_A_GOLD):
            continue
        value = getattr(colors, name)
        if isinstance(value, str) and HEX.match(value):
            out.add(value.lower())
    return out


def _fstrings(source: str):
    """(lineno, text, local bindings) for every f-string mentioning a colour.

    Read through ast.JoinedStr, NOT the token stream. Python 3.12 splits an
    f-string into FSTRING_START/MIDDLE/END tokens (PEP 701) rather than one
    STRING token, so a tokenising version finds every f-string on 3.11 and none
    on 3.12 -- reporting zero sites, which reads as clean and is blind.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out, seen = [], set()
    #: INNERMOST SCOPE FIRST. `ast.walk` yields the Module before the functions
    #: inside it, and walking the Module collects assignments from EVERY
    #: function in the file -- last one wins. Since `seen` gives each f-string
    #: to whichever scope reaches it first, the Module used to claim them all
    #: with file-global bindings.
    #:
    #: That is harmless where an application builds both stylesheets in one
    #: function with an if/else, because the bindings agree. It is not harmless
    #: in rnv-color-palette-manager, which has _get_style_dark() and
    #: _get_style_light() as separate functions: the dark block's
    #: `pressed_text = TRUE_BLACK` was resolved as the light block's
    #: `pressed_text = WHITE`, and the sweep reported four failures --
    #: white-on-gold at 1.85 in DARK -- that cannot render.
    #:
    #: Sorting by depth, deepest first, makes the nearest enclosing function
    #: claim its own f-strings and leaves the Module only what sits outside
    #: every function.
    depth = {id(tree): 0}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            depth[id(child)] = depth.get(id(parent), 0) + 1
    scopes = sorted(
        (n for n in ast.walk(tree)
         if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef))),
        key=lambda n: depth.get(id(n), 0), reverse=True)
    for scope in scopes:
        binds = {}
        for node in ast.walk(scope):
            #: AN ALIASED IMPORT IS A BINDING. rnv-color-palette-manager binds
            #: its palette with a lazy import inside each style function --
            #: `from ui.colors import LIGHT_THEME_COLORS as colors` -- to break
            #: a circular dependency. Reading only Assign missed that, so a
            #: light-only block's `{accent_dark}` resolved to a bare local with
            #: no mode marker in it, the mode reader fell back to all three,
            #: and the sweep scored a light stylesheet against the dark palette.
            #: The marker was there; it was on the import line.
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.asname:
                        binds[alias.asname] = alias.name
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                try:
                    binds[node.targets[0].id] = ast.unparse(node.value)
                except Exception:
                    continue
        for node in ast.walk(scope):
            if not isinstance(node, ast.JoinedStr):
                continue
            segment = ast.get_source_segment(source, node)
            if not segment or 'color' not in segment:
                continue
            key = (node.lineno, segment[:80])
            if key in seen:
                continue
            seen.add(key)
            out.append((node.lineno, segment, dict(binds)))
    return out


def _resolve(expr: str, palette: dict, binds: dict):
    expr = expr.strip()
    match = BARE.match(expr)
    if match and match.group(1) in binds:
        expr = '{' + binds[match.group(1)] + '}'
    if HEX.match(expr):
        return expr.lower()
    match = LOOKUP.match(expr) or GETLOOKUP.match(expr)
    if match:
        value = palette.get(match.group(2))
        return value.lower() if isinstance(value, str) and HEX.match(value) else None
    match = BARE.match(expr)
    if match:
        value = getattr(colors, match.group(1), None)
        return value.lower() if isinstance(value, str) and HEX.match(value) else None
    return None


def _modes_for(expr: str, binds: dict):
    expr = expr.strip()
    #: Expand a bare local through the bindings FIRST, the way _resolve does.
    #: Without this, `{accent_dark}` is not a lookup, so the mode reader gave
    #: up and returned all three -- and a light-only stylesheet got scored
    #: against the dark palette. The two readers have to agree about what an
    #: expression is, or the value comes from one palette and the mode from
    #: another.
    match = BARE.match(expr)
    if match and match.group(1) in binds:
        expr = '{' + binds[match.group(1)] + '}'
    match = LOOKUP.match(expr) or GETLOOKUP.match(expr)
    if not match:
        return list(PALETTES)
    bound = binds.get(match.group(1), '')
    for mode, markers in MODE_MARKERS:
        if any(marker in bound for marker in markers):
            return [mode] if mode in PALETTES else []
    return list(PALETTES)


#: Rules whose background is what an unstyled child sits on.
CONTAINER_SELECTORS = ('body', '*', 'QDialog', 'QWidget', 'QFrame', 'QMainWindow')


def _enclosing_ground(text: str, palette: dict, binds: dict):
    """The ground an inheriting rule actually sits on: the background painted
    by the container rule in the same stylesheet."""
    for selector, body in BLOCK.findall(text):
        name = ' '.join(selector.split())
        if not any(name == c or name.startswith(c + ' ') or name.startswith(c + ',')
                   for c in CONTAINER_SELECTORS):
            continue
        decl = BGDECL.search(body)
        if decl:
            resolved = _resolve(decl.group(1), palette, binds)
            if resolved:
                return resolved
    return None


#: Qt sub-controls that PAINT rather than draw text. A scrollbar handle, a
#: progress-bar chunk and a checkbox indicator carry no label, so inheriting a
#: foreground onto them invents a pairing that never renders.
#:
#: The first version of this sweep did exactly that and reported eleven
#: failures in rnv-text-transformer -- APP_TEXT on the brand gold at 1.3616,
#: on scrollbar handles and progress chunks. Every one impossible.
#:
#: Not every sub-control is textless: ::item, ::tab, ::section and ::title all
#: draw labels, which is why this is a list and not a rule about `::`. The
#: form and the first seven entries are taken from
#: tests/test_contrast_pairs.py, which already had to make this distinction.
TEXTLESS = ('add-line', 'add-page', 'corner', 'down-button', 'drop-down', 'groove', 'handle', 'indicator', 'separator', 'sub-line', 'sub-page', 'up-button')


def _is_textless(selector: str) -> bool:
    if '::' not in selector:
        return False
    part = selector.split('::', 1)[1]
    name = re.split(r'[:\[ ,]', part)[0].strip()
    return name in TEXTLESS


def _enclosing_label(text: str, palette: dict, binds: dict):
    """The label an inheriting rule actually draws: the `color:` declared by
    the container rule in the same stylesheet.

    A fill rule often sets only a background -- `QPushButton:hover { background
    -color: ... }` -- and the label comes from the base `QPushButton` rule.
    Reading it is what makes the fill direction checkable at all: six of the
    ten gold fills across these apps declare no colour of their own.
    """
    for selector, body in BLOCK.findall(text):
        name = ' '.join(selector.split())
        if ':' in name or '::' in name:
            continue          # a state rule, not the base it inherits from
        decl = DECL.search(body)
        if decl:
            resolved = _resolve(decl.group(1), palette, binds)
            if resolved:
                return resolved
    return None


def _fill_sweep():
    """(key, mode, label, fill, ratio, where) for every rule whose BACKGROUND
    is a gold-family value, with the label drawn on it."""
    rows, unresolved = [], 0
    golds = _golds()
    for path in sorted(ROOT.rglob('*.py')):
        if any(part in {'.git', 'tests', 'build'} for part in path.parts):
            continue
        if path.name == 'up.py':
            continue
        source = path.read_text(encoding='utf-8-sig', errors='replace')
        if 'background-color' not in source:
            continue
        for lineno, text, binds in _fstrings(source):
            for selector, body in BLOCK.findall(text):
                bg_decl = BGDECL.search(body)
                if not bg_decl:
                    continue
                fg_decl = DECL.search(body)
                key = f'{path.relative_to(ROOT)} :: {" ".join(bg_decl.group(0).split())}'
                modes = _modes_for(bg_decl.group(1), binds)
                if fg_decl is not None:
                    modes = [m for m in modes
                             if m in _modes_for(fg_decl.group(1), binds)]
                for mode in modes:
                    palette = PALETTES[mode]
                    fill = _resolve(bg_decl.group(1), palette, binds)
                    if fill is None:
                        unresolved += 1
                        continue
                    if fill not in golds:
                        continue
                    label = (_resolve(fg_decl.group(1), palette, binds)
                             if fg_decl is not None else None)
                    if label is None and fg_decl is not None:
                        #: A DECLARED COLOUR THIS READER CANNOT PARSE IS NOT AN
                        #: ABSENT ONE. rnv-color-palette-manager writes
                        #: `color: {WHITE if is_light else TRUE_BLACK}` on its
                        #: pressed gold button -- correct in both modes, 6.03:1
                        #: in dark. The resolver does not read conditionals, so
                        #: the label came back None, fell through to the
                        #: container rule below, and the sweep reported black
                        #: text as #dddddd at 1.36 in two files.
                        #:
                        #: Inheriting is only right where the rule declares
                        #: NOTHING. Where it declares something unreadable, the
                        #: honest answer is "unresolved" -- counted, and visible
                        #: in the count that test_the_sweep_still_finds_things
                        #: guards, rather than turned into a failure that cannot
                        #: render.
                        unresolved += 1
                        continue
                    if label is None:
                        if _is_textless(selector):
                            # A painted sub-control. It has no label to
                            # inherit, and giving it one manufactures a
                            # failure that cannot render.
                            continue
                        label = _enclosing_label(text, palette, binds)
                    if label is None:
                        # No text is drawn here that this reader can find --
                        # a checkbox indicator or a progress chunk. Counted,
                        # not guessed at.
                        unresolved += 1
                        continue
                    rows.append((key, mode, label, fill, _contrast(label, fill),
                                 f'{path.relative_to(ROOT)}:{lineno} '
                                 f'{" ".join(selector.split())}'))
    return rows, unresolved


def _sweep():
    """(key, mode, fg, bg, ratio, where) for every resolved gold-as-text pair,
    plus the count of declarations that could not be resolved."""
    rows, unresolved = [], 0
    golds = _golds()
    for path in sorted(ROOT.rglob('*.py')):
        if any(part in {'.git', 'tests', 'build'} for part in path.parts):
            continue
        if path.name == 'up.py':
            continue
        source = path.read_text(encoding='utf-8-sig', errors='replace')
        if 'color:' not in source:
            continue
        for lineno, text, binds in _fstrings(source):
            for selector, body in BLOCK.findall(text):
                fg_decl = DECL.search(body)
                if not fg_decl:
                    continue
                bg_decl = BGDECL.search(body)
                key = f'{path.relative_to(ROOT)} :: {" ".join(fg_decl.group(0).split())}'
                modes = _modes_for(fg_decl.group(1), binds)
                if bg_decl is not None:
                    modes = [m for m in modes
                             if m in _modes_for(bg_decl.group(1), binds)]
                for mode in modes:
                    palette = PALETTES[mode]
                    fg = _resolve(fg_decl.group(1), palette, binds)
                    if fg is None:
                        unresolved += 1
                        continue
                    if fg not in golds:
                        continue
                    bg = (_resolve(bg_decl.group(1), palette, binds)
                          if bg_decl is not None else None)
                    if bg is None:
                        # INHERITANCE, in three steps, most specific first.
                        # A rule with no ground of its own sits on whatever the
                        # enclosing rule painted -- usually `body` or the
                        # top-level widget in the SAME stylesheet. Reading that
                        # is the difference between measuring what renders and
                        # measuring a guess: rnv-text-transformer's exported
                        # h1 inherits #ffffff from `body` and clears at 4.5429,
                        # and a palette guess of #f5f5f5 scored it 4.1670 and
                        # called it a failure.
                        bg = _enclosing_ground(text, palette, binds)
                    if bg is None:
                        for candidate in GROUND_KEYS:
                            value = palette.get(candidate)
                            if isinstance(value, str) and HEX.match(value):
                                bg = value.lower()
                                break
                    if bg is None:
                        unresolved += 1
                        continue
                    rows.append((key, mode, fg, bg, _contrast(fg, bg),
                                 f'{path.relative_to(ROOT)}:{lineno} {" ".join(selector.split())}'))
    return rows, unresolved


# ------------------------------------------------------------- guard the guard

def test_the_sweep_still_finds_things():
    """Every assertion below reads this sweep. One that resolves nothing
    reports no failures and passes -- which is what a blind check looks like
    from the outside."""
    rows, _ = _sweep()
    assert len(rows) >= MIN_RESOLVED, (
        f'only {len(rows)} gold-as-text pairs resolved, expected at least '
        f'{MIN_RESOLVED}. Either the QSS moved out of f-strings or the '
        f'resolver stopped following it. A sweep that finds nothing is not a '
        f'clean sweep.')


def test_the_gold_family_is_not_empty():
    """The sweep filters on this set. Empty, it matches nothing."""
    golds = _golds()
    assert len(golds) >= 3, f'only {sorted(golds)} found as gold values'


def test_the_two_golds_actually_differ_in_light():
    """The premise of this whole file. If accent and accent_ink ever hold the
    same value in light mode, the distinction it enforces has gone and the
    tests below would pass without meaning anything."""
    light = PALETTES.get('LIGHT')
    if light is None or 'accent' not in light or 'accent_ink' not in light:
        pytest.skip('this app does not name accent and accent_ink')
    assert light['accent'] != light['accent_ink'], (
        'accent and accent_ink are the same value in light mode. In dark they '
        'legitimately are; in light the whole point is that they are not.')


# ------------------------------------------------------------------- the floor

def test_no_gold_is_drawn_as_text_below_the_floor():
    rows, _unresolved = _sweep()
    failures = []
    for key, mode, fg, bg, ratio, where in rows:
        if ratio >= TEXT_FLOOR or key in ACCEPTED:
            continue
        failures.append(f'{ratio:.4f}  {mode}  {fg} on {bg}  {where}')
    assert not failures, (
        'gold drawn as text below the 4.5 floor:\n  ' + '\n  '.join(sorted(failures))
        + '\n\nThe palette names a derivative for this: accent_ink. In dark it '
          'is the same value as accent, which is why the difference only shows '
          'in light.')


def test_no_exemption_has_outlived_its_reason():
    """An exemption whose site has stopped failing is a licence with no
    subject -- it would let a future regression at the same declaration pass
    unseen. Fixing a site means deleting its entry in the same commit."""
    rows, _unresolved = _sweep()
    failing = {key for key, _m, _f, _b, ratio, _w in rows if ratio < TEXT_FLOOR}
    stale = sorted(set(ACCEPTED) - failing)
    assert not stale, (
        'these ACCEPTED entries no longer describe a failing site:\n  '
        + '\n  '.join(stale)
        + '\n\nDelete the entry in the commit that fixed it.')


# ------------------------------------------------------- the other direction

def test_no_gold_fill_carries_a_label_below_the_floor():
    """THE OTHER HALF OF THE RULE, and it is not symmetric.

    rnv-brand rev 25 publishes it bidirectionally:

        On a light ground, gold as TEXT is BRAND_DARK_GOLD_DEEP.
        Gold as a FILL or an EDGE is BRAND_DARK_GOLD.

    The second sentence is not politeness. BRAND_DARK_GOLD_DEEP is derived for
    text and FAILS the fill job -- black on it reads 3.7806 against a 4.5
    floor, where BRAND_DARK_GOLD reads 4.6226. So a sweep that replaced every
    BRAND_DARK_GOLD with the derivative, reading the rule as "prefer DEEP",
    would fix the text sites and break the fills.

    Nothing fails this today, in any of the five applications. That is the
    reason to arm it now: a guard proposed against a live defect writes
    itself, and a guard proposed against a clean sweep gets harder to justify
    every month the sweep stays clean.
    """
    rows, _unresolved = _fill_sweep()
    failures = []
    for key, mode, label, fill, ratio, where in rows:
        if ratio >= TEXT_FLOOR or key in ACCEPTED:
            continue
        failures.append(f'{ratio:.4f}  {mode}  {label} on {fill}  {where}')
    assert not failures, (
        'a label falls below the floor on a gold fill:\n  '
        + '\n  '.join(sorted(failures))
        + '\n\nA FILL takes BRAND_DARK_GOLD, not the text derivative. Black '
          'on the derivative is 3.7806.')


def test_the_fill_sweep_still_finds_things():
    """Guard the guard, on the half with no failures. A sweep over a clean
    codebase and a sweep that resolves nothing produce the same report, and
    this is the only thing that tells them apart."""
    rows, _unresolved = _fill_sweep()
    assert rows, (
        'no gold fills resolved at all. Either this app draws none -- in '
        'which case delete this test rather than leave it passing over '
        'nothing -- or the resolver has stopped following the expressions '
        'that reach them.')


def test_every_textless_entry_is_a_real_sub_control():
    """TEXTLESS is an exclusion list, so it is an exemption: an entry that
    names nothing excludes nothing, and one that names a sub-control which
    actually draws text excludes a site that should be checked.

    Only the first half can be asserted -- that every entry appears as a
    `::name` somewhere in this app's stylesheets. Whether a sub-control draws
    text is a fact about Qt, not about this repository, and it lives in the
    comment beside the list.
    """
    seen = set()
    for path in ROOT.rglob('*.py'):
        if any(part in {'.git', 'build'} for part in path.parts):
            continue
        source = path.read_text(encoding='utf-8-sig', errors='replace')
        for match in re.finditer(r'::([a-z][a-z-]*)', source):
            seen.add(match.group(1))
    stale = [name for name in TEXTLESS if name not in seen]
    assert not stale, (
        f'TEXTLESS names sub-controls this app never styles: {stale}. An '
        f'exclusion that excludes nothing is a licence with no subject -- '
        f'delete it, or find out why the sub-control went away.')
'''


POINTER = (
    "\n"
    "# RNV-GOLD-GUARD (2026-09-07): the values below are swept by\n"
    "# tests/test_gold_as_text.py, which resolves every QSS f-string in this\n"
    "# repository through these palettes and measures the gold family as text\n"
    "# and as a fill. A gold that reads correctly here can still be drawn on\n"
    "# the wrong ground three files away, and that is what it is for.\n")


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL in src:
        raise SystemExit("already applied")
    # One pointer comment, at the end of the module. The palette file is where
    # someone changes a gold; the guard is two directories away and they will
    # not find it by accident.
    tree.write(SENTINEL_FILE, src.rstrip("\n") + "\n" + POINTER)
    print(f"  {'installed' if IS_NEW else 'updated'} {GUARD}")
    print("  one pointer comment added to " + SENTINEL_FILE)


def checks(tree) -> None:
    guard = tree.read(GUARD)
    for marker in ("INNERMOST SCOPE FIRST",
                   "AN ALIASED IMPORT IS A BINDING",
                   "Expand a bare local",
                   "A DECLARED COLOUR THIS READER CANNOT PARSE"):
        if marker not in guard:
            raise SystemExit(f"the guard is missing the fix marked {marker!r}")
    # the sweep must have a subject: PALETTES has to name things the import
    # block actually provides, which is the check whose absence let an earlier
    # build of this script ship a file that could not be collected.
    head = guard[:guard.index("ROOT =")]
    pal = re.search(r"^PALETTES = \{.*?\}$", guard, re.M | re.S).group(0)
    used = {n.id for n in ast.walk(ast.parse(pal))
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    missing = sorted(n for n in used if n not in head)
    if missing:
        raise SystemExit(f"PALETTES uses {missing}, which the guard's import "
                         f"block does not provide")
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise SystemExit("the pointer comment did not land")
    print("  guards: four resolver fixes present, PALETTES fully imported, "
          "pointer landed")


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
