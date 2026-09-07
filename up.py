#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: make the dependency declarations coherent.

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

THIS IS THE SECOND HALF OF THE PYTEST ROUND. That round fixed the one
conflict that was actively breaking: pytest==9.0.2 against pytest<9.0.0, no
version satisfying both, site-packages rewritten on every switch between two
repositories. This one fixes the same CLASS of defect everywhere else it
appears, before any of it costs anybody a morning.

Three findings, all measured across the five rather than assumed.

1. SIX PLACES WHERE ONE REPOSITORY DISAGREES WITH ITSELF.

       transformer  chardet    pyproject >=5.0.0        requirements >=5.2.0
       transformer  watchdog   pyproject >=3.0.0        requirements >=4.0.0
       mixer        Pillow     pyproject >=9.0.0,<12.0  requirements >=10.0
       mixer        PyQt6      pyproject >=6.5.0,<7.0.0 requirements >=6.5
       palette mgr  Pillow     pyproject >=10.0.0,<12.0 requirements >=10.0.0
       palette mgr  PyQt6      pyproject >=6.5.0,<7.0   requirements >=6.5.0

   Whichever file you install from wins, and which one that is depends on
   the command somebody typed. Both pyproject files in the fleet carry a
   comment SAYING they mirror the requirements. Nothing checked it.

2. TWO EXACT PINS LEFT, both in rnv-color-picker: PyQt6==6.10.2 and
   hypothesis==6.152.4. Currently satisfiable, so nothing is breaking today
   -- but it is the identical mechanism to pytest==9.0.2, one release away
   from doing the identical thing on a much heavier package. Each becomes a
   range whose FLOOR is the version it was pinned to, because that is the
   version this application is known to work on and a lower floor would be
   a claim nothing has tested.

3. PILLOW'S `<12.0` CAP EXCLUDED THE API THE FLEET JUST ADOPTED.
   `get_flattened_data` arrived in Pillow 12.1. utils/pil_compat.py was
   installed to prefer it. The cap meant the pyproject install path could
   never reach it -- and the cap has to move before 2027-10-15 regardless,
   because that is the day Pillow 14 removes `getdata()`.

   All five suites were run on Pillow 12.2.0 before this change. Lifted to
   `<13.0`, fleet-wide and identical in all five: past the version that
   matters, still short of a major boundary nobody has tested.

WHAT THIS DOES HERE. Rewrites 4 specifier(s) in 2 file(s).

WHAT IT DOES NOT DO. No package is added or removed. No floor is lowered.
No source file is touched. The test-tooling ranges are governed separately
by tests/test_test_tooling_pins.py and are not in scope here.

