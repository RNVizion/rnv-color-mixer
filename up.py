#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: make the test-tooling pins agree with the other four applications.

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT WAS WRONG, AND IT IS ARITHMETIC RATHER THAN OPINION. Across the five
applications, two packages are declared with ranges that NO single version
satisfies:

    pytest       picker  ==9.0.2          icon builder  >=8.0.0,<9.0.0
    pytest-cov   picker  ==7.1.0          icon builder  >=5.0.0,<7.0.0

There is no version of pytest that is both exactly 9.0.2 and below 9.0.0.
So on one interpreter -- which is what a laptop is -- installing the
picker's dev requirements and then the icon builder's UNINSTALLS pytest 9
and installs pytest 8; going the other way undoes it. Every switch between
those two repositories rewrites site-packages, and the window while pip is
mid-swap is a partially-populated _pytest package. That is exactly the
shape of

    ModuleNotFoundError: No module named '_pytest.compat'

appearing seconds after the same command had succeeded. No amount of care
about install order fixes it, because the constraint is unsatisfiable.

THE CAPS HAD NO EVIDENCE BEHIND THEM. The icon builder's `pytest<9.0.0` and
`pytest-cov<7.0.0` were tested rather than trusted. On pytest 9.1.1 with
pytest-cov 7.1.0 -- both past its own ceiling -- its suite passes 632 tests.
All five were run on the exact set these new ranges resolve to today:

    rnv-text-transformer        669 passed, 1 skipped
    rnv-color-picker           1452 passed, 4 skipped
    rnv-color-palette-manager   564 passed, 1 skipped
    rnv-color-mixer             723 passed, 14 skipped  + 355 locked
    rnv-icon-builder            632 passed, 2 skipped

WHAT THIS DOES. Rewrites 5 specifier(s) in 2 file(s) to the fleet
standard, identical in all five:

        pytest>=8.0,<10.0
        pytest-qt>=4.4,<5.0
        pytest-cov>=5.0,<8.0
        pytest-timeout>=2.4,<3.0
        pytest-benchmark>=4.0,<6.0

The floor of each is the highest floor any of the five already declared, so
no repository gives up ground. The ceiling is the next MAJOR version, which
is the thing the old caps were reaching for and the thing `==` cannot
express: nothing crosses a major boundary without someone editing a line.

WHY NOT `==`. An exact pin on a shared tool makes one repository fight the
other four every time anything moves. It belongs in a lock file, not in the
dev requirements of five applications developed together on one machine.

NO PACKAGE IS ADDED OR REMOVED. This repository declares exactly the
packages it declared before; only the specifiers change.

