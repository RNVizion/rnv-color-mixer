"""Derived values: a colour that is a named colour AT AN ALPHA.

The three stylesheet templates were made literal-free for HEX on 2026-09-06 --
tests/test_neutral_ramp.py holds that -- and eleven rgba() literals stayed
behind, because a hex sweep cannot see them. rgba(26, 26, 26, 191) IS
APP_SURFACE_DARK at alpha 191; written out, a move of APP_SURFACE_DARK would
have reached every opaque use and none of these. Each is now
translucent_rgba(BASE, ALPHA) inside the template. The palettes' three
checkbox grounds were translucent(BASE, ALPHA) too, until a render proved
nothing read them and they were removed -- RNV-CHART-RULINGS, 2026-09-26,
which also moved the control panel's hand-sliced harmony wash onto
translucent(). Both are held at the end of this file.

WHY TWO SPELLINGS, AND WHERE EACH IS ALLOWED. rgba() is valid in a stylesheet
and INVALID in QColor(), which reads it as opaque black. So rgba() is allowed
only INSIDE a stylesheet template -- where a value can never travel to a
QColor -- and the locked suite needs it there (test_image_stylesheet_rgba).
Everywhere else a derived value is #aarrggbb, which both accept.

WHAT MOVES A PIXEL: ONE THING, BY RULING. The image scrollbar handle leaves
#505050 for APP_CHROME_DARK -- grey(4), #444444, the GREY_44 of the ruling --
at the same alpha, 150. The dark handle's rgba(51, 51, 51, 0.7) is respelled
with the byte Qt makes of 0.7, 178, MEASURED through Qt's stylesheet parser on
three grounds; the same pixels. Everything else renders byte for byte as
before, and tests/test_snapshots.py still compares all three sheets whole.
"""
from __future__ import annotations

import ast
import pathlib
import re

from utils import config as C

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "utils" / "config.py"
PALETTES = ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME")
TEMPLATES = ("DARK_STYLESHEET", "LIGHT_STYLESHEET", "IMAGE_STYLESHEET")
HELPERS = ("translucent", "translucent_rgba")

#: constant -> the byte. Each is the alpha its literal already carried; the
#: dark handle's is the byte Qt MEASURES for 0.7 (0.7 * 255 = 178.5, and Qt
#: gives 178 -- the same on #1a1a1a, #ffffff and #d2bc93 grounds).
ALPHAS = {
    "SCROLLBAR_HANDLE_ALPHA_DARK": 0xB2,
    "SCROLLBAR_HANDLE_ALPHA": 0x96,
    "SCROLLBAR_BG_ALPHA": 0x64,
    "SCROLL_AREA_BORDER_ALPHA": 0x64,
    "IMAGE_FIELD_ALPHA": 0xAB,
    "STATUS_BAR_ALPHA": 0xC8,
    "IMAGE_CHECKBOX_ALPHA": 0x64,
    "COMBO_ALPHA": 0xBF,
    "HARMONY_DESCRIPTION_ALPHA": 0x19,
}

#: What each template's derived values are MADE OF, by NAME: (base, alpha).
#: A register move passes through; a value re-made from something else fails.
MADE_OF = {
    "DARK_STYLESHEET": [("APP_BORDER_DARK", "SCROLLBAR_HANDLE_ALPHA_DARK")] * 2,
    "LIGHT_STYLESHEET": [],
    "IMAGE_STYLESHEET": sorted(
        [("TRUE_BLACK", "IMAGE_FIELD_ALPHA"),
         ("APP_BORDER_DARK", "SCROLL_AREA_BORDER_ALPHA")]
        + [("APP_BORDER_DARK", "SCROLLBAR_BG_ALPHA")] * 2
        + [("APP_CHROME_DARK", "SCROLLBAR_HANDLE_ALPHA")] * 2       # ruled
        + [("APP_SURFACE_DARK", "STATUS_BAR_ALPHA"),
           ("TRUE_BLACK", "IMAGE_CHECKBOX_ALPHA")]
        + [("APP_SURFACE_DARK", "COMBO_ALPHA")] * 2),
}
#: The palettes hold no derived value now. Their only ones were the three
#: checkbox_bg grounds, which nothing read; see REMOVED_KEYS below.
PALETTE_MADE_OF: dict[str, tuple[str, str]] = {}

