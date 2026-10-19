"""The mixer: the History tab's five sample colors in lower case

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (da6e475).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-18: #66 A. Hex is lower case in source (ruled 2026-08-14 and
2026-09-25). This app's own sample colors were written in capitals, kept so
under #56 A so that no shown text moved. Chris ruled that app-owned sample
data is held to the notation rule too.

WHAT LANDS.
  brand_map.json: the five values in lower case.
  utils/colors.py and COLORS.md, written from the map by
    tools/sync_colors.py, as the color file always is; the comment and
    docstring that named the upper case say lower case.

WHAT SHOWS. The History tab's fallback rows, shown only when its history
module cannot load, write their hex in lower case: #ff5733 for #FF5733, and
so on. That is how a real History row writes its own. Each row's swatch is
the color it was.

JUDGMENT CALLS, each reported:
  - The values change through brand_map.json and tools/sync_colors.py, not
    by hand, as every color in the color file does.

NO COLOR MOVES. Each value is the one it was, lower-cased; every other value
in the color file is what it was.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tokenize
import types
from pathlib import Path

REPO = 'rnv-color-mixer'
SENTINEL = '#66 A'   # the color file names the ruling that lower-cased its samples
SENTINEL_FILE = 'utils/colors.py'
GUARD = 'tests/test_colors_in_sync.py'
GUARD_FILES = ['tests/test_colors_in_sync.py', 'tests/test_named_and_used.py', 'tests/test_derived_values.py']
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "The mixer: the History tab's five sample colors in lower case"

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS: the locked file's hash first, both
#: suites under coverage, the combine, and the floor. The Windows workflow runs
#: the same two suites without coverage.
_LOCK = ("import hashlib, sys\n"
         "want = 'ec45a92e92ffa1179b36bf4fe9a37727983b2fb31b7b704448e9fb1c4a75ad1b'\n"
         "got = hashlib.sha256(open('test_rnv_color_mixer.py', 'rb').read()).hexdigest()\n"
         "if got != want:\n"
         "    raise AssertionError(f'locked file changed: {got}')\n"
         "print('Locked file SHA-256 matches:', got)\n")
#: coverage exits 2 for a shortfall, which this harness would read as the
#: environment; wrapped so falling under the floor reads as a failure.
#: THIS SCRIPT IS LEFT OUT OF THE MEASURE. .coveragerc measures every file in
#: the checkout, run or not, and while this file is in it this file is one:
#: several hundred statements at 0%. CI never sees it, so counting it measured
#: something CI does not, and a long script could fall under the floor on its
#: own weight. Measured 2026-10-04: 69.6 with a 1,030-line script, 73.4 without.
_FLOOR = ("import subprocess, sys\n"
          "r = subprocess.run([sys.executable, '-m', 'coverage', 'report', "
          "'--fail-under=69', '--omit=' + sys.argv[1]])\n"
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
    ("CI: coverage floor 69", [sys.executable, "-c", _FLOOR, Path(__file__).name]),
]

#: The workflows SUITES mirrors, by content hash, as this round leaves them.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '64c1ab0ff2bc09144f9160df2b84a9a7ce8131ebb90ccba5deb366a04d7c3251', '.github/workflows/tests-windows.yml': '7e0337fd001cffec4b8d261ef05126ab371d8e08d529bcdc30084e8ed08fb580'}

SHADOWS = ['colors.py', 'conftest.py', 'run_tests.py', 'sync_colors.py', 'test_colors_in_sync.py', 'test_derived_values.py', 'test_named_and_used.py', 'test_rnv_color_mixer.py']

LEFT_ALONE = ['every other value, and every color drawn: the swatches are the colors they were.', 'hex that is upper case on purpose: user data, and the test inputs that check either case is read, each named in tests/color_values.py with its reason.', 'rnv-brand, which the brand chat keeps.']

# ======================================================================== this round

COLOR_FILE = 'utils/colors.py'

#: each name this round lower-cases, and the value the head wrote
WAS = {'HISTORY_SAMPLE_ORANGE_RED': '#FF5733', 'HISTORY_SAMPLE_GREEN': '#33FF57', 'HISTORY_SAMPLE_BLUE': '#3357FF', 'HISTORY_SAMPLE_MAGENTA': '#FF33F5', 'HISTORY_SAMPLE_YELLOW': '#F5FF33'}

#: sha256 of each file the round reaches, as the head holds it
BASE_SHAS = {'COLORS.md': '6ddcb27d0b79eb60b3042caa42d02a1282b1bacdfdb7aa92702b78581d9f535b', 'brand_map.json': '5a0570da6740f45a059710c21f57011514983118bb3092d1577b24a22a5aea06', 'utils/colors.py': 'a28562545dba15a5eae5f019d9db9262b7f0d3825096159d6b912b4c38bb89b9'}

#: (file, anchor, replacement), applied in order; each anchor is found exactly once
SUBS = [('COLORS.md', "| `CANVAS_LABEL_PLATE_LIGHT` | `#c8c8c8` | The plate behind a dragged selection's size, in light. | — |\n| `HISTORY_SAMPLE_ORANGE_RED` | `#FF5733` | Data, not chrome: the first sample row the History tab shows when the history module cannot be loaded (#56 A). | — |\n| `HISTORY_SAMPLE_GREEN` | `#33FF57` | Data, not chrome: the second sample row of the History tab's fallback (#56 A). | — |\n| `HISTORY_SAMPLE_BLUE` | `#3357FF` | Data, not chrome: the third sample row of the History tab's fallback (#56 A). | — |\n| `HISTORY_SAMPLE_MAGENTA` | `#FF33F5` | Data, not chrome: the fourth sample row of the History tab's fallback (#56 A). | — |\n| `HISTORY_SAMPLE_YELLOW` | `#F5FF33` | Data, not chrome: the fifth sample row of the History tab's fallback (#56 A). | — |\n\n", "| `CANVAS_LABEL_PLATE_LIGHT` | `#c8c8c8` | The plate behind a dragged selection's size, in light. | — |\n| `HISTORY_SAMPLE_ORANGE_RED` | `#ff5733` | Data, not chrome: the first sample row the History tab shows when the history module cannot be loaded (#56 A). | — |\n| `HISTORY_SAMPLE_GREEN` | `#33ff57` | Data, not chrome: the second sample row of the History tab's fallback (#56 A). | — |\n| `HISTORY_SAMPLE_BLUE` | `#3357ff` | Data, not chrome: the third sample row of the History tab's fallback (#56 A). | — |\n| `HISTORY_SAMPLE_MAGENTA` | `#ff33f5` | Data, not chrome: the fourth sample row of the History tab's fallback (#56 A). | — |\n| `HISTORY_SAMPLE_YELLOW` | `#f5ff33` | Data, not chrome: the fifth sample row of the History tab's fallback (#56 A). | — |\n\n"), ('brand_map.json', '    "HISTORY_SAMPLE_ORANGE_RED": {\n      "app": "#FF5733",\n      "why": "Data, not chrome: the first sample row the History tab shows when the history module cannot be loaded (#56 A)."\n    },\n    "HISTORY_SAMPLE_GREEN": {\n      "app": "#33FF57",\n      "why": "Data, not chrome: the second sample row of the History tab\'s fallback (#56 A)."\n    },\n    "HISTORY_SAMPLE_BLUE": {\n      "app": "#3357FF",\n      "why": "Data, not chrome: the third sample row of the History tab\'s fallback (#56 A)."\n    },\n    "HISTORY_SAMPLE_MAGENTA": {\n      "app": "#FF33F5",\n      "why": "Data, not chrome: the fourth sample row of the History tab\'s fallback (#56 A)."\n    },\n    "HISTORY_SAMPLE_YELLOW": {\n      "app": "#F5FF33",\n      "why": "Data, not chrome: the fifth sample row of the History tab\'s fallback (#56 A)."\n', '    "HISTORY_SAMPLE_ORANGE_RED": {\n      "app": "#ff5733",\n      "why": "Data, not chrome: the first sample row the History tab shows when the history module cannot be loaded (#56 A)."\n    },\n    "HISTORY_SAMPLE_GREEN": {\n      "app": "#33ff57",\n      "why": "Data, not chrome: the second sample row of the History tab\'s fallback (#56 A)."\n    },\n    "HISTORY_SAMPLE_BLUE": {\n      "app": "#3357ff",\n      "why": "Data, not chrome: the third sample row of the History tab\'s fallback (#56 A)."\n    },\n    "HISTORY_SAMPLE_MAGENTA": {\n      "app": "#ff33f5",\n      "why": "Data, not chrome: the fourth sample row of the History tab\'s fallback (#56 A)."\n    },\n    "HISTORY_SAMPLE_YELLOW": {\n      "app": "#f5ff33",\n      "why": "Data, not chrome: the fifth sample row of the History tab\'s fallback (#56 A)."\n'), ('utils/colors.py', '# RNV-COLOR-SYNC (2026-10-17), #56 A: colors the application\'s own code\n# still wrote out, named here at the value and in the case they had, so\n# no pixel and no line of shown text moves. Each is DATA, the\n# application\'s own, and a brand move never touches it.\n\nHISTORY_SAMPLE_ORANGE_RED: Final[str] = "#FF5733"  # app-owned\n"""The first of five sample rows the History tab shows when the history\nmodule cannot be loaded (core/package_d_panel.py,\n_populate_history_placeholder). Data, not chrome: each row shows its\ncolor and its hex, in the upper case written here. App-owned."""\n\nHISTORY_SAMPLE_GREEN: Final[str] = "#33FF57"  # app-owned\n"""The second sample row of the History tab\'s fallback. App-owned."""\n\nHISTORY_SAMPLE_BLUE: Final[str] = "#3357FF"  # app-owned\n"""The third sample row of the History tab\'s fallback. App-owned."""\n\nHISTORY_SAMPLE_MAGENTA: Final[str] = "#FF33F5"  # app-owned\n"""The fourth sample row of the History tab\'s fallback. App-owned."""\n\nHISTORY_SAMPLE_YELLOW: Final[str] = "#F5FF33"  # app-owned\n"""The fifth sample row of the History tab\'s fallback. App-owned."""\n', '# RNV-COLOR-SYNC (2026-10-17), #56 A: colors the application\'s own code\n# still wrote out, named here at the value they had, so no pixel moves.\n# #66 A (2026-10-18) wrote them in lower case, as every hex in the source\n# is. Each is DATA, the application\'s own, and a brand move never\n# touches it.\n\nHISTORY_SAMPLE_ORANGE_RED: Final[str] = "#ff5733"  # app-owned\n"""The first of five sample rows the History tab shows when the history\nmodule cannot be loaded (core/package_d_panel.py,\n_populate_history_placeholder). Data, not chrome: each row shows its\ncolor and its hex, in lower case, as a real History row writes its own\n(#66 A). App-owned."""\n\nHISTORY_SAMPLE_GREEN: Final[str] = "#33ff57"  # app-owned\n"""The second sample row of the History tab\'s fallback. App-owned."""\n\nHISTORY_SAMPLE_BLUE: Final[str] = "#3357ff"  # app-owned\n"""The third sample row of the History tab\'s fallback. App-owned."""\n\nHISTORY_SAMPLE_MAGENTA: Final[str] = "#ff33f5"  # app-owned\n"""The fourth sample row of the History tab\'s fallback. App-owned."""\n\nHISTORY_SAMPLE_YELLOW: Final[str] = "#f5ff33"  # app-owned\n"""The fifth sample row of the History tab\'s fallback. App-owned."""\n')]