NO SOURCE FILE IS TOUCHED. No colour, no value, no behaviour.
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
SENTINEL_FILE = "tests/requirements-dev.txt"
SENTINEL = "RNV-TEST-TOOLING"
GUARD = "tests/test_test_tooling_pins.py"
DESCRIPTION = "align the test-tooling pins with the other four applications"
SUITES = [("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("the LOCKED file, 355 tests", [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-TEST-TOOLING-GUARD -- the five applications share one interpreter, so
their dev-tooling ranges have to be mutually satisfiable.

Installed 2026-09-07. Until today they were not, and it was arithmetic rather
than a matter of taste:

    pytest       picker  ==9.0.2      icon builder  >=8.0.0,<9.0.0
    pytest-cov   picker  ==7.1.0      icon builder  >=5.0.0,<7.0.0

No version of pytest is both exactly 9.0.2 and below 9.0.0. On a development
machine -- one interpreter, five checkouts -- installing one repository's dev
requirements and then the other's UNINSTALLS pytest 9 and installs pytest 8,
and going back undoes it. While pip is mid-swap the _pytest package on disk is
partially populated, which is where

    ModuleNotFoundError: No module named '_pytest.compat'

comes from, seconds after the same command had just succeeded. No install
order avoids it. The constraint itself was impossible.

WHAT THIS FILE GUARDS. Four things, in the order they are likely to break:

  1. This repository's ranges are still the fleet's.
  2. Every file in this repository that declares them agrees with the others.
     Both pyproject.toml files in the fleet SAY IN A COMMENT that they mirror
     tests/requirements-dev.txt. Nothing checked it. Now something does.
  3. No exact `==` pin has come back. That is the mechanism, not the symptom:
     an exact pin on a shared tool makes one repository fight the other four
     every time anything moves.
  4. The pytest actually running this test satisfies what the file declares.
     Points 1 to 3 read files; this one looks at the machine, and it is the
     one that would have caught the failure that started all this.

WHAT IT CANNOT DO. A test in this repository cannot see the other four. If
someone edits a range here, this fails here -- which is the point. If someone
edits it in all five identically, that is a fleet decision and this agrees
with it, as it should.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The fleet standard, identical in all five applications. The floor of each
#: is the highest floor any of the five already declared; the ceiling is the
#: next MAJOR version, so nothing crosses a major boundary without an edit.
#:
#: Measured at the top, not assumed: every one of the five suites was run on
#: pytest 9.1.1, pytest-qt 4.5.0, pytest-cov 7.1.0, pytest-timeout 2.4.0 and
#: pytest-benchmark 5.3.0 -- the exact set a fresh install resolves these to.
FLEET = {
    'pytest': '>=8.0,<10.0',
    'pytest-qt': '>=4.4,<5.0',
    'pytest-cov': '>=5.0,<8.0',
    'pytest-timeout': '>=2.4,<3.0',
    'pytest-benchmark': '>=4.0,<6.0',
}

#: Every file in THIS repository that may declare them. Absent ones are
#: skipped: the five do not all use the same layout, and a repository that
#: has no pyproject.toml is not thereby in breach.
#:
#: THE RETIRED ROOT-LEVEL requirements-dev PATH IS DELIBERATELY NOT HERE. All
#: six RNV repositories moved that file under tests/, and
#: tests/test_dependency_file_placement.py sweeps the tree to keep it moved.
#: The first build of this file listed the root path as a candidate 'just in
#: case', which is how a retired path comes back -- and that sweep caught it,
#: which is exactly what it is for. (Named without its extension here on
#: purpose: the sweep is scoped to the filename WITH extension so that prose
#: can still discuss it.)
CANDIDATES = ('tests/requirements-dev.txt', 'requirements.txt',
              'pyproject.toml')

_LINE = re.compile(
    r'^(?:\s*"?)([A-Za-z0-9_.-]+)'
    r'(\s*(?:[<>=!~]=?\s*[0-9][^,"#\n]*)(?:\s*,\s*[<>=!~]=?\s*[0-9][^,"#\n]*)*)')


def _declared(path: Path) -> dict:
    """The test-tooling requirements in one file, as {name: specifier}."""
    found = {}
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.lstrip().startswith('#'):
            continue
        match = _LINE.match(line)
        if not match:
            continue
        name = match.group(1).lower()
        if name in FLEET:
            found[name] = match.group(2).strip().replace(' ', '').rstrip('",')
    return found


def _files():
    return [ROOT / rel for rel in CANDIDATES if (ROOT / rel).exists()]


def test_the_ranges_are_the_fleet_s():
    """Every test-tooling requirement this repository declares, anywhere, is
    the one all five agree on."""
    wrong = []
    for path in _files():
        for name, spec in _declared(path).items():
            if spec != FLEET[name]:
                wrong.append(
                    f'{path.relative_to(ROOT).as_posix()}: {name}{spec} '
                    f'(fleet: {name}{FLEET[name]})')
    assert not wrong, (
        'these ranges have drifted from the fleet standard:\n  '
        + '\n  '.join(wrong)
        + '\n\nThe five applications share one interpreter. A range only this '
          'repository holds is a range that fights the other four, and pip '
          'resolves that fight by rewriting site-packages.')


def test_the_declaring_files_in_this_repository_agree():
    """pyproject.toml and tests/requirements-dev.txt say the same thing.

    Both pyproject files in the fleet carry a comment claiming exactly this.
    A comment is a promise; this is the part that keeps it.
    """
    per_file = {p.relative_to(ROOT).as_posix(): _declared(p) for p in _files()}
    disagreements = []
    names = {n for d in per_file.values() for n in d}
    for name in sorted(names):
        specs = {rel: d[name] for rel, d in per_file.items() if name in d}
        if len(set(specs.values())) > 1:
            disagreements.append(
                f'{name}: ' + ', '.join(f'{r} says {s}' for r, s in specs.items()))
    assert not disagreements, (
        'two files in this repository declare different versions of the same '
        'package:\n  ' + '\n  '.join(disagreements)
        + '\n\nWhichever one you install from wins, and which one that is '
          'depends on the command someone happened to type.')


def test_no_exact_pin_came_back():
    """`==` is the mechanism, not the symptom.

    An exact pin on a tool five repositories share means this one demands a
    version the others merely tolerate. It is right for a lock file, which
    is regenerated, and wrong for dev requirements that are read by hand.
    """
    exact = []
    for path in _files():
        for name, spec in _declared(path).items():
            if spec.startswith('=='):
                exact.append(f'{path.relative_to(ROOT).as_posix()}: {name}{spec}')
    assert not exact, (
        'exact pins on shared test tooling:\n  ' + '\n  '.join(exact)
        + '\n\nUse a range with a major-version ceiling instead.')


def test_every_range_has_an_upper_bound():
    """A ceiling is the whole reason these are ranges and not floors.

    Without one, the next major release of pytest lands silently on the first
    machine that installs after it ships, and the first anyone knows is a
    suite failing on a commit that changed nothing.
    """
    unbounded = []
    for path in _files():
        for name, spec in _declared(path).items():
            if '<' not in spec:
                unbounded.append(
                    f'{path.relative_to(ROOT).as_posix()}: {name}{spec}')
    assert not unbounded, (
        'these declare a floor and no ceiling:\n  ' + '\n  '.join(unbounded)
        + '\n\nAdd a major-version ceiling.')


def test_the_installed_pytest_satisfies_what_this_repository_declares():
    """The one that looks at the machine rather than the files.

    Everything above reads text. This asks whether the pytest currently
    running is the pytest this repository asked for -- and a mismatch here
    means the last `pip install` someone ran was for a different repository.
    """
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version
    except ImportError:  # pragma: no cover -- packaging ships with pytest
        pytest.skip('packaging is not importable')

    # EVERY declaring file, separately. Merging them into one dict lets
    # whichever file sorts last overwrite the others, and the file that
    # loses is tests/requirements-dev.txt -- the one people actually
    # install from. The first build of this guard did exactly that and
    # reported green against a range it was not testing.
    running = Version(pytest.__version__)
    declared = [(path.relative_to(ROOT).as_posix(), spec['pytest'])
                for path, spec in ((p, _declared(p)) for p in _files())
                if 'pytest' in spec]
    if not declared:
        pytest.skip('this repository declares no pytest requirement')

    outside = [f'{rel} declares pytest{spec}'
               for rel, spec in declared
               if running not in SpecifierSet(spec)]
    assert not outside, (
        f'pytest {running} is running, but:\n  ' + '\n  '.join(outside)
        + '\n\nOn a machine with all five checkouts this usually means the '
          'last `pip install -r tests/requirements-dev.txt` you ran was in a '
          'different repository. Re-run it here:\n\n'
          '    python -m pip install -r tests/requirements-dev.txt')


def test_this_guard_can_see_the_files_it_judges():
    """Guard the guard. A parser that matches nothing finds no drift and
    passes, which looks exactly like a repository in perfect order."""
    files = _files()
    assert files, f'no requirements files found under {ROOT}'
    total = sum(len(_declared(p)) for p in files)
    assert total >= 2, (
        f'only {total} test-tooling requirement(s) were parsed out of '
        f'{[p.name for p in files]}. Every one of the five declares at least '
        f'pytest and pytest-qt, so this parser is not reading what it thinks.')
'''

EDITS = [('tests/requirements-dev.txt', 'pytest>=7.4\n', 'pytest>=8.0,<10.0\n', 1), ('tests/requirements-dev.txt', 'pytest-qt>=4.2\n', 'pytest-qt>=4.4,<5.0\n', 1), ('tests/requirements-dev.txt', 'pytest-timeout>=2.2\n', 'pytest-timeout>=2.4,<3.0\n', 1), ('pyproject.toml', '    "pytest>=7.4",\n', '    "pytest>=8.0,<10.0",\n', 1), ('pyproject.toml', '    "pytest-qt>=4.2",\n', '    "pytest-qt>=4.4,<5.0",\n', 1)]
CANON = {'pytest': '>=8.0,<10.0', 'pytest-qt': '>=4.4,<5.0', 'pytest-cov': '>=5.0,<8.0', 'pytest-timeout': '>=2.4,<3.0', 'pytest-benchmark': '>=4.0,<6.0'}
DECLARING_FILES = ['tests/requirements-dev.txt', 'pyproject.toml']

NOTE = (
    "\n"
    "# ── Test tooling (RNV-TEST-TOOLING, 2026-09-07) ────────────────────\n"
    "# The five RNV applications share one interpreter on a development\n"
    "# machine, so their dev-tooling ranges have to be mutually\n"
    "# satisfiable. They were not: the picker pinned pytest==9.0.2 while\n"
    "# the icon builder capped it below 9.0.0, and pip rewrote\n"
    "# site-packages on every switch between them.\n"
    "#\n"
    "# The ranges above are the fleet standard, identical in all five.\n"
    "# tests/test_test_tooling_pins.py fails if this repository drifts\n"
    "# from it, if a declaration here disagrees with another file in this\n"
    "# repository, or if an exact `==` pin comes back.\n")


def edits(tree) -> None:
    reqs = tree.read(SENTINEL_FILE)
    if SENTINEL in reqs:
        raise SystemExit("already applied")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    tree.write(SENTINEL_FILE, tree.read(SENTINEL_FILE).rstrip("\n") + "\n" + NOTE)
    touched = sorted({e[0] for e in EDITS})
    print(f"  {len(EDITS)} specifier(s) rewritten across {len(touched)} file(s)")
    for rel in touched:
        n = len([e for e in EDITS if e[0] == rel])
        print(f"    {rel}  ({n})")


def _declared(text: str):
    """Every test-tooling requirement in one file, as {name: specifier}."""
    found = {}
    line_re = re.compile(
        r'^(?:\s*"?)([A-Za-z0-9_.-]+)'
        r'(\s*(?:[<>=!~]=?\s*[0-9][^,"#\n]*)(?:\s*,\s*[<>=!~]=?\s*[0-9][^,"#\n]*)*)')
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = line_re.match(line)
        if not m:
            continue
        name = m.group(1).lower()
        if name in CANON:
            found[name] = m.group(2).strip().replace(" ", "").rstrip('",')
    return found


def checks(tree) -> None:
    # 1. every declaration in every declaring file is now the fleet's
    seen = {}
    for rel in DECLARING_FILES:
        got = _declared(tree.read(rel))
        for name, spec in got.items():
            if spec != CANON[name]:
                raise SystemExit(f"{rel}: {name}{spec} is not the fleet's "
                                 f"{name}{CANON[name]}")
            seen.setdefault(name, set()).add(rel)
    if not seen:
        raise SystemExit("no test-tooling requirement was found at all; the "
                         "rewrite matched nothing, which is not a clean repo")

    # 2. no exact pin survives anywhere in a declaring file
    for rel in DECLARING_FILES:
        for name, spec in _declared(tree.read(rel)).items():
            if spec.startswith("=="):
                raise SystemExit(f"{rel}: {name}{spec} is an exact pin")

    # 3. the note landed
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise SystemExit("the explanatory note did not land")

    print(f"  guards: {len(seen)} package(s) aligned, "
          f"{len(DECLARING_FILES)} declaring file(s) agree, no exact pins")


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