#: Diagnostic, and so outside the brand by rule: the debug overlay must read on
#: any window whatever the theme.
DIAGNOSTIC_FILES = {"ui/debug_overlay.py"}
DIAGNOSTIC_FUNCTIONS = {"_create_debug_overlays"}
DIAGNOSTIC_NAMES = {"DEBUG_OVERLAY_COLORS"}

_HEX8 = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{6})$")
_RGBA = re.compile(r"rgba\((\d{1,3}), (\d{1,3}), (\d{1,3}), (\d{1,3})\)")
_COMPOSED = re.compile(r"#[0-9a-fA-F]{8}\b|\brgba\(\s*\d{1,3}\s*,\s*\d{1,3}"
                       r"\s*,\s*\d{1,3}\s*,\s*[0-9]*\.?[0-9]+\s*\)")
_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_FUNC = re.compile(r"\brgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
                   r"\s*(?:,\s*[0-9]*\.?[0-9]+\s*)?\)")
SKIP_DIRS = {".git", "tests", "snapshots", "build", "dist", ".venv", "venv",
             "__pycache__"}


def decompose(value: str) -> tuple[str, int] | None:
    """(base '#rrggbb', alpha byte) -- taken apart, never rebuilt."""
    m = _HEX8.match(value)
    if m:
        return "#" + m.group(2).lower(), int(m.group(1), 16)
    m = _RGBA.fullmatch(value)
    if m:
        r, g, b, a = (int(x) for x in m.groups())
        return "#%02x%02x%02x" % (r, g, b), a
    return None


def _parts_of(spelled: str) -> tuple[str, int]:
    if spelled.startswith("#"):
        return "#" + spelled[3:].lower(), int(spelled[1:3], 16)
    numbers = re.findall(r"[0-9]*\.?[0-9]+", spelled)
    r, g, b = (int(x) for x in numbers[:3])
    a = numbers[3]
    return "#%02x%02x%02x" % (r, g, b), (int(float(a) * 255) if "." in a
                                         else int(a))


def colours_in(text: str) -> set[str]:
    found = set()
    for m in _HEX.finditer(text):
        h = m.group(0)[1:].lower()
        h = h[2:] if len(h) == 8 else ("".join(c * 2 for c in h) if len(h) == 3 else h)
        found.add("#" + h)
    for m in _FUNC.finditer(text):
        channels = [int(g) for g in m.groups()]
        if all(c <= 255 for c in channels):
            found.add("#%02x%02x%02x" % tuple(channels))
    return found


def _module() -> ast.Module:
    return ast.parse(SRC.read_text(encoding="utf-8-sig"))


