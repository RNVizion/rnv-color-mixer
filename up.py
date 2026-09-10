#!/usr/bin/env python3
"""RNV-NO-VACUOUS-TESTS — a test that cannot fail is not a test.

    python up.py             # apply, then run the guard and both suites
    python up.py --check     # rehearse every edit in memory, write nothing

Derived against a fresh clone of rnv-color-mixer at head 34e3536, after a
sweep of all 1,049 test functions in 51 files.

THE HEADLINE IS GOOD, AND IT IS THE POINT OF SAYING IT FIRST. `tests/` held
exactly **one** assertion that could not fail. No empty test bodies. Every
one of the 94 tests with no assertion turned out to be a deliberate smoke
test — they are named `..._no_crash` and `..._does_not_crash`, and they fail
if the call raises, which is what they are for. This round does not touch
them, and the guard it installs does not either.

THE ONE.

    result = FileUtils.detect_palette_format(ext)
    assert result is not None or True   # Some impls return None

`x or True` is true whatever x is. Worse, the assertion never executed:
`FileUtils.detect_palette_format` does not exist and never has, so the call
raised AttributeError, which the test caught and turned into

    pytest.skip("detect_palette_format not in this version")

A permanent skip, a reason that was wrong, and an inert assertion behind it.
Its `expected` column — "gpl", "aco", "ase", "json" — was never compared
against anything either. It now drives `PaletteFormats.detect_format`, the
function that does exist, and asserts the extension it returns.

TWO MORE OF THE SAME FAMILY.

  * `get_palette_format_filter` names a function that exists nowhere in the
    codebase. Rewritten against `PaletteFormats.get_import_formats()`, the
    (label, pattern) pairs a QFileDialog filter is actually built from.

  * `safe_execute(default=)` names a parameter that has never existed, and
    the test's docstring asserted in prose that "some callers pass
    `default=`" — a factual claim, and a false one: nothing in the
    application passes it. Deleted, with the reason left in its place. The
    behaviour that does exist is covered by the test above it.

A specification reported as a skip reads, in a summary line, exactly like
coverage.

WHAT THE GUARD ENFORCES, over tests/ only: no assertion that is true
regardless of the code; no test body that is only `pass`; no test that can
never fail (no assertion AND every statement swallowed); no test that skips
itself on AttributeError. What it deliberately does NOT enforce: a test
having no assertion. Ninety of those are legitimate here, and a rule against
them would be noise that gets suppressed — which is worse than no rule.

WHERE THE PROBLEM ACTUALLY IS, AND WHY THIS ROUND LEAVES IT.
`test_rnv_color_mixer.py` holds every remaining instance in the repository:
all 13 `except Exception: pass` handlers, and all 3 tests that can never
fail —

    test_handle_exception_no_crash          line 1177
    test_set_autosave_interval_no_crash     line 1482
    test_load_settings_no_crash             line 1545

each with no assertion and everything it calls swallowed. Two others there
call `FileUtils.auto_detect_and_import_palette` on the class with one
argument, so both raise TypeError before reaching the function and both
swallow it. That file is locked by convention, so this round records rather
than edits, in KNOWN_ISSUES.md and in the guard's own docstring. The
exclusion is a statement about ownership, not about quality: those are the
tests worth fixing.
"""
from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
SENTINEL_FILE = "tests/test_app_event_handlers.py"
SENTINEL = "RNV-NO-VACUOUS-TESTS"
GUARD = "tests/test_no_vacuous_tests.py"
DESCRIPTION = "remove the assertions that cannot fail"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, 356 tests\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-NO-VACUOUS-TESTS-GUARD -- a test that cannot fail is not a test.

Installed 2026-09-10, after a sweep of all 1,049 test functions in the
repository.

WHAT THE SWEEP FOUND, AND WHAT IT DID NOT. The honest headline first: this
suite is in good shape. Across 51 files there was exactly **one** assertion
in tests/ that could not fail, no empty test bodies, and every one of the 94
tests without an assertion turned out to be a deliberate smoke test -- they
are named `..._no_crash` and `..._does_not_crash`, and they fail if the call
raises, which is the whole point of them. Those are not defects and this
guard does not touch them.

