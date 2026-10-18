"""Every document says how many tests there are in a way that stays true.

RNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".
RNV-RULINGS-2026-10-11, item 23. Ruled 2026-10-11: "Yes". The other
documents that state how many tests there are take the README's floors, and
this guard reads them too.

WHAT WAS THERE. Exact totals, written once and kept in step by nothing. On
2026-10-05 the README said 886 tests and pytest collected 1,206.
No other document here states a total.

WHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of
test functions the suites define, rounded down to the hundred. A test added
leaves it true, so there is nothing to keep in step. pytest collects more
than that number, because a parametrized function is written once and
collected once for each case.

A DATED RECORD IS LEFT AS IT WAS. A section that records the counts at a
moment past, such as the log of the campaign that built the suite, says
what was true then; a floor would make it say something else. Each such
section is named in RECORDS, and its counts are not read.

WHAT THIS GUARD HOLDS.

1. Every number of tests a document in DOCUMENTS states, outside a dated
   record, is a floor. An exact count, written as a sentence, as a badge
   or as a cell of a table of suites, is how the old ones went stale.
2. Every floor is true. The suite it speaks of defines more test functions
   than it says. Take tests away until one is not, and this names it: lower
   the document's number.
3. The reader is looking. It finds each document's floors, and every dated
   record it is told to leave alone, still holding counts; it tells an
   exact count from a floor in each of the three ways one is written; and
   it reads a table's cell for its column's heading alone, as for its row's
   label alone.

WHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage
figure depends on the platform it was taken on.
"""
from __future__ import annotations

import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The unittest suite at the repository root.
ROOT_SUITE = "test_rnv_color_mixer.py"

#: Every document that says how many tests there are, and how many floors it
#: states. Fewer and the reader has gone blind, or the document has stopped
#: saying. The README is the first.
DOCUMENTS = {'README.md': 6}

#: Sections that are dated records, by the document and the heading's text.
#: Their counts are what was true when they were written, and are not read.
RECORDS = {}

NUMBER = r"\d{1,3}(?:,\d{3})+|\d+"
SENTENCE = re.compile(rf"(?P<n>{NUMBER})\s+(?:(?:unittest|pytest|passing|automated)\s+)?tests\b", re.I)
BADGE = re.compile(r"\btests-(?P<n>\d+)(?P<plus>%2B)?", re.I)
OVER_BEFORE = re.compile(r"over\s+\**$", re.I)
#: A table's cell holds a count of tests when its column is headed so, or
#: when its row is labeled so ("Total tests"). A cell is its number alone.
SEPARATOR = re.compile(r"^\s*\|?(?:\s*:?-{2,}:?\s*\|)+\s*:?-*:?\s*$")
COUNT_COLUMN = re.compile(r"\b(?:tests?|count)\b", re.I)
TEST_ROW = re.compile(r"\btests?\b|unittest|pytest", re.I)
CELL = re.compile(rf"^\s*\**(?P<over>over\s+)?(?P<n>{NUMBER})\**\*?\s*$", re.I)
HEADING = re.compile(r"^(?P<level>#{1,6})\s+(?P<text>.+?)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")


def _cells(line: str) -> list:
    """(where it starts in the line, its text) for each cell of a table's row."""
    edges = [i for i, ch in enumerate(line) if ch == "|"]
    return [(a + 1, line[a + 1:b]) for a, b in zip(edges, edges[1:])]


def _claims(text: str) -> list:
    """(line number, the number, whether it is a floor, which suites it
    counts) for every number of tests the text states."""
    found = []
    lines = text.splitlines()
    header = None
    for number, line in enumerate(lines, 1):
        seen = set()
        in_table = line.lstrip().startswith("|")
        if not in_table:
            header = None
        elif SEPARATOR.match(line):
            continue
        elif number < len(lines) and SEPARATOR.match(lines[number]):
            header = [cell.strip() for _at, cell in _cells(line)]
            continue

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
        if in_table and header is not None:
            cells = _cells(line)
            labeled = bool(cells) and bool(TEST_ROW.search(cells[0][1]))
            for column, (at, cell) in enumerate(cells):
                match = CELL.match(cell)
                headed = column < len(header) and bool(COUNT_COLUMN.search(header[column]))
                if match and column and (headed or labeled):
                    add(_Shifted(match, at), bool(match.group("over")))
    return found