def _palette_nodes() -> dict[str, ast.Dict]:
    cls = next(n for n in _module().body
               if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")
    out = {}
    for node in cls.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(t, "id", None) in PALETTES and isinstance(node.value, ast.Dict):
                out[t.id] = node.value
    return out


def _template_calls(tree: ast.Module | None = None) -> dict[str, list[ast.Call]]:
    """The helper calls inside each stylesheet template, in source order.
    Pass the tree when the caller compares node identities: two parses of one
    file are two sets of objects, and an id() from one never matches the
    other -- which is how the first version of the rgba check below flagged
    all twelve calls as outside the templates they sat in."""
    out = {}
    for node in (tree or _module()).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(t, "id", None) in TEMPLATES:
                out[t.id] = [c for c in ast.walk(node.value)
                             if isinstance(c, ast.Call)
                             and getattr(c.func, "id", None) in HELPERS]
    return out


def _names(call: ast.Call) -> tuple[str, str] | None:
    if len(call.args) == 2 and all(isinstance(a, ast.Name) for a in call.args):
        return call.args[0].id, call.args[1].id
    return None


def _bare_strings(tree: ast.AST) -> set[int]:
    bare = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for st in body:
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
                    bare.add(id(st.value))
    return bare


def _sources():
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        yield rel, ast.parse(text)


# ------------------------------------------------------------ guard the guard

def test_the_helpers_compose_alpha_first_and_agree():
    assert C.translucent("#1a1a1a", 0xBF) == "#bf1a1a1a"
    assert C.translucent_rgba("#1a1a1a", 0xBF) == "rgba(26, 26, 26, 191)"
    for base in ("#1a1a1a", "#d2bc93", "#444444"):
        for alpha in (0, 0x64, 0xB2, 255):
            assert (decompose(C.translucent(base, alpha))
                    == decompose(C.translucent_rgba(base, alpha))
                    == (base, alpha))


def test_the_helpers_refuse_what_they_cannot_compose():
    for helper in (C.translucent, C.translucent_rgba):
        for bad in (-1, 256, 0.7, True):
            try:
                helper("#1a1a1a", bad)
            except (ValueError, TypeError):
                pass
            else:
                raise AssertionError(f"{helper.__name__} took alpha {bad!r}")
        for bad in ("#1a1a1", "#1a1a1a1a", "nonsense", "#gggggg"):
            try:
                helper(bad, 0xBF)
            except ValueError:
                pass
            else:
                raise AssertionError(f"{helper.__name__} took base {bad!r}")


def test_the_alphas_are_the_declared_bytes():
    for name, byte in ALPHAS.items():
        assert hasattr(C, name), f"utils.config has no {name}"
        value = getattr(C, name)
        assert type(value) is int, f"{name} is {value!r}, not an int byte"
        assert value == byte, f"{name} is {value:#x}, declared {byte:#x}"


def test_the_derivation_sweep_is_looking():
    calls = _template_calls()
    assert set(calls) == set(TEMPLATES), sorted(calls)
    assert sum(len(v) for v in calls.values()) == 12, (
        {k: len(v) for k, v in calls.items()})
    palettes = _palette_nodes()
    assert set(palettes) == set(PALETTES)
    derived = [k.value for p in palettes.values() for k, v in zip(p.keys, p.values)
               if isinstance(v, ast.Call)
               and getattr(v.func, "id", None) in HELPERS]
    # The three checkbox_bg grounds were the palettes' only derived values,
    # and nothing read them. Removed 2026-09-26 (RNV-CHART-RULINGS).
    assert derived == [], derived


# ----------------------------------------------------------- the derivations

def test_every_derived_value_names_constants_that_exist():
    bad = []
    everything = [(f"{t}#{i}", c) for t, calls in _template_calls().items()
                  for i, c in enumerate(calls)]
    everything += [(f"{p}[{k.value!r}]", v) for p, d in _palette_nodes().items()
                   for k, v in zip(d.keys, d.values)
                   if isinstance(v, ast.Call) and getattr(v.func, "id", None) in HELPERS]
    for where, call in everything:
        names = _names(call)
        if names is None or call.keywords:
            bad.append(f"{where}: {ast.unparse(call)} is not (BASE, ALPHA) by name")
            continue
        base, alpha = names
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(getattr(C, base, ""))):
            bad.append(f"{where}: {base} is not a six-digit colour in utils.config")
        if alpha not in ALPHAS:
            bad.append(f"{where}: {alpha} is not a declared composite alpha")
    assert not bad, "derived values that do not derive:\n  " + "\n  ".join(bad)


def test_rgba_is_spelled_only_inside_the_templates():
    """translucent_rgba() anywhere but a stylesheet template is a value that
    can reach QColor(), which reads rgba() as opaque black. And the pin that
    requires rgba() in IMAGE_STYLESHEET is re-read from the locked suite, so
    the reason outlives nothing."""
    tree = _module()
    inside = {id(c) for calls in _template_calls(tree).values() for c in calls}
    assert len(inside) == 12, f"the template sweep sees {len(inside)} calls"
    stray = [f"line {n.lineno}" for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "translucent_rgba"
             and id(n) not in inside]
    assert not stray, f"translucent_rgba() outside a stylesheet template: {stray}"
    locked = (ROOT / "test_rnv_color_mixer.py").read_text(encoding="utf-8-sig")
    assert 'self.assertIn("rgba(",config.IMAGE_STYLESHEET)' in locked


def test_every_template_value_decomposes_to_what_it_is_made_of():
    """The rendered sheet, TAKEN APART: every rgba() in it, read back to a
    (base, alpha) pair, must be exactly the multiset its calls name -- by the
    constants' values now, so a register move passes straight through."""
    for template, made_of in MADE_OF.items():
        rendered = getattr(C, template)
        found = sorted((("#%02x%02x%02x" % (int(r), int(g), int(b))), int(a))
                       for r, g, b, a in _RGBA.findall(rendered))
        want = sorted((getattr(C, base).lower(), getattr(C, alpha))
                      for base, alpha in made_of)
        assert found == want, f"{template}: rendered {found}, made of {want}"