THE ONE. tests/test_app_event_handlers.py held

    result = FileUtils.detect_palette_format(ext)
    assert result is not None or True   # Some impls return None

`x or True` is true whatever x is. The assertion could not fail. Worse, it
never ran: `FileUtils.detect_palette_format` does not exist and never has,
so the call raised AttributeError, which the test caught and turned into
`pytest.skip("detect_palette_format not in this version")`. A permanent
skip, a wrong reason, and an assertion that was inert anyway. Its `expected`
column was never compared with anything either.

TWO MORE OF THE SAME FAMILY went with it. `get_palette_format_filter` names
a function that exists nowhere in the codebase, and
`safe_execute(default=)` a parameter that has never existed -- and whose
test claimed in its docstring that "some callers pass `default=`" when none
do. Both skipped themselves permanently. A specification reported as a skip
reads, in a summary line, exactly like coverage.

WHAT THIS GUARD ENFORCES, over tests/ only:

  * no assertion that is true regardless of the code under test;
  * no test whose body is only `pass`;
  * no test that can never fail -- no assertion of any kind AND every
    statement wrapped in a `try` whose handler is a bare `pass`.

WHAT IT DELIBERATELY DOES NOT ENFORCE. A test with no assertion is fine on
its own: `def test_set_theme_does_not_crash` asserts by not raising. Ninety
of those are legitimate here and a rule against them would be noise that
gets suppressed, which is worse than no rule.

THE LOCKED FILE IS EXCLUDED, AND IT IS WHERE THE PROBLEM ACTUALLY IS.
test_rnv_color_mixer.py holds all 13 `except Exception: pass` handlers in
the repository and all 3 tests that can never fail:

    test_handle_exception_no_crash          (line 1177)
    test_set_autosave_interval_no_crash     (line 1482)
    test_load_settings_no_crash             (line 1545)

Each has no assertion and swallows everything it calls. Two others in that
file call `FileUtils.auto_detect_and_import_palette` on the class with one
argument, so both raise TypeError before reaching the function and both
swallow it -- documented in tests/test_palette_import.py.

That file is locked by convention, so this round reports rather than edits.
LOCKED below is the exclusion, and it is a statement about ownership, not
about quality: those tests are the ones worth fixing.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

#: Not swept: changing it is out of scope by convention, not because it is
#: clean. See the module docstring -- it is where every finding lives.
LOCKED = "test_rnv_color_mixer.py"

#: Names that promise the test asserts by not raising. Used only to explain
#: a NO-ASSERT test in a message, never to excuse one from a real rule.
SMOKE_MARKERS = ("no_crash", "does_not_crash", "no_error", "survives")


def _test_files():
    for path in sorted(TESTS.rglob("test_*.py")):
        if path.name == LOCKED:
            continue
        yield path


def _tests(path: Path):
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, str(path))
    except SyntaxError as exc:                      # pragma: no cover
        raise AssertionError(f"{path} does not parse: {exc}")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            yield src, node


def _body(fn: ast.FunctionDef) -> list:
    body = list(fn.body)
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return body


def _always_true(node: ast.expr) -> str | None:
    """Why this expression is true whatever the code does, or None."""
    if isinstance(node, ast.Constant):
        if node.value is True:
            return "the literal True"
        if isinstance(node.value, (int, float, str)) and node.value:
            return f"the truthy literal {node.value!r}"
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        for value in node.values:
            why = _always_true(value)
            if why:
                return f"an `or` against {why}"
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        # Both sides must be side-effect-free. `list(g) == list(g)` is NOT a
        # tautology: if g is lazy the first call exhausts it and the second
        # returns []. tests/test_pil_compat.py uses exactly that to prove a
        # result is not a generator, and the first draft of this rule called
        # that clever test a defect.
        pure = (ast.Name, ast.Attribute, ast.Constant)
        left, op, right = node.left, node.ops[0], node.comparators[0]
        if (isinstance(op, (ast.Eq, ast.Is))
                and isinstance(left, pure) and isinstance(right, pure)
                and ast.dump(left) == ast.dump(right)):
            return "a comparison of a value with itself"
    if (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "isinstance"
            and len(node.args) == 2 and getattr(node.args[1], "id", "") == "object"):
        return "isinstance(..., object), which holds for everything"
    return None


