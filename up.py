#!/usr/bin/env python3
"""RNV-FLEET-FLOOR — one interpreter and one ceiling, fleet-wide.

    python up.py             # apply, then run the guard and both suites
    python up.py --check     # rehearse every edit in memory, write nothing

For rnv-color-mixer, derived against a fresh clone at the live head.

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it quotes the code it replaces. That marker is what
tells the brand scanners in this fleet to skip it — installed by this same
round, so it takes effect in the run that installs it.

WHAT THE FLEET LOOKED LIKE. Five applications, one developer, one machine,
and five different answers to "what Python does this run on":

    repo              requires-python   CI ran                  classifiers
    mixer             >=3.10            3.11 only               3.10-3.13
    picker            >=3.13            3.13                    3.13
    palette manager   >=3.13            3.13                    3.13
    text transformer  >=3.10            3.13 only               3.10-3.13
    icon builder      >=3.10            3.10 3.11 3.12 3.13     3.10-3.13

Three declared support for 3.10 and never ran it. The palette manager
declared 3.13 and meant it — seven of its files use PEP 695 `type X = ...`,
which 3.11 cannot parse, so its suite does not even COLLECT on the floor
three of its siblings were claiming.

A declared floor nobody runs is the same shape as a deselect nobody reads:
an exemption with no subject. It looks like support and is not.

WHAT THIS REPOSITORY NEEDED.

    requires-python said >=3.10 and both CI jobs ran 3.11 -- so the one version
this application was ever tested on was neither the floor it declared nor
the one its siblings ran. Its classifiers advertised 3.10 through 3.13 and
mypy was pinned at 3.10.

    pyproject.toml    >=3.10 -> >=3.13, four classifiers -> one,
                      [tool.mypy] python_version 3.10 -> 3.13
    both workflows    3.11 -> 3.13
    the marker        tests/test_brand_mirror.py

MEASURED, NOT ASSUMED. This is the repository that had never run on 3.13 at
all. PyQt6 6.11 was installed for a real 3.13 and both suites run there
before this script was written: 801 + 356, against 795 + 356 on 3.11. The
six new tests are the guard.

THE FLEET IS NOW 3.13 EVERYWHERE, declared and run, PyQt6 capped below 7.0
in all five, and pytest-timeout declared in all five. tests/test_fleet_floor.py
is the guard; it is byte-identical in every checkout and reads pyproject.toml
as TOML rather than sweeping it as text, because `version = "3.3.13"` and
`scikit-learn>=1.3.0` both match a regex for a Python version and neither is
one.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from importlib.util import find_spec
from pathlib import Path

REPO = "rnv-color-mixer"
SENTINEL_FILE = "tests/conftest.py"
SENTINEL = "RNV-FLEET-FLOOR"
GUARD = "tests/test_fleet_floor.py"
MARKER = "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP"
FLOOR = "3.13"
DESCRIPTION = "put this application on the fleet's Python floor"

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}


def _timeout_flag() -> list:
    """--timeout only when the plugin can actually be imported.

    This round ADDS pytest-timeout to two repositories, and declaring is not
    installing: the script writes the requirements line and then runs pytest
    in the interpreter it was started with. A flag no plugin defines is a
    pytest USAGE error — exit 4, not a test failure — which is exactly how
    the previous round's palette-manager run died. Asked of the environment
    rather than answered from a list, so this cannot go stale.
    """
    return ["--timeout=120"] if find_spec("pytest_timeout") else []


SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q",
            "-p", "no:cacheprovider"]),
          ("\"the LOCKED file\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider"] + _timeout_flag())]

GUARD_SOURCE = r'''"""RNV-FLEET-FLOOR-GUARD -- one interpreter and one ceiling, fleet-wide.

Installed 2026-09-11, after a survey found the fleet stating its Python floor
three different ways and disagreeing with itself in four repositories out of
five.