def test_nothing_moved_that_was_not_ruled():
    """Held BY NAME: each template call's (base, alpha) names are what this
    round made them. A value re-made from another constant fails here even
    when the sheet still agrees with its own source. The byte-for-byte
    before-and-after is tests/test_snapshots.py, which compares all three
    rendered sheets whole. The palettes carried three derived entries
    until 2026-09-26; the test that holds them removed is below."""
    for template, made_of in MADE_OF.items():
        names = sorted(_names(c) for c in _template_calls()[template])
        assert names == sorted(made_of), f"{template}: {names}"
    assert not PALETTE_MADE_OF, "a palette entry is derived again: hold it here"


def test_the_image_scrollbar_handle_is_grey_44_at_150():
    """RNV-COLLAPSE-505050, closed here 2026-09-25: rgba(80, 80, 80, 150) in
    both of IMAGE_STYLESHEET's handles, ruled onto grey(4) on 2026-09-02."""
    handles = re.findall(r"QScrollBar::handle:(?:vertical|horizontal)\s*\{\s*"
                         r"background-color:\s*([^;]+);", C.IMAGE_STYLESHEET)
    assert len(handles) == 2, handles
    for h in handles:
        assert decompose(h.strip()) == ("#444444", 150) == (
            C.APP_CHROME_DARK, C.SCROLLBAR_HANDLE_ALPHA), h


def test_no_composed_literal_is_left_in_the_application():
    """Every EVALUATED string in the application's own source that spells a
    named colour at an alpha. Docstrings are mentions; alpha 0 is not a
    colour; a base no constant names has no row; and the debug overlay is
    diagnostic, outside the brand by rule."""
    named = {v.lower() for n, v in vars(C).items()
             if n.isupper() and isinstance(v, str)
             and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}
    strays, files = [], 0
    for rel, tree in _sources():
        if rel.as_posix() in DIAGNOSTIC_FILES:
            continue
        files += 1
        skip = set(_bare_strings(tree))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name in DIAGNOSTIC_FUNCTIONS:
                skip |= {id(n) for n in ast.walk(node)}
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                t = node.targets[0] if isinstance(node, ast.Assign) else node.target
                if getattr(t, "id", None) in DIAGNOSTIC_NAMES:
                    skip |= {id(n) for n in ast.walk(node)}
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if id(node) in skip:
                continue
            for spelled in _COMPOSED.findall(node.value):
                base, alpha = _parts_of(spelled)
                if alpha and base in named:
                    strays.append(f"{rel}:{node.lineno}  {spelled}")
    # 32 application files on 2026-09-25; below 20 the walk has lost a package.
    assert files >= 20, f"only {files} files swept -- the walk has gone blind"
    assert not strays, ("composed values still written out rather than "
                        "derived:\n  " + "\n  ".join(strays))


def test_the_debug_overlay_stays_outside_the_brand():
    """The exclusion rule, asserted: DEBUG_OVERLAY_COLORS holds literals, and
    no brand constant or helper call appears in it."""
    node = next(n for n in _module().body if isinstance(n, (ast.Assign, ast.AnnAssign))
                and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target,
                            "id", None) == "DEBUG_OVERLAY_COLORS")
    bound = [ast.unparse(v) for v in node.value.values
             if not isinstance(v, ast.Constant)]
    assert not bound, f"the debug overlay follows the application's values: {bound}"
    # ... and nothing rebinds it after the literal: the dict is written before
    # any brand constant exists, so a later assignment is the only way in
    assert C.DEBUG_OVERLAY_COLORS == ast.literal_eval(node.value), (
        "DEBUG_OVERLAY_COLORS is changed after it is written")


def test_the_collapsed_value_is_gone_in_every_spelling():
    found = []
    for rel, tree in _sources():
        bare = _bare_strings(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and id(node) not in bare and "#505050" in colours_in(node.value)):
                found.append(f"{rel}:{node.lineno}")
            values = None
            if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4):
                values = node.elts
            elif isinstance(node, ast.Call) and len(node.args) >= 3 and (
                    getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                    ) in ("QColor", "fromRgb", "QPen", "QBrush"):
                values = node.args
            if values:
                ints = tuple(v.value for v in values[:3]
                             if isinstance(v, ast.Constant) and type(v.value) is int)
                if ints == (80, 80, 80):
                    found.append(f"{rel}:{node.lineno}  (80, 80, 80)")
    assert not found, "#505050 is still here:\n  " + "\n  ".join(found)
    assert "#505050" not in colours_in(C.IMAGE_STYLESHEET)
    assert colours_in("rgba(80, 80, 80, 150)") == {"#505050"}, "the decoder is blind"

# RNV-DERIVE-ALPHA


# ------------------------------------------------- colours spelled in integers

import importlib as _importlib