STILL OPEN, AND NOT DECIDED BY THIS SCRIPT: rnv-text-transformer and
rnv-icon-builder declare PyQt6 with no upper bound at all, while the mixer
and the palette manager cap it below 7.0. That asymmetry is reported rather
than fixed -- adding a ceiling to a runtime dependency is a decision about
what an application claims to support, and it is not a delivery script's to
make.
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
SENTINEL_FILE = "pyproject.toml"
SENTINEL = "RNV-DEPENDENCY-COHERENCE"
GUARD = "tests/test_dependency_coherence.py"
DESCRIPTION = "make the dependency declarations agree with each other"
SUITES = [("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("the LOCKED file, 355 tests", [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-DEPENDENCY-COHERENCE-GUARD -- one repository, one answer per package.

Installed 2026-09-07, as the second half of the pytest round. That round
fixed the conflict that was actively breaking:

    pytest       picker  ==9.0.2      icon builder  >=8.0.0,<9.0.0

No version is both. On one interpreter, pip rewrote site-packages on every
switch between those two repositories, and a half-rewritten _pytest package
is where `ModuleNotFoundError: No module named '_pytest.compat'` came from.

This file guards the same CLASS of defect in the packages that had not yet
bitten -- and one of them is PyQt6, where it would have cost a great deal
more than a morning.

WHAT THIS FILE GUARDS.

  1. Two files in this repository do not declare different ranges for the
     same package. Six such disagreements existed across the fleet. Both
     pyproject.toml files in it carry a comment SAYING they mirror the
     requirements; a comment is a promise, and this is the part that keeps
     it. Whichever file you install from wins, and which one that is
     depends on the command somebody happened to type.
  2. No exact `==` pin. Two were left -- PyQt6==6.10.2 and
     hypothesis==6.152.4, both in rnv-color-picker. Neither was breaking
     anything, which is the point: neither was pytest==9.0.2 either, until
     the day another repository disagreed with it.
  3. Pillow matches the range all five share. It is the one package with a
     DATED deadline behind it: the old pixel-access method is removed in
     Pillow 14 on 2027-10-15, and `get_flattened_data` -- the replacement
     that utils/pil_compat.py prefers -- arrived in Pillow 12.1. The old
     `<12.0` cap excluded it.

     (Named indirectly on purpose. tests/test_pil_compat.py sweeps every
     file for the retired call and this one is not exempt from that sweep,
     so writing the call form here -- even in prose -- fails it. Use versus
     mention, and this file was the tenth instance in this programme.)
  4. What is installed satisfies what is declared. Everything above reads
     text; this one looks at the machine, and it is the shape of check that
     would have caught the failure that started all this.

WHAT IT DELIBERATELY DOES NOT DO.

  It does not require every range to have a ceiling, and it does not require
  the five to agree on floors other than Pillow's. Applications legitimately
  support different minimum versions of the same library. What they may not
  do is contradict themselves, pin exactly, or make a version no combination
  can satisfy.

  The test-tooling packages are excluded here. They have a fleet standard of
  their own and their own guard, tests/test_test_tooling_pins.py, because a
  tool five repositories run on one interpreter is a different question from
  a library one application imports.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The one package with a fleet-wide range this round. See the docstring for
#: why it is the one: a dated removal, and an API the fleet has already
#: adopted that the old cap excluded.
FLEET = {'pillow': '>=10.0.0,<13.0'}

#: Governed by tests/test_test_tooling_pins.py instead. Checking them here
#: as well would mean two files disagreeing about the same thing, which is
#: the exact failure this one exists to prevent.
TEST_TOOLING = {'pytest', 'pytest-qt', 'pytest-cov', 'pytest-timeout',
                'pytest-benchmark'}

#: Lines that look like a requirement and are not. `line-length = 100` in
#: ruff's config and `precision = 0` in coverage's both parse as a name
#: followed by a number, and a sweep that rewrote them would break the tool
#: rather than the pin.
NOT_REQUIREMENTS = {'line-length', 'precision', 'python', 'name', 'version',
                    'requires-python', 'description', 'target-version'}

CANDIDATES = ('pyproject.toml', 'requirements.txt',
              'tests/requirements-dev.txt')

_LINE = re.compile(
    r'^(?:\s*"?)([A-Za-z0-9_.-]+)'
    r'(\s*(?:[<>=!~]=?\s*[0-9][^,"#\n]*)(?:\s*,\s*[<>=!~]=?\s*[0-9][^,"#\n]*)*)')


def _declared(path: Path) -> dict:
    """The dependencies one file declares, as {name: specifier}."""
    found = {}
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.lstrip().startswith('#'):
            continue
        match = _LINE.match(line)
        if not match:
            continue
        name = match.group(1).lower()
        if name in NOT_REQUIREMENTS or name in TEST_TOOLING:
            continue
        found[name] = match.group(2).strip().replace(' ', '').rstrip('",')
    return found


def _files():
    return [ROOT / rel for rel in CANDIDATES if (ROOT / rel).exists()]


def _per_file():
    return {p.relative_to(ROOT).as_posix(): _declared(p) for p in _files()}


def test_this_repository_does_not_contradict_itself():
    """One package, one answer.

    Six of these existed across the five applications. None of them broke
    anything on its own -- they decide which range applies based on which
    file somebody installed from, which is a coin flip dressed as a
    declaration.
    """
    per_file = _per_file()
    disagreements = []
    for name in sorted({n for d in per_file.values() for n in d}):
        specs = {rel: d[name] for rel, d in per_file.items() if name in d}
        if len(set(specs.values())) > 1:
            disagreements.append(
                f'{name}: ' + ', '.join(f'{r} says {s}' for r, s in specs.items()))
    assert not disagreements, (
        'two files in this repository declare different ranges for the same '
        'package:\n  ' + '\n  '.join(disagreements)
        + '\n\nWhichever one you install from wins, and which one that is '
          'depends on the command someone happened to type.')


def test_no_dependency_is_pinned_exactly():
    """`==` is the mechanism behind the pytest failure, not the symptom.

    An exact pin means this repository demands a version the others merely
    tolerate. Installing it downgrades or upgrades the package for every
    checkout sharing that interpreter, and the window while pip is mid-swap
    is a partially-populated package on disk.

    It is right in a lock file, which is regenerated. It is wrong in a
    declaration that is read by hand.
    """
    exact = []
    for rel, declared in _per_file().items():
        for name, spec in declared.items():
            if spec.startswith('=='):
                exact.append(f'{rel}: {name}{spec}')
    assert not exact, (
        'exact pins:\n  ' + '\n  '.join(exact)
        + '\n\nUse a range whose floor is the version you know works.')


def test_pillow_matches_the_range_all_five_share():
    """The one package with a dated deadline behind it.

    Pillow 14 removes the old pixel-access method on 2027-10-15.
    `get_flattened_data`, which utils/pil_compat.py prefers, arrived in
    Pillow 12.1 -- so the old `<12.0` cap excluded the API the fleet had
    just adopted. The ceiling is what makes somebody look before 14 lands.
    """
    wrong = []
    for rel, declared in _per_file().items():
        for name, want in FLEET.items():
            if name in declared and declared[name] != want:
                wrong.append(f'{rel}: {name}{declared[name]} (fleet: {name}{want})')
    assert not wrong, (
        'these have drifted from the range all five applications share:\n  '
        + '\n  '.join(wrong))


def test_what_is_installed_satisfies_what_is_declared():
    """The one that looks at the machine rather than the files.

    A package that is not installed is skipped -- plenty of these are
    optional development tools. A package installed at a version this
    repository forbids is a real disagreement between the declaration and
    the environment, and one of the two is wrong.
    """
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version
    except ImportError:  # pragma: no cover -- packaging ships with pytest
        pytest.skip('packaging is not importable')
    from importlib.metadata import PackageNotFoundError, version as installed_version

    # Every declaring file separately. Merging them into one mapping lets
    # whichever file sorts last silently overwrite the others, and then the
    # check reports green against a range it never tested.
    outside = []
    for rel, declared in _per_file().items():
        for name, spec in sorted(declared.items()):
            try:
                have = Version(installed_version(name))
            except PackageNotFoundError:
                continue
            except Exception:               # pragma: no cover
                continue
            if have not in SpecifierSet(spec):
                outside.append(f'{rel} declares {name}{spec}, but {have} is installed')
    assert not outside, (
        'the environment does not match the declarations:\n  '
        + '\n  '.join(outside)
        + '\n\nEither the declaration is wrong or the install is stale:\n\n'
          '    python -m pip install -r requirements.txt')


def test_this_guard_can_see_the_files_it_judges():
    """Guard the guard. A parser that matches nothing finds no disagreement
    and passes, which looks exactly like a repository in perfect order."""
    files = _files()
    assert files, f'no dependency files found under {ROOT}'
    total = sum(len(_declared(p)) for p in files)
    assert total >= 3, (
        f'only {total} dependency declaration(s) parsed out of '
        f'{[p.name for p in files]}. Every one of the five declares at least '
        f'PyQt6 and Pillow, so this parser is not reading what it thinks.')


def test_a_tool_setting_is_not_read_as_a_dependency():
    """The exclusion list, tested by behaviour rather than by census.

    `line-length = 100` in ruff's config and `precision = 0` in coverage's
    both parse as a name followed by a comparison and a number -- the regex
    cannot tell them from `chardet >= 5.2.0`, because structurally they are
    the same. A sweep without the exclusion would report ruff's config as a
    dependency disagreement, and a REWRITE without it would set
    `line-length` to a version range.

    Driven with a stand-in file rather than asserted against this
    repository's, so it holds whether or not this particular repository
    happens to configure those tools today.
    """
    import tempfile
    sample = ('[tool.ruff]\n'
              'line-length = 100\n'
              'target-version = "py311"\n'
              '\n'
              '[tool.coverage.report]\n'
              'precision = 0\n'
              '\n'
              'dependencies = [\n'
              '    "Pillow>=10.0.0,<13.0",\n'
              ']\n')
    with tempfile.NamedTemporaryFile('w', suffix='.toml', delete=False,
                                     encoding='utf-8') as handle:
        handle.write(sample)
        path = Path(handle.name)
    try:
        found = _declared(path)
    finally:
        path.unlink()
    assert 'line-length' not in found, 'ruff config read as a dependency'
    assert 'precision' not in found, 'coverage config read as a dependency'
    assert found.get('pillow') == '>=10.0.0,<13.0', (
        f'the parser missed the real requirement in the same file: {found}')
'''

EDITS = [('pyproject.toml', '    "PyQt6>=6.5.0,<7.0.0",\n', '    "PyQt6>=6.5.0,<7.0",\n', 1), ('pyproject.toml', '    "Pillow>=9.0.0,<12.0.0",\n', '    "Pillow>=10.0.0,<13.0",\n', 1), ('requirements.txt', 'PyQt6>=6.5\n', 'PyQt6>=6.5.0,<7.0\n', 1), ('requirements.txt', 'Pillow>=10.0\n', 'Pillow>=10.0.0,<13.0\n', 1)]
DECLARING_FILES = ['pyproject.toml', 'requirements.txt', 'tests/requirements-dev.txt']
FLEET = {'pillow': '>=10.0.0,<13.0'}

NOTE = (
    "\n"
    "# ── Dependency coherence (RNV-DEPENDENCY-COHERENCE, 2026-09-07) ────\n"
    "# The declarations in this file and in requirements.txt had drifted\n"
    "# apart, so which range applied depended on which file you installed\n"
    "# from. tests/test_dependency_coherence.py fails if they disagree\n"
    "# again, if an exact `==` pin comes back, or if Pillow stops matching\n"
    "# the range all five applications share.\n")


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL in src:
        raise SystemExit("already applied")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    tree.write(SENTINEL_FILE, tree.read(SENTINEL_FILE).rstrip("\n") + "\n" + NOTE)
    touched = sorted({e[0] for e in EDITS})
    print(f"  {len(EDITS)} specifier(s) rewritten across {len(touched)} file(s)")
    for rel in touched:
        for _, old, new, _ in [e for e in EDITS if e[0] == rel]:
            print(f"    {rel}:  {old.strip()}  ->  {new.strip()}")


NOT_REQUIREMENTS = {"line-length", "precision", "python", "name", "version",
                    "requires-python", "description", "target-version"}
TEST_TOOLING = {"pytest", "pytest-qt", "pytest-cov", "pytest-timeout",
                "pytest-benchmark"}

_LINE = re.compile(
    r'^(?:\s*"?)([A-Za-z0-9_.-]+)'
    r'(\s*(?:[<>=!~]=?\s*[0-9][^,"#\n]*)(?:\s*,\s*[<>=!~]=?\s*[0-9][^,"#\n]*)*)')


def _declared(text: str) -> dict:
    found = {}
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        name = m.group(1).lower()
        if name in NOT_REQUIREMENTS or name in TEST_TOOLING:
            continue
        found[name] = m.group(2).strip().replace(" ", "").rstrip('",')
    return found


def checks(tree) -> None:
    per_file = {}
    for rel in DECLARING_FILES:
        try:
            per_file[rel] = _declared(tree.read(rel))
        except SystemExit:
            continue                       # the repo does not have that file

    # 1. no two files in this repository disagree
    disagreements = []
    for name in sorted({n for d in per_file.values() for n in d}):
        specs = {rel: d[name] for rel, d in per_file.items() if name in d}
        if len(set(specs.values())) > 1:
            disagreements.append(f"{name}: " + ", ".join(
                f"{r} says {s}" for r, s in specs.items()))
    if disagreements:
        raise SystemExit("files still disagree: " + "; ".join(disagreements))

    # 2. no exact pin survives
    exact = [f"{rel}: {n}{s}" for rel, d in per_file.items()
             for n, s in d.items() if s.startswith("==")]
    if exact:
        raise SystemExit("exact pins survive: " + ", ".join(exact))

    # 3. the fleet-wide ranges are what they should be
    for rel, d in per_file.items():
        for name, want in FLEET.items():
            if name in d and d[name] != want:
                raise SystemExit(f"{rel}: {name}{d[name]} is not the fleet's "
                                 f"{name}{want}")

    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise SystemExit("the explanatory note did not land")

    n = len({n for d in per_file.values() for n in d})
    print(f"  guards: {len(per_file)} file(s) agree on {n} package(s), "
          f"no exact pins, Pillow at the fleet range")


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