WHAT WAS THERE. Three separate statements, none of them agreeing:

    repo              requires-python   CI ran
    mixer             >=3.10            3.11 only
    picker            >=3.13            3.13
    palette manager   >=3.13            3.13
    text transformer  >=3.10            3.13 only
    icon builder      >=3.10            3.10, 3.11, 3.12, 3.13

Three declared support for 3.10 and never ran it. The palette manager
declared 3.13 and meant it -- seven of its files use PEP 695
`type X = ...`, which 3.11 cannot parse, so its entire suite fails to
collect on the floor three of its siblings claimed. The icon builder was the
only one whose declaration matched what it tested, and it paid for that in
`ui/theme_manager.py`, which carried a note explaining it avoided PEP 695
"so the module imports on Python 3.10 and 3.11".

A declared floor nobody runs is the same shape as a deselect nobody reads:
an exemption with no subject. It looks like support and is not.

WHAT IS TRUE NOW. Every repository declares `requires-python >= 3.13` and
every CI job runs 3.13. Measured before shipping, under a real 3.13 with
PyQt6 6.11: the mixer -- the one repository that had never run on 3.13 --
passes 795 + 356, identical to its 3.11 numbers, and the icon builder passes
649 with `type ThemeDict = dict[str, str]` in place of the note.

THE SECOND PASS, AND WHY THERE HAD TO BE ONE. The first sweep read
`requires-python` and the CI matrices, fixed both, and called the fleet
consistent. It was not. Asked instead what ELSE in pyproject.toml names a
Python version, three more statements came out:

    repo              classifiers            mypy      ruff
    mixer             3.10 3.11 3.12 3.13    "3.10"    --
    picker            3.13                   --        --
    palette manager   3.13                   --        --
    text transformer  3.10 3.11 3.12 3.13    "3.10"    "py310"
    icon builder      3.10 3.11 3.12 3.13    --        --

Classifiers are what the package advertises publicly; three repositories
were advertising support for three versions they had just stopped running.
The text transformer's ruff target was live behaviour rather than
decoration -- with `UP` (pyupgrade) selected, `py310` tells the linter to
rewrite modern syntax BACKWARDS, in the one repository whose runtime check
this round moved to 3.13.

Picker and palette manager needed no edit: they already listed 3.13 alone.
The fix everywhere else is what those two already do.

A RULE THAT WAS TRIED AND REMOVED. A fourth check flagged comments
mentioning Python 3.10 or 3.11 next to words like "import" or "support". As
a SURVEY it earned its place: it found the icon builder's PEP 695 note and,
in the text transformer, `MIN_PYTHON_VERSION = (3, 10)` sitting above an
error message that already called 3.13 "recommended" -- the code knew the
answer and the constant did not. Both are fixed.

As a standing guard it was useless, because it cannot tell a live
constraint from a record of one. The comments written to EXPLAIN each fix
mention the old versions, so the rule failed on its own repairs in both
repositories. A rule that fires on the note explaining why it no longer
applies is noise, and noise is what gets suppressed.

TWO MORE RULES LIVE HERE, AND IT IS WORTH SAYING WHY. This repository
already has `tests/test_dependency_coherence.py` (runtime packages) and
`tests/test_test_tooling_pins.py` (dev packages), both byte-identical across
the fleet. Neither has a rule of the kind added here: coherence checks that
a repository does not contradict ITSELF and that nothing is pinned exactly;
tooling-pins checks that declared RANGES match the fleet's. Neither asks
whether a ceiling exists, or whether a package is declared at all.

So the PyQt6 ceiling and pytest-timeout's presence are checked here rather
than bolted onto files that would then be answering a different question.
One round's decisions, enforced in one place. If either of those guards ever
grows a rule of this kind, this is the file to fold into it.

WHAT THIS GUARD DOES NOT DO. It does not check what interpreter is running
it. Pinning that would make the guard fail on a developer's machine for a
reason that is not a defect; CI is where the floor is enforced, and CI is
what this reads.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The floor, stated once. Every other statement in the repository is
#: checked against this one rather than against a copy.
FLOOR = "3.13"

