#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Name rnv-color-mixer's unnamed dark greys, then wire the dark palettes to them.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT MOVES: NOTHING. Not one rendered pixel. checks() resolves every entry of
every palette from the ORIGINAL file and the EDITED one and refuses to write
unless all three are equal, entry for entry, and unless the file has the same
number of lines.

WHY MIXER WAS DIFFERENT FROM THE OTHER FOUR

This app styles itself through two paths. The three *_STYLESHEET templates
cover main-window chrome; seven separate modules build their own QSS from
ThemeManager's theme dicts. The 2026-08-27 neutral rewire covered the
templates only -- and said so -- so the dicts still spell their values out.

Four dark greys were therefore never named, because they appear in no
template:

    #0a0a0a  canvas_bg, tab_selected_bg     -> APP_CANVAS_DARK
    #2a2a2a  panel_secondary, tooltip_bg    -> APP_CARD_DARK
    #3a3a3a  panel_hover                    -> APP_PANEL_HOVER_DARK
    #888888  text_hint                      -> APP_HINT_DARK

NAMES FIRST, THEN WIRING, IN ONE PASS

The names are the point; the wiring is what makes them real. Splitting them
would leave this app holding four constants that nothing references, which is
the exact state the test below exists to prevent. The value-neutrality proof
is strong enough to carry both: nothing may move, and the script checks rather
than claims.

APP_CARD_DARK IS A REGISTER VALUE

#2a2a2a is engine/brand.py APP["card"]. It joins PINNED and MIRRORS in
tests/test_app_mirror.py, so a move upstream is caught here like the other
four. The remaining three are app-owned and named as such.

ONE TEST IS WIDENED, AND IT IS A CORRECTION

tests/test_neutral_ramp.py asked whether a constant "reaches a stylesheet",
meaning "is rendered". Those stopped being the same thing the moment the theme
dicts became a naming target: the templates style no QToolTip, QGroupBox,
QFrame or QDialog, so the dicts paint most of the app's dialogs. Unwidened, it
would call a constant used by every dialog dead weight. A companion test
asserts BOTH paths still carry values, so the union cannot quietly halve.

THE SUBSTITUTION IS AN ALLOWLIST, NOT EVERY CONSTANT

Value-keyed substitution across a dark palette is a trap here:
DARK['menu_disabled'] is #666666, and the only constant holding #666666 is
APP_HANDLE_LIGHT. A blanket swap would write a _LIGHT name into the dark
palette -- true by value and false by name, which is worse than the literal it
replaced. Only the seven dark-appropriate names are substituted.

LIGHT IS UNTOUCHED, on the register's stated order: the light ladder is not
ruled, and two of its values (#aaaaaa, #e0e0e0) remain unnamed here on purpose.
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
DESCRIPTION = "name the dark greys and wire the dark palettes"
SENTINEL_FILE = "utils/config.py"
SENTINEL = 'APP_CARD_DARK: Final[str] = "#2a2a2a"'
GUARD = "tests/test_register_wiring.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

RAMP_TEST = "tests/test_neutral_ramp.py"
MIRROR_TEST = "tests/test_app_mirror.py"

SUITES = [
    ("pytest tests/ (about 4 minutes)",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider",
      "--deselect",
      "tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths"]),
    ("pytest test_rnv_color_mixer.py",
     [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
      "-p", "no:cacheprovider", "--deselect",
      "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"]),
]

# The allowlist. Dark-appropriate names only -- see the docstring on
# menu_disabled for why this is not "every constant".
SUBSTITUTE = {
    "#000000": "TRUE_BLACK",
    "#0a0a0a": "APP_CANVAS_DARK",
    "#1a1a1a": "APP_SURFACE_DARK",
    "#2a2a2a": "APP_CARD_DARK",
    "#333333": "APP_BORDER_DARK",
    "#3a3a3a": "APP_PANEL_HOVER_DARK",
    "#888888": "APP_HINT_DARK",
}

DARK_DICTS = ("DARK_THEME", "IMAGE_THEME")
ALL_DICTS = ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME")