def _has_assertion(fn: ast.FunctionDef) -> bool:
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            return True
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "").startswith("assert"):
            return True
    rendered = ast.unparse(fn)
    return "raises" in rendered or "warns" in rendered


def test_no_assertion_is_true_no_matter_what_the_code_does():
    """The rule that caught the one.

    An assertion whose truth does not depend on the subject is worse than no
    assertion: it reports as coverage, it survives every refactor, and it
    reads at a glance like a real check.
    """
    bad = []
    for path, fn in ((p, f) for p in _test_files() for _, f in _tests(p)):
        for node in ast.walk(fn):
            if isinstance(node, ast.Assert):
                why = _always_true(node.test)
                if why:
                    rel = path.relative_to(ROOT).as_posix()
                    bad.append(f"{rel}:{node.lineno}  {fn.name}\n"
                               f"      {ast.unparse(node)[:96]}\n"
                               f"      -- always true, because of {why}")
    assert not bad, (
        "these assertions cannot fail:\n  " + "\n  ".join(bad)
        + "\n\nAssert the thing the test is named after, or delete the line. "
          "A check that cannot fail is worse than none: it looks like one.")


def test_no_test_body_is_only_pass():
    """A skipped `pass` was how the palette-import hang stayed hidden.

    It reported as a skip for a year and covered nothing; the reason
    attached to it was the only thing it ever contributed, and the reason
    was wrong.
    """
    bad = []
    for path, fn in ((p, f) for p in _test_files() for _, f in _tests(p)):
        body = _body(fn)
        if body and all(isinstance(s, ast.Pass) for s in body):
            rel = path.relative_to(ROOT).as_posix()
            bad.append(f"{rel}:{fn.lineno}  {fn.name}")
    assert not bad, (
        "these tests have no body:\n  " + "\n  ".join(bad)
        + "\n\nIf the note attached to it is the point, put the note in the "
          "module docstring and delete the function.")


def test_no_test_can_never_fail():
    """No assertion AND everything swallowed. The complete case.

    Either half alone is defensible -- a smoke test asserts by not raising,
    and a `try/except` can be the assertion when something else checks the
    result. Together they are a function that runs and reports success
    unconditionally.
    """
    bad = []
    for path, fn in ((p, f) for p in _test_files() for _, f in _tests(p)):
        body = _body(fn)
        if not body or _has_assertion(fn):
            continue
        tries = [s for s in body if isinstance(s, ast.Try)]
        if len(tries) != len(body) or not tries:
            continue
        if all(all(len(h.body) == 1 and isinstance(h.body[0], ast.Pass)
                   for h in t.handlers) for t in tries):
            rel = path.relative_to(ROOT).as_posix()
            bad.append(f"{rel}:{fn.lineno}  {fn.name}")
    assert not bad, (
        "these tests cannot fail -- no assertion, and every call swallowed:\n  "
        + "\n  ".join(bad)
        + "\n\nAssert something, or narrow the except to the exception the "
          "test is about, or delete it.")


def test_no_test_skips_itself_over_a_name_that_does_not_exist():
    """The permanent skip.

    `except AttributeError: pytest.skip("not in this version")` is how three
    tests here reported as skipped for a year while naming functions that
    had never existed. A skip whose condition can never change is a deleted
    test that still shows up in the summary line.
    """
    bad = []
    for path, fn in ((p, f) for p in _test_files() for _, f in _tests(p)):
        for handler in [n for n in ast.walk(fn) if isinstance(n, ast.ExceptHandler)]:
            catches = ast.unparse(handler.type) if handler.type else ""
            if "AttributeError" not in catches:
                continue
            if any(isinstance(n, ast.Call)
                   and getattr(n.func, "attr", "") == "skip"
                   for n in ast.walk(handler)):
                rel = path.relative_to(ROOT).as_posix()
                bad.append(f"{rel}:{handler.lineno}  {fn.name}")
    assert not bad, (
        "these tests skip themselves when an attribute is missing:\n  "
        + "\n  ".join(bad)
        + "\n\nThat skip is permanent if the name never existed, and it "
          "reads as coverage. Call the function that does exist, or delete "
          "the test and say why.")