class _Shifted:
    """A match in a cell, read as a match in its line."""

    def __init__(self, match, at: int) -> None:
        self.match, self.at = match, at

    def start(self, group: str) -> int:
        return self.at + self.match.start(group)

    def group(self, name: str):
        return self.match.group(name)


def _records(text: str, headings) -> dict:
    """heading -> the line numbers of its section, for each dated record a
    text holds: from its heading to the next heading of its level or above.
    A heading inside a fenced block of code is not one."""
    lines, fenced, found = text.splitlines(), False, {}
    marks = []
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        match = None if fenced else HEADING.match(line)
        if match:
            marks.append((number, len(match.group("level")), match.group("text")))
    for i, (number, level, title) in enumerate(marks):
        if title in headings:
            end = next((n for n, lv, _t in marks[i + 1:] if lv <= level), len(lines) + 1)
            found.setdefault(title, []).append(range(number, end))
    return found


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def _stated(rel: str) -> list:
    """The claims a document makes, outside its dated records."""
    text = _read(rel)
    skipped = set()
    for spans in _records(text, RECORDS.get(rel, ())).values():
        for span in spans:
            skipped.update(span)
    return [claim for claim in _claims(text) if claim[0] not in skipped]


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


def test_every_number_of_tests_a_document_states_is_a_floor():
    exact = [f"{rel}:{line}: {n:,}" for rel in DOCUMENTS
             for line, n, floor, _s in _stated(rel) if not floor]
    assert not exact, (
        "a document states an exact number of tests, which goes stale with the next "
        "test:\n  " + "\n  ".join(exact) + "\nSay it as a floor: over N. A section that records the "
        "counts at a moment past is named in RECORDS instead.")


def test_every_floor_is_true():
    defined = _suites()
    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}
    false = [f"{rel}:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"
             for rel in DOCUMENTS for line, n, floor, suites in _stated(rel)
             if floor and not n < defined[suites]]
    assert not false, (
        "a document promises more tests than the suites define:\n  " + "\n  ".join(false)
        + "\nLower the document's number.")


def test_the_reader_is_looking():
    """A reader that finds nothing passes both tests above."""
    readme = next(iter(DOCUMENTS))
    assert readme == "README.md", f"the README is not the first document: {list(DOCUMENTS)}"
    for rel, least in DOCUMENTS.items():
        floors = [c for c in _stated(rel) if c[2]]
        assert len(floors) >= least, f"the reader finds {len(floors)} floors in {rel}, not {least}"
    floors = [c for c in _stated(readme) if c[2]]
    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \
        f"the README's floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"
    for rel, headings in RECORDS.items():
        text = _read(rel)
        found = _records(text, headings)
        for heading in headings:
            spans = found.get(heading, [])
            assert len(spans) == 1, f"{rel}: the dated record {heading!r} is there {len(spans)} times"
            held = [c for c in _claims(text) if c[0] in spans[0]]
            assert held, f"{rel}: the dated record {heading!r} holds no count: it needs no exemption"
    defined = _suites()
    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"

    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\n"
              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\n"
              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\n"
              "| Suite | Tests | Purpose |\n"
              "|---|---:|---|\n"
              f"| `{ROOT_SUITE}` (unittest) | 398 | the root suite |\n"
              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\n"
              "| Both, together | over 1,000 | read for its column alone |\n"
              "\n"
              "| Metric | Value |\n"
              "|---|---|\n"
              "| Total tests | **1,641** |\n"
              "| Modules at 90% coverage | 12 |\n"
              "| Shortcut | Count |\n"
              "\n"
              "| # | Item | Status |\n"
              "|---|---|---|\n"
              "| 1 | pytest-qt with qtbot | Done |\n"
              "Python 3.13, 2 suites, tests/test_x.py\n")
    assert _claims(sample) == [
        (1, 786, False, "all"), (2, 1000, True, "all"),
        (3, 786, False, "all"), (3, 1000, True, "all"),
        (6, 398, False, "root"),
        (7, 600, True, "pytest"),
        (8, 1000, True, "all"),
        (12, 1641, False, "all"),
    ], _claims(sample)
    record = ("## Now\nover 300 unittest tests\n## The log\n### Phase 1\n| 1 | unittest | 400 |\n"
              "```\n# not a heading\n```\n## After\n12 tests\n")
    assert _records(record, ("The log",)) == {"The log": [range(3, 9)]}, _records(record, ("The log",))
