#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Deselect the second AsyncFileOps class on Linux CI, as KNOWN_ISSUES.md
already prescribes, and make every deselect prove it still points at a real
test.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THIS CHANGES NO APPLICATION CODE AT ALL. One workflow line, one
KNOWN_ISSUES.md entry, one new test.

WHAT HAPPENED

Linux CI aborted on 2026-08-31 with exit 134 at
tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths::test_writer_binary_format_writes_bytes.
Windows was green on the same commit.

IT IS NOT THE ALIGNMENT WORK, AND THAT IS CHECKED RATHER THAN ASSERTED. The
same file was run three times on an UNTOUCHED checkout of the same commit,
with none of the colour changes applied: run 1 aborted at exactly that test,
twenty tests in; runs 2 and 3 passed 27/27. Same abort, same position, no
changes present.

THE REPOSITORY ALREADY PREDICTED THIS

KNOWN_ISSUES.md carries an entry titled "FileWriterThread signal tests --
intermittent SIGABRT, deliberately not skipped". It says the abort surfaces
during whatever work is in flight and "reads exactly like a regression in
that work. It is not one." It also says, in as many words:

    If it becomes noisy, deselect it the way TestAsyncFileOpsErrorPaths is
    deselected rather than marking it skip, so the cost stays visible.

It has become noisy. This does what that sentence says.

WHY THE EXISTING DESELECT DID NOT COVER IT

The workflow already deselects
tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths -- the same
root cause, the same thread lifecycle, a nearly identical class name, in a
different file. The exemption was written for one home of the pattern and
the pattern has two.

A DESELECT IS AN EXEMPTION, SO IT GETS A GUARD

pytest SILENTLY IGNORES a --deselect that matches nothing. No warning, no
error -- the run just collects everything and the exemption stops applying.
Three hand-written node ids now live in these workflows, and a rename would
turn any of them off without a word.

tests/test_ci_deselects.py reads every workflow, extracts every --deselect,
and asserts pytest can still collect the node it names. It also asserts that
each deselected AsyncFileOps class is described in KNOWN_ISSUES.md, so the
workflow and the prose cannot drift apart in the direction that can be
checked.

WHAT THIS DOES NOT FIX

The underlying lifecycle bug. KNOWN_ISSUES.md names the real repair -- hold
the thread on the object rather than on the stack -- and that is still the
right fix and still outstanding. Worth adding: the abort is preceded in the
CI log by a swallowed

    RuntimeError: wrapped C/C++ object of type QLabel has been deleted

from RNV_Color_Mixer.py:2365, a preview callback firing after its label is
gone. That is the same lifecycle smell one level up, and it deserves its own
look rather than being bundled in here.
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
DESCRIPTION = "deselect the second AsyncFileOps class on Linux CI"
SENTINEL_FILE = ".github/workflows/tests-linux.yml"
SENTINEL = "TestAsyncFileOpsFormatPaths"
KNOWN = "KNOWN_ISSUES.md"
GUARD = "tests/test_ci_deselects.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

#: The guard is the point of this pass, so it is what gets run. The full
#: suites are not re-run here: this pass touches no application code, and
#: the thing it is responding to is an intermittent abort in the suite it
#: is deselecting from.
SUITES = [
    ('the deselect guard',
     [sys.executable, "-m", "pytest", GUARD, "-q", "-p", "no:cacheprovider"]),
]

OLD_COMMENT = '          #   - TestAsyncFileOpsErrorPaths (pytest):\n          #       Qt threading + filesystem ops crash Python natively\n          #       (SIGABRT) on offscreen Linux.'
NEW_COMMENT = '          #   - TestAsyncFileOpsErrorPaths (pytest):\n          #       Qt threading + filesystem ops crash Python natively\n          #       (SIGABRT) on offscreen Linux.\n          #   - TestAsyncFileOpsFormatPaths (pytest):\n          #       The same family, in a different file. Aborted CI on\n          #       2026-08-31 at test_writer_binary_format_writes_bytes.\n          #       Reproduced on an UNTOUCHED checkout of the same commit:\n          #       one abort in three runs, at the identical test.\n          #       KNOWN_ISSUES.md said to deselect this family the way\n          #       TestAsyncFileOpsErrorPaths is deselected if it ever\n          #       became noisy. It has.'
OLD_RUN = '          coverage run --data-file=.coverage.pytest --branch -m pytest tests/ -v --deselect tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths'
NEW_RUN = '          coverage run --data-file=.coverage.pytest --branch -m pytest tests/ -v --deselect tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths --deselect tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths'
KNOWN_ANCHOR = '**Planned fix:** the same refactor as above — hold the thread on the\nobject, not on the stack.\n\n---'
KNOWN_NEW = '**Planned fix:** the same refactor as above — hold the thread on the\nobject, not on the stack.\n\n**Update, 31 Aug 2026 — it became noisy, so it is deselected.**\n`tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths` aborted\nLinux CI at `test_writer_binary_format_writes_bytes`, with Windows green on\nthe same commit. Reproduced locally on an **untouched checkout of that same\ncommit**: one abort in three runs, at the identical test, twenty tests in.\nThe abort is preceded by a swallowed\n`RuntimeError: wrapped C/C++ object of type QLabel has been deleted` from\n`RNV_Color_Mixer.py:2365` — a preview callback firing after its label is\ngone — which is the same lifecycle smell described above and is worth its\nown look.\n\nDeselected on Linux only, in the manner this entry already prescribed:\nvisible in the workflow, not marked skip, so the cost stays countable. The\nplanned fix is unchanged and is still the right one.\n\n---'


