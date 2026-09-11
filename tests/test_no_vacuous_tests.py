"""RNV-NO-VACUOUS-TESTS-GUARD -- a test that cannot fail is not a test.

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

THIS GUARD IS FLEET-PORTABLE, AND THAT COST TWO REPO-SPECIFIC MISTAKES.
The first version swept `tests/` only and asserted at least 500 test
functions. Ported unchanged it would have landed RED in the palette
manager, which has 443 under tests/, and BLIND in the same repo, whose
snapshots/ directory holds six more tests the sweep would never have read.
Both were numbers and paths taken from the repository it was written in.

It now discovers what to read: every `test_*.py` anywhere in the checkout
except the repository ROOT, where each application keeps its one locked
suite. The floor is structural rather than magic -- at least twenty files,
and at least as many test functions as files, since a test file with no
tests in it means the walk has gone blind.

THE LOCKED SUITE IS EXCLUDED, AND IN THE MIXER IT IS WHERE THE PROBLEM
ACTUALLY IS. test_rnv_color_mixer.py holds all 13 `except Exception: pass`
handlers in that repository and all 3 tests that can never fail:

    test_handle_exception_no_crash          (line 1177)
    test_set_autosave_interval_no_crash     (line 1482)
    test_load_settings_no_crash             (line 1545)

Each has no assertion and swallows everything it calls. Two others in that
file call `FileUtils.auto_detect_and_import_palette` on the class with one
argument, so both raise TypeError before reaching the function and both
swallow it -- documented in tests/test_palette_import.py.

That file is locked by convention, so this round reports rather than edits.
The exclusion is a statement about ownership, not about quality: those
tests are the ones worth fixing.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Each application keeps its one locked suite as a `test_*.py` at the
#: repository root. Discovered rather than named, so this file is identical
#: in all five checkouts -- two copies of a guard that differ by a filename
#: are two copies that drift.
def _locked_suites():
    return sorted(p.name for p in ROOT.glob("test_*.py"))

#: Names that promise the test asserts by not raising. Used only to explain
#: a NO-ASSERT test in a message, never to excuse one from a real rule.
SMOKE_MARKERS = ("no_crash", "does_not_crash", "no_error", "survives")


def _test_files():
    """Every test file this guard governs, wherever it lives.

    Anything at the repository root is a locked suite and is skipped; so is
    a delivery script. Everything else is swept, which is how the palette
    manager's snapshots/ directory gets read at all.
    """
    for path in sorted(ROOT.rglob("test_*.py")):
        if ".git" in path.parts:
            continue
        if path.parent == ROOT:
            continue
        if path.name.startswith("up"):
            continue
        yield path


def _read(path: Path) -> str:
    """BOM-aware, because six files in this fleet carry one.

    `read_text("utf-8")` leaves a U+FEFF at the start of the string and
    ast.parse rejects it, so a BOM'd test file would turn this guard into a
    collection error rather than a result. Python's own import machinery
    strips it; tests/test_brand_mirror.py already decodes this way.
    """
    raw = path.read_bytes()
    return raw.decode("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8")


def _tests(path: Path):
    src = _read(path)
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
    assert len(files) >= 20, (
        f"only {len(files)} test files found under {ROOT}; the sweep is "
        f"looking in the wrong place")

    counted = sum(1 for p in files for _ in _tests(p))
    assert counted >= len(files), (
        f"{counted} test functions parsed out of {len(files)} files. At "
        f"least one file yielded none, which means the walk has gone blind "
        f"rather than that the repository is small -- a structural floor, "
        f"not a number copied from whichever repository this was written in. "
        f"The first version asserted 500 and would have landed red in the "
        f"palette manager, which has 443.")

    locked = _locked_suites()
    assert locked, (
        "no locked suite found at the repository root. Either this is not "
        "one of the five applications, or the suite moved -- in which case "
        "the exclusion in _test_files is now hiding it from the sweep.")
