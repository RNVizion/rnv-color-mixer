"""Gold drawn as TEXT must clear the text floor on the ground it is drawn on.

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
    scopes = [n for n in ast.walk(tree)
              if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef))]
    for scope in scopes:
        binds = {}
        for node in ast.walk(scope):
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
