#!/usr/bin/env python3
"""RNV-GOLD-HOVER — the main surface lights gold under the pointer.

    python up.py             # apply, then run the guard and both suites
    python up.py --check     # rehearse every edit in memory, write nothing

For rnv-color-mixer, derived against a fresh clone at the live head.

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

THE RULING. Every hover on the main surface takes the mode's gold —
BRAND_GOLD (#d2bc93) in dark and image, BRAND_DARK_GOLD (#8c7337) in light.
All five applications already define both under those names. The extras —
About, Settings, other dialogs — were always allowed gold; this extends the
same treatment to the surface, which the mixer's combo box already used it on.

IT WAS SETTLED BY A RENDER, after three readings of the source got it wrong
in the same way — a palette KEY read instead of the widget. The mixer's gold
`scrollbar_hover` is dialogs only. The transformer's `scrollbar_handle_hover`
key is dead while its text windows hover from `theme['accent']`. The icon
builder's zoom slider lives inside `settings_dialog.py`. What settled it was
drawing the control and reading the pixels that changed.

WHAT CHANGES HERE.

    Nine hover rules, three rendered snapshots, and one ramp step.

    utils/config.py                six scrollbar and three slider hover
                                   rules, across all three templates;
                                   APP_HANDLE_EDGE_LIGHT #999999 -> #888888
    snapshots/stylesheet_*.txt     ten lines, regenerated from the app
    tests/test_mixer_wiring.py     #888888 declared in SPLITS with the role
                                   each of its two names plays

THE SURFACE ALREADY DID THIS. `QComboBox:hover` takes a #d2bc93 border here
and the dropdown item's hover text is #d2bc93, both on the main window. The
scrollbar and the slider join a treatment this sheet already uses.

#999999 WAS HELD BY THIS ONE CONSTANT IN THE WHOLE FLEET. Losing the
scrollbar role to the gold left it the slider handle's border and the light
palette's `menu_disabled`, and on those two it moves to #888888 -- which
also lifts disabled menu text from 2.85 to 3.54 against the white menu
ground.

THE GUARD CAUGHT THAT ONE FIRST. Giving #888888 a second name landed
`test_no_undeclared_second_name_for_one_colour` red, which is what it is for
-- a colour with two names is a split with a stated role, or a defect. The
declaration is the fix, and it adds a test, because the check that reads
SPLITS is parametrized over it.

THE WEIGHT SLIDER IN core/color_slot.py IS LEFT ALONE. It has no `:hover`
rule at all and sets its own sheet, so it overrides the main window's slider
rules and will not light up. Giving it one is new behaviour rather than a
recolour, and that wants seeing before it is confirmed.

WHAT THIS ROUND DOES NOT INSTALL: a guard. What already exists covers it —
this repository's is named below and runs first — and in the mixer the three
regenerated stylesheet snapshots are the proof the gold renders.
"""
from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
import tempfile
from importlib.util import find_spec
from pathlib import Path

REPO = "rnv-color-mixer"
SENTINEL_FILE = "tests/conftest.py"
SENTINEL = "RNV-GOLD-HOVER"
GUARD = "tests/test_mixer_wiring.py"
DESCRIPTION = "give the main surface the mode's gold on hover"

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}


def _timeout_flag() -> list:
    """--timeout only when the plugin can actually be imported."""
    return ["--timeout=120"] if find_spec("pytest_timeout") else []


SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q",
            "-p", "no:cacheprovider"]),
          ("\"the LOCKED file\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider"] + _timeout_flag())]

