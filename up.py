#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: stop calling Image.getdata(), which Pillow removes on 2027-10-15.

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

THE DEADLINE IS REAL AND DATED. Pillow 12.1 deprecated `Image.getdata()` and
Pillow 14 removes it, on 2027-10-15, naming `get_flattened_data()` as the
replacement. On that day these call sites stop working -- and in three colour
applications, sampling colour out of an image is not a side feature.

THE OBVIOUS FIX IS WRONG. Swapping the call breaks the application today,
because `get_flattened_data` does not exist before Pillow 12.1 and this
project supports Pillow 10. Measured across six releases in a clean
virtualenv rather than assumed:

    Pillow 10.4.0   get_flattened_data absent    getdata not deprecated
    Pillow 11.0.0   absent                       not deprecated
    Pillow 11.3.0   absent                       not deprecated
    Pillow 12.0.0   absent                       not deprecated
    Pillow 12.1.0   PRESENT                      DEPRECATED
    Pillow 12.2.0   present                      deprecated

So the call has to ask the object which API it has. This installs
utils/pil_compat.py, which asks once, and routes 1 call site(s) through it.

The two APIs are behaviourally identical -- same length, same tuples, same
palette indices -- verified on RGB, RGBA, L and P.

WHAT DOES NOT CHANGE. No colour, no pixel, no palette. `flat_pixels(x)`
returns precisely what `list(x.getdata())` returned.