WORKFLOWS = ROOT / ".github" / "workflows"
PYPROJECT = ROOT / "pyproject.toml"
REQUIREMENTS = ROOT / "requirements.txt"
#: Written as one joined string rather than ROOT / "tests" / "...": the
#: palette manager's test_dependency_file_placement.py reads these paths as
#: TEXT, and skips a line only when it contains "tests/requirements-dev.txt"
#: literally. The pathlib form is the same path and was invisible to it, so
#: a correct line was reported as naming the root. Tenth time in this
#: programme that a check matched text where the text was the wrong surface.
DEV_REQUIREMENTS = ROOT / "tests/requirements-dev.txt"

#: Runtime packages whose MAJOR version must be capped. PyQt7 does not exist
#: yet; the cap is what stops five applications on one interpreter following
#: a major version they have never been tested against. Two repositories had
#: no ceiling at all until 2026-09-11.
CEILINGS = {"pyqt6": "<7.0"}

#: Dev tooling every repository must declare, not merely agree about. A
#: timeout is the only thing that turns a hang into a failure, and this fleet
#: has had two hangs -- a modal dialog on a palette import, and another in
#: the image loader. Two repositories did not declare it, and a script that
#: passed --timeout anyway exited 4 on a pytest USAGE error.
REQUIRED_DEV_TOOLING = {"pytest-timeout"}

#: `python-version: "3.13"`, `python-version: ['3.13']`, and the matrix form
#: `python-version: ${{ matrix.python-version }}` all appear in this fleet.
#: The third names no version and is checked through the matrix it reads.
_VERSION_LINE = re.compile(r"python-version:\s*(.+?)\s*$")
_MATRIX_REF = re.compile(r"\$\{\{\s*matrix\.python-version\s*\}\}")
_VERSIONS = re.compile(r"\d+\.\d+")

#: Keys under [tool.*] that name the Python a tool assumes. Five spellings
#: because five tools chose differently: mypy's `python_version`, ruff's and
#: black's `target-version`, pylint's `py-version`. Matched by NAME at any
#: depth rather than by section, so a tool added later is covered without
#: this list being revisited.
_TOOL_VERSION_KEYS = {"python_version", "python-version", "target-version",
                      "target_version", "py-version"}
_PY_SHORT = re.compile(r"^py(\d)(\d+)$")
_PY_DOTTED = re.compile(r"^(\d+)\.(\d+)$")


def _as_version(value) -> str | None:
    """"3.10" and "py310" are one statement in two spellings; else None."""
    text = str(value).strip()
    for pattern in (_PY_DOTTED, _PY_SHORT):
        found = pattern.match(text)
        if found:
            return f"{found.group(1)}.{found.group(2)}"
    return None


def _tool_version_settings(table, path=()):
    """Every [tool] key naming a Python version, however deeply nested."""
    if not isinstance(table, dict):
        return
    for key, value in table.items():
        here = path + (str(key),)
        if key in _TOOL_VERSION_KEYS:
            # black takes a LIST here, ruff and mypy take a string.
            for item in (value if isinstance(value, list) else [value]):
                version = _as_version(item)
                if version:
                    yield ".".join(here), item, version
        elif isinstance(value, dict):
            yield from _tool_version_settings(value, here)


def _classifier_versions(classifiers):
    """The minor version each `Programming Language :: Python ::` entry names.

    `:: Python :: 3` and `:: Python :: 3 :: Only` name no minor version and
    are not claims about 3.10 -- the palette manager carries the second and
    is correct. Only an `X.Y` third field is a statement this rule judges.
    """
    for entry in classifiers:
        parts = [p.strip() for p in str(entry).split("::")]
        if parts[:2] != ["Programming Language", "Python"] or len(parts) < 3:
            continue
        version = _as_version(parts[2])
        if version:
            yield entry, version


def _workflow_files():
    if not WORKFLOWS.is_dir():
        return []
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def _declared_versions(text: str):
    """Every concrete Python version a workflow names, with its line number."""
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        found = _VERSION_LINE.search(line)
        if not found:
            continue
        value = found.group(1)
        if _MATRIX_REF.search(value):
            # Reads the matrix rather than naming a version; the matrix
            # itself is caught by its own `python-version:` line.
            continue
        for version in _VERSIONS.findall(value):
            yield number, version


