#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Move rnv-color-mixer's dark ink onto the published grid, and take the slider
handle with it.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT MOVES

  APP_TEXT_DARK          #e0e0e0 -> #dddddd    grey(13)
  APP_HANDLE_HOVER_DARK  #f0f0f0 -> #eeeeee    grey(14)

  DARK + IMAGE  text_color, button_text, input_text, slot_border,
                slider_handle    literal -> APP_TEXT_DARK

  LIGHT hover_color stays #e0e0e0. It is a SURFACE, and the published grid
  governs inks and edges and deliberately not surfaces.

WHY THE HANDLE HOVER MOVES TOO

APP_HANDLE_HOVER_DARK's docstring says "One step above the text." That was
true of #f0f0f0 above #e0e0e0 only by coincidence -- the gap was 0x10, which
is the SURFACE ladder's step, not the ink grid's 0x11. Leaving it behind would
have made the sentence false and stranded the last off-grid value in dark
mode. At grey(14) the sentence is exactly true, and the guard asserts the
relationship rather than restating it in prose.

This app is the only place #f0f0f0 appears as a dark-mode value anywhere in
the five. Every other use of it is a light surface.

THIS APP ALREADY DID THE HARD PART

The 2026-08-27 neutral rewire gave every rendered hex a constant, so moving
the ink is one line and twenty stylesheet sites follow it. What it did NOT
cover is ThemeManager's three theme dicts, which still spell their neutrals as
literals -- so the ink entries there are wired to the constant here. The rest
of that rewire is the grey-ramp derivation pass.

THE NAMING CONVENTION DIVERGES HERE, ON PURPOSE

The other four apps mirror the brand as APP_TEXT -> APP["text"], which
resolves mechanically. This app names by role AND MODE -- APP_TEXT_DARK,
APP_WINDOW_LIGHT -- because it registers a light set beside the dark one. The
brand's APP dict is the dark palette only. Renaming eleven constants to fit
the other convention would make them wrong within this file, so the mirror
test carries an explicit map instead. Recorded rather than quietly tolerated.

THE SNAPSHOTS ARE HAND-EDITED, NOT REGENERATED

snapshots/stylesheet_dark.txt and stylesheet_image.txt are byte-exact
references. Regenerating them would make the test agree with whatever the code
now emits, which destroys the only evidence that nothing else moved. Each file
gets exactly 11 ink substitutions and 1 handle substitution, asserted by count
before and after. stylesheet_light.txt contains neither value and is not
touched -- which is itself the proof the light half was left alone.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
DESCRIPTION = "move the dark ink and the slider handle onto the grid"
SENTINEL_FILE = "utils/config.py"
SENTINEL = 'APP_TEXT_DARK: Final[str] = "#dddddd"'
GUARD = "tests/test_app_mirror.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

CONTRAST_TEST = "tests/test_contrast_pairs.py"
SNAPSHOTS = ("snapshots/stylesheet_dark.txt", "snapshots/stylesheet_image.txt")
LIGHT_SNAPSHOT = "snapshots/stylesheet_light.txt"

# RUN THE WAY THIS REPO'S CI RUNS, deselects included. KNOWN_ISSUES.md
# documents why: TestAsyncFileOpsErrorPaths aborts natively on offscreen Linux,
# and the abort surfaces during whatever work is in flight, reading exactly
# like a regression in it. It is not one.
#
# The paths below are copied from .github/workflows/tests-linux.yml lines 93-94
# rather than remembered. A --deselect that matches nothing is silently ignored
# by pytest, so a wrong path does not fail -- it just stops deselecting, and
# the run looks green for the wrong reason. This script had that bug once.
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

OLD_INK = '"#e0e0e0"'
NEW_INK = '"#dddddd"'
OLD_HANDLE = '"#f0f0f0"'
NEW_HANDLE = '"#eeeeee"'

INK_KEYS = ("text_color", "button_text", "input_text", "slot_border",
            "slider_handle")

INK_HITS = 11        # per dark/image snapshot
HANDLE_HITS = 1      # per dark/image snapshot