#: sha256 of every file as this round writes it
WANT = {'COLORS.md': 'a31eebddb8b7fb43151edde4f1043dcb94d70812e9480b0292f387e9faaab595', 'brand_map.json': '93bd648ac8f1d622918211bba2bd2cf58cd69b01bb1a6675e361332caef57421', 'utils/colors.py': 'ba8011d1b0a9323b2088362f518f73aac0664f31c686900dcb70d1474e2f5af1'}


def edits(tree) -> None:
    for rel, was in BASE_SHAS.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        if got != was:
            raise Stop(f"{rel} is not the head's file this round was derived from ({got[:12]}). "
                       f"Nothing was written. The file moved; re-derive before trusting the script.",
                       EXIT_CANNOT_RUN)
    for rel, old, new in SUBS:
        tree.sub(rel, old, new)


def _module(tree, text: str):
    module = types.ModuleType("utils.colors")
    module.__file__ = str(tree.root / COLOR_FILE)
    added = str(tree.root) not in sys.path
    if added:
        sys.path.insert(0, str(tree.root))
    try:
        exec(compile(text, COLOR_FILE, "exec"), module.__dict__)
    finally:
        if added:
            sys.path.remove(str(tree.root))
    return module


def _values(module) -> dict:
    return {k: v for k, v in vars(module).items() if not k.startswith("__")
            and not callable(v) and not isinstance(v, (types.ModuleType, type))
            and type(v).__eq__ is not object.__eq__}


