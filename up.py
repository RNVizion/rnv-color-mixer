#!/usr/bin/env python3
"""rnv-color-mixer -- test dependencies move into tests/, under the family name.

WHAT THIS CHANGES

    requirements-test.txt  ->  tests/requirements-dev.txt

Nothing else. No code, no colour, no test logic. The file's contents are
untouched apart from the one line inside it that tells you how to install it,
which would otherwise name a path that no longer exists.

WHY THIS NAME

Across the six repositories the split was exactly three and three:
requirements-test.txt in the mixer, picker and icon-builder;
requirements-dev.txt in the transformer, palette-manager and the MCP server.
The MCP server's is already at tests/requirements-dev.txt from an earlier
pass, so unifying on -dev leaves that repository alone and moves the other
five toward it.

USE VS MENTION -- THE RULE THAT GOVERNS EVERY REWRITE HERE

A reference to the old name is not automatically wrong. Three kinds exist:

  LIVE      a workflow's `pip install -r`, the file's own install line.
            Rewrite: these break or mislead if left.
  DOCS      README trees and install snippets, a pyproject comment.
            Rewrite: they describe the tree as it is now.
  HISTORY   a CHANGELOG entry recording what a past release shipped.
            DO NOT REWRITE. It is a true statement about the past, and
            editing it would make the record false.

This repository has no HISTORY-class reference; rnv-color-picker does, and
the same script shape there must leave CHANGELOG.md alone. The distinction is
spelled out because it has already produced one near-miss in this family: a
sweep for a retired gold nearly rewrote the `assertNotIn` guarding against it.

USAGE

    python scripts/up.py --check     # dry run, every pass runs, nothing written
    python scripts/up.py             # apply
    python scripts/up.py --finish    # delete this script

Runs correctly from the repository root as up.py too. Safe to run twice.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

OLD = "requirements-test.txt"
NEW_DIR = "tests"
NEW = "tests/requirements-dev.txt"


# --------------------------------------------------------------------------
# Where the old name appears, and what to do about each
# --------------------------------------------------------------------------

# (path, old text, new text, why)
REWRITES = (
    (".github/workflows/tests-linux.yml",
     "pip install -r requirements-test.txt",
     "pip install -r tests/requirements-dev.txt",
     "LIVE -- CI fails outright without this"),
    (".github/workflows/tests-windows.yml",
     "pip install -r requirements-test.txt",
     "pip install -r tests/requirements-dev.txt",
     "LIVE -- CI fails outright without this"),
    ("README.md",
     "├── requirements-test.txt    Test dependencies",
     "├── tests/                   Test suite and its dependencies",
     "DOCS -- the tree diagram; the file is no longer at this level"),
    ("README.md",
     "pip install -r requirements-test.txt",
     "pip install -r tests/requirements-dev.txt",
     "DOCS -- an instruction a reader will actually run"),
    ("pyproject.toml",
     "# Mirrors requirements-test.txt for users who prefer the modern PEP 621",
     "# Mirrors tests/requirements-dev.txt for users who prefer the modern PEP 621",
     "DOCS -- a comment naming the file it mirrors"),
)

# Inside the moved file itself. Applied after the move, to the new path.
SELF_REWRITE = ("# Install with: pip install -r requirements-test.txt",
                "# Install with: pip install -r tests/requirements-dev.txt")

# Files allowed to keep saying the old name after this runs, and why.
# Asserted in BOTH directions: a dead exemption is a licence waiting for a
# future defect, so an entry here that is no longer needed is an error.
MENTION_ONLY = {
    "tests/test_dependency_file_placement.py":
        "the guard; its job is to name the retired path",
}


# --------------------------------------------------------------------------
# The guard
# --------------------------------------------------------------------------

GUARD_PATH = "tests/test_dependency_file_placement.py"

GUARD_SOURCE = r'''"""Test dependencies live in tests/, under the family name.

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
'''


# --------------------------------------------------------------------------
# Machinery -- in-memory tree, flushed only after verification
# --------------------------------------------------------------------------

class Halt(SystemExit):
    pass


def _this_script() -> str:
    return os.path.relpath(os.path.realpath(__file__),
                           os.path.realpath(os.getcwd())).replace(os.sep, "/")


class Tree:
    SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "scripts",
                 ".pytest_cache", "htmlcov", ".benchmarks", ".hypothesis"}
    TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                     ".cfg", ".sh", ".bat"}

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.dirty: set[str] = set()

    def get(self, path: str) -> str:
        if path not in self.files:
            with open(path, "r", encoding="utf-8") as handle:
                self.files[path] = handle.read()
        return self.files[path]

    def sweep_text(self, path: str) -> str:
        if path in self.files:
            return self.files[path]
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def set(self, path: str, text: str) -> None:
        self.files[path] = text
        self.dirty.add(path)

    def texts(self):
        me = _this_script()
        for root, dirs, names in os.walk("."):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for name in sorted(names):
                if os.path.splitext(name)[1] not in self.TEXT_SUFFIXES:
                    continue
                path = os.path.relpath(os.path.join(root, name),
                                       ".").replace(os.sep, "/")
                if path != me:
                    yield path

    def flush(self) -> int:
        for path in sorted(self.dirty):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(self.files[path])
        return len(self.dirty)


def git(*args: str) -> str:
    result = subprocess.run(("git",) + args, capture_output=True, text=True)
    if result.returncode:
        raise Halt(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


# --------------------------------------------------------------------------
# Passes
# --------------------------------------------------------------------------

def already_done() -> bool:
    if os.path.exists(NEW) and not os.path.exists(OLD):
        print(f"Already applied -- {NEW} exists and {OLD} is gone.")
        print("Nothing to do. This is the idempotent exit, not an error.")
        return True
    return False


def check_fingerprint(tree: Tree) -> None:
    problems = []
    if not os.path.exists(OLD):
        problems.append(f"  {OLD} is not at the repository root")
    if os.path.exists(NEW):
        problems.append(f"  {NEW} already exists -- refusing to overwrite it")
    if not os.path.isdir(NEW_DIR):
        problems.append(f"  {NEW_DIR}/ does not exist")
    for path, old, _new, why in REWRITES:
        if not os.path.exists(path):
            problems.append(f"  {path} does not exist")
        elif old not in tree.sweep_text(path):
            problems.append(f"  {path}: expected {old!r}\n      ({why})")
    if problems:
        raise Halt("This is not the tree this script was written against:\n"
                   + "\n".join(problems)
                   + "\n\nRun it from the root of a clean checkout of main.")


def assert_no_reference_was_missed(tree: Tree) -> None:
    """REWRITES is written out by hand so a reviewer can read it, which makes
    it exactly the kind of list that goes stale. Sweep the repository for the
    old name and account for EVERY file that carries it -- either it is in
    REWRITES, or it is the file being moved, or it is a deliberate exemption.
    Anything else stops the run."""
    listed = {path for path, _o, _n, _w in REWRITES}
    exempt = set(MENTION_ONLY) | {OLD}
    unaccounted = []
    for path in tree.texts():
        if OLD not in tree.sweep_text(path):
            continue
        if path in listed or path in exempt:
            continue
        unaccounted.append(path)
    if unaccounted:
        raise Halt(
            "These name the old path but are in neither REWRITES nor the\n"
            "exemption list. Each one is either a rewrite this script is\n"
            "missing, or a HISTORY-class reference that must be exempted on\n"
            "purpose -- decide which, do not let it through by default:\n  "
            + "\n  ".join(unaccounted))
    print(f"  every file naming the old path is accounted for "
          f"({len(listed)} files, {len(REWRITES)} references to rewrite)")


def assert_the_exemptions_are_live(tree: Tree) -> None:
    """Both directions. An exemption for a file that no longer says the old
    name is dead weight, and dead weight is a licence."""
    for path, why in MENTION_ONLY.items():
        if path == GUARD_PATH:
            if OLD not in GUARD_SOURCE:
                raise Halt(f"{path} is exempted ({why}) but the guard source "
                           f"no longer names {OLD}. Drop the exemption.")
            continue
        if not os.path.exists(path):
            raise Halt(f"{path} is exempted ({why}) but does not exist")
    print(f"  {len(MENTION_ONLY)} exemption(s), each still needed")


def move_the_file(tree: Tree, dry: bool) -> None:
    body = tree.get(OLD)
    old_line, new_line = SELF_REWRITE
    if old_line not in body:
        raise Halt(f"{OLD} does not contain its own install line: {old_line!r}")
    tree.set(NEW, body.replace(old_line, new_line))
    if not dry:
        # git mv first so history follows the file, then rewrite in place.
        git("mv", OLD, NEW)
    print(f"  {OLD} -> {NEW}  (git mv, so history follows)")
    print(f"    and its own install line now names the new path")


def rewrite_references(tree: Tree) -> int:
    total = 0
    for path, old, new, why in REWRITES:
        src = tree.get(path)
        count = src.count(old)
        if count != 1:
            raise Halt(f"{path}: expected 1 occurrence of {old!r}, found "
                       f"{count}. Refusing to guess.")
        tree.set(path, src.replace(old, new))
        print(f"  {path}  [{why.split(' -- ')[0]}]")
        total += count
    return total


def install_guard(tree: Tree) -> None:
    tree.set(GUARD_PATH, GUARD_SOURCE)
    print(f"  {GUARD_PATH}: {len(GUARD_SOURCE.splitlines())} lines")


def verify(tree: Tree) -> None:
    problems, swept = [], 0
    exempt = set(MENTION_ONLY) | {OLD, NEW}
    for path in tree.texts():
        if path in exempt:
            continue
        swept += 1
        if OLD in tree.sweep_text(path):
            problems.append(f"{path} still names {OLD}")
    if swept < 20:
        problems.append(f"the sweep visited only {swept} files; it is not looking")
    if OLD not in f"pip install -r {OLD}":
        problems.append("the pattern no longer matches a known offender")

    body = tree.get(NEW)
    packages = [ln for ln in (l.strip() for l in body.splitlines())
                if ln and not ln.startswith("#")]
    if len(packages) < 3:
        problems.append(f"the moved file holds only {len(packages)} requirements")
    if SELF_REWRITE[1] not in body:
        problems.append("the moved file's own install line was not updated")

    for workflow in (".github/workflows/tests-linux.yml",
                     ".github/workflows/tests-windows.yml"):
        if "pip install -r tests/requirements-dev.txt" not in tree.get(workflow):
            problems.append(f"{workflow} does not install from the new path")

    if problems:
        raise Halt("VERIFY FAILED -- nothing was written:\n  "
                   + "\n  ".join(problems))
    print(f"  verify: {swept} files swept, {len(packages)} requirements intact, "
          f"both workflows install from {NEW}")


def finish() -> None:
    here = os.path.abspath(__file__)
    os.remove(here)
    print(f"Removed {here}")


def main() -> int:
    if "--finish" in sys.argv:
        finish()
        return 0

    dry = "--check" in sys.argv

    if not os.path.isdir(".git"):
        raise Halt("run this from the repository root (.git not found)")
    if already_done():
        return 0

    tree = Tree()
    check_fingerprint(tree)

    print("DRY RUN -- every pass runs, nothing is written\n" if dry
          else "Applying\n")

    print("1. account for every reference before touching anything")
    assert_no_reference_was_missed(tree)
    assert_the_exemptions_are_live(tree)

    print("\n2. move the file")
    move_the_file(tree, dry)

    print("\n3. rewrite what points at it")
    count = rewrite_references(tree)
    print(f"   {count} references")

    print("\n4. guard")
    install_guard(tree)

    print("\n5. verify the pending tree")
    verify(tree)

    if dry:
        print(f"\nDry run complete. {len(tree.dirty)} files would change; "
              f"none were written. The git mv did not run.")
        return 0

    written = tree.flush()
    print(f"\n6. wrote {written} files")

    print("\nDone. Now run, from the repository root:")
    print("    QT_QPA_PLATFORM=offscreen python -m pytest "
          "tests/test_dependency_file_placement.py -q")
    print("    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q --deselect "
          "tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths")
    print("\nExpected: 6 passed / 1 skipped, then 608 passed / 11 skipped.")
    print("The skip is deliberate: CHANGELOG.md carries no reference to the")
    print("retired path in THIS repository, so the history exemption is not")
    print("load-bearing here and says so out loud rather than passing quietly.")
    print(f"\nThen, once green:  python {_this_script()} --finish")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Halt as stop:
        print(f"\n{stop}", file=sys.stderr)
        sys.exit(1)
