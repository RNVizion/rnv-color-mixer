"""derive the named colours written as integer tuples (ruling 3)

    python up.py             # apply, then run the guard and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guard and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (e4f3a32).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-25 (ruling 3): colours written as integer tuples are derived,
the NAMED ones only; the structural QColor(0, 0, 0) and QColor(255, 255, 255)
calls are left alone. The screen picker's three module-level QColors were written in integers:
the dim QColor(0, 0, 0, 50), the readout panel QColor(0, 0, 0, 180), and
the grid gold QColor(*BRAND_GOLD_RGB, 50), whose alpha had no name. Each is
QColor(translucent(BASE, ALPHA)) now, by name. Nothing moves on screen.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import typing
from pathlib import Path

REPO = 'rnv-color-mixer'
SENTINEL = 'RNV-TUPLE-ROUND'
SENTINEL_FILE = 'tests/test_derived_values.py'
GUARD = 'tests/test_derived_values.py'
DESCRIPTION = 'derive the named colours written as integer tuples (ruling 3)'

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS: the locked file's hash first, both
#: suites under coverage, the combine, and the floor. The Windows workflow runs
#: the same two suites without coverage.
_LOCK = ("import hashlib, sys\n"
         "want = '0827b02dbaa946087da83a27b391065aaa6114cfe43a78c958f6b0a502b0eddd'\n"
         "got = hashlib.sha256(open('test_rnv_color_mixer.py', 'rb').read()).hexdigest()\n"
         "if got != want:\n"
         "    raise AssertionError(f'locked file changed: {got}')\n"
         "print('Locked file SHA-256 matches:', got)\n")
#: coverage exits 2 for a shortfall, which this harness would read as the
#: environment; wrapped so falling under the floor reads as a failure.
_FLOOR = ("import subprocess, sys\n"
          "r = subprocess.run([sys.executable, '-m', 'coverage', 'report', "
          "'--fail-under=69'])\n"
          "if r.returncode == 2:\n"
          "    raise AssertionError('coverage is under the Linux CI floor of 69')\n"
          "sys.exit(r.returncode)\n")
SUITES = [
    ("CI: locked file integrity", [sys.executable, "-c", _LOCK]),
    ("CI: pytest test_rnv_color_mixer.py under coverage",
     [sys.executable, "-m", "coverage", "run", "--data-file=.coverage.unittest",
      "--branch", "-m", "pytest", "test_rnv_color_mixer.py", "-v"]),
    ("CI: pytest tests/ under coverage",
     [sys.executable, "-m", "coverage", "run", "--data-file=.coverage.pytest",
      "--branch", "-m", "pytest", "tests/", "-v"]),
    ("CI: coverage combine",
     [sys.executable, "-m", "coverage", "combine", ".coverage.unittest",
      ".coverage.pytest"]),
    ("CI: coverage floor 69", [sys.executable, "-c", _FLOOR]),
]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '769b9b7034c0599b5d655cfb502741706693e765d51e2db95406c140a6b92ffd', '.github/workflows/tests-windows.yml': 'd123e5da015c9b988e5c52e9c0bb9879d492365b6db6c1f3672dc1b34f57d967'}

SHADOWS = {"config.py", "conftest.py", "screen_color_picker.py", "test_rnv_color_mixer.py"}

LEFT_ALONE = ["QColors built inside paint methods -- the canvas labels' QColor(0, 0, 0, 200), QColor(255, 255, 255, 200) and the rest. They are locals, not named constants, and ruling 3 covers named ones only.", 'DEFAULT_COLOR (200, 200, 200) and INITIAL_COLOR_TUPLE (0, 0, 0): the colours a slot and the preview start from. Data, not a brand element; #c8c8c8 has no row at all.', 'the debug overlays, diagnostic by rule.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('core/screen_color_picker.py',
             '# Colors - created once, used forever\nfrom utils.config import BRAND_GOLD, BRAND_GOLD_RGB\n\n_OVERLAY_COLOR = QColor(0, 0, 0, 50)\n_GOLD_BRAND = QColor(BRAND_GOLD)\n_GOLD_TRANSPARENT = QColor(*BRAND_GOLD_RGB, 50)\n_INFO_BG = QColor(0, 0, 0, 180)\n',
             '# Colors - created once, used forever. Each translucent one is DERIVED: a\n# named colour at a named alpha (RNV-TUPLE-ROUND, 2026-09-26), so it\n# follows its base like every other composite in the application.\nfrom utils.config import (BRAND_GOLD, TRUE_BLACK, translucent,\n                          SCREEN_OVERLAY_ALPHA, SCREEN_GRID_ALPHA,\n                          SCREEN_INFO_ALPHA)\n\n_OVERLAY_COLOR = QColor(translucent(TRUE_BLACK, SCREEN_OVERLAY_ALPHA))\n_GOLD_BRAND = QColor(BRAND_GOLD)\n_GOLD_TRANSPARENT = QColor(translucent(BRAND_GOLD, SCREEN_GRID_ALPHA))\n_INFO_BG = QColor(translucent(TRUE_BLACK, SCREEN_INFO_ALPHA))\n')
    tree.sub('utils/config.py',
             'CHECKBOX_BG_ALPHA_LIGHT: Final[int] = 0xC8\n"""200. checkbox_bg in the light palette (WHITE). Unread, like its dark twin."""\n',
             'CHECKBOX_BG_ALPHA_LIGHT: Final[int] = 0xC8\n"""200. checkbox_bg in the light palette (WHITE). Unread, like its dark twin."""\n\nSCREEN_OVERLAY_ALPHA: Final[int] = 0x32\n"""50. The screen picker\'s dim over the whole screen (TRUE_BLACK)."""\n\nSCREEN_GRID_ALPHA: Final[int] = 0x32\n"""50. The screen picker\'s magnifier grid lines (BRAND_GOLD). The same byte\nas the dim, for an unrelated job, so it keeps its own name."""\n\nSCREEN_INFO_ALPHA: Final[int] = 0xB4\n"""180. The screen picker\'s colour readout panel (TRUE_BLACK)."""\n')
    tree.sub('tests/test_derived_values.py',
             '    assert colours_in("rgba(80, 80, 80, 150)") == {"#505050"}, "the decoder is blind"\n\n# RNV-DERIVE-ALPHA\n',
             '    assert colours_in("rgba(80, 80, 80, 150)") == {"#505050"}, "the decoder is blind"\n\n# RNV-DERIVE-ALPHA\n\n\n# ------------------------------------------------- colours spelled in integers\n\nimport importlib as _importlib\n\n#: Where the derived constants live, and where their bases and alphas live.\nTUPLE_HOME = \'core/screen_color_picker.py\'\nTUPLE_HOME_MODULE = \'core.screen_color_picker\'\nTUPLE_BASES_MODULE = \'utils.config\'\n#: Each derived constant, by NAME: (helper, base, alpha or None). A register\n#: move passes straight through; a value re-made from something else fails.\nTUPLES_MADE_OF = {\'_OVERLAY_COLOR\': (\'translucent\', \'TRUE_BLACK\', \'SCREEN_OVERLAY_ALPHA\'), \'_GOLD_TRANSPARENT\': (\'translucent\', \'BRAND_GOLD\', \'SCREEN_GRID_ALPHA\'), \'_INFO_BG\': (\'translucent\', \'TRUE_BLACK\', \'SCREEN_INFO_ALPHA\')}\n#: The alpha bytes behind them, each the one its literal already carried.\nTUPLE_ALPHAS = {\'SCREEN_OVERLAY_ALPHA\': 50, \'SCREEN_GRID_ALPHA\': 50, \'SCREEN_INFO_ALPHA\': 180}\n#: Module- and class-level constants spelled in integers ON PURPOSE -- data a\n#: person starts from, not a brand element -- with the reason.\nINT_DATA = {\'INITIAL_COLOR_TUPLE\': \'the colour shown before anything is mixed -- data, like the hex and rgb() twins beside it\'}\nTUPLE_FILES = 20\n#: The call each derived constant is wrapped in, if any.\n_WRAP = \'QColor\'\n\n\ndef _int_spelled(tree):\n    """(name, #rrggbb, alpha) for every module- or class-level constant whose\n    value spells a colour in integers: a tuple or list of three or four int\n    literals, or QColor/QPen/QBrush called with them. Locals inside functions\n    are state, not constants, and are not read."""\n    bodies = [tree.body] + [n.body for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]\n    for body in bodies:\n        for statement in body:\n            if (not isinstance(statement, (ast.Assign, ast.AnnAssign))\n                    or statement.value is None):\n                continue\n            target = (statement.targets[0] if isinstance(statement, ast.Assign)\n                      else statement.target)\n            name, value = getattr(target, "id", None), statement.value\n            if isinstance(value, (ast.Tuple, ast.List)):\n                elts = value.elts\n            elif isinstance(value, ast.Call) and (\n                    getattr(value.func, "id", None) or getattr(value.func, "attr", None)\n                    ) in ("QColor", "fromRgb", "QPen", "QBrush"):\n                elts = value.args\n            else:\n                continue\n            if name is None or len(elts) not in (3, 4):\n                continue\n            ints = [e.value for e in elts\n                    if isinstance(e, ast.Constant) and type(e.value) is int]\n            if len(ints) != len(elts) or not all(0 <= i <= 255 for i in ints):\n                continue\n            yield (name, "#%02x%02x%02x" % tuple(ints[:3]),\n                   ints[3] if len(ints) == 4 else 255)\n\n\ndef _tuple_trees():\n    """Application source: not tests, not a root test suite, not a delivery\n    script. BOM-aware."""\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT)\n        if any(p in {".git", "tests", "snapshots", "build", "dist", ".venv",\n                     "venv", "__pycache__"} for p in rel.parts):\n            continue\n        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):\n            continue\n        text = path.read_bytes().decode("utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, ast.parse(text)\n\n\ndef _rgb_of(hex_color):\n    h = hex_color.lstrip("#")\n    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))\n\n\ndef _as_rgba(value):\n    """A tuple as it is; a QColor as its channels."""\n    if hasattr(value, "alpha") and callable(value.alpha):\n        return (value.red(), value.green(), value.blue(), value.alpha())\n    return tuple(value)\n\n\ndef test_the_integer_sweep_reads_both_notations():\n    """Guard the guard: a tuple and a QColor at module or class level are\n    read; a local inside a function is not."""\n    probe = ast.parse("A = (0, 0, 0, 50)\\n"\n                      "class K:\\n    B = QColor(68, 68, 68)\\n"\n                      "def f():\\n    c = (0, 0, 0)\\n")\n    assert sorted(_int_spelled(probe)) == [("A", "#000000", 50), ("B", "#444444", 255)]\n\n\ndef test_every_tuple_constant_is_derived_by_name():\n    """RNV-TUPLE-ROUND, 2026-09-26. A colour spelled in integers is a colour\n    every string sweep in the fleet was blind to, and #505050 sat in two of\n    them for three weeks after it was ruled away. Each constant here is now\n    its helper called on a named base and a named alpha, and it evaluates to\n    exactly that pair -- held BY NAME, so a register move passes through."""\n    tree = ast.parse((ROOT / TUPLE_HOME).read_text(encoding="utf-8-sig"))\n    values = {}\n    for node in tree.body:\n        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:\n            t = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(t, "id", None):\n                values[t.id] = node.value\n    home = _importlib.import_module(TUPLE_HOME_MODULE)\n    bases = _importlib.import_module(TUPLE_BASES_MODULE)\n    assert TUPLES_MADE_OF, "nothing to check"\n    for name, (helper, base, alpha) in TUPLES_MADE_OF.items():\n        call = values.get(name)\n        assert call is not None, f"{name} is gone from {TUPLE_HOME}"\n        if _WRAP:\n            assert (isinstance(call, ast.Call)\n                    and getattr(call.func, "id", None) == _WRAP\n                    and len(call.args) == 1), (\n                f"{name} is not {_WRAP}(...): {ast.unparse(call)}")\n            call = call.args[0]\n        want_names = [base] + ([alpha] if alpha else [])\n        assert (isinstance(call, ast.Call) and getattr(call.func, "id", None) == helper\n                and [getattr(a, "id", None) for a in call.args] == want_names\n                and not call.keywords), (\n            f"{name} is {ast.unparse(call)}, not {helper}({\', \'.join(want_names)})")\n        live = _as_rgba(getattr(home, name))\n        want = _rgb_of(getattr(bases, base)) + ((TUPLE_ALPHAS[alpha],) if alpha else ())\n        if len(live) == 4 and len(want) == 3:\n            want += (255,)\n        assert live == want, f"{name} is {live}; made of {want_names} it is {want}"\n\n\ndef test_the_tuple_alphas_are_the_declared_bytes():\n    bases = _importlib.import_module(TUPLE_BASES_MODULE)\n    for name, byte in TUPLE_ALPHAS.items():\n        value = getattr(bases, name)\n        assert type(value) is int and value == byte, (\n            f"{name} is {value!r}, declared {byte:#x}")\n\n\ndef test_no_named_colour_is_spelled_in_integers():\n    """The completeness half. Every module- or class-level constant in the\n    application that spells a NAMED colour in integers. Alpha 0 draws no\n    colour; a base no constant names has no row to follow; and INT_DATA is\n    data a person starts from, each with its reason."""\n    bases = _importlib.import_module(TUPLE_BASES_MODULE)\n    named = {v.lower() for n, v in vars(bases).items()\n             if n.isupper() and isinstance(v, str)\n             and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}\n    strays, files = [], 0\n    for rel, tree in _tuple_trees():\n        files += 1\n        for name, rgb, alpha in _int_spelled(tree):\n            if name in INT_DATA or alpha == 0 or rgb not in named:\n                continue\n            strays.append(f"{rel}: {name} = {rgb} at alpha {alpha}")\n    assert files >= TUPLE_FILES, f"only {files} files swept -- the walk has gone blind"\n    assert not strays, ("named colours still spelled in integers, where no "\n                        "register move reaches them:\\n  " + "\\n  ".join(strays))\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _picked(src: str, names: set) -> dict:
    """The named top-level definitions, and nothing else, evaluated in source
    order -- the values checked here without importing the module, which
    pulls in PyQt6 and the application's logger."""
    body = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            body.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(t, "id", None) in names:
                body.append(node)
    ns = {"Final": typing.Final}
    exec(compile(ast.Module(body=body, type_ignores=[]), "picked", "exec"), ns)
    missing = set(names) - set(ns)
    assert not missing, f"not found: {sorted(missing)}"
    return ns


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""

    cfg = _picked(tree.read("utils/config.py"),
                  {"_hex6", "_alpha_byte", "translucent", "TRUE_BLACK", "BRAND_GOLD",
                   "SCREEN_OVERLAY_ALPHA", "SCREEN_GRID_ALPHA", "SCREEN_INFO_ALPHA"})
    gold = cfg["BRAND_GOLD"].lstrip("#")
    before = {"_OVERLAY_COLOR": (0, 0, 0, 50),
              "_GOLD_TRANSPARENT": tuple(int(gold[i:i + 2], 16) for i in (0, 2, 4)) + (50,),
              "_INFO_BG": (0, 0, 0, 180)}
    # the old spellings really were those
    src_old = _original(tree, "core/screen_color_picker.py")
    for line in ("_OVERLAY_COLOR = QColor(0, 0, 0, 50)",
                 "_GOLD_TRANSPARENT = QColor(*BRAND_GOLD_RGB, 50)",
                 "_INFO_BG = QColor(0, 0, 0, 180)"):
        assert line in src_old, line
    module = ast.parse(tree.read("core/screen_color_picker.py"))
    for node in module.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) in before:
            name = node.targets[0].id
            inner = node.value.args[0]
            spelled = eval(compile(ast.Expression(inner), name, "eval"), dict(cfg))
            alpha, rgb = int(spelled[1:3], 16), spelled[3:]
            got = tuple(int(rgb[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)
            assert got == before.pop(name), f"{name}: {spelled} is not what it was"
    assert not before, f"not rebuilt: {sorted(before)}"
    assert "BRAND_GOLD_RGB" not in tree.read("core/screen_color_picker.py")
    guard = tree.read(GUARD)
    ast.parse(guard)
    assert "def test_every_tuple_constant_is_derived_by_name" in guard
    assert SENTINEL in guard
# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

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
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


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
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