#: Where the derived constants live, and where their bases and alphas live.
TUPLE_HOME = 'core/screen_color_picker.py'
TUPLE_HOME_MODULE = 'core.screen_color_picker'
TUPLE_BASES_MODULE = 'utils.config'
#: Each derived constant, by NAME: (helper, base, alpha or None). A register
#: move passes straight through; a value re-made from something else fails.
TUPLES_MADE_OF = {'_OVERLAY_COLOR': ('translucent', 'TRUE_BLACK', 'SCREEN_OVERLAY_ALPHA'), '_GOLD_TRANSPARENT': ('translucent', 'BRAND_GOLD', 'SCREEN_GRID_ALPHA'), '_INFO_BG': ('translucent', 'TRUE_BLACK', 'SCREEN_INFO_ALPHA')}
#: The alpha bytes behind them, each the one its literal already carried.
TUPLE_ALPHAS = {'SCREEN_OVERLAY_ALPHA': 50, 'SCREEN_GRID_ALPHA': 50, 'SCREEN_INFO_ALPHA': 180}
#: Module- and class-level constants spelled in integers ON PURPOSE -- data a
#: person starts from, not a brand element -- with the reason.
INT_DATA = {'INITIAL_COLOR_TUPLE': 'the colour shown before anything is mixed -- data, like the hex and rgb() twins beside it',
            # RNV-RULINGS-2026-10-05, item 3: the canvas label's light plate has a name now,
            # CANVAS_LABEL_PLATE_LIGHT, and its value is this one's. They are two things: the
            # plate is the look, and this is data.
            'DEFAULT_COLOR': 'the colour a slot holds until one is set, and what a session file falls back to -- data a person starts from'}
TUPLE_FILES = 20
#: The call each derived constant is wrapped in, if any.
_WRAP = 'QColor'