def checks(tree) -> None:
    # ---- the head's color file, then the round's, each run as written
    was = _values(_module(tree, _original(tree, COLOR_FILE)))
    now = _values(_module(tree, tree.read(COLOR_FILE)))
    assert sorted(was) == sorted(now), f"names came or went: {sorted(set(was) ^ set(now))}"
    assert len(was) >= 40, f"only {len(was)} values compared -- the comparison is blind"
    for name, value in WAS.items():
        assert was[name] == value, f"{name} was {was[name]!r} at the head, not {value!r}"
        assert now[name] == value.lower(), f"{name} is {now[name]!r}, not {value.lower()!r}"
    other = sorted(k for k in was if k not in WAS and not (type(was[k]) is type(now[k]) and was[k] == now[k]))
    assert not other, f"other values moved: {other}"
    # ---- no hex the color file defines is written in capitals now
    capitals = [f"{n.lineno}: {n.value}" for n in ast.walk(ast.parse(tree.read(COLOR_FILE)))
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and re.fullmatch(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", n.value) and n.value != n.value.lower()]
    assert not capitals, f"hex in capitals in {COLOR_FILE}: {capitals}"
    # ---- the map holds what the color file holds
    brand_map = json.loads(tree.read("brand_map.json"))
    for name, value in WAS.items():
        assert brand_map["colors"][name]["app"] == value.lower(), (name, brand_map["colors"][name])
    # ---- every file this round writes, as it writes it
    assert sorted(tree.files) == sorted(WANT), f"this round writes {sorted(tree.files)}"
    assert not tree.deleted, f"this round removes {sorted(tree.deleted)}"
    for rel, want in WANT.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == want, f"{rel} is not the file this round writes: {got[:12]}"

def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


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
