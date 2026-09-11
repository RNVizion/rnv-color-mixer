#!/usr/bin/env python3
"""RNV-NO-VACUOUS-TESTS — a test that cannot fail is not a test.

    python up.py             # apply, then run the guard and both suites
    python up.py --check     # rehearse every edit in memory, write nothing

For rnv-color-mixer, derived against a fresh clone at the live head.

WHY THIS EXISTS HERE. The rule was written for rnv-color-mixer, where one
assertion in tests/ could not fail:

    assert result is not None or True

It sat in a test that had never run — it called a function that does not
exist, caught the AttributeError, and turned it into a permanent
`pytest.skip("not in this version")`. A specification reported as a skip
reads, in a summary line, exactly like coverage.

Then the same sweep was run across the whole fleet: **5,667 test functions
in five applications**. This is what it found here.

    nothing -- the one vacuous assertion here was fixed on 2026-09-10.
    This round replaces the repo-specific copy of the guard with the
    portable one, so all five checkouts carry the same file.

WHAT THE GUARD ENFORCES: no assertion true regardless of the code; no test
body that is only `pass`; no test that can never fail (no assertion AND
every statement swallowed); no test that skips itself on AttributeError.

WHAT IT DELIBERATELY DOES NOT: forbid a test having no assertion. Hundreds
of those across this fleet are legitimate — they are named `..._no_crash`
and they fail if the call raises. A rule against them would be noise that
gets suppressed, which is worse than no rule.

THE GUARD IS IDENTICAL IN ALL FIVE CHECKOUTS, AND THAT COST TWO MISTAKES.
Its first version swept `tests/` only and asserted at least 500 test
functions. Ported unchanged it would have landed **red** in the palette
manager, which has 443 under tests/, and **blind** in the same repository,
whose snapshots/ directory holds six more tests it would never have read.
Both were numbers and paths taken from the repository it was written in. It
now discovers what to read — every `test_*.py` except the ones at the
repository root, where each application keeps its locked suite — and its
floor is structural: at least twenty files, and at least as many test
functions as files.

THE LOCKED SUITE IS EXCLUDED EVERYWHERE, by ownership rather than by
quality. In the mixer it is where every remaining instance lives: all 13
`except Exception: pass` handlers and all 3 tests that can never fail.
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
SENTINEL_FILE = "tests/conftest.py"
SENTINEL = "RNV-NO-VACUOUS-TESTS"
GUARD = "tests/test_no_vacuous_tests.py"
DESCRIPTION = "install the rule that a test must be able to fail"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file\"",
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
'''

EDITS = [('tests/conftest.py', '"""\nRNV Color Mixer — /tests/ Pytest Configuration  (Phase 1 deliverable)\n', '# RNV-NO-VACUOUS-TESTS, 2026-09-10 -- tests/test_no_vacuous_tests.py\n# sweeps this repository for tests that cannot fail: assertions true\n# whatever the code does, bodies that are only `pass`, tests with no\n# assertion that swallow everything they call, and self-skips on a\n# name that never existed. It deliberately permits a test with no\n# assertion at all -- those assert by not raising.\n"""\nRNV Color Mixer — /tests/ Pytest Configuration  (Phase 1 deliverable)\n', 1)]


def edits(tree) -> None:
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))


def _read(path: Path) -> str:
    raw = path.read_bytes()
    return raw.decode("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8")


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
        pure = (ast.Name, ast.Attribute, ast.Constant)
        left, op, right = node.left, node.ops[0], node.comparators[0]
        if (isinstance(op, (ast.Eq, ast.Is))
                and isinstance(left, pure) and isinstance(right, pure)
                and ast.dump(left) == ast.dump(right)):
            return "a comparison of a value with itself"
    return None


def checks(tree) -> None:
    root = Path.cwd()

    # 1. no assertion under sweep can be true regardless of the code.
    #    Checked here as well as in the installed guard, so a bad tree is
    #    refused before anything is written to it.
    files = [p for p in sorted(root.rglob("test_*.py"))
             if ".git" not in p.parts and p.parent != root
             and not p.name.startswith("up")]
    bad = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = tree.files.get(rel) or _read(path)
        try:
            parsed = ast.parse(text, rel)
        except SyntaxError as e:
            raise SystemExit(f"{rel} does not parse: {e}")
        for n in ast.walk(parsed):
            if isinstance(n, ast.Assert):
                why = _always_true(n.test)
                if why:
                    bad.append(f"{rel}:{n.lineno} {ast.unparse(n)[:56]} ({why})")
    if bad:
        raise SystemExit("assertions that cannot fail survive: " + "; ".join(bad))

    # 2. the sweep can see something. A guard that reads no file passes
    #    every rule above; the image-budget round shipped exactly that.
    if len(files) < 20:
        raise SystemExit(f"only {len(files)} test files found; the sweep is "
                         f"looking in the wrong place")
    counted = sum(1 for p in files
                  for n in ast.walk(ast.parse(tree.files.get(
                      p.relative_to(root).as_posix()) or _read(p)))
                  if isinstance(n, ast.FunctionDef) and n.name.startswith("test"))
    if counted < len(files):
        raise SystemExit(f"{counted} test functions across {len(files)} files; "
                         f"at least one file yielded none")

    # 3. the locked suite is at the root, where the sweep skips it. If it
    #    moved under tests/, the exclusion would now be hiding it.
    locked = sorted(p.name for p in root.glob("test_*.py"))
    if not locked:
        raise SystemExit("no locked suite at the repository root; either this "
                         "is the wrong checkout or the suite moved")

    # 4. the sentinel is in the file the re-run check reads. Shipped broken
    #    once in this programme; never again without a check.
    if SENTINEL not in tree.files[SENTINEL_FILE]:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    print(f"  guards: 0 tautologies across {len(files)} test files, "
          f"{counted} test functions, locked suite {locked[0]} left alone")


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