def _int_spelled(tree):
    """(name, #rrggbb, alpha) for every module- or class-level constant whose
    value spells a colour in integers: a tuple or list of three or four int
    literals, or QColor/QPen/QBrush called with them. Locals inside functions
    are state, not constants, and are not read."""
    bodies = [tree.body] + [n.body for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    for body in bodies:
        for statement in body:
            if (not isinstance(statement, (ast.Assign, ast.AnnAssign))
                    or statement.value is None):
                continue
            target = (statement.targets[0] if isinstance(statement, ast.Assign)
                      else statement.target)
            name, value = getattr(target, "id", None), statement.value
            if isinstance(value, (ast.Tuple, ast.List)):
                elts = value.elts
            elif isinstance(value, ast.Call) and (
                    getattr(value.func, "id", None) or getattr(value.func, "attr", None)
                    ) in ("QColor", "fromRgb", "QPen", "QBrush"):
                elts = value.args
            else:
                continue
            if name is None or len(elts) not in (3, 4):
                continue
            ints = [e.value for e in elts
                    if isinstance(e, ast.Constant) and type(e.value) is int]
            if len(ints) != len(elts) or not all(0 <= i <= 255 for i in ints):
                continue
            yield (name, "#%02x%02x%02x" % tuple(ints[:3]),
                   ints[3] if len(ints) == 4 else 255)


def _tuple_trees():
    """Application source: not tests, not a root test suite, not a delivery
    script. BOM-aware."""
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(p in {".git", "tests", "snapshots", "build", "dist", ".venv",
                     "venv", "__pycache__"} for p in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        yield rel, ast.parse(text)


def _rgb_of(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _as_rgba(value):
    """A tuple as it is; a QColor as its channels."""
    if hasattr(value, "alpha") and callable(value.alpha):
        return (value.red(), value.green(), value.blue(), value.alpha())
    return tuple(value)


def test_the_integer_sweep_reads_both_notations():
    """Guard the guard: a tuple and a QColor at module or class level are
    read; a local inside a function is not."""
    probe = ast.parse("A = (0, 0, 0, 50)\n"
                      "class K:\n    B = QColor(68, 68, 68)\n"
                      "def f():\n    c = (0, 0, 0)\n")
    assert sorted(_int_spelled(probe)) == [("A", "#000000", 50), ("B", "#444444", 255)]


def test_every_tuple_constant_is_derived_by_name():
    """RNV-TUPLE-ROUND, 2026-09-26. A colour spelled in integers is a colour
    every string sweep in the fleet was blind to, and #505050 sat in two of
    them for three weeks after it was ruled away. Each constant here is now
    its helper called on a named base and a named alpha, and it evaluates to
    exactly that pair -- held BY NAME, so a register move passes through."""
    tree = ast.parse((ROOT / TUPLE_HOME).read_text(encoding="utf-8-sig"))
    values = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(t, "id", None):
                values[t.id] = node.value
    home = _importlib.import_module(TUPLE_HOME_MODULE)
    bases = _importlib.import_module(TUPLE_BASES_MODULE)
    assert TUPLES_MADE_OF, "nothing to check"
    for name, (helper, base, alpha) in TUPLES_MADE_OF.items():
        call = values.get(name)
        assert call is not None, f"{name} is gone from {TUPLE_HOME}"
        if _WRAP:
            assert (isinstance(call, ast.Call)
                    and getattr(call.func, "id", None) == _WRAP
                    and len(call.args) == 1), (
                f"{name} is not {_WRAP}(...): {ast.unparse(call)}")
            call = call.args[0]
        want_names = [base] + ([alpha] if alpha else [])
        assert (isinstance(call, ast.Call) and getattr(call.func, "id", None) == helper
                and [getattr(a, "id", None) for a in call.args] == want_names
                and not call.keywords), (
            f"{name} is {ast.unparse(call)}, not {helper}({', '.join(want_names)})")
        live = _as_rgba(getattr(home, name))
        want = _rgb_of(getattr(bases, base)) + ((TUPLE_ALPHAS[alpha],) if alpha else ())
        if len(live) == 4 and len(want) == 3:
            want += (255,)
        assert live == want, f"{name} is {live}; made of {want_names} it is {want}"


def test_the_tuple_alphas_are_the_declared_bytes():
    bases = _importlib.import_module(TUPLE_BASES_MODULE)
    for name, byte in TUPLE_ALPHAS.items():
        value = getattr(bases, name)
        assert type(value) is int and value == byte, (
            f"{name} is {value!r}, declared {byte:#x}")


def test_no_named_colour_is_spelled_in_integers():
    """The completeness half. Every module- or class-level constant in the
    application that spells a NAMED colour in integers. Alpha 0 draws no
    colour; a base no constant names has no row to follow; and INT_DATA is
    data a person starts from, each with its reason."""
    bases = _importlib.import_module(TUPLE_BASES_MODULE)
    named = {v.lower() for n, v in vars(bases).items()
             if n.isupper() and isinstance(v, str)
             and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}
    strays, files = [], 0
    for rel, tree in _tuple_trees():
        files += 1
        for name, rgb, alpha in _int_spelled(tree):
            if name in INT_DATA or alpha == 0 or rgb not in named:
                continue
            strays.append(f"{rel}: {name} = {rgb} at alpha {alpha}")
    assert files >= TUPLE_FILES, f"only {files} files swept -- the walk has gone blind"
    assert not strays, ("named colours still spelled in integers, where no "
                        "register move reaches them:\n  " + "\n  ".join(strays))


# RNV-CHART-RULINGS
# ------------------------------------------ what nothing read, and the wash

#: Palette keys nothing read, proven by render and removed: rulings 2 and 5
#: of 2026-09-26.
REMOVED_KEYS = ("checkbox_bg", "checkbox_border", "label_bg", "label_border")
#: The two alphas that existed only for checkbox_bg.
REMOVED_ALPHAS = ("CHECKBOX_BG_ALPHA_DARK", "CHECKBOX_BG_ALPHA_LIGHT")


def test_the_unread_palette_keys_stay_removed():
    """RNV-CHART-RULINGS, rulings 2 and 5. Four keys in all three palettes
    painted nothing: checkbox_bg, derived at 0xE6 and 0xC8, and
    checkbox_border, label_bg and label_border -- the last three spelled in
    LIGHT_THEME with the CSS names gray, white and black, which a hex census
    cannot see. A render set all twelve entries to #ff00ff. No pixel changed
    in 105 captures of the main window, the control panel and the About
    dialog in all three modes, and no text changed in 1,020 stylesheet and
    palette entries, while a control that moved DARK's canvas_bg changed 1
    capture and 10 entries. So they went, with the two alphas that existed
    only for checkbox_bg.

    Gone from every palette and named nowhere in the application. A key
    brought back is a colour on no element, and has to be decided rather
    than inherited."""
    for palette in PALETTES:
        back = [k for k in REMOVED_KEYS if k in getattr(C.ThemeManager, palette)]
        assert not back, f"{palette} declares {back} again"
    for name in REMOVED_ALPHAS:
        assert not hasattr(C, name), f"utils.config declares {name} again"
    sources = list(_sources())
    assert any(rel.as_posix() == "utils/config.py" for rel, _ in sources), (
        "the sweep cannot see the palettes, so it proves nothing")
    named = [f"{rel}:{node.lineno}  {node.value}" for rel, tree in sources
             for node in ast.walk(tree)
             if isinstance(node, ast.Constant) and isinstance(node.value, str)
             and node.value in REMOVED_KEYS]
    named += [f"{rel}:{node.lineno}  {node.id}" for rel, tree in sources
              for node in ast.walk(tree)
              if isinstance(node, ast.Name) and node.id in REMOVED_ALPHAS]
    assert not named, "named again:\n  " + "\n  ".join(named)


def test_the_harmony_description_derives_its_wash(qapp):
    """RNV-CHART-RULINGS, ruling 4. The control panel's harmony description
    sits on a wash of its own accent ink. It was rgba(r, g, b, 0.1) from
    channels sliced out of the hex by hand, the one derived value in the
    fleet that did not go through a helper. Now it is translucent(accent,
    HARMONY_DESCRIPTION_ALPHA), and 0x19 is the byte Qt makes of 0.1:
    measured on five grounds under both inks, and the panel renders pixel for
    pixel as it did.

    Held twice: in the source, the helper by name and no rgba() built by hand
    left in the function; and in the sheet the function actually sets, in
    both palettes, the wash taken apart to (accent_ink, 0x19)."""
    from types import SimpleNamespace

    from PyQt6.QtWidgets import QLabel

    from core import package_d_panel as panel_module
    tree = ast.parse((ROOT / "core" / "package_d_panel.py").read_text(encoding="utf-8-sig"))
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "_style_harmony_description")
    body = fn.body[1:] if ast.get_docstring(fn) else fn.body
    code = "\n".join(ast.unparse(s) for s in body)
    calls = [ast.unparse(c) for s in body for c in ast.walk(s)
             if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "translucent"]
    assert calls == ["config.translucent(accent, config.HARMONY_DESCRIPTION_ALPHA)"], calls
    assert "rgba(" not in code and "[1:3]" not in code, "the wash is built by hand again"
    for is_dark, palette in ((True, "DARK_THEME"), (False, "LIGHT_THEME")):
        panel = SimpleNamespace(_is_dark=is_dark, harmony_description=QLabel())
        panel_module._style_harmony_description(panel)
        sheet = panel.harmony_description.styleSheet()
        wash = re.search(r"background-color:\s*([^;]+);", sheet).group(1).strip()
        ink = getattr(C.ThemeManager, palette)["accent_ink"].lower()
        assert decompose(wash) == (ink, C.HARMONY_DESCRIPTION_ALPHA), (palette, sheet)



# ------------------------------------------------ eight-digit hex, lower case
# RNV-LOWER-EIGHT-GUARD, 2026-09-29: the test the transformer, the picker and
# the palette manager gained on 2026-09-25, added here by ruling ("Add the
# same test"). This application already wrote lower case, so nothing else
# moves; the register's Notation section (rev 42) says each app's guard holds
# its eight-digit values to lower case, and until now this one did not.
#
# The same two halves, with one difference in where the built values are
# found. The other apps hold theirs at module level, in palettes and
# constants. This one holds none there: every eight-digit value is
# translucent(...) at the place it is used. So each call is evaluated where
# it stands, and the helper is held to lower case for any spelling of any
# named colour.

#: Found when this was written; below a floor, the sweep has gone blind.
#: RNV-NAMED-AND-USED, 2026-10-04: three of the canvas's plates are built
#: by translucent() now, and three colours the code spelled out have names
#: with a value of their own.
#: RNV-RULINGS-2026-10-05, item 3: the canvas's light plate, and its selection
#: fill for each palette and for no theme.
LOWER8_FLOOR = 13
LOWER8_FILES = 32
LOWER8_NAMED = 24
#: translucent() calls whose base is not a name the test can look up. Each is
#: read from what it sets instead; a new one fails the test until it is.
LOWER8_READ_WHERE_SET = {("core/package_d_panel.py", "_style_harmony_description"),
                         ("ui/canvas_view.py", "_selection_fill")}


def _lower8_calls():
    """(rel, enclosing function, call, module name) for every translucent()
    call in the application, in the order the source holds them."""
    for rel, tree in _sources():
        name = ".".join(rel.with_suffix("").parts)
        owners = {}
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for node in ast.walk(fn):
                    owners.setdefault(id(node), fn.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and (
                    getattr(node.func, "id", None) == "translucent"
                    or getattr(node.func, "attr", None) == "translucent"):
                yield rel, owners.get(id(node)), node, name


def _lower8_values():
    """(where, value) for every eight-digit hex string the application
    builds: each translucent() call evaluated in its own module, and each
    call in LOWER8_READ_WHERE_SET read from the sheet it sets, in both
    palettes. The third item is the calls neither could read."""
    import importlib
    from types import SimpleNamespace

    from PyQt6.QtWidgets import QLabel

    def look_up(module, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return getattr(module, node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return getattr(getattr(module, node.value.id), node.attr)
        raise AttributeError(ast.unparse(node))

    built, unread = [], set()
    for rel, owner, call, name in _lower8_calls():
        module = importlib.import_module(name)
        try:
            helper = look_up(module, call.func)
            args = [look_up(module, a) for a in call.args]
        except AttributeError:
            unread.add((rel.as_posix(), owner))
            continue
        built.append((f"{rel}:{call.lineno}  {ast.unparse(call)}", helper(*args)))
    from core import package_d_panel
    for is_dark in (True, False):
        panel = SimpleNamespace(_is_dark=is_dark, harmony_description=QLabel())
        package_d_panel._style_harmony_description(panel)
        sheet = panel.harmony_description.styleSheet()
        wash = re.search(r"background-color:\s*([^;]+);", sheet).group(1).strip()
        built.append((f"the harmony wash, {'dark' if is_dark else 'light'}", wash))
    # RNV-RULINGS-2026-10-05, item 3: the canvas's selection fill, whose base is the
    # accent of the theme it is handed. Read from the method that builds it,
    # for each palette and for no theme at all.
    from ui.canvas_view import ImageDisplayLabel
    for palette in PALETTES:
        built.append((f"the canvas's selection fill, {palette}",
                      ImageDisplayLabel._selection_fill(getattr(C.ThemeManager, palette))))
    built.append(("the canvas's selection fill, no theme", ImageDisplayLabel._selection_fill(None)))
    return built, unread


def test_eight_digit_hex_is_lower_case(qapp):
    """RNV-LOWER-EIGHT, 2026-09-25. The register writes hex in lower case --
    Notation, ruled 2026-08-15, Brand Book decision #19 -- and on 2026-09-25
    Chris ruled that eight digits are hex too: #ed1a1a1a, never #ED1A1A1A.
    Qt reads either case. This application's helper wrote lower case from
    the start; this holds it there.

    Both halves: every eight-digit value the application BUILDS -- each
    translucent() call where it stands, and the helper itself for every
    named colour in either case -- and every eight-digit literal it WRITES
    in code. Docstrings are prose, and a sentence that names an upper-case
    value as history keeps its case."""
    built, unread = _lower8_values()
    assert unread == LOWER8_READ_WHERE_SET, (
        f"translucent() calls this test cannot read: {sorted(unread - LOWER8_READ_WHERE_SET)}; "
        f"read each where it is set, as the harmony wash is")
    assert len(built) >= LOWER8_FLOOR, (
        f"only {len(built)} eight-digit values found; the sweep has gone blind")
    upper = [f"{where} = {value}" for where, value in built
             if not re.fullmatch(r"#[0-9a-f]{8}", value)]
    named = sorted({v for v in vars(C).values()
                    if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v)})
    assert len(named) >= LOWER8_NAMED, f"only {len(named)} named colours found; the sweep has gone blind"
    for base in named:
        for spelling in (base.lower(), base.upper(), base[1:].upper()):
            for alpha in (0, 0x19, 0xED, 0xFF):
                value = C.translucent(spelling, alpha)
                if value != "#%02x%s" % (alpha, base[1:].lower()):
                    upper.append(f"translucent({spelling!r}, {alpha:#04x}) = {value}")
    written, files = [], 0
    for rel, tree in _sources():
        files += 1
        bare = _bare_strings(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and id(node) not in bare):
                for hex8 in re.findall(r"#[0-9a-fA-F]{8}\b", node.value):
                    if hex8 != hex8.lower():
                        written.append(f"{rel}:{node.lineno}  {hex8}")
    assert files >= LOWER8_FILES, f"only {files} files swept"
    assert not upper, "built in upper case:\n  " + "\n  ".join(upper)
    assert not written, "written in upper case:\n  " + "\n  ".join(written)
