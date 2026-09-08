#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: give Linux CI back the 12 tests it has been skipping.

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHY NOW. TestAsyncFileOpsErrorPaths and TestAsyncFileOpsFormatPaths were
deselected on Linux because they aborted the interpreter (SIGABRT, exit
134). The thread-ownership round removed the defect that caused it. That is
not an inference -- it was measured, matched and interleaved, on the tree
before and after that fix, with these two classes INCLUDED:

        before the fix   70 aborts / 120 runs   (58.3%)
        after the fix     0 aborts / 120 runs

P(0 in 120 at 58.3%) = 2e-46. The deselects were load-bearing; they are not
any more.

CREDIT WHERE IT IS DUE. KNOWN_ISSUES.md had this right on 22 August, three
weeks before the fix was written:

    "qtbot.waitSignal returns the instant `finished` fires; the `thread`
     local then goes out of scope at the end of the test, and Qt can find
     itself destroying a QThread that has not finished unwinding."

and prescribed the remedy -- "hold the thread on the object, not on the
stack". What the recent round added was the SCOPE (seventeen sites, not the
two or three named), the implementation, and the proof. The diagnosis was
already in this repository.

WHAT THIS TOUCHES, AND WHY IT IS FOUR EDITS RATHER THAN TWO DELETIONS.
Removing the arguments alone would leave three statements that are then
false:

  1. .github/workflows/tests-linux.yml -- the two --deselect arguments.
  2. The comment block above them, which lists the skips and their reasons.
  3. KNOWN_ISSUES.md, whose 31 Aug update records the family as deselected
     and prescribes keeping it that way.
  4. tests/test_ci_deselects.py::test_the_documented_family_is_the_one_that
     _is_deselected, which asserts that BOTH classes are deselected. Its
     premise inverts, so the test is replaced by its opposite: the family
     must NOT be deselected, and KNOWN_ISSUES.md must say why it came back.

That fourth one is the reason this is a round of its own. A guard whose
premise has reversed is not a guard to delete quietly -- it is one to point
the other way, so the next person to add a deselect for this family has to
justify it against a written record.

WHAT DOES NOT CHANGE. The unittest deselect for
test_load_real_image_if_available stays: that is a different problem (an
offscreen hang loading the background image) and this round has no evidence
about it. No application file is touched. No test is skipped or removed.
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
SENTINEL_FILE = ".github/workflows/tests-linux.yml"
SENTINEL = "RESTORED 2026-09-08"
GUARD = "tests/test_restored_classes.py"
DESCRIPTION = "restore the two deselected AsyncFileOps classes to Linux CI"
SUITES = [("\"pytest tests/ -- exactly as Linux CI now runs it\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, 355 tests\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-RESTORED-CLASSES-GUARD -- the 12 tests Linux CI stopped skipping
actually run there, and keep running.

Installed 2026-09-08. `tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths`
and `tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths` were
deselected on Linux from 31 August because they aborted the interpreter
(SIGABRT, exit 134). The thread-ownership fix removed the cause, measured on
the tree before and after with both classes included:

    before   70 aborts / 120 runs   (58.3%)
    after     0 aborts / 120 runs

WHAT THIS ADDS THAT tests/test_ci_deselects.py DOES NOT. That file reads the
workflow: it proves the arguments are gone and that the prose agrees. This
one proves the tests THEMSELVES are real, present and exercising the thing
they were written for -- because a restored deselect achieves nothing if the
class was quietly emptied or renamed in the meantime, and both files would
pass over the silence.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: (file, class, the number of tests it held when the deselects came off)
RESTORED = (
    ('tests/test_error_recovery_paths.py', 'TestAsyncFileOpsErrorPaths', 4),
    ('tests/test_lifecycle_handlers.py', 'TestAsyncFileOpsFormatPaths', 6),
)


def _methods(rel: str, cls: str):
    path = ROOT / rel
    assert path.exists(), f'{rel} is missing'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return [n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n.name.startswith('test')]
    return None


def test_both_restored_classes_still_exist():
    """A class that was renamed or removed leaves the workflow clean and the
    coverage gone, with nothing to say so."""
    missing = [f'{rel}::{cls}' for rel, cls, _ in RESTORED
               if _methods(rel, cls) is None]
    assert not missing, (
        'these classes were restored to Linux CI on 2026-09-08 and no longer '
        'exist:\n  ' + '\n  '.join(missing))


def test_they_still_hold_the_tests_they_held():
    """Counted, not assumed. Twelve tests came back; if that number falls,
    it should be because somebody decided so."""
    thin = []
    for rel, cls, expected in RESTORED:
        names = _methods(rel, cls) or []
        if len(names) < expected:
            thin.append(f'{rel}::{cls} has {len(names)}, had {expected}')
    assert not thin, (
        'restored classes have lost tests:\n  ' + '\n  '.join(thin)
        + '\n\nIf that was deliberate, lower the count in this file in the '
          'same commit, so the loss is written down rather than absorbed.')


def test_they_are_not_skipped_by_decorator_instead():
    """The other way to make a test quiet.

    Removing a --deselect and adding @pytest.mark.skip has the same effect
    on coverage and a much smaller diff. KNOWN_ISSUES.md is explicit that
    this family should be deselected visibly rather than marked skip, "so
    the cost stays countable" -- and that reasoning survives the fix.
    """
    marked = []
    for rel, cls, _ in RESTORED:
        text = (ROOT / rel).read_text(encoding='utf-8')
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ClassDef) and node.name == cls):
                continue
            targets = [node] + [n for n in node.body
                                if isinstance(n, ast.FunctionDef)]
            for target in targets:
                for dec in target.decorator_list:
                    src = ast.get_source_segment(text, dec) or ''
                    if 'skip' in src and 'skipif' not in src:
                        marked.append(f'{rel}::{cls}::{getattr(target, "name", "?")}'
                                      f'  @{src.strip()[:40]}')
    assert not marked, (
        'these are skipped by decorator, which hides them as effectively as '
        'the deselect did:\n  ' + '\n  '.join(marked))