EDITS = [('tests/conftest.py', "# RNV-FLEET-FLOOR, 2026-09-11 -- tests/test_fleet_floor.py holds this\n# application to the fleet's Python floor (3.13, declared and run), the\n", "# RNV-GOLD-HOVER, 2026-09-12 -- every hover on the main surface takes the\n# mode's gold: BRAND_GOLD in dark and image, BRAND_DARK_GOLD in light. The\n# extras were always allowed it; this extends the same treatment to the\n# surface, which already used it on the mixer's combo box. Two ramp steps\n# lost their last consumer on the way and are retired.\n# RNV-FLEET-FLOOR, 2026-09-11 -- tests/test_fleet_floor.py holds this\n# application to the fleet's Python floor (3.13, declared and run), the\n", 1), ('utils/config.py', 'QScrollBar::handle:vertical:hover {{\n    background-color: rgba(68, 68, 68, 0.9);', 'QScrollBar::handle:vertical:hover {{\n    background-color: {BRAND_GOLD};', 1), ('utils/config.py', 'QScrollBar::handle:horizontal:hover {{\n    background-color: rgba(68, 68, 68, 0.9);', 'QScrollBar::handle:horizontal:hover {{\n    background-color: {BRAND_GOLD};', 1), ('utils/config.py', 'QScrollBar::handle:vertical:hover {{\n    background-color: {APP_HANDLE_EDGE_LIGHT};', 'QScrollBar::handle:vertical:hover {{\n    background-color: {BRAND_DARK_GOLD};', 1), ('utils/config.py', 'QScrollBar::handle:horizontal:hover {{\n    background-color: {APP_HANDLE_EDGE_LIGHT};', 'QScrollBar::handle:horizontal:hover {{\n    background-color: {BRAND_DARK_GOLD};', 1), ('utils/config.py', 'QScrollBar::handle:vertical:hover {{\n    background-color: rgba(100, 100, 100, 200);', 'QScrollBar::handle:vertical:hover {{\n    background-color: {BRAND_GOLD};', 1), ('utils/config.py', 'QScrollBar::handle:horizontal:hover {{\n    background-color: rgba(100, 100, 100, 200);', 'QScrollBar::handle:horizontal:hover {{\n    background-color: {BRAND_GOLD};', 1), ('utils/config.py', 'QSlider::handle:horizontal:hover {{\n    background: {APP_HANDLE_HOVER_DARK};', 'QSlider::handle:horizontal:hover {{\n    background: {BRAND_GOLD};', 2), ('utils/config.py', 'QSlider::handle:horizontal:hover {{\n    background: {APP_CONTROL_DIM};', 'QSlider::handle:horizontal:hover {{\n    background: {BRAND_DARK_GOLD};', 1), ('utils/config.py', 'APP_HANDLE_EDGE_LIGHT: Final[str] = "#999999"\n"""The emphasised edge of a light handle: the slider handle\'s border, and the\nscrollbar handle when hovered."""', 'APP_HANDLE_EDGE_LIGHT: Final[str] = "#888888"\n"""The emphasised edge of a light handle: the slider handle\'s border.\n\nRNV-GOLD-HOVER, 2026-09-12: the light scrollbar handle on hover used to read\nthis too, and now takes BRAND_DARK_GOLD with every other hover on the main\nsurface. What is left is the border, and the light palette\'s `menu_disabled`.\nThe value was #999999, a step this constant held alone in the whole fleet;\nagainst the white menu ground #888888 lifts disabled menu text from 2.85 to\n3.54."""', 1), ('tests/test_mixer_wiring.py', '    \'#eeeeee\': {\'APP_HANDLE_HOVER_DARK\': \'a dark ink-grid step, app-owned\',\n                \'APP_ITEM_HOVER_LIGHT\': \'the light register plate APP["hover-light"]\'},\n}', '    \'#eeeeee\': {\'APP_HANDLE_HOVER_DARK\': \'a dark ink-grid step, app-owned\',\n                \'APP_ITEM_HOVER_LIGHT\': \'the light register plate APP["hover-light"]\'},\n    # RNV-GOLD-HOVER, 2026-09-12. The light handle edge held a step no other\n    # application used and nothing else in this one, and it lost its scrollbar\n    # role to the gold. It now takes the step this file already calls hint and\n    # muted text. Two roles, one value, both stated: as the #666666 split above.\n    \'#888888\': {\'APP_HINT_DARK\': \'hint and muted text in dark and image\',\n                \'APP_HANDLE_EDGE_LIGHT\': \'the light slider handle edge, and the \'\n                                         \'light palette\\\'s disabled menu label\'},\n}', 1), ('tests/test_mixer_wiring.py', '  * the two SPLITS: #444444 and #666666 each carry two constants, because each\n    plays two roles, and the guard states which name goes with which role;', '  * the SPLITS: each value in that table carries two constants, because each\n    plays two roles, and the guard states which name goes with which role.\n    Written as a count of two when this file was installed, which stopped\n    being true the moment #eeeeee was declared and nobody noticed -- a\n    parametrized test now names every entry, so the table is its own record\n    and this line does not have to be;', 1), ('snapshots/stylesheet_dark.txt', '    background: #eeeeee;\n', '    background: #d2bc93;\n', 1), ('snapshots/stylesheet_dark.txt', 'QScrollBar::handle:vertical:hover {\n    background-color: rgba(68, 68, 68, 0.9);\n', 'QScrollBar::handle:vertical:hover {\n    background-color: #d2bc93;\n', 1), ('snapshots/stylesheet_dark.txt', 'QScrollBar::handle:horizontal:hover {\n    background-color: rgba(68, 68, 68, 0.9);\n', 'QScrollBar::handle:horizontal:hover {\n    background-color: #d2bc93;\n', 1), ('snapshots/stylesheet_light.txt', '    border: 1px solid #999999;\n', '    border: 1px solid #888888;\n', 1), ('snapshots/stylesheet_light.txt', '    background: #555555;\n', '    background: #8c7337;\n', 1), ('snapshots/stylesheet_light.txt', 'QScrollBar::handle:vertical:hover {\n    background-color: #999999;\n', 'QScrollBar::handle:vertical:hover {\n    background-color: #8c7337;\n', 1), ('snapshots/stylesheet_light.txt', 'QScrollBar::handle:horizontal:hover {\n    background-color: #999999;\n', 'QScrollBar::handle:horizontal:hover {\n    background-color: #8c7337;\n', 1), ('snapshots/stylesheet_image.txt', '    background: #eeeeee;\n', '    background: #d2bc93;\n', 1), ('snapshots/stylesheet_image.txt', 'QScrollBar::handle:vertical:hover {\n    background-color: rgba(100, 100, 100, 200);\n', 'QScrollBar::handle:vertical:hover {\n    background-color: #d2bc93;\n', 1), ('snapshots/stylesheet_image.txt', 'QScrollBar::handle:horizontal:hover {\n    background-color: rgba(100, 100, 100, 200);\n', 'QScrollBar::handle:horizontal:hover {\n    background-color: #d2bc93;\n', 1)]