def edits(tree) -> None:
    tree.sub(SENTINEL_FILE, OLD_COMMENT, NEW_COMMENT)
    tree.sub(SENTINEL_FILE, OLD_RUN, NEW_RUN)
    # The comment and the run line move together. A deselect with no note
    # beside it is the thing this pass is complaining about.
    tree.sub(KNOWN, KNOWN_ANCHOR, KNOWN_NEW)
    print("  deselected TestAsyncFileOpsFormatPaths on Linux, and said why")


def checks(tree) -> None:
    workflow = tree.read(SENTINEL_FILE)

    # The deselect must name a class that EXISTS. A --deselect matching
    # nothing is silently ignored, which is the whole reason the new guard
    # exists -- so this script does not get to assume it either.
    node = "tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths"
    path, cls = node.split("::")
    source = (Path.cwd() / path)
    if not source.exists():
        raise SystemExit(f"{path} does not exist")
    module = ast.parse(source.read_text(encoding="utf-8"))
    classes = {n.name for n in ast.walk(module) if isinstance(n, ast.ClassDef)}
    if cls not in classes:
        raise SystemExit(
            f"{path} defines no class {cls}. Deselecting it would be a "
            f"no-op that looks like a fix.")

    if node not in workflow:
        raise SystemExit("the deselect did not land in the workflow")
    # Count the USES, not the token. The comment block above the run lines
    # contains the words "and --deselect to skip CI-incompatible tests",
    # and counting the bare string reads that sentence as a fourth
    # exemption. Same use-versus-mention trap this programme keeps hitting;
    # the claim is `--deselect` followed by something with a `::` in it.
    uses = re.findall(r'--deselect\s+"?([^\s"]+::[^\s"]+)"?', workflow)
    if len(uses) != 3:
        raise SystemExit(
            f"expected 3 deselected node ids in this workflow, found "
            f"{len(uses)}: {uses}")

    # Windows must be left alone. The abort is offscreen-Linux only, and
    # Windows was green on the commit that produced it -- deselecting there
    # would drop coverage on the platform where the test works.
    win = tree.read(".github/workflows/tests-windows.yml")
    if "AsyncFileOps" in win:
        raise SystemExit(
            "tests-windows.yml now mentions AsyncFileOps. This abort is "
            "offscreen-Linux only and Windows is green; deselecting there "
            "would lose real coverage.")

    known = tree.read(KNOWN)
    if SENTINEL not in known:
        raise SystemExit(
            f"{KNOWN} does not mention {SENTINEL}. A deselect with no "
            f"written reason is an exemption nobody can review.")

    # Shape, on both edited files. These are anchored substitutions plus one
    # inserted block; the counts are derived from the text, not remembered.
    for rel, added in ((SENTINEL_FILE,
                        NEW_COMMENT.count("\n") - OLD_COMMENT.count("\n")
                        + NEW_RUN.count("\n") - OLD_RUN.count("\n")),
                       (KNOWN, KNOWN_NEW.count("\n") - KNOWN_ANCHOR.count("\n"))):
        before = (Path.cwd() / rel).read_text(encoding="utf-8-sig")
        after = tree.read(rel)
        delta = after.count("\n") - before.count("\n")
        if delta != added:
            raise SystemExit(
                f"{rel} changed shape by {delta} lines; this pass adds "
                f"exactly {added}.")