A NOTE ON THE PINS, WHICH THIS SCRIPT DOES NOT TOUCH. This repository declares
Pillow in two files and they disagree. That is worth a decision of its own and
is reported separately; nothing here changes a dependency.
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
SENTINEL_FILE = "core/image_handler.py"
SENTINEL = "RNV-PIL-COMPAT"
GUARD = "tests/test_pil_compat.py"
MODULE = "utils/pil_compat.py"
DESCRIPTION = "route Image.getdata() through a compatibility helper"
SUITES = [("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("the LOCKED file, 355 tests", [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py",
           "pil_compat.py"}

MODULE_SOURCE = r'''"""Pillow compatibility -- one API that moved under us, in one place.

WHY THIS FILE EXISTS. `Image.getdata()` was deprecated in Pillow 12.1 and will
be REMOVED in Pillow 14, dated 2027-10-15. The deprecation names
`get_flattened_data()` as its replacement.

The obvious fix -- swap the call -- breaks this application today, because
`get_flattened_data` does not exist before Pillow 12.1 and this project
supports Pillow 10. Measured rather than assumed:

    Pillow 10.4.0   get_flattened_data absent    getdata not deprecated
    Pillow 11.0.0   absent                       not deprecated
    Pillow 11.3.0   absent                       not deprecated
    Pillow 12.0.0   absent                       not deprecated
    Pillow 12.1.0   PRESENT                      DEPRECATED
    Pillow 12.2.0   present                      deprecated

So the call has to ask which Pillow it is running on. Asking once, here, is
better than asking at each call site: there were five of them across three
applications, and the next person to add a sixth will not know to ask.

The two are behaviourally identical -- same length, same tuples, same palette
indices -- verified on RGB, RGBA, L and P in tests/test_pil_compat.py.
"""
from __future__ import annotations

from typing import Any


def flat_pixels(image: Any) -> list:
    """Every pixel of `image`, in row-major order.

    The replacement for `list(image.getdata())`. Returns exactly what that
    returned: RGB and RGBA give tuples, L gives ints, P gives palette indices.

    `getattr` rather than a version comparison on purpose. A version string
    answers "which Pillow is this", which is a proxy for the question actually
    being asked -- "does this object have the method" -- and the proxy is wrong
    for anyone running a fork, a pre-release, or a vendored build.
    """
    getter = getattr(image, "get_flattened_data", None)
    return list(getter() if getter is not None else image.getdata())
'''

GUARD_SOURCE = r'''"""RNV-PIL-COMPAT-GUARD -- getdata() is removed in Pillow 14, and this is why
nothing here calls it.

Installed 2026-09-07. `Image.getdata()` was deprecated in Pillow 12.1 and is
removed in Pillow 14, dated 2027-10-15. Every call site now goes through
utils.pil_compat.flat_pixels, which picks the available API at runtime.

WHAT MAKES THIS GUARD HARD TO WRITE HONESTLY. Whichever Pillow the suite runs
on, only ONE branch of the helper executes. A test that exercises the
installed branch and reports green says nothing about the other one -- and the
other one is the one that matters, because it is either the future (removal)
or the past (every version this project still supports). So both branches are
driven explicitly, with stand-in objects, rather than being left to whichever
Pillow happens to be installed.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from PIL import Image

from utils.pil_compat import flat_pixels

ROOT = Path(__file__).resolve().parent.parent

#: The one file allowed to name the deprecated API, plus the tests that must
#: mention it to talk about it.
ALLOWED = ('utils/pil_compat.py', 'tests/test_pil_compat.py')


def _images():
    base = Image.new('RGB', (3, 2), (10, 20, 30))
    return {'RGB': base,
            'RGBA': base.convert('RGBA'),
            'L': base.convert('L'),
            'P': base.convert('P')}


@pytest.mark.parametrize('mode', ['RGB', 'RGBA', 'L', 'P'])
def test_flat_pixels_matches_the_api_this_pillow_has(mode):
    """Whatever this Pillow provides, the helper returns exactly it."""
    image = _images()[mode]
    getter = getattr(image, 'get_flattened_data', None)
    expected = list(getter() if getter is not None else image.getdata())
    assert flat_pixels(image) == expected
    assert len(flat_pixels(image)) == image.width * image.height


class _OldPillow:
    """An image object as Pillow 10 through 12.0 present one: getdata, and no
    get_flattened_data. Driving this explicitly is the only way to exercise
    the fallback on a machine running 12.1 or later."""

    def __init__(self, data):
        self._data = data
        self.calls = 0

    def getdata(self):
        self.calls += 1
        return iter(self._data)


class _NewPillow:
    """And the other side: get_flattened_data present. On an older Pillow this
    is the only way to exercise the branch that will be the ONLY branch once
    Pillow 14 removes getdata entirely."""

    def __init__(self, data):
        self._data = data
        self.calls = 0

    def get_flattened_data(self):
        self.calls += 1
        return iter(self._data)

    def getdata(self):  # pragma: no cover -- must never be reached
        raise AssertionError(
            'flat_pixels called getdata() on an object that has '
            'get_flattened_data. After Pillow 14 that method is gone.')


def test_the_old_api_is_used_when_it_is_the_only_one():
    data = [(1, 2, 3), (4, 5, 6)]
    old = _OldPillow(data)
    assert flat_pixels(old) == data
    assert old.calls == 1


def test_the_new_api_is_preferred_when_present():
    data = [(1, 2, 3), (4, 5, 6)]
    new = _NewPillow(data)
    assert flat_pixels(new) == data
    assert new.calls == 1


def test_the_result_is_a_list_not_a_generator():
    """Callers index it, take len() of it, and iterate it more than once.
    Both underlying APIs can return something lazy."""
    result = flat_pixels(_OldPillow([(1, 2, 3), (4, 5, 6)]))
    assert isinstance(result, list)
    assert len(result) == 2
    assert list(result) == list(result)


def test_no_source_file_calls_getdata_directly():
    """The point of the helper. A call that bypasses it is a call that stops
    working on 2027-10-15, and it will not announce itself -- the deprecation
    warning is silent in a passing suite."""
    offenders = []
    for path in sorted(ROOT.rglob('*.py')):
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED or rel.startswith(('build/', '.venv/')):
            continue
        if path.parent == ROOT and path.name.startswith('up'):
            continue          # a delivery script names what it moves
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith('#'):
                continue
            if re.search(r'\.getdata\s*\(', line):
                offenders.append(f'{rel}:{lineno}  {line.strip()[:70]}')
    assert not offenders, (
        'these call Image.getdata() directly, which Pillow 14 removes on '
        '2027-10-15:\n  ' + '\n  '.join(offenders)
        + '\n\nUse utils.pil_compat.flat_pixels instead.')


def test_the_sweep_above_can_see_this_repository():
    """Guard the guard. A sweep that walks no files finds no offenders and
    passes, which looks exactly like a clean repository."""
    seen = [p for p in ROOT.rglob('*.py')
            if not p.relative_to(ROOT).as_posix().startswith(('build/', '.venv/'))]
    assert len(seen) > 20, f'only {len(seen)} python files found under {ROOT}'


def test_the_helper_is_reached_from_where_it_is_needed():
    """The other direction: the sweep only proves nothing calls the old API.
    This proves something calls the new one -- otherwise deleting every call
    site would also pass."""
    users = []
    for path in sorted(ROOT.rglob('*.py')):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(('tests/', 'build/', '.venv/')) or rel == 'utils/pil_compat.py':
            continue
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        if 'flat_pixels' in text:
            users.append(rel)
    assert users, ('nothing imports flat_pixels. Either the call sites were '
                   'removed, or the helper was installed and never wired.')
'''

EDITS = [('core/image_handler.py', 'from core.color_math import ColorMath\n', 'from core.color_math import ColorMath\nfrom utils.pil_compat import flat_pixels\n', 1), ('core/image_handler.py', '            pixels = list(region.getdata())\n', '            pixels = flat_pixels(region)\n', 1)]

POINTER = (
    "\n"
    "# RNV-PIL-COMPAT (2026-09-07): pixel access in this file goes through\n"
    "# utils.pil_compat.flat_pixels, not Image.getdata(), which Pillow removes\n"
    "# on 2027-10-15. tests/test_pil_compat.py fails if a direct call returns.\n")


def edits_fn(tree) -> None:
    tree.write(MODULE, MODULE_SOURCE)
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    src = tree.read(SENTINEL_FILE)
    if SENTINEL in src:
        raise SystemExit("already applied")
    tree.write(SENTINEL_FILE, src.rstrip("\n") + "\n" + POINTER)
    print(f"  installed {MODULE}")
    print(f"  {len([e for e in EDITS if 'getdata' in e[1]])} call site(s) rerouted")


edits = edits_fn


def checks(tree) -> None:
    module = tree.read(MODULE)
    if "get_flattened_data" not in module or "getdata" not in module:
        raise SystemExit("the helper does not reference both APIs")
    # It must ask the OBJECT, not the version. A version comparison is a proxy
    # for the real question and is wrong for a fork or a vendored build.
    if "getattr(image" not in module:
        raise SystemExit("the helper does not probe the object for the method")

    # no direct call survives outside the helper and the tests
    offenders = []
    root = Path.cwd()
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel in (MODULE, GUARD) or rel.startswith(("build/", ".venv/")):
            continue
        if path.parent == root and path.name.startswith("up"):
            continue
        text = tree.files[rel] if rel in tree.files else \
            path.read_text(encoding="utf-8-sig", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if re.search(r"\.getdata\s*\(", line):
                offenders.append(f"{rel}:{lineno}")
    if offenders:
        raise SystemExit("direct getdata() calls survive: " + ", ".join(offenders))

    # and the helper is actually reached -- deleting every call site would
    # also satisfy the sweep above
    users = [rel for rel in tree.files
             if rel not in (MODULE, GUARD) and "flat_pixels" in tree.files[rel]]
    if not users:
        raise SystemExit("nothing was wired to flat_pixels")

    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise SystemExit("the pointer comment did not land")
    print(f"  guards: 0 direct getdata() calls, helper probes the object, "
          f"{len(users)} file(s) wired")


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