def _bounds(lines):
    """The three palettes are CLASS attributes here, so they are indented and
    carry identically-spelled key lines. Every edit is scoped to its own."""
    starts = {}
    for i, line in enumerate(lines):
        m = re.match(r"^\s+(DARK_THEME|LIGHT_THEME|IMAGE_THEME)\s*=", line)
        if m:
            starts[m.group(1)] = i
    if len(starts) != 3:
        raise SystemExit(f"expected three theme dicts, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def _set(lines, span, key, expect, value):
    st, en = span
    hits = [i for i in range(st, en) if lines[i].strip().startswith(f"'{key}':")]
    if len(hits) != 1:
        raise SystemExit(f"expected one '{key}' in that palette, found {len(hits)}")
    if expect not in lines[hits[0]]:
        raise SystemExit(f"'{key}' is not {expect}: {lines[hits[0]].strip()!r}")
    lines[hits[0]] = lines[hits[0]].replace(expect, value)


def edits(tree) -> None:
    # The two constants. Twenty stylesheet sites follow the first one.
    tree.sub(SENTINEL_FILE, 'APP_TEXT_DARK: Final[str] = "#e0e0e0"',
             'APP_TEXT_DARK: Final[str] = "#dddddd"')
    tree.sub(SENTINEL_FILE, 'APP_HANDLE_HOVER_DARK: Final[str] = "#f0f0f0"',
             'APP_HANDLE_HOVER_DARK: Final[str] = "#eeeeee"')

    # The docstring that the move makes true rather than approximately true.
    tree.sub(SENTINEL_FILE,
             '"""Slider handle when hovered, dark and image. One step above the text."""',
             '"""Slider handle when hovered, dark and image. One step above the\n'
             'text: grey(14), where APP_TEXT_DARK is grey(13), on the published\n'
             'ink grid. Held #f0f0f0 until 2026-08-28, when the gap to #e0e0e0 was\n'
             '0x10 -- the surface ladder step, not the grid step -- and the\n'
             'sentence was true by accident."""')

    # The theme dicts, dark and image only. Light's #e0e0e0 is a surface.
    lines = tree.read(SENTINEL_FILE).splitlines(keepends=True)
    b = _bounds(lines)
    for name in ("DARK_THEME", "IMAGE_THEME"):
        for key in INK_KEYS:
            _set(lines, b[name], key, "'#e0e0e0'", "APP_TEXT_DARK")
    tree.write(SENTINEL_FILE, "".join(lines))

    # The button-scheme reference pairs.
    tree.sub(CONTRAST_TEST,
             '    "DARK":  (("#1a1a1a", "#e0e0e0"), ("#333333", "#e0e0e0"), ("#444444", "#000000")),',
             '    "DARK":  (("#1a1a1a", "#dddddd"), ("#333333", "#dddddd"), ("#444444", "#000000")),')
    tree.sub(CONTRAST_TEST,
             '    "IMAGE": (("#1a1a1a", "#e0e0e0"), ("#333333", "#e0e0e0"), ("#444444", "#000000")),',
             '    "IMAGE": (("#1a1a1a", "#dddddd"), ("#333333", "#dddddd"), ("#444444", "#000000")),')

    # The snapshots, by count rather than blanket replace.
    for rel in SNAPSHOTS:
        text = tree.read(rel)
        ink, handle = text.count("#e0e0e0"), text.count("#f0f0f0")
        if (ink, handle) != (INK_HITS, HANDLE_HITS):
            raise SystemExit(
                f"{rel}: expected {INK_HITS} ink and {HANDLE_HITS} handle "
                f"occurrence(s), found {ink} and {handle}. The stylesheet "
                f"moved; re-derive this edit before trusting the script.")
        tree.write(rel, text.replace("#e0e0e0", "#dddddd")
                            .replace("#f0f0f0", "#eeeeee"))


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count(SENTINEL) != 1:
        raise SystemExit("APP_TEXT_DARK was not moved exactly once")
    if 'APP_HANDLE_HOVER_DARK: Final[str] = "#eeeeee"' not in src:
        raise SystemExit("APP_HANDLE_HOVER_DARK was not moved")
    for key in INK_KEYS:
        if len(re.findall(rf"'{key}':\s+APP_TEXT_DARK,", src)) != 2:
            raise SystemExit(f"{key} does not read APP_TEXT_DARK in dark and image")
    # Exactly one #e0e0e0 must survive: LIGHT hover_color.
    if src.count("'#e0e0e0'") != 1:
        raise SystemExit(
            f"expected exactly one surviving #e0e0e0 (the light surface), "
            f"found {src.count(chr(39) + '#e0e0e0' + chr(39))}")
    # The ASSIGNMENT, not the string. The docstring beside it explains what the
    # value used to be, so sweeping for the bare hex fails on a mention -- the
    # same trap that made an early grey census count a comment as a use, and
    # that this script tripped once already on tab_pane_bg in the sister repo.
    if re.search(r'=\s*"#f0f0f0"', src):
        raise SystemExit("a #f0f0f0 is still assigned in the palette file")
    for rel in SNAPSHOTS:
        text = tree.read(rel)
        if "#e0e0e0" in text or "#f0f0f0" in text:
            raise SystemExit(f"{rel} still carries a retired value")
        if text.count("#dddddd") != INK_HITS:
            raise SystemExit(f"{rel}: expected {INK_HITS} #dddddd")
    # Guard the guard for the snapshots: the light one proves the sweep was
    # scoped rather than global.
    light = tree.read(LIGHT_SNAPSHOT)
    if "#dddddd" in light:
        raise SystemExit("the light stylesheet snapshot changed -- the ink "
                         "substitution was not scoped to dark and image")
    pairs = tree.read(CONTRAST_TEST)
    if '("#1a1a1a", "#e0e0e0")' in pairs:
        raise SystemExit("the main-button reference scheme still names #e0e0e0")


GUARD_SOURCE = '"""\nThe APP register, mirrored -- and the ink move that made mirroring necessary.\n\nWHY THIS FILE EXISTS. Until 2026-08-28 this app carried #e0e0e0, #1a1a1a,\n#2a2a2a and #333333 as bare hex literals with no constant and no provenance.\nEvery one of them is a REGISTERED value in RNVizion/rnv-brand. A registered\nvalue could have moved upstream and this app would have kept the old one\nsilently -- the same failure #c4a458 had, one level down.\n\nIt nearly happened. `APP["text"]` moved from #e0e0e0 to #dddddd in\nrnv-brand@68d195e, and nothing here would have noticed.\n\nTHE INK GRID, published in the brand beside that move:\n\n    grey(n) = n * 0x11, n in 0..15.   TRUE_BLACK -> WHITE in fifteen steps.\n\nIt governs INKS AND EDGES and deliberately does not govern surfaces --\nBRAND_BLACK sits at n = 1.53 and APP_CARD at n = 2.47, and BRAND_BLACK is a\npermanent that will not move to fit a ladder.\n\nTWO GUARDS, NOT ONE. rnv-text-transformer\'s mirror test guards with\n`pytest.importorskip(\'engine.brand\')`, so where rnv-brand is not importable it\nreports clean and drift hides. Every register value here is therefore pinned\nLOCALLY as well as mirrored UPSTREAM: the pin catches drift when the brand is\nabsent, the mirror catches the brand moving. Neither alone is enough.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nimport pytest\n\nfrom utils import config as colors\nfrom utils.config import ThemeManager\n\nDARK = ThemeManager.DARK_THEME\nLIGHT = ThemeManager.LIGHT_THEME\nIMAGE = ThemeManager.IMAGE_THEME\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'utils\' / \'config.py\'\n\nGRID_STEP = 0x11\n\n#: What the brand register held on 2026-08-28, written down so this file still\n#: has an opinion when engine.brand cannot be imported.\nPINNED = {\n    \'TRUE_BLACK\': \'#000000\',\n    \'WHITE\': \'#ffffff\',\n    \'APP_SURFACE_DARK\': \'#1a1a1a\',\n    \'APP_BORDER_DARK\': \'#333333\',\n    \'APP_TEXT_DARK\': \'#dddddd\',\n}\n\n#: This app names its neutrals by ROLE AND MODE -- APP_SURFACE_DARK, not\n#: APP_CARD -- because it registers a light set beside the dark one. The brand\'s\n#: APP dict is the dark palette only, so the APP_<KEY> convention the other four\n#: apps resolve by cannot be used here. Mapped explicitly rather than renaming\n#: eleven constants to fit a convention that would then be wrong within this\n#: file.\nMIRRORS = {\n    \'TRUE_BLACK\': (\'module\', \'TRUE_BLACK\'),\n    \'WHITE\': (\'module\', \'WHITE\'),\n    \'APP_SURFACE_DARK\': (\'APP\', \'panel\'),\n    \'APP_BORDER_DARK\': (\'APP\', \'border\'),\n    \'APP_TEXT_DARK\': (\'APP\', \'text\'),\n}\n\n#: Dark-mode ink and edge. These carry APP_TEXT and must reference it by name.\nINK_KEYS = (\'text_color\', \'button_text\', \'input_text\', \'slot_border\',\n            \'slider_handle\')\n\n#: The other half of #e0e0e0\'s old double life: a LIGHT surface, which the\n#: grid does not govern and which did not move.\nLIGHT_SURFACE_KEYS = (\'hover_color\',)\n\n\ndef grey(n: int) -> str:\n    v = n * GRID_STEP\n    return \'#%02x%02x%02x\' % (v, v, v)\n\n\ndef _dict_node(name: str) -> ast.Dict:\n    tree = ast.parse(SRC.read_text(encoding=\'utf-8-sig\'))\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(target, \'id\', None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f\'{name} is not a dict literal in utils/config.py\')\n\n\ndef _entry(node: ast.Dict, key: str) -> ast.AST | None:\n    for k, v in zip(node.keys, node.values):\n        if isinstance(k, ast.Constant) and k.value == key:\n            return v\n    return None\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_the_keys_this_file_reads_still_exist():\n    """Every assertion below reads these. If a key is renamed, this fails\n    loudly instead of the rest quietly passing over nothing."""\n    for key in INK_KEYS:\n        assert key in DARK, f\'DARK has no {key}\'\n    for key in LIGHT_SURFACE_KEYS:\n        assert key in LIGHT, f\'LIGHT has no {key}\'\n    for name in PINNED:\n        assert hasattr(colors, name), f\'utils.config has no {name}\'\n\n\n# ------------------------------------------------------------------- the value\n\ndef test_the_ink_is_a_step_on_the_grid():\n    assert colors.APP_TEXT_DARK == grey(13) == \'#dddddd\', (\n        f\'APP_TEXT is {colors.APP_TEXT_DARK}, not grey(13). The ink grid admits no \'\n        f\'exceptions -- see rnv-brand engine/brand.py APP.\')\n\n\ndef test_every_pinned_neutral_is_what_the_register_held():\n    """The local half of the mirror. Runs everywhere, including where\n    engine.brand is not importable."""\n    drift = {n: getattr(colors, n) for n, v in PINNED.items()\n             if getattr(colors, n) != v}\n    assert not drift, (\n        f\'these constants no longer hold their registered values: {drift}\\n\'\n        f\'If the brand moved, update PINNED here in the same commit that \'\n        f\'updates utils/config.py -- never one without the other.\')\n\n\ndef test_register_values_match_rnv_brand():\n    """The upstream half. Skips where rnv-brand is not importable, which is\n    exactly why the pin above is not optional."""\n    brand = pytest.importorskip(\n        \'engine.brand\',\n        reason=\'rnv-brand not importable here; the local pin is doing the work\')\n    drift = []\n    for name in PINNED:\n        where, key = MIRRORS[name]\n        theirs = brand.APP[key] if where == \'APP\' else getattr(brand, key)\n        mine = getattr(colors, name)\n        if mine.lower() != theirs.lower():\n            drift.append(f\'{name}: ours {mine}, theirs {theirs}\')\n    assert not drift, \'drift from rnv-brand:\\n  \' + \'\\n  \'.join(drift)\n\n\n# --------------------------------------------------- the ink references the name\n\ndef test_every_dark_ink_reads_the_constant_not_a_literal():\n    """A literal cannot follow its base. This is the whole point of the pass:\n    if APP_TEXT moves again, these move with it or this test fails."""\n    node = _dict_node(\'DARK_THEME\')\n    literals = []\n    for key in INK_KEYS:\n        value = _entry(node, key)\n        if not (isinstance(value, ast.Name) and value.id == \'APP_TEXT_DARK\'):\n            literals.append(f\'{key} = {ast.unparse(value) if value else "missing"}\')\n    assert not literals, (\n        \'dark ink entries still written as literals:\\n  \' + \'\\n  \'.join(literals))\n\n\ndef test_the_resolved_ink_is_the_constant():\n    """The AST check above proves the spelling; this proves the value."""\n    for key in INK_KEYS:\n        assert DARK[key] == colors.APP_TEXT_DARK, f\'DARK[{key!r}] is {DARK[key]}\'\n\n\ndef test_image_mode_carries_the_same_ink():\n    """IMAGE_THEME is a separate literal block here, not a spread of DARK, so\n    the move has to be made twice and asserted twice."""\n    node = _dict_node(\'IMAGE_THEME\')\n    literals = []\n    for key in INK_KEYS:\n        value = _entry(node, key)\n        if not (isinstance(value, ast.Name) and value.id == \'APP_TEXT_DARK\'):\n            literals.append(\n                f\'{key} = {ast.unparse(value) if value is not None else "missing"}\')\n    assert not literals, (\'image ink still written as literals:\\n  \'\n                          + \'\\n  \'.join(literals))\n    for key in INK_KEYS:\n        assert IMAGE[key] == colors.APP_TEXT_DARK, f\'IMAGE[{key!r}]\'\n\n\ndef test_the_handle_hover_is_still_one_step_above_the_text():\n    """APP_HANDLE_HOVER_DARK is documented as \'one step above the text\'. That\n    sentence was true of #f0f0f0 above #e0e0e0 only by accident -- the gap was\n    0x10, not a grid step. Both are on the grid now and the relationship is\n    asserted rather than described."""\n    assert colors.APP_HANDLE_HOVER_DARK == grey(14) == \'#eeeeee\'\n    assert colors.APP_HANDLE_HOVER_DARK == grey(\n        (int(colors.APP_TEXT_DARK[1:3], 16) // GRID_STEP) + 1)\n\n\ndef test_the_light_surface_did_not_follow_the_ink():\n    """#e0e0e0\'s other half. LIGHT hover_color is a SURFACE, and the grid does\n    not govern surfaces."""\n    assert LIGHT[\'hover_color\'] == \'#e0e0e0\'\n\n\n# ------------------------------------------------------------- what did NOT move\n\ndef test_the_light_ink_is_true_black():\n    """Primary text is one role with two mode values: dark is a grey on the\n    grid, light is TRUE_BLACK."""\n    assert LIGHT[\'text_color\'] == colors.TRUE_BLACK == \'#000000\'\n\n\n# ---------------------------------------------------------------- what it costs\n\ndef _luminance(value: str) -> float:\n    channels = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n                for c in channels]\n    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (high + 0.05) / (low + 0.05)\n\n\ndef test_the_ink_clears_the_text_floor_on_every_dark_ground_it_touches():\n    """Measured, not assumed. The darkest ground the ink is drawn on is the\n    pressed plate; everything else has more room."""\n    grounds = (\'#000000\', \'#1a1a1a\', \'#2a2a2a\', \'#333333\', \'#3a3a3a\', \'#444444\')\n    worst = min((_contrast(colors.APP_TEXT_DARK, g), g) for g in grounds)\n    assert worst[0] >= 4.5, (\n        f\'the ink falls to {worst[0]:.2f}:1 on {worst[1]}, under the 4.5 floor\')\n'


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