#: Values whose last consumer this round removes. Empty where the round only
#: rewires a role and retires nothing.
GONE = {'#999999'}


def edits(tree) -> None:
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))


def _is_source(path: Path, text: str) -> bool:
    """Application source and its records -- not this script, not a guard."""
    if path.name.startswith("up") or "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
        return False
    if path.name.startswith("test_") or path.name == "conftest.py":
        return False
    return "__pycache__" not in path.parts and ".git" not in path.parts


def _uses_value(text: str, value: str, is_python: bool) -> bool:
    """Is this value USED here, or only mentioned?

    In Python a colour is a string inside an assignment or an f-string
    template; a BARE string statement is documentation, and this fleet
    writes its constants exactly that way -- the annotated assignment on one
    line, a triple-quoted paragraph on the next as the attribute's note. So
    every `Expr` holding a string is skipped and everything else is read.
    The check that preceded this one matched the retired hex anywhere in a
    file and landed red on the docstring written to record the retirement.

    A rendered snapshot has no syntax and no prose; there the text IS the
    value, so plain matching is what that file wants.
    """
    if not is_python:
        return value in text
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return value in text
    documentation = {id(n.value) for n in ast.walk(tree)
                     if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                     and isinstance(n.value.value, str)}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in documentation and value in node.value):
            return True
    return False


def checks(tree) -> None:
    root = Path.cwd()

    # 1. Nothing this round retires is still used in application source.
    for value in sorted(GONE):
        left = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in (".py", ".txt", ".ambr"):
                continue
            rel = path.relative_to(root).as_posix()
            text = tree.files.get(rel)
            if text is None:
                try:
                    text = path.read_text(encoding="utf-8-sig", errors="replace")
                except OSError:
                    continue
            if _is_source(path, text) and _uses_value(text, value, path.suffix == ".py"):
                left.append(rel)
        if left:
            raise SystemExit(f"{value} still in application source: {left}")

    # 2. Every Python file this round edits still parses. A dropped import or
    #    a half-removed tuple entry is a syntax error, and the cheapest place
    #    to find one is before anything is written.
    for rel in sorted({rel for rel, *_ in EDITS}):
        if not rel.endswith(".py"):
            continue
        try:
            # lstrip the BOM: it is a legal first character of a file and an
            # illegal first token of a module. One file in this fleet has one.
            ast.parse(tree.read(rel).lstrip("\ufeff"), rel)
        except SyntaxError as exc:
            raise SystemExit(f"{rel} no longer parses: {exc}")

    # 3. The sentinel is in the file the already-applied check reads.
    if SENTINEL not in tree.files[SENTINEL_FILE]:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    # NO CHECK HERE ASSERTS THE GOLD LANDED, and that is deliberate. Every
    # way of asking before the write -- is BRAND_GOLD in the file, does the
    # hover rule name it -- is true because the edits above wrote it, and a
    # check that cannot fail is the shape this fleet's own vacuity guard
    # forbids. What verifies the landing is downstream and real: the mixer's
    # regenerated stylesheet snapshots and the palette mirrors in every
    # repository, all of which verify() runs.
    print(f"  guards: {len(GONE)} value(s) retired and gone, "
          f"{len({rel for rel, *_ in EDITS if rel.endswith('.py')})} file(s) parse")


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
        self.deleted: set[str] = set()

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush().

        Added for the round that retired the last CI deselect: with no
        deselects left, tests/test_ci_deselects.py swept an empty set and
        would have passed over nothing. Its own failure message said to
        delete it in the commit that removed the last one, so the harness
        needed to be able to.
        """
        if not (self.root / rel).exists() and rel not in self.files:
            raise SystemExit(f"cannot delete {rel}: it is not in this checkout")
        self.files.pop(rel, None)
        self.deleted.add(rel)

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
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
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