def test_the_declared_floor_is_the_fleet_s():
    """`requires-python` says what this application supports.

    Three repositories said `>=3.10` while their CI ran only 3.11 or 3.13.
    A floor nobody exercises is a claim, not support.
    """
    assert PYPROJECT.exists(), f"{PYPROJECT} is missing"
    text = PYPROJECT.read_text(encoding="utf-8")

    found = re.search(r'requires-python\s*=\s*"([^"]+)"', text)
    assert found, "pyproject.toml declares no requires-python at all"

    declared = found.group(1).strip()
    assert declared == f">={FLOOR}", (
        f'pyproject.toml declares requires-python = "{declared}", not '
        f'">={FLOOR}". The fleet moved to {FLOOR} on 2026-09-11 because the '
        f'palette manager already required it -- seven of its files use PEP '
        f'695 syntax that 3.11 cannot parse -- and because three repositories '
        f'were declaring support for 3.10 without ever running it.')


def test_every_ci_job_runs_the_floor():
    """And that CI actually exercises it.

    The mixer declared `>=3.10` and ran 3.11. The icon builder ran four
    versions. Neither is wrong on its own; both together mean the fleet has
    no single answer to "what does this run on".
    """
    wrong = []
    for path in _workflow_files():
        rel = path.relative_to(ROOT).as_posix()
        for number, version in _declared_versions(
                path.read_text(encoding="utf-8")):
            if version != FLOOR:
                wrong.append(f"{rel}:{number} runs {version}")

    assert not wrong, (
        f"these CI jobs do not run Python {FLOOR}:\n  " + "\n  ".join(wrong)
        + f"\n\nThe fleet's floor is {FLOOR} and `requires-python` says so. "
          f"A job on another version is either testing something the "
          f"application does not claim to support, or the floor moved and "
          f"this constant did not.")


def test_nothing_else_in_pyproject_names_an_older_version():
    """`requires-python` was never the only statement in this file.

    PARSED AS TOML, NOT SWEPT AS TEXT, and that is the whole reason this
    rule is trustworthy. `version = "3.3.13"` in the palette manager and
    `version = "3.0.3"` in the picker are APPLICATION versions;
    `scikit-learn>=1.3.0` is a DEPENDENCY's. A sweep for `\\b3\\.\\d+\\b`
    hits all three -- run, not imagined -- so a rule built that way would
    land red in the two repositories that were ALREADY CORRECT, over three
    numbers with nothing to do with Python. Eleventh time in this programme
    that a check would have matched text where the text meant something
    else, and the first where reading the structure cost nothing: the file
    is TOML and the floor is 3.13, so tomllib is in the standard library.

    Comments are invisible to the parse, which is the behaviour this rule
    wants: a note in pyproject.toml explaining that the classifiers used to
    list 3.10 is a mention, not a declaration. The rule that had to be
    removed from this guard died precisely because it could not tell those
    apart.
    """
    with PYPROJECT.open("rb") as handle:
        data = tomllib.load(handle)

    wrong = []
    for entry, version in _classifier_versions(
            data.get("project", {}).get("classifiers", [])):
        if version != FLOOR:
            wrong.append(f"classifiers: {entry!r} advertises {version}")
    for key, raw, version in _tool_version_settings(data.get("tool", {}),
                                                    ("tool",)):
        if version != FLOOR:
            wrong.append(f"[{key}] = {raw!r} assumes {version}")

    assert not wrong, (
        f"pyproject.toml still names Python versions other than {FLOOR}:\n  "
        + "\n  ".join(wrong)
        + f"\n\nA classifier is what this package advertises publicly, and a "
          f"tool's target version changes what the tool DOES -- ruff with "
          f"`UP` selected and an old target rewrites modern syntax backwards. "
          f"Both are statements about the supported interpreter, and this "
          f"repository has exactly one: {FLOOR}.")


