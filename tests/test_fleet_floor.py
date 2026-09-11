"""RNV-FLEET-FLOOR-GUARD -- one interpreter and one ceiling, fleet-wide.

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