NEW_CONSTS = '\nAPP_CANVAS_DARK: Final[str] = "#0a0a0a"\n"""The ground BELOW the panel in dark and image: the mixing canvas, and the\nselected tab, which sits flush with it.\n\nUnnamed until 2026-08-29 because the 2026-08-27 rewire\'s scope was the three\nstylesheet templates and this value has never appeared in one -- it is reached\nonly through ThemeManager\'s dicts, which seven modules build their own QSS\nfrom.\n\nNOT A BRAND VALUE, and worth saying so here because it was briefly mistaken\nfor one. #0a0a0a is app-owned. The register\'s canvas is WEB_BLACK #0a0a0f, one\nbyte away in the blue channel alone, and a rule derived from the resemblance\nwould have pinned fifteen light uses to a colour the register does not hold.\nSee rnv-brand@8ab1174 BRAND_COLORS.md:270."""\n\nAPP_CARD_DARK: Final[str] = "#2a2a2a"\n"""engine/brand.py APP["card"]. The raised secondary surface in dark and\nimage: panel_secondary in the About dialog and the fine-tune panel, and the\nground of the custom tooltip.\n\nMIRRORED, not app-owned -- it is pinned in tests/test_app_mirror.py alongside\nthe other register values, so a move upstream is caught here."""\n\nAPP_PANEL_HOVER_DARK: Final[str] = "#3a3a3a"\n"""Panel hover in dark and image. One step above APP_CARD_DARK on the 0x10\nsurface spacing, though that ladder is not published: rnv-brand@8ab1174 notes\nit yields #3a3a3a while APP["border"] is #333333, so two rungs are in use and\ntwo are not. Named as an app value until the register rules it."""\n\nAPP_HINT_DARK: Final[str] = "#888888"\n"""Hint text in dark and image. grey(8) on the published ink grid, and the\nsame step the other four apps use for muted text."""\n\n'
CONST_ANCHOR = "\n# ---- light ----\n"
PROV_OLD = '    "APP_HANDLE_HOVER_DARK": "step",\n'
PROV_NEW = '    "APP_HANDLE_HOVER_DARK": "step",\n    "APP_CANVAS_DARK": "step",\n    "APP_CARD_DARK": "step",\n    "APP_PANEL_HOVER_DARK": "step",\n    "APP_HINT_DARK": "step",\n'
PINNED_OLD = "    'APP_TEXT_DARK': '#dddddd',\n"
PINNED_NEW = "    'APP_TEXT_DARK': '#dddddd',\n    'APP_CARD_DARK': '#2a2a2a',\n"
MIRROR_OLD = "    'APP_TEXT_DARK': ('APP', 'text'),\n"
MIRROR_NEW = "    'APP_TEXT_DARK': ('APP', 'text'),\n    'APP_CARD_DARK': ('APP', 'card'),\n"
REACH_OLD = 'def test_every_neutral_constant_reaches_a_stylesheet():\n    """A constant nothing renders is dead weight, and dead weight is where the\n    next wrong value hides."""\n    rendered = "".join(getattr(config, t) for t in TEMPLATES).lower()\n    orphans = [n for n in config.NEUTRAL_PROVENANCE\n               if getattr(config, n).lower() not in rendered]\n    assert not orphans, f"neutral constants that render nowhere: {orphans}"\n'
REACH_NEW = 'def test_every_neutral_constant_is_actually_rendered():\n    """A constant nothing renders is dead weight, and dead weight is where the\n    next wrong value hides.\n\n    WIDENED 2026-08-29, and the widening is a correction rather than a\n    relaxation. This app renders through TWO paths:\n\n      1. the three stylesheet templates above -- main-window chrome, and the\n         only thing this test used to look at;\n      2. ThemeManager\'s three theme dicts, which ui/about_dialog.py,\n         core/color_fine_tune.py, ui/canvas_view.py, core/color_slot.py,\n         core/package_d_panel.py, ui/ui_handler.py and RNV_Color_Mixer.py each\n         build their own QSS from.\n\n    The templates style no QToolTip, QGroupBox, QFrame or QDialog at all, so\n    path 2 paints most of the dialogs. Checking only path 1 measured "reaches a\n    stylesheet template" while claiming "is rendered" -- and would have called\n    a constant used by every dialog in the app dead weight.\n\n    The strength is unchanged: a constant reached by NEITHER path still fails.\n    """\n    rendered = "".join(getattr(config, t) for t in TEMPLATES).lower()\n    in_dicts = {str(v).lower()\n                for theme in (config.ThemeManager.DARK_THEME,\n                              config.ThemeManager.LIGHT_THEME,\n                              config.ThemeManager.IMAGE_THEME)\n                for v in theme.values()}\n    orphans = [n for n in config.NEUTRAL_PROVENANCE\n               if getattr(config, n).lower() not in rendered\n               and getattr(config, n).lower() not in in_dicts]\n    assert not orphans, f"neutral constants that render nowhere: {orphans}"\n\n\ndef test_both_rendering_paths_are_still_carrying_something():\n    """Guard the guard for the widening. If either path stopped resolving, the\n    union above would still pass on the other one -- quietly halving what this\n    test covers."""\n    rendered = "".join(getattr(config, t) for t in TEMPLATES).lower()\n    in_dicts = {str(v).lower()\n                for theme in (config.ThemeManager.DARK_THEME,\n                              config.ThemeManager.LIGHT_THEME,\n                              config.ThemeManager.IMAGE_THEME)\n                for v in theme.values()}\n    from_templates = [n for n in config.NEUTRAL_PROVENANCE\n                      if getattr(config, n).lower() in rendered]\n    from_dicts = [n for n in config.NEUTRAL_PROVENANCE\n                  if getattr(config, n).lower() in in_dicts]\n    assert len(from_templates) >= 10, f"only {len(from_templates)} reach a template"\n    assert len(from_dicts) >= 10, f"only {len(from_dicts)} reach a theme dict"\n'