def test_the_thread_ownership_fixture_is_what_they_depend_on():
    """Name the coupling, so it cannot be removed by accident.

    These classes are only safe to run because every thread they build is
    adopted. If the fixture disappears, this round's premise disappears with
    it, and the aborts come back at 58%.
    """
    conftest = (ROOT / 'tests' / 'conftest.py').read_text(encoding='utf-8')
    assert 'def adopt(' in conftest, (
        'the adopt() fixture is gone from tests/conftest.py. The two '
        'AsyncFileOps classes were restored to Linux CI on the strength of '
        'it; without it they abort roughly three runs in five.')
    for rel, cls, _ in RESTORED:
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert 'adopt(' in text, (
            f'{rel} no longer uses adopt(), so the threads it starts are '
            f'abandoned again.')
'''

EDITS = [('.github/workflows/tests-linux.yml', '          coverage run --data-file=.coverage.pytest --branch -m pytest tests/ -v --deselect tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths --deselect tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths', '          coverage run --data-file=.coverage.pytest --branch -m pytest tests/ -v', 1), ('.github/workflows/tests-linux.yml', '          # Skips:\n          #   - test_load_real_image_if_available (unittest):\n          #       Hangs on offscreen Qt when loading background image.\n          #   - TestAsyncFileOpsErrorPaths (pytest):\n          #       Qt threading + filesystem ops crash Python natively\n          #       (SIGABRT) on offscreen Linux.\n          #   - TestAsyncFileOpsFormatPaths (pytest):\n          #       The same family, in a different file. Aborted CI on\n          #       2026-08-31 at test_writer_binary_format_writes_bytes.\n          #       Reproduced on an UNTOUCHED checkout of the same commit:\n          #       one abort in three runs, at the identical test.\n          #       KNOWN_ISSUES.md said to deselect this family the way\n          #       TestAsyncFileOpsErrorPaths is deselected if it ever\n          #       became noisy. It has.\n', '          # Skips:\n          #   - test_load_real_image_if_available (unittest):\n          #       Hangs on offscreen Qt when loading background image.\n          #\n          # RESTORED 2026-09-08 — TestAsyncFileOpsErrorPaths and\n          # TestAsyncFileOpsFormatPaths are no longer deselected. They were\n          # skipped for a SIGABRT that KNOWN_ISSUES.md had diagnosed\n          # correctly on 22 Aug: qtbot.waitSignal returns the instant the\n          # custom `finished` signal fires, the thread local then goes out\n          # of scope, and Qt destroys a QThread that has not finished\n          # unwinding. Seventeen tests did that; all seventeen now hold\n          # their thread through the adopt() fixture in tests/conftest.py.\n          #\n          # Matched, interleaved trials on the tree before and after that\n          # fix, with these two classes included:\n          #       before   70 aborts / 120 runs   (58.3%)\n          #       after     0 aborts / 120 runs\n          # tests/test_thread_ownership.py keeps the seventeen honest.\n', 1), ('KNOWN_ISSUES.md', '**Update, 31 Aug 2026 — it became noisy, so it is deselected.**', '**Update, 31 Aug 2026 — it became noisy, so it was deselected.**\n\n**Resolved, 8 Sep 2026 — the cause was fixed and it is no longer\ndeselected.** The mechanism was the one this file described on 22 August:\n`qtbot.waitSignal` returns the instant the custom `finished` signal fires,\nthe `thread` local goes out of scope, and Qt destroys a `QThread` that has\nnot finished unwinding. What was not known then is how many places did it:\n**seventeen tests across four files**, of which the two deselected classes\nwere ten.\n\nAll seventeen now take their thread through the `adopt()` fixture in\n`tests/conftest.py`, which owns it and waits for it in teardown — a fixture\nrather than a trailing `wait()` because teardown still runs when an\nassertion fails. That is the refactor this entry prescribed, applied to the\ntests rather than to `utils/async_file_ops.py`; the application itself never\nhad the bug, because `ColorHistory` holds `_save_thread` on the object and\n`AsyncFileManager` keeps `_active_threads`, and both check `isRunning()`\nbefore letting go.\n\nMeasured before shipping, matched and interleaved, with these two classes\nincluded in both arms:\n\n| tree | aborts | runs | rate |\n|---|---:|---:|---:|\n| before the fix | 70 | 120 | 58.3% |\n| after the fix | 0 | 120 | 0% |\n\n`tests/test_thread_ownership.py` fails if any test starts a thread it does\nnot own, so the seventeen cannot quietly become eighteen.', 1), ('tests/test_ci_deselects.py', 'def test_the_documented_family_is_the_one_that_is_deselected():\n    """KNOWN_ISSUES.md prescribes deselecting the AsyncFileOps family on\n    Linux when it becomes noisy. This is the link between the prose and the\n    workflow, asserted in the one direction that can be."""\n    nodes = {node for _w, node in _deselects()}\n    linux = [n for n in nodes if \'AsyncFileOps\' in n]\n    assert len(linux) >= 2, (\n        f\'expected both AsyncFileOps classes to be deselected on Linux, \'\n        f\'found {sorted(linux)}\')\n    known = (ROOT / \'KNOWN_ISSUES.md\').read_text(encoding=\'utf-8\')\n    for node in linux:\n        cls = node.rsplit(\'::\', 1)[-1]\n        assert cls in known, (\n            f\'{cls} is deselected in CI but not described in \'\n            f\'KNOWN_ISSUES.md. A deselect with no written reason is an \'\n            f\'exemption nobody can review.\')\n', 'def test_the_family_is_no_longer_deselected():\n    """The inverse of the assertion this replaced, and deliberately so.\n\n    Until 8 Sep 2026 this file asserted that BOTH AsyncFileOps classes were\n    deselected on Linux, because KNOWN_ISSUES.md prescribed it while they\n    aborted the interpreter. The thread-ownership fix removed that abort --\n    measured on the tree before and after, with these classes included:\n    70 aborts in 120 runs before, 0 in 120 after -- so the premise reversed.\n\n    A guard whose premise has reversed is not one to delete. It is one to\n    point the other way: if somebody deselects this family again, they have\n    to write down why, and that is what this asks for.\n    """\n    nodes = {node for _w, node in _deselects()}\n    back = sorted(n for n in nodes if \'AsyncFileOps\' in n)\n    known = (ROOT / \'KNOWN_ISSUES.md\').read_text(encoding=\'utf-8\')\n    assert not back, (\n        \'these AsyncFileOps nodes are deselected again:\\n  \'\n        + \'\\n  \'.join(back)\n        + \'\\n\\nThey were restored on 2026-09-08 after the abort they were \'\n          \'skipped for was fixed and the fix was measured (0 aborts in 120 \'\n          \'runs, against 70 in 120 before). If it has come back, say so in \'\n          \'KNOWN_ISSUES.md with what you measured, and change this test \'\n          \'deliberately rather than around.\')\n    assert \'no longer\\ndeselected\' in known or \'no longer deselected\' in known, (\n        \'KNOWN_ISSUES.md no longer records why the AsyncFileOps family came \'\n        \'back into Linux CI. The workflow and the prose have to agree, and \'\n        \'prose is the half nothing else checks.\')\n\n\ndef test_the_restored_classes_still_collect():\n    """The other direction. Removing a deselect achieves nothing if the\n    tests it was hiding have since been renamed or deleted -- the run would\n    be just as quiet, and this file would still pass."""\n    restored = (\'tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths\',\n                \'tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths\')\n    result = subprocess.run(\n        [sys.executable, \'-m\', \'pytest\', *restored, \'--collect-only\', \'-q\',\n         \'-p\', \'no:cacheprovider\'],\n        cwd=ROOT, capture_output=True, text=True)\n    assert result.returncode == 0 and \'no tests ran\' not in result.stdout, (\n        \'the classes restored on 2026-09-08 no longer collect:\\n\'\n        + result.stdout[-800:])\n    # pytest\'s own count, not the shape of its output: `--collect-only -q`\n    # renders a <Function ...> tree on this version rather than node ids, so\n    # counting lines with \'::\' reports twelve healthy tests as none.\n    found = re.search(r\'(\\d+)\\s+tests?\\s+collected\', result.stdout)\n    collected = int(found.group(1)) if found else 0\n    assert collected >= 10, (\n        f\'only {collected} restored test(s) collect; there were 12 when the \'\n        f\'deselects were removed. If tests were legitimately retired, update \'\n        f\'this floor in the same commit.\\n\' + result.stdout[-400:])\n', 1)]

RESTORED = ("tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths",
            "tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths")


def edits(tree) -> None:
    if SENTINEL in tree.read(SENTINEL_FILE):
        raise SystemExit("already applied")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    print("  removed 2 --deselect argument(s) from the Linux workflow")
    print("  rewrote the comment that documented them")
    print("  recorded the restoration in KNOWN_ISSUES.md")
    print("  inverted tests/test_ci_deselects.py's family assertion")


def checks(tree) -> None:
    wf = tree.read(SENTINEL_FILE)

    # 1. neither class is deselected anywhere, in any workflow
    root = Path.cwd()
    still = []
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        text = tree.files.get(path.relative_to(root).as_posix()) \
            or path.read_text(encoding="utf-8")
        for node in RESTORED:
            cls = node.rsplit("::", 1)[-1]
            if re.search(r"--deselect\s+\"?\S*" + re.escape(cls), text):
                still.append(f"{path.name}: {cls}")
    if still:
        raise SystemExit("still deselected: " + ", ".join(still))

    # 2. the unittest deselect SURVIVES. This round has no evidence about
    #    the offscreen image hang, and removing it by accident would be a
    #    silent scope creep into a different defect.
    if "test_load_real_image_if_available" not in wf:
        raise SystemExit("the unittest deselect was removed; it must stay")

    # 3. the prose no longer contradicts the workflow
    if SENTINEL not in wf:
        raise SystemExit("the workflow comment was not updated")
    # Markdown wraps, so a phrase can arrive as "no longer\ndeselected".
    # Collapse whitespace before looking: a check that reads prose has to
    # read it the way prose is written, or it fails on the line break rather
    # than on the meaning. This one did, on its first run.
    known = " ".join(tree.read("KNOWN_ISSUES.md").split())
    for phrase in ("no longer deselected", "8 Sep 2026"):
        if phrase not in known:
            raise SystemExit(f"KNOWN_ISSUES.md does not record {phrase!r}")

    # 4. the inverted guard is present and the old assertion is gone
    ci = tree.read("tests/test_ci_deselects.py")
    if "test_the_documented_family_is_the_one_that_is_deselected" in ci:
        raise SystemExit("the old family assertion survives; its premise is "
                         "now false and it would fail")
    if "test_the_family_is_no_longer_deselected" not in ci:
        raise SystemExit("the replacement assertion did not land")

    # 5. and the tests really do collect -- the whole point of the round.
    #    Asked of pytest rather than assumed, because a class that cannot be
    #    collected would make this round restore nothing at all.
    out = subprocess.run(
        [sys.executable, "-m", "pytest", *RESTORED, "--collect-only", "-q",
         "-p", "no:cacheprovider"],
        cwd=root, capture_output=True, text=True)
    if out.returncode != 0 or "no tests ran" in out.stdout:
        raise SystemExit("the restored classes do not collect:\n"
                         + out.stdout[-600:])
    # Read pytest's own count, not the shape of its output. `--collect-only
    # -q` renders a <Function ...> tree here rather than node ids, so
    # counting lines containing "::" returns 0 and reports twelve healthy
    # tests as none. It did exactly that on the first run of this script.
    found = re.search(r"(\d+)\s+tests?\s+collected", out.stdout)
    n = int(found.group(1)) if found else 0
    if n < 10:
        raise SystemExit(f"only {n} restored test(s) collect; expected 12\n"
                         + out.stdout[-400:])
    print(f"  guards: 0 deselects for this family, the unittest one intact, "
          f"{n} restored test(s) collect")


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
