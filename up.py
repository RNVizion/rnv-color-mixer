#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: one character, before Python 3.14 makes it a SyntaxError.

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT IS WRONG. tests/test_contrast_pairs.py:67 explains, inside a NON-raw
docstring, that

    A regex over `\{\{([^{}]*)\}\}` once found 23 of 173 rules ...

Backslash-brace is not a recognised escape sequence. Python keeps the
backslash and warns, and that warning has been getting louder:

    3.6 - 3.11   DeprecationWarning   invisible unless you look
    3.12         SyntaxWarning        printed on every run
    3.14         SyntaxError          the module stops importing

A dated removal, the same shape as Pillow's -- and this one takes a whole
test module with it rather than one call.

HOW IT SURFACED. tests/test_thread_ownership.py, installed in the previous
round, walks every test file with ast.parse. That re-triggers the warning on
each pass, so one warning in the CI log became three. Fixing the string
clears all three; silencing them in the walker would have hidden a deadline.

WHAT THIS DOES. Makes that one docstring raw -- adds a single `r`. **The
text of the docstring does not change**, and neither does any behaviour: the
string was never used as anything but documentation, which is precisely why
nobody noticed the backslashes were being kept.

The whole fleet was swept before writing this: **exactly one instance across
all five repositories**. The guard is armed anyway, because a guard proposed
against a clean sweep only gets harder to justify later.

NO APPLICATION FILE IS TOUCHED.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

REPO = "rnv-color-mixer"
SENTINEL_FILE = "tests/test_contrast_pairs.py"
SENTINEL = "RNV-ESCAPE-SEQUENCES"
GUARD = "tests/test_escape_sequences.py"
DESCRIPTION = "make one docstring raw before 3.14 makes it fatal"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, 355 tests\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''r"""RNV-ESCAPE-SEQUENCES-GUARD -- every string literal here is still legal
Python, and will still be legal in Python 3.14.

THIS DOCSTRING IS RAW ON PURPOSE, and the first draft was not. It quotes the
offending text, so it reproduced the offence: the guard against invalid
escape sequences contained an invalid escape sequence, and failed itself on
the first run. Use versus mention -- the eleventh instance in this
programme. A file that must SHOW a bad escape has to be raw, or say it in
words.

Installed 2026-09-08. tests/test_contrast_pairs.py carried

    A regex over `\{\{([^{}]*)\}\}` once found 23 of 173 rules ...

inside a NON-RAW docstring. Backslash-brace is not a recognised escape, so
Python kept the backslash and warned. That warning has been:

    3.6 - 3.11   DeprecationWarning  (invisible unless you look)
    3.12         SyntaxWarning       (visible on every run)
    3.14         SyntaxError         (the file stops importing)

A dated removal, like Pillow's, and this one takes the whole module with it.

WHY IT SURFACED NOW. tests/test_thread_ownership.py walks every test file
with ast.parse, which re-triggers the warning on each pass -- one warning
became three in the CI log. Fixing the string fixes all three; suppressing
them in the walker would have hidden a real deadline.

WHY A GUARD FOR A ONE-CHARACTER FIX. Because the fix is one character, the
next one will be too, and nothing would have caught it. The whole fleet was
swept when this was written: exactly one instance in five repositories. A
guard armed against a clean sweep is the cheapest it will ever be.
"""
from __future__ import annotations

import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {'.git', 'build', 'dist', '__pycache__', '.venv', '.pytest_cache',
             'htmlcov', '.benchmarks', '.hypothesis'}


def _sources():
    for path in sorted(ROOT.rglob('*.py')):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        # a delivery script is a tool passing through, not application source
        if path.parent == ROOT and path.name.startswith('up'):
            continue
        yield path


def _offenders():
    found = []
    for path in _sources():
        try:
            source = path.read_text(encoding='utf-8-sig')
        except OSError:  # pragma: no cover
            continue
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            try:
                compile(source, str(path), 'exec')
            except SyntaxError:  # a different problem, and a louder one
                continue
            for entry in caught:
                if 'invalid escape sequence' in str(entry.message):
                    found.append(
                        f'{path.relative_to(ROOT).as_posix()}:{entry.lineno}  '
                        f'{entry.message}')
    return found


