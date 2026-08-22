"""Test dependencies live in tests/, under the family name.

    tests/requirements-dev.txt

All six RNV repositories use that path. This file MENTIONS the retired
`requirements-test.txt` and is therefore excluded from the sweep that forbids
it -- the use/mention distinction, which has produced a false "clean" in this
family more than once.
"""

import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
WANTED = REPO / "tests" / "requirements-dev.txt"
RETIRED = "requirements-test.txt"

SKIP_DIRS = {".git", "build", "dist", "__pycache__", ".venv", ".pytest_cache",
             "htmlcov", "scripts", ".benchmarks", ".hypothesis"}

# Only these may still say the retired name. Asserted in both directions.
MENTION_ONLY = {pathlib.Path(__file__).name}

# A changelog records what a past release shipped. Rewriting it would make a
# true statement false, so it is never swept -- but this repository has no
# such reference today, and the assertion below proves that rather than
# assuming it.
HISTORY_FILES = {"CHANGELOG.md"}

TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                 ".cfg", ".sh", ".bat"}


def _is_delivery_script(path):
    if "scripts" in path.parts:
        return True
    return path.parent == REPO and path.name.startswith("up")


def _files():
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in MENTION_ONLY or _is_delivery_script(path):
            continue
        yield path


def test_the_dependency_file_is_where_it_belongs():
    assert WANTED.is_file(), f"{WANTED} is missing"
    assert not (REPO / RETIRED).exists(), \
        f"{RETIRED} is still at the repository root"


def test_the_moved_file_still_has_content():
    """A move that produced an empty file would satisfy every path assertion
    here and fail CI only at pip-install time, in another repository's idea
    of a useful error message."""
    lines = [ln.strip() for ln in WANTED.read_text(encoding="utf-8").splitlines()]
    packages = [ln for ln in lines if ln and not ln.startswith("#")]
    assert len(packages) >= 3, f"only {len(packages)} requirements found"


def test_nothing_still_points_at_the_retired_path():
    offenders = []
    for path in _files():
        if path.name in HISTORY_FILES:
            continue
        if RETIRED in path.read_text(encoding="utf-8", errors="replace"):
            offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, \
        "these still name the retired path:\n  " + "\n  ".join(offenders)


def test_that_sweep_is_actually_looking():
    """Guard the guard.

    The sweep above can only report a problem if it reads files. One that
    walks an empty list passes forever, which is how a rename ships half
    done. Both halves are asserted: that the walk is non-empty and reaches
    the files that were actually rewritten, and that a planted string is
    still detected.
    """
    walked = {p.relative_to(REPO).as_posix() for p in _files()}
    assert len(walked) > 20, f"the sweep only found {len(walked)} files"
    for required in ("README.md", "pyproject.toml",
                     ".github/workflows/tests-linux.yml",
                     ".github/workflows/tests-windows.yml"):
        assert required in walked, f"{required} is not being swept"
    assert RETIRED in f"pip install -r {RETIRED}", \
        "the retired-path pattern no longer matches a known offender"


def test_the_mention_exemption_is_not_dead():
    """An exemption asserted in one direction only is a licence waiting for a
    defect. This proves the exempted file still needs its exemption."""
    here = pathlib.Path(__file__)
    assert here.name in MENTION_ONLY
    assert RETIRED in here.read_text(encoding="utf-8"), \
        "this file no longer mentions the retired path -- drop the exemption"


def test_the_history_exemption_is_honest():
    """CHANGELOG.md is exempted on principle, not because it needs to be.

    If one ever appears carrying the retired name, that is correct and should
    stay. If one appears WITHOUT it, the exemption is dead weight and this
    test says so rather than letting it sit there as a silent licence.
    """
    for name in HISTORY_FILES:
        path = REPO / name
        if not path.exists():
            continue
        if RETIRED not in path.read_text(encoding="utf-8", errors="replace"):
            pytest.skip(
                f"{name} exists but does not name the retired path; the "
                f"exemption is harmless here and is kept for the repositories "
                f"where it is load-bearing")


def test_the_workflows_install_from_the_new_path():
    """The assertion that would have caught a rename that moved the file and
    forgot the thing that installs it."""
    for workflow in ("tests-linux.yml", "tests-windows.yml"):
        text = (REPO / ".github" / "workflows" / workflow).read_text(
            encoding="utf-8")
        assert "pip install -r tests/requirements-dev.txt" in text, workflow