GUARD_SOURCE = '"""Every --deselect in CI names a test that exists.\n\nWHY THIS EXISTS. A `--deselect` whose path matches nothing is SILENTLY\nIGNORED by pytest. It does not warn and it does not fail; the run simply\ncollects everything and the exemption quietly stops applying. Two of these\nhave been added to this repository by hand, and a third would have been\njust as easy to mistype.\n\nThat makes a deselect an exemption with no reason attached, which is the\nfailure shape this repository keeps recording elsewhere: a licence that\noutlives its subject, or one that never had a subject at all. This test\nreads the workflow, extracts every deselect argument, and asserts that\npytest can still collect the node it names.\n\nWHAT IT DOES NOT DO. It does not judge whether the deselect is justified --\nthat is what KNOWN_ISSUES.md is for, and prose cannot be checked. It only\nproves the exemption still points at something real.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\nimport subprocess\nimport sys\n\nimport pytest\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / \'.github\' / \'workflows\'\n\n#: A deselect USE, not the word. The argument must contain `::`, because\n#: the comment block above the run lines says "and --deselect to skip\n#: CI-incompatible tests" -- and a pattern that matches the token alone\n#: reads that sentence as an exemption named `to`, then fails because no\n#: test called `to` exists. This test failed exactly that way when it was\n#: written, which is the eighth time use-versus-mention has caught a check\n#: in this programme. Match the claim, never the token.\nDESELECT = re.compile(r\'--deselect\\s+"?([^\\s"]+::[^\\s"]+)"?\')\n\n\ndef _deselects() -> list[tuple[str, str]]:\n    out = []\n    for workflow in sorted(WORKFLOWS.glob(\'*.yml\')):\n        text = workflow.read_text(encoding=\'utf-8\')\n        for match in DESELECT.finditer(text):\n            out.append((workflow.name, match.group(1)))\n    return out\n\n\ndef test_the_workflows_are_where_this_test_thinks_they_are():\n    """Guard the guard. If the directory moved, every assertion below would\n    iterate an empty list and pass."""\n    assert WORKFLOWS.is_dir(), f\'no workflow directory at {WORKFLOWS}\'\n    assert list(WORKFLOWS.glob(\'*.yml\')), \'no workflow files found\'\n\n\ndef test_at_least_one_deselect_is_still_declared():\n    """The sweep exists because deselects exist. If they are all gone, this\n    file should be deleted rather than left passing over nothing."""\n    found = _deselects()\n    assert found, (\n        \'no --deselect found in any workflow. If CI no longer needs any, \'\n        \'delete this test in the same commit that removed the last one.\')\n\n\n@pytest.mark.parametrize(\'workflow,node\', _deselects(),\n                         ids=lambda v: v.replace(\'/\', \'-\'))\ndef test_every_deselected_node_still_exists(workflow: str, node: str):\n    """pytest ignores a --deselect that matches nothing, so a typo or a\n    renamed class turns the exemption off without saying so."""\n    path = node.split(\'::\', 1)[0]\n    assert (ROOT / path).exists(), (\n        f\'{workflow} deselects {node}, but {path} does not exist\')\n    result = subprocess.run(\n        [sys.executable, \'-m\', \'pytest\', node, \'--collect-only\', \'-q\',\n         \'-p\', \'no:cacheprovider\'],\n        cwd=ROOT, capture_output=True, text=True)\n    assert result.returncode == 0 and \'no tests ran\' not in result.stdout, (\n        f\'{workflow} deselects {node}, which pytest cannot collect.\\n\'\n        f\'A --deselect that matches nothing is silently ignored, so this \'\n        f\'exemption is not doing anything.\\n\\n{result.stdout[-800:]}\')\n\n\ndef test_the_documented_family_is_the_one_that_is_deselected():\n    """KNOWN_ISSUES.md prescribes deselecting the AsyncFileOps family on\n    Linux when it becomes noisy. This is the link between the prose and the\n    workflow, asserted in the one direction that can be."""\n    nodes = {node for _w, node in _deselects()}\n    linux = [n for n in nodes if \'AsyncFileOps\' in n]\n    assert len(linux) >= 2, (\n        f\'expected both AsyncFileOps classes to be deselected on Linux, \'\n        f\'found {sorted(linux)}\')\n    known = (ROOT / \'KNOWN_ISSUES.md\').read_text(encoding=\'utf-8\')\n    for node in linux:\n        cls = node.rsplit(\'::\', 1)[-1]\n        assert cls in known, (\n            f\'{cls} is deselected in CI but not described in \'\n            f\'KNOWN_ISSUES.md. A deselect with no written reason is an \'\n            f\'exemption nobody can review.\')\n'


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
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
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
        raise SystemExit(f"run this from the root of a {REPO} checkout "
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