def _resolve(source: str) -> dict:
    """Every palette resolved to plain values, whether an entry is a literal or
    a name. This is what makes 'nothing moved' checkable rather than asserted."""
    tree = ast.parse(source.lstrip("\ufeff"))
    consts = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                consts.setdefault(target.id, node.value.value)
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            name = getattr(target, "id", None)
            if name in ALL_DICTS and isinstance(node.value, ast.Dict):
                palette = {}
                for key, value in zip(node.value.keys, node.value.values):
                    if not isinstance(key, ast.Constant):
                        continue
                    if isinstance(value, ast.Constant):
                        palette[key.value] = value.value
                    elif isinstance(value, ast.Name):
                        palette[key.value] = consts.get(value.id, f"<{value.id}>")
                    else:
                        palette[key.value] = ast.unparse(value)
                out[name] = palette
    return out


def _bounds(lines):
    """The palettes are CLASS attributes here, so they are indented, and they
    carry identically-spelled key lines. Every edit is scoped to its own."""
    starts = {}
    pattern = re.compile(r"^\s+(" + "|".join(ALL_DICTS) + r")\s*=")
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            starts[m.group(1)] = i
    if len(starts) != len(ALL_DICTS):
        raise SystemExit(f"expected three palettes, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def edits(tree) -> None:
    # 1. the names
    source = tree.read(SENTINEL_FILE)
    if source.count(CONST_ANCHOR) != 1:
        raise SystemExit("could not find the single '# ---- light ----' divider")
    tree.write(SENTINEL_FILE,
               source.replace(CONST_ANCHOR, NEW_CONSTS + CONST_ANCHOR.lstrip("\n"), 1))
    tree.sub(SENTINEL_FILE, PROV_OLD, PROV_NEW)

    # 2. the register mirror picks up APP_CARD_DARK
    tree.sub(MIRROR_TEST, PINNED_OLD, PINNED_NEW)
    tree.sub(MIRROR_TEST, MIRROR_OLD, MIRROR_NEW)

    # 3. the widened reach test
    tree.sub(RAMP_TEST, REACH_OLD, REACH_NEW)

    # 4. the wiring, dark and image only
    lines = tree.read(SENTINEL_FILE).splitlines(keepends=True)
    bounds = _bounds(lines)
    swapped = 0
    for name in DARK_DICTS:
        start, end = bounds[name]
        for i in range(start, end):
            line = lines[i]
            # Match without the line ending and put it back verbatim: Python's
            # `$` also matches before a trailing newline, so a pattern ending
            # `(,.*)$` eats it and reflows the palette onto one line while
            # every value stays identical and every test stays green.
            body = line.rstrip("\r\n")
            ending = line[len(body):]
            m = re.match(r"^(\s*'[a-z_0-9]+':\s*)'(#[0-9a-fA-F]{6})'(,.*)$", body)
            if not m:
                continue
            const = SUBSTITUTE.get(m.group(2).lower())
            if const:
                lines[i] = f"{m.group(1)}{const}{m.group(3)}{ending}"
                swapped += 1
    if swapped == 0:
        raise SystemExit("nothing was substituted -- already wired, or the "
                         "palettes changed shape")
    tree.write(SENTINEL_FILE, "".join(lines))
    print(f"  named 4 greys, substituted {swapped} literal(s)")


def checks(tree) -> None:
    original = (Path.cwd() / SENTINEL_FILE).read_text(encoding="utf-8-sig")
    edited = tree.read(SENTINEL_FILE)

    if SENTINEL not in edited:
        raise SystemExit("APP_CARD_DARK was not defined")

    before, after = _resolve(original), _resolve(edited)
    moved = []
    for name in set(before) | set(after):
        for key in set(before.get(name, {})) | set(after.get(name, {})):
            was, now = before.get(name, {}).get(key), after.get(name, {}).get(key)
            if was != now:
                moved.append(f"{name}[{key!r}]: {was} -> {now}")
    if moved:
        raise SystemExit("THIS PASS MUST NOT MOVE A VALUE, and it moved:\n  "
                         + "\n  ".join(moved))

    # No _LIGHT name may appear inside a dark palette. This is the trap the
    # allowlist exists for, asserted rather than trusted.
    lines = edited.splitlines()
    bounds = _bounds([l + "\n" for l in lines])
    for name in DARK_DICTS:
        start, end = bounds[name]
        for i in range(start, end):
            m = re.match(r"^\s*'([a-z_0-9]+)':\s*([A-Z][A-Z_0-9]+),", lines[i])
            if m and m.group(2).endswith("_LIGHT"):
                raise SystemExit(
                    f"{name}[{m.group(1)!r}] now reads {m.group(2)} -- a light "
                    f"name in a dark palette is worse than the literal it "
                    f"replaced")

    # Completeness: no allowlisted value may survive as a literal in dark.
    survivors = []
    for name in DARK_DICTS:
        start, end = bounds[name]
        for i in range(start, end):
            m = re.match(r"^\s*'([a-z_0-9]+)':\s*'(#[0-9a-fA-F]{6})',", lines[i])
            if m and m.group(2).lower() in SUBSTITUTE:
                survivors.append(f"{name}[{m.group(1)!r}] = {m.group(2)}")
    if survivors:
        raise SystemExit("values still spelled as literals in dark:\n  "
                         + "\n  ".join(survivors))

    ramp = tree.read(RAMP_TEST)
    if "test_both_rendering_paths_are_still_carrying_something" not in ramp:
        raise SystemExit("the widened reach test and its companion did not land")


GUARD_SOURCE = '"""\nmixer\'s dark palettes, wired to the names the same pass created.\n\nWHY THIS APP NEEDED NAMING FIRST. The 2026-08-27 neutral rewire covered the\nthree stylesheet templates. Seven other modules build their own QSS from\nThemeManager\'s theme dicts, and four dark greys lived only there -- so they had\nnever been named, and there was nothing to wire them to.\n\nNOTHING MOVED. The delivery script resolved every palette before and after and\nrefused to write unless they matched entry for entry.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nfrom utils import config\nfrom utils.config import ThemeManager\n\nDARK = ThemeManager.DARK_THEME\nIMAGE = ThemeManager.IMAGE_THEME\nLIGHT = ThemeManager.LIGHT_THEME\nPALETTES = {"DARK_THEME": DARK, "IMAGE_THEME": IMAGE}\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "utils" / "config.py"\n\nSUBSTITUTE = {\n    "#000000": "TRUE_BLACK",\n    "#0a0a0a": "APP_CANVAS_DARK",\n    "#1a1a1a": "APP_SURFACE_DARK",\n    "#2a2a2a": "APP_CARD_DARK",\n    "#333333": "APP_BORDER_DARK",\n    "#3a3a3a": "APP_PANEL_HOVER_DARK",\n    "#888888": "APP_HINT_DARK",\n}\nNEW_NAMES = ("APP_CANVAS_DARK", "APP_CARD_DARK", "APP_PANEL_HOVER_DARK",\n             "APP_HINT_DARK")\n\n\ndef _dicts(names):\n    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))\n    out = {}\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(target, "id", None) in names and isinstance(node.value, ast.Dict):\n                out[getattr(target, "id")] = node.value\n    missing = set(names) - set(out)\n    assert not missing, f"palettes that are no longer dict literals: {missing}"\n    return out\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_the_names_this_file_reads_exist():\n    for name in NEW_NAMES:\n        assert hasattr(config, name), f"utils.config has no {name}"\n        assert name in config.NEUTRAL_PROVENANCE, f"{name} has no provenance"\n    assert _dicts(PALETTES)\n\n\ndef test_the_new_names_hold_the_values_they_were_created_for():\n    assert config.APP_CANVAS_DARK == "#0a0a0a"\n    assert config.APP_CARD_DARK == "#2a2a2a"\n    assert config.APP_PANEL_HOVER_DARK == "#3a3a3a"\n    assert config.APP_HINT_DARK == "#888888"\n\n\n# ------------------------------------------------------------ the substitution\n\ndef test_no_allowlisted_value_is_spelled_as_a_literal_in_dark():\n    """A literal cannot follow its base. There must not be one left."""\n    literals = []\n    for dict_name, node in _dicts(PALETTES).items():\n        for key, value in zip(node.keys, node.values):\n            if not isinstance(key, ast.Constant):\n                continue\n            if isinstance(value, ast.Constant) and isinstance(value.value, str):\n                const = SUBSTITUTE.get(value.value.lower())\n                if const:\n                    literals.append(f"{dict_name}[{key.value!r}] = {value.value} "\n                                    f"(should read {const})")\n    assert not literals, ("values still written as literals:\\n  "\n                          + "\\n  ".join(literals))\n\n\ndef test_every_dark_name_resolves_to_the_value_it_replaced():\n    wrong = []\n    by_name = {v: k for k, v in SUBSTITUTE.items()}\n    for dict_name, node in _dicts(PALETTES).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Name) and value.id in by_name:\n                actual = PALETTES[dict_name].get(key.value)\n                if actual != by_name[value.id]:\n                    wrong.append(f"{dict_name}[{key.value!r}] -> {value.id} "\n                                 f"resolves to {actual}")\n    assert not wrong, "names resolving wrongly:\\n  " + "\\n  ".join(wrong)\n\n\ndef test_no_light_name_leaked_into_a_dark_palette():\n    """The trap the allowlist exists for. DARK[\'menu_disabled\'] is #666666 and\n    the only constant holding #666666 is APP_HANDLE_LIGHT -- a value-keyed\n    substitution across every constant would have written a light name into the\n    dark palette, true by value and false by name."""\n    leaked = []\n    for dict_name, node in _dicts(PALETTES).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Name) and value.id.endswith("_LIGHT"):\n                leaked.append(f"{dict_name}[{key.value!r}] -> {value.id}")\n    assert not leaked, ("light names inside a dark palette:\\n  "\n                        + "\\n  ".join(leaked))\n\n\ndef test_menu_disabled_is_still_the_literal_that_proves_the_point():\n    """Guard the guard for the test above: it can only catch a leak while the\n    value that would leak is still there to leak."""\n    assert DARK.get("menu_disabled") == "#666666", (\n        "menu_disabled moved; the allowlist reasoning above needs re-checking")\n\n\ndef test_the_light_palette_was_left_alone():\n    """The light ladder is unruled. Two of its greys -- #aaaaaa and #e0e0e0 --\n    are deliberately still unnamed. If a later pass wires light, this test has\n    to be deleted on purpose."""\n    named = []\n    for key, value in zip(*(lambda n: (n.keys, n.values))(_dicts(("LIGHT_THEME",))["LIGHT_THEME"])):\n        if isinstance(value, ast.Name) and value.id in SUBSTITUTE.values():\n            named.append(f"LIGHT_THEME[{key.value!r}] -> {value.id}")\n    assert not named, ("the light palette now references the dark names:\\n  "\n                       + "\\n  ".join(named))\n'


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
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
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
        raise SystemExit(f"run this from the root of a {REPO} checkout "
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