def test_every_capped_package_is_actually_capped():
    """A lower bound with no upper bound is a promise about the future.

    The text transformer and the icon builder declared `PyQt6>=6.6.0` and
    nothing else, while the other three capped below 7.0. On a shared
    interpreter that is the same shape as the pytest conflict that produced
    `ModuleNotFoundError: No module named '_pytest.compat'`.
    """
    uncapped = []
    for path in (REQUIREMENTS, PYPROJECT, DEV_REQUIREMENTS):
        if not path.exists():
            continue
        rel = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip().strip('"').strip("',")
            if stripped.startswith("#") or not stripped:
                continue
            for package, ceiling in CEILINGS.items():
                if not stripped.lower().startswith(package):
                    continue
                # A bare name with no comparison at all is not an uncapped
                # RANGE -- pyproject lists `"pyqt6"` under dependencies with
                # the version left to requirements.txt. The first version of
                # this rule flagged that line in all five repositories.
                if not any(op in stripped for op in ("<", ">", "=", "~", "!")):
                    continue
                if ceiling not in stripped.replace(" ", ""):
                    uncapped.append(f"{rel}:{number} {stripped[:60]}")

    assert not uncapped, (
        "these declarations have no upper bound:\n  " + "\n  ".join(uncapped)
        + "\n\nCEILINGS says what the cap is. A package with a floor and no "
          "ceiling follows its next major version into five applications at "
          "once, none of which have been tested against it.")


def test_the_dev_tooling_this_fleet_relies_on_is_declared():
    """Declared, not just agreed about.

    `tests/test_test_tooling_pins.py` checks that what IS declared matches
    the fleet's ranges. It cannot notice a package that is simply absent,
    and two repositories were missing this one.
    """
    assert DEV_REQUIREMENTS.exists(), f"{DEV_REQUIREMENTS} is missing"
    text = DEV_REQUIREMENTS.read_text(encoding="utf-8").lower()

    declared = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            declared.add(re.split(r"[<>=!~\[ ]", stripped, maxsplit=1)[0])

    missing = sorted(REQUIRED_DEV_TOOLING - declared)
    assert not missing, (
        f"tests/requirements-dev.txt does not declare {missing}. "
        f"A run that passes --timeout without the plugin installed is a "
        f"pytest usage error -- exit 4, not a test failure -- and a run "
        f"without a timeout turns a hang into a job that sits until someone "
        f"cancels it.")


def test_this_guard_can_see_the_files_it_judges():
    """A sweep that finds nothing passes every assertion above."""
    files = _workflow_files()
    assert files, f"no workflow files found under {WORKFLOWS}"

    named = [(p, n, v) for p in files
             for n, v in _declared_versions(p.read_text(encoding="utf-8"))]
    assert named, (
        f"none of the {len(files)} workflow files names a concrete Python "
        f"version, so the rule above has no subject. Either they all read a "
        f"matrix this guard cannot follow, or the sweep is broken.")

    assert PYPROJECT.exists(), "pyproject.toml is not where this guard looks"
    with PYPROJECT.open("rb") as handle:
        data = tomllib.load(handle)

    # The classifier rule above passes over an empty list without noticing.
    # Every one of these five declares them, so an empty list means the
    # parse found the wrong table, not that the repository stopped
    # advertising.
    classifiers = data.get("project", {}).get("classifiers", [])
    assert any(str(c).startswith("Programming Language :: Python")
               for c in classifiers), (
        f"pyproject.toml lists {len(classifiers)} classifiers and none names "
        f"Python, so the rule above has nothing to judge")