def test_this_guard_can_see_the_files_it_judges():
    """A sweep that finds nothing passes every assertion above.

    Not hypothetical here: the image-budget guard shipped with a rule whose
    glob matched no file in three of five repositories, and every other test
    in it was green.
    """
    files = list(_test_files())
    assert len(files) >= 30, (
        f"only {len(files)} test files found under {TESTS}; the sweep is "
        f"looking in the wrong place")

    counted = sum(1 for p in files for _ in _tests(p))
    assert counted >= 500, (
        f"only {counted} test functions parsed out of those files; the "
        f"walk has stopped seeing them")

    assert not (TESTS / LOCKED).exists(), (
        f"{LOCKED} is inside tests/, so the exclusion above is silently "
        f"skipping a file this guard was meant to read")
'''

EDITS = [('tests/test_app_event_handlers.py', '    def test_detect_palette_format_for_known_extensions(self):\n        from file_utils import FileUtils\n        for ext, expected in [\n            ("test.gpl", "gpl"),\n            ("test.aco", "aco"),\n            ("test.ase", "ase"),\n            ("test.json", "json"),\n        ]:\n            try:\n                result = FileUtils.detect_palette_format(ext)\n                # Result should be the format name or similar\n                assert result is not None or True  # Some impls return None\n            except AttributeError:\n                # Method doesn\'t exist — skip\n                pytest.skip("detect_palette_format not in this version")\n                return\n\n    def test_get_palette_format_filter_returns_string(self):\n        """`get_palette_format_filter()` builds the QFileDialog filter\n        string for palette imports."""\n        from file_utils import FileUtils\n        try:\n            result = FileUtils.get_palette_format_filter()\n            assert isinstance(result, str)\n            assert len(result) > 0\n        except AttributeError:\n            pytest.skip("get_palette_format_filter not in this version")\n', '    def test_detect_format_returns_the_extension_for_known_types(self):\n        """RNV-NO-VACUOUS-TESTS, 2026-09-10.\n\n        This was `test_detect_palette_format_for_known_extensions`, and it\n        had never run. It called `FileUtils.detect_palette_format`, which\n        does not exist and never has; the AttributeError was caught and\n        turned into `pytest.skip("not in this version")`, so the skip was\n        permanent and the reason was wrong. Its one assertion was\n\n            assert result is not None or True\n\n        which is true whatever `result` is, so even had it run it would have\n        checked nothing. Its `expected` column was never compared against\n        anything either.\n\n        The real function is `PaletteFormats.detect_format`, and it returns\n        the lowercased extension INCLUDING the leading dot.\n        """\n        from core.palette_formats import PaletteFormats\n\n        for filename, expected in [\n            ("test.gpl", ".gpl"),\n            ("test.aco", ".aco"),\n            ("test.ase", ".ase"),\n            ("test.json", ".json"),\n            ("TEST.GPL", ".gpl"),\n        ]:\n            assert PaletteFormats.detect_format(filename) == expected, (\n                f"detect_format({filename!r}) should be {expected!r}")\n\n    def test_the_import_filter_data_is_usable_by_a_file_dialog(self):\n        """RNV-NO-VACUOUS-TESTS, 2026-09-10.\n\n        This was `test_get_palette_format_filter_returns_string`, which\n        called `FileUtils.get_palette_format_filter()` — a name that exists\n        nowhere in the codebase — and skipped on the AttributeError. It was\n        a specification for a function nobody wrote, reported as a skip.\n\n        What does exist is `PaletteFormats.get_import_formats()`, returning\n        the (label, pattern) pairs a QFileDialog filter is built from. That\n        is the thing worth guarding.\n        """\n        from core.palette_formats import PaletteFormats\n\n        formats = PaletteFormats.get_import_formats()\n        assert formats, "no import formats are offered at all"\n\n        for entry in formats:\n            assert isinstance(entry, tuple) and len(entry) == 2, (\n                f"expected (label, pattern) pairs, got {entry!r}")\n            label, pattern = entry\n            assert label and isinstance(label, str), f"empty label in {entry!r}"\n            assert pattern.startswith("*."), (\n                f"{pattern!r} is not a glob a file dialog can use")\n\n        patterns = " ".join(p for _, p in formats)\n        assert "*.gpl" in patterns, (\n            f"GIMP palettes are importable but not offered: {patterns[:120]}")\n', 1), ('tests/test_utility_modules.py', '    def test_safe_execute_with_default_value_returns_default_on_exception(self):\n        """Some callers pass `default=` to get a non-None fallback."""\n        # Check whether safe_execute supports a `default` kwarg\n        import inspect\n        sig = inspect.signature(ErrorHandler.safe_execute)\n        if "default" not in sig.parameters:\n            pytest.skip("safe_execute doesn\'t support `default=` kwarg")\n        result = ErrorHandler.safe_execute(\n            lambda: 1 / 0, "div zero", default="fallback"\n        )\n        assert result == "fallback"\n\n', '    # RNV-NO-VACUOUS-TESTS, 2026-09-10.\n    # `test_safe_execute_with_default_value_returns_default_on_exception`\n    # stood here. It skipped itself with "safe_execute doesn\'t support\n    # `default=` kwarg", which was true and permanent: no such parameter has\n    # ever existed. Its docstring said "Some callers pass `default=`" -- a\n    # factual claim, and a false one; nothing in the application passes it.\n    # It was a specification for a feature nobody asked for, reported as a\n    # skip. The behaviour that DOES exist -- returning None when the call\n    # raises -- is asserted by the test immediately above. Deleted rather\n    # than left skipping, because a permanent skip reads as coverage.\n\n', 1), ('KNOWN_ISSUES.md', '*No open user-facing bugs at this time.*', '*No open user-facing bugs at this time.*\n\n---\n\n## Tests that cannot fail\n\nSwept 2026-09-10 across all 1,049 test functions in 51 files. The headline\nis good: `tests/` held exactly **one** assertion that could not fail, no\nempty test bodies, and every one of the 94 tests without an assertion is a\ndeliberate smoke test — named `..._no_crash` or `..._does_not_crash`, and\nfailing if the call raises. Those are not defects.\n\nThe one, now fixed, was `assert result is not None or True` — true whatever\n`result` is. It sat in a test that had never run: it called\n`FileUtils.detect_palette_format`, a name that does not exist, caught the\n`AttributeError` and turned it into a permanent\n`pytest.skip("not in this version")`. Two siblings did the same for\n`get_palette_format_filter` and `safe_execute(default=)`, neither of which\nhas ever existed. `tests/test_no_vacuous_tests.py` now fails on any of these\nfour shapes.\n\n**Open, and in the locked file.** `test_rnv_color_mixer.py` holds every\nremaining instance — all 13 `except Exception: pass` handlers in the\nrepository, and all 3 tests that can never fail:\n\n| test | line |\n|---|---|\n| `test_handle_exception_no_crash` | 1177 |\n| `test_set_autosave_interval_no_crash` | 1482 |\n| `test_load_settings_no_crash` | 1545 |\n\nEach has no assertion and wraps everything it calls in `try/except: pass`,\nso it reports success unconditionally. Two others —\n`test_auto_detect_import_missing_graceful` and\n`test_auto_detect_import_json` — call\n`FileUtils.auto_detect_and_import_palette` on the class with one argument,\nso both raise `TypeError` before reaching the function and both swallow it.\n\nThat file is locked by convention, so this is a record rather than a fix.\nThe guard excludes it and says so; the exclusion is about ownership, not\nabout quality.', 1)]

LOCKED = "test_rnv_color_mixer.py"


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL in src:
        raise SystemExit(f"already applied -- '{SENTINEL}' is present in "
                         f"{SENTINEL_FILE}")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)

    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))


def _always_true(node):
    if isinstance(node, ast.Constant):
        if node.value is True:
            return "the literal True"
        if isinstance(node.value, (int, float, str)) and node.value:
            return f"the truthy literal {node.value!r}"
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        for value in node.values:
            why = _always_true(value)
            if why:
                return f"an `or` against {why}"
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        # Both sides side-effect-free only. `list(g) == list(g)` is not a
        # tautology: a generator exhausts, so the second call returns [].
        # tests/test_pil_compat.py uses exactly that, and the first draft of
        # this rule called that clever test a defect.
        pure = (ast.Name, ast.Attribute, ast.Constant)
        left, op, right = node.left, node.ops[0], node.comparators[0]
        if (isinstance(op, (ast.Eq, ast.Is))
                and isinstance(left, pure) and isinstance(right, pure)
                and ast.dump(left) == ast.dump(right)):
            return "a comparison of a value with itself"
    return None


def checks(tree) -> None:
    root = Path.cwd()

    # 1. the two rewritten tests parse, run against real functions, and
    #    carry no tautology.
    aeh = tree.files["tests/test_app_event_handlers.py"]
    try:
        aeh_tree = ast.parse(aeh, "tests/test_app_event_handlers.py")
    except SyntaxError as e:
        raise SystemExit(f"the rewritten test file does not parse: {e}")

    for name in ("test_detect_format_returns_the_extension_for_known_types",
                 "test_the_import_filter_data_is_usable_by_a_file_dialog"):
        if not any(isinstance(n, ast.FunctionDef) and n.name == name
                   for n in ast.walk(aeh_tree)):
            raise SystemExit(f"{name} did not land")
    for gone in ("test_detect_palette_format_for_known_extensions",
                 "test_get_palette_format_filter_returns_string"):
        if any(isinstance(n, ast.FunctionDef) and n.name == gone
               for n in ast.walk(aeh_tree)):
            raise SystemExit(f"{gone} is still present; it never ran")

    # 2. no tautology survives anywhere under tests/. Checked here as well
    #    as in the installed guard, so a bad tree is refused before
    #    anything is written to it.
    bad = []
    for path in sorted((root / "tests").rglob("test_*.py")):
        rel = path.relative_to(root).as_posix()
        text = tree.files.get(rel)
        if text is None:
            text = path.read_text(encoding="utf-8")
        try:
            parsed = ast.parse(text, rel)
        except SyntaxError:
            continue
        for n in ast.walk(parsed):
            if isinstance(n, ast.Assert):
                why = _always_true(n.test)
                if why:
                    bad.append(f"{rel}:{n.lineno} {ast.unparse(n)[:60]} ({why})")
    if bad:
        raise SystemExit("assertions that cannot fail survive: " + "; ".join(bad))

    # 3. the deleted test is gone and left a reason behind. A silent
    #    deletion looks identical to a test that was never written.
    tum = tree.files["tests/test_utility_modules.py"]
    if "test_safe_execute_with_default_value" in tum and "def test_safe_execute_with_default_value" in tum:
        raise SystemExit("the aspirational test is still defined")
    if SENTINEL not in tum:
        raise SystemExit("the deletion left no note saying why")

    # 4. the guard excludes the locked file BY NAME, and the locked file is
    #    not under tests/ -- otherwise the exclusion would be silently
    #    skipping a file the sweep was meant to read.
    guard = tree.files[GUARD]
    if LOCKED not in guard:
        raise SystemExit("the guard does not name the file it excludes")
    if (root / "tests" / LOCKED).exists():
        raise SystemExit(f"{LOCKED} is inside tests/; the exclusion would "
                         f"blind the sweep")

    # 5. the record. Read with whitespace collapsed, because markdown wraps
    #    where the width runs out and a check has failed here before on a
    #    line break rather than the meaning.
    ki = " ".join(tree.files["KNOWN_ISSUES.md"].split())
    for phrase in ("1,049 test functions", "test_handle_exception_no_crash",
                   "test_no_vacuous_tests.py"):
        if phrase not in ki:
            raise SystemExit(f"KNOWN_ISSUES.md does not record {phrase!r}")

    # 6. the sentinel is in the file the re-run check reads. Shipped broken
    #    once; never again without a check.
    if SENTINEL not in aeh:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    print("  guards: 0 tautologies under tests/, both rewritten tests drive "
          "real functions, the locked file is named not hidden")


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
