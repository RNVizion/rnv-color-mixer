"""The README says how many tests there are in a way that stays true.

RNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".

WHAT WAS THERE. Exact totals, written once and kept in step by nothing. On
2026-10-05 the README said 886 tests and pytest collected 1,206.

WHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of
test functions the suites define, rounded down to the hundred. A test added
leaves it true, so there is nothing to keep in step. pytest collects more
than that number, because a parametrised function is written once and
collected once for each case.

WHAT THIS GUARD HOLDS.

1. Every number of tests the README states is a floor. An exact count,
   written as a sentence, as a badge or as a cell of the suites' table, is
   how the old ones went stale.
2. Every floor is true. The suite it speaks of defines more test functions
   than it says. Take tests away until one is not, and this names it: lower
   the README's number.
3. The reader is looking. It finds the README's floors, and it tells an
   exact count from a floor in each of the three ways one is written.

WHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage
figure depends on the platform it was taken on.
"""
from __future__ import annotations

import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

#: The unittest suite at the repository root.
ROOT_SUITE = "test_rnv_color_mixer.py"

#: The README states this many floors. Fewer and the reader has gone blind,
#: or the README has stopped saying.
MIN_FLOORS = 6

NUMBER = r"\d{1,3}(?:,\d{3})+|\d+"
SENTENCE = re.compile(rf"(?P<n>{NUMBER})\s+(?:(?:unittest|pytest|passing|automated)\s+)?tests\b", re.I)
BADGE = re.compile(r"\btests-(?P<n>\d+)(?P<plus>%2B)?", re.I)
CELL = re.compile(rf"\|\s*\**(?P<over>over\s+)?(?P<n>{NUMBER})\**\s*(?=\|)", re.I)
OVER_BEFORE = re.compile(r"over\s+\**$", re.I)
A_SUITE_ROW = re.compile(r"unittest|pytest|\btests\b|coverage", re.I)


def _claims(text: str) -> list:
    """(line number, the number, whether it is a floor, which suites it
    counts) for every number of tests the text states."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        seen = set()

        def add(match, floor: bool) -> None:
            if match.start("n") in seen:
                return
            seen.add(match.start("n"))
            low = line.lower()
            root = "unittest" in low or ROOT_SUITE.lower() in low
            modern = "pytest" in low or "`tests/`" in low
            suites = "root" if root and not modern else "pytest" if modern and not root else "all"
            found.append((number, int(match.group("n").replace(",", "")), floor, suites))

        for match in BADGE.finditer(line):
            add(match, bool(match.group("plus")))
        for match in SENTENCE.finditer(line):
            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))
        if line.lstrip().startswith("|") and A_SUITE_ROW.search(line):
            for match in CELL.finditer(line):
                add(match, bool(match.group("over")))
    return found


def _defined_in(source: str, unittest_file: bool) -> int:
    """How many test functions a file's text defines: a lower bound on what
    is collected from it, since a function is collected at least once."""
    tree = ast.parse(source)
    count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count += node.name.startswith("test_") and not unittest_file
        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):
            prefix = "test" if unittest_file else "test_"
            count += sum(1 for member in node.body
                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                         and member.name.startswith(prefix))
    return count


def _defined(path: pathlib.Path, unittest_file: bool) -> int:
    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)


def _suites() -> dict:
    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)
    modern = sum(_defined(path, unittest_file=False)
                 for path in sorted((ROOT / "tests").glob("test_*.py")))
    return {"root": root, "pytest": modern, "all": root + modern}


def test_every_number_of_tests_the_readme_states_is_a_floor():
    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in
             _claims(README.read_text(encoding="utf-8")) if not floor]
    assert not exact, (
        "the README states an exact number of tests, which goes stale with the next "
        "test:\n  " + "\n  ".join(exact) + "\nSay it as a floor: over N.")


def test_every_floor_is_true():
    defined = _suites()
    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}
    false = [f"README.md:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"
             for line, n, floor, suites in _claims(README.read_text(encoding="utf-8"))
             if floor and not n < defined[suites]]
    assert not false, (
        "the README promises more tests than the suites define:\n  " + "\n  ".join(false)
        + "\nLower the README's number.")


def test_the_reader_is_looking():
    """A reader that finds nothing passes both tests above."""
    floors = [c for c in _claims(README.read_text(encoding="utf-8")) if c[2]]
    assert len(floors) >= MIN_FLOORS, f"the reader finds {len(floors)} floors in the README, not {MIN_FLOORS}"
    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \
        f"the README's floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"
    defined = _suites()
    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"

    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\n"
              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\n"
              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\n"
              f"| `{ROOT_SUITE}` (unittest) | 398 | Frozen |\n"
              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\n"
              "| Ctrl+T | 12 | a row of some other table |\n"
              "Python 3.13, 2 suites, tests/test_x.py\n")
    assert _claims(sample) == [
        (1, 786, False, "all"), (2, 1000, True, "all"),
        (3, 786, False, "all"), (3, 1000, True, "all"),
        (4, 398, False, "root"),
        (5, 600, True, "pytest"),
    ], _claims(sample)