'''

EDITS = [('tests/conftest.py', '# RNV-NO-VACUOUS-TESTS, 2026-09-10 -- tests/test_no_vacuous_tests.py\n# sweeps this repository for tests that cannot fail: assertions true\n', "# RNV-FLEET-FLOOR, 2026-09-11 -- tests/test_fleet_floor.py holds this\n# application to the fleet's Python floor (3.13, declared and run), the\n# PyQt6 major-version ceiling, and the dev tooling every repository must\n# declare rather than merely agree about.\n# RNV-NO-VACUOUS-TESTS, 2026-09-10 -- tests/test_no_vacuous_tests.py\n# sweeps this repository for tests that cannot fail: assertions true\n"), ('pyproject.toml', 'requires-python = ">=3.10"', 'requires-python = ">=3.13"'), ('pyproject.toml', '    "Programming Language :: Python :: 3.10",\n    "Programming Language :: Python :: 3.11",\n    "Programming Language :: Python :: 3.12",\n    "Programming Language :: Python :: 3.13",\n', '    "Programming Language :: Python :: 3.13",\n'), ('pyproject.toml', '[tool.mypy]\npython_version = "3.10"', '[tool.mypy]\npython_version = "3.13"'), ('.github/workflows/tests-linux.yml', 'python-version: "3.11"', 'python-version: "3.13"'), ('.github/workflows/tests-windows.yml', 'python-version: "3.11"', 'python-version: "3.13"'), ('tests/test_brand_mirror.py', '        if "RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN" in text or "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP" in text:\n', '        # RNV-FLEET-FLOOR 2026-09-11: one marker every scanner in this\n        # fleet honours, so a delivery script is skipped whatever it is\n        # called. Such a script QUOTES the code it replaces, which reads\n        # to a sweep exactly like a live call site.\n        if ("RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN" in text\n                or "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP" in text\n                or "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text):\n')]


def edits(tree) -> None:
    for rel, old, new in EDITS:
        tree.sub(rel, old, new, 1)
    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))


_TOOL_VERSION_KEYS = {"python_version", "python-version", "target-version",
                      "target_version", "py-version"}
_PY_SHORT = re.compile(r"^py(\d)(\d+)$")
_PY_DOTTED = re.compile(r"^(\d+)\.(\d+)$")


def _as_version(value):
    text = str(value).strip()
    for pattern in (_PY_DOTTED, _PY_SHORT):
        found = pattern.match(text)
        if found:
            return f"{found.group(1)}.{found.group(2)}"
    return None


def _tool_versions(table, path=()):
    if not isinstance(table, dict):
        return
    for key, value in table.items():
        here = path + (str(key),)
        if key in _TOOL_VERSION_KEYS:
            for item in (value if isinstance(value, list) else [value]):
                version = _as_version(item)
                if version:
                    yield ".".join(here), version
        elif isinstance(value, dict):
            yield from _tool_versions(value, here)


def _marker_is_honoured(text: str) -> bool:
    """Does this file SKIP on the marker, or merely mention it?

    Parsed, not matched. The substring is in the file either way — the
    replacement quotes the condition it replaces — and every one of the ten
    times this programme has been caught out, the answer was to read the
    tree. This looks for a `continue` guarded by an `in` test against the
    marker, by literal or through a constant bound to it.
    """
    tree = ast.parse(text)
    aliases = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
               for t in n.targets
               if isinstance(t, ast.Name) and isinstance(n.value, ast.Constant)
               and n.value.value == MARKER}
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if not any(isinstance(s, ast.Continue) for s in node.body):
            continue
        for cmp_ in [n for n in ast.walk(node.test) if isinstance(n, ast.Compare)]:
            if len(cmp_.ops) != 1 or not isinstance(cmp_.ops[0], ast.In):
                continue
            left = cmp_.left
            if ((isinstance(left, ast.Constant) and left.value == MARKER)
                    or (isinstance(left, ast.Name) and left.id in aliases)):
                return True
    return False


def checks(tree) -> None:
    root = Path.cwd()

    # 1. Everything pyproject.toml says about Python says the same thing.
    #    Read as TOML: `version = "3.3.13"` is an application version and a
    #    text sweep cannot tell it from a Python one.
    data = tomllib.loads(tree.read("pyproject.toml"))
    declared = data.get("project", {}).get("requires-python", "")
    if declared.strip() != f">={FLOOR}":
        raise SystemExit(f'requires-python is {declared!r}, not ">={FLOOR}"')

    named = []
    for entry in data.get("project", {}).get("classifiers", []):
        parts = [p.strip() for p in str(entry).split("::")]
        if parts[:2] == ["Programming Language", "Python"] and len(parts) > 2:
            version = _as_version(parts[2])
            if version:
                named.append((f"classifier {entry!r}", version))
    if not named:
        raise SystemExit("no Programming Language :: Python :: X.Y classifier "
                         "survives, so nothing advertises a version at all")
    named += list(_tool_versions(data.get("tool", {}), ("tool",)))
    wrong = [f"{where} says {version}" for where, version in named
             if version != FLOOR]
    if wrong:
        raise SystemExit("pyproject.toml still names other versions: "
                         + "; ".join(wrong))

    # 2. Every CI job runs the floor, and there is at least one to run it.
    jobs = 0
    for path in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        rel = path.relative_to(root).as_posix()
        text = tree.files.get(rel, path.read_text(encoding="utf-8"))
        for number, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#") or "python-version:" not in line:
                continue
            value = line.split("python-version:", 1)[1]
            if "matrix.python-version" in value:
                continue
            for version in re.findall(r"\d+\.\d+", value):
                jobs += 1
                if version != FLOOR:
                    raise SystemExit(f"{rel}:{number} still runs {version}")
    if not jobs:
        raise SystemExit("no workflow names a concrete Python version, so "
                         "rule 2 passed over nothing")

    # 3. PyQt6 is capped wherever it is declared with a version at all. A
    #    bare `"pyqt6"` under dependencies is not an uncapped range.
    for rel in ("requirements.txt", "pyproject.toml", "tests/requirements-dev.txt"):
        if not (root / rel).exists():
            continue
        text = tree.files.get(rel, (root / rel).read_text(encoding="utf-8"))
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip().strip('"').strip("',")
            if not stripped.lower().startswith("pyqt6"):
                continue
            if not any(op in stripped for op in "<>=~!"):
                continue
            if "<7.0" not in stripped.replace(" ", ""):
                raise SystemExit(f"{rel}:{number} has no ceiling: {stripped}")

    # 4. pytest-timeout is declared here, not merely agreed about elsewhere.
    dev = tree.read("tests/requirements-dev.txt").lower()
    names = {re.split(r"[<>=!~\[ ]", ln.strip(), maxsplit=1)[0]
             for ln in dev.splitlines()
             if ln.strip() and not ln.strip().startswith("#")}
    if "pytest-timeout" not in names:
        raise SystemExit("tests/requirements-dev.txt does not declare "
                         "pytest-timeout")

    # 5. Every scanner this round edits actually SKIPS on the marker.
    #
    #    A CHECK THAT CANNOT FAIL WAS REMOVED FROM HERE. It read
    #    `if MARKER not in Path(__file__).read_text()` — does this script
    #    carry the marker — and it could never fire, because the script
    #    binds MARKER to that literal four lines above. Present by
    #    construction, asserted anyway: the exact shape
    #    tests/test_no_vacuous_tests.py was installed across this fleet to
    #    forbid, written by the same hand a round later. Found by trying to
    #    falsify it and failing. The question it was reaching for is asked
    #    at build time instead, of the module docstring, where a human
    #    writes the answer and can leave it out.
    scanners = sorted({rel for rel, *_ in EDITS
                       if rel.startswith("tests/test_brand")})
    for rel in scanners:
        if not _marker_is_honoured(tree.read(rel)):
            raise SystemExit(f"{rel} mentions the marker but does not skip "
                             f"on it -- the exclusion is decorative")

    # 6. The sentinel is in the file the already-applied check reads.
    if SENTINEL not in tree.files[SENTINEL_FILE]:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    where = f", {len(scanners)} scanner(s) skip on the marker" if scanners else ""
    print(f"  guards: requires-python >={FLOOR}, {len(named)} version "
          f"statement(s) in pyproject agree, {jobs} CI job(s) run it{where}")


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