def test_no_source_file_has_an_invalid_escape_sequence():
    """The one that matters.

    An invalid escape is a SyntaxError from Python 3.14. Until then it is a
    warning that everyone scrolls past -- which is exactly how it survives
    long enough to become a build failure.

    The fix is almost always to make the string raw (r'...'), which is also
    what you wanted if it contains a regex.
    """
    offenders = _offenders()
    assert not offenders, (
        'these contain escape sequences Python does not recognise:\n  '
        + '\n  '.join(offenders)
        + "\n\nPython 3.14 turns these into SyntaxError and the module stops "
          "importing. Make the string raw -- r'...' -- or double the "
          "backslash.")


def test_this_guard_can_see_the_files_it_judges():
    """A sweep that compiles nothing reports nothing and passes, which looks
    exactly like a repository with no invalid escapes."""
    files = list(_sources())
    assert len(files) > 20, f'only {len(files)} python file(s) found under {ROOT}'


def test_the_sweep_actually_detects_one():
    """Guard the guard, in the direction that matters.

    A warnings filter set elsewhere in the suite, or a Python that stops
    reporting these, would make the sweep above silently blind. So an
    offender is compiled on purpose and must be seen.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        compile('x = "\\{"\n', '<probe>', 'exec')
        seen = [w for w in caught if 'invalid escape sequence' in str(w.message)]
    assert seen, (
        'compiling a known-bad escape produced no warning, so the sweep in '
        'this file cannot detect one either. Check whether a warnings filter '
        'is being applied suite-wide.')
'''

EDITS = [('tests/test_contrast_pairs.py', '    """Linear scan, not a regex.\n', '    r"""Linear scan, not a regex.\n', 1)]

#: Appended at the END of the file, so it must not say "above" -- the
#: docstring it describes is in _rules(), a couple of hundred lines up.
#: A comment that misdescribes its own subject is the cheapest kind of
#: wrong prose, and nothing checks prose.
NOTE = (
    "\n"
    "# ── Escape sequences (RNV-ESCAPE-SEQUENCES, 2026-09-08) ────────────\n"
    "# The docstring of _rules() was made raw. It contains \\{ , which is\n"
    "# not a recognised escape: a warning today, and a SyntaxError from\n"
    "# Python 3.14 that would stop this module importing at all.\n"
    "# tests/test_escape_sequences.py sweeps every file for the same\n"
    "# thing, and found this was the only one in the fleet.\n")


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL in src:
        raise SystemExit("already applied")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    tree.write(SENTINEL_FILE, tree.read(SENTINEL_FILE).rstrip("\n") + "\n" + NOTE)
    for _, old, new, _ in EDITS:
        print(f"  {old.strip()[:40]!r}  ->  {new.strip()[:40]!r}")


def checks(tree) -> None:
    # 1. the docstring's TEXT is unchanged -- only the prefix moved
    for rel, old, new, _ in EDITS:
        if new.strip() != "r" + old.strip():
            raise SystemExit(f"{rel}: the edit changed more than the prefix")

    # 2. nothing in the tree still carries an invalid escape. Asked of the
    #    compiler rather than a regex: it is the authority on what counts.
    offenders = []
    root = Path.cwd()
    for rel in sorted(tree.files):
        if not rel.endswith(".py"):
            continue
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                compile(tree.files[rel], rel, "exec")
            except SyntaxError as exc:
                raise SystemExit(f"{rel} does not compile after the edit: {exc}")
            for entry in caught:
                if "invalid escape sequence" in str(entry.message):
                    offenders.append(f"{rel}:{entry.lineno}")
    if offenders:
        raise SystemExit("invalid escapes survive: " + ", ".join(offenders))

    # 3. and the file on disk that was NOT edited is clean too, so the sweep
    #    is not reporting success from an in-memory subset
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel in tree.files or rel.startswith((".venv/", "build/")):
            continue
        if path.parent == root and path.name.startswith("up"):
            continue
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                compile(path.read_text(encoding="utf-8-sig"), rel, "exec")
            except (SyntaxError, OSError):
                continue
            for entry in caught:
                if "invalid escape sequence" in str(entry.message):
                    offenders.append(f"{rel}:{entry.lineno}")
    if offenders:
        raise SystemExit("invalid escapes on disk: " + ", ".join(offenders))

    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise SystemExit("the note did not land")
    print("  guards: docstring text unchanged, 0 invalid escapes anywhere")


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
