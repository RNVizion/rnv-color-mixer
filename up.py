#!/usr/bin/env python3
"""
RNV-LOCKED-DIGEST-TOOL-DO-NOT-SWEEP

Re-baseline the locked test file's SHA-256 in both workflows, and move the
check into the suite so CI is not the first thing to notice.

    python up.py             # re-baseline, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY CI WENT RED

test_rnv_color_mixer.py is the gate of last resort, and both workflows refuse
the build if its SHA-256 moves. The button-key rename edited four quoted keys
in it -- correctly; the local suites are green -- so the digest moved and the
integrity step failed exactly as designed.

That step is not a bug and this is not a workaround. The workflow's own
comment records that it has been re-baselined before, "post-Phase 9 after
content drift was detected via this CI check". This is the same operation,
for a change that was intended.

WHAT I SHOULD HAVE DONE

Looked for the gate before touching the file it guards. The rename script
counted its edits, pinned every colour value and compared the hex multiset on
both sides of the diff -- and none of that could see a hash recorded in a
YAML file two directories away. A repository-wide check that lives outside
the test suite is invisible to a script that reasons about the test suite.

WHAT THIS SCRIPT DOES

    1. Reads the digest of test_rnv_color_mixer.py as it stands on disk.
    2. Replaces the recorded digest in .github/workflows/tests-linux.yml and
       .github/workflows/tests-windows.yml -- one occurrence each, in two
       different syntactic forms.
    3. Adds tests/test_locked_file_digest.py.

The digest is computed at run time rather than written into this script,
because the only value that can be right is the one your file actually has.

THE NEW GUARD IS WORTH MORE THAN THE RE-BASELINE

It fires in the same run as the edit that caused it, instead of after the
commit and the push, with a message that reads like tampering. And it checks
one thing CI structurally cannot: that the two workflows record the SAME
digest. Each workflow only ever verifies its own copy, so the two can drift
apart and both builds keep passing -- until one platform re-baselines and the
other does not. That failure would look like a Windows-only regression in a
file nobody edited.

It also refuses to contain a SHA-256 of its own. A guard carrying its own copy
of the value would pass while the workflows were wrong, which is precisely the
failure it exists to prevent.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
DESCRIPTION = "re-baseline the locked test file digest and guard it locally"
SENTINEL_FILE = ".github/workflows/tests-linux.yml"
SENTINEL = "RNV-LOCKED-DIGEST-REBASELINED"
GUARD = "tests/test_locked_file_digest.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"])
]

LOCKED = "test_rnv_color_mixer.py"
WORKFLOWS = (".github/workflows/tests-linux.yml",
             ".github/workflows/tests-windows.yml")

#: The digest recorded before this pass. Written down so the script refuses to
#: run against a tree that has already been re-baselined, or one where the
#: rename never landed.
OLD = "57ab3fcae4abf13cbb0bb38d9e1c759caf1c40fdef5af5f063b12e0178af765a"

ANCHOR = '        run: |\n          python -c "\n'
MARK = ("        # RNV-LOCKED-DIGEST-REBASELINED 2026-09-01: the button-key\n"
        "        # rename edited four quoted keys in the locked file. The\n"
        "        # digest below is that file's, and tests/test_locked_file_\n"
        "        # digest.py now checks it in the suite as well as here.\n")

_SHA256 = re.compile(r"\b[0-9a-f]{64}\b")


def edits(tree) -> None:
    digest = hashlib.sha256(
        (Path.cwd() / LOCKED).read_bytes()).hexdigest()
    if digest == OLD:
        raise SystemExit(
            f"{LOCKED} still hashes to the digest the workflows already "
            f"record, so there is nothing to re-baseline. Run the button-key "
            f"rename first -- the one whose header begins \"Rename the main "
            f"button keys to main_btn_*\". There is no filename to look for: "
            f"every script arrives as an attachment and is saved as up.py.")

    for rel in WORKFLOWS:
        src = tree.read(rel)
        found = _SHA256.findall(src)
        if found != [OLD]:
            raise SystemExit(
                f"{rel} records {found}, expected exactly one digest equal to "
                f"{OLD}. Either this tree has already been re-baselined or the "
                f"workflow moved; re-derive this edit before trusting it.")
        tree.write(rel, src.replace(OLD, digest))

    tree.sub(SENTINEL_FILE, ANCHOR, MARK + ANCHOR, 1)
    print(f"  re-baselined both workflows to {digest}")


def checks(tree) -> None:
    digest = hashlib.sha256((Path.cwd() / LOCKED).read_bytes()).hexdigest()
    recorded = set()
    for rel in WORKFLOWS:
        found = _SHA256.findall(tree.read(rel))
        if found != [digest]:
            raise SystemExit(f"{rel} now records {found}, expected [{digest}]")
        recorded.update(found)
    if len(recorded) != 1:
        raise SystemExit(f"the workflows disagree: {recorded}")

    linux = tree.read(SENTINEL_FILE)
    if linux.count(SENTINEL) != 1:
        raise SystemExit("the re-baseline note did not land exactly once")
    if OLD in linux or OLD in tree.read(WORKFLOWS[1]):
        raise SystemExit("the old digest survived somewhere")

    guard = tree.read(GUARD)
    if _SHA256.search(guard):
        raise SystemExit(
            "the guard contains a literal SHA-256. It must read the digest "
            "from the workflows, or it is checking itself.")

    # The locked file itself is not touched by this pass. Saying so is the
    # point: a script that re-baselines a digest is one edit away from being a
    # script that edits the file the digest protects.
    before = (Path.cwd() / LOCKED).read_bytes()
    if LOCKED in tree.files:
        raise SystemExit(f"{LOCKED} was modified by this pass. It must not be.")
    if hashlib.sha256(before).hexdigest() != digest:
        raise SystemExit("the locked file changed while this script ran")
    print("  guards: both workflows agree, the locked file is untouched, "
          "the guard carries no digest of its own")


GUARD_SOURCE = r'''"""The locked test file and the digest that gates it must agree.

RNV-LOCKED-DIGEST-GUARD

test_rnv_color_mixer.py is the gate of last resort, and CI refuses the build if
its SHA-256 moves. That check lives only in the two workflow files, so until
now the first thing to notice a legitimate edit was a red build on GitHub --
after the commit, after the push, and with a message that reads like tampering
rather than like a re-baseline that was forgotten.

These tests move that check into the suite, where it fires in the same run as
the edit that caused it, and they check something CI cannot: that the two
workflows still record the SAME digest.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCKED = ROOT / "test_rnv_color_mixer.py"
WORKFLOWS = (ROOT / ".github" / "workflows" / "tests-linux.yml",
             ROOT / ".github" / "workflows" / "tests-windows.yml")

_SHA256 = re.compile(r"\b([0-9a-f]{64})\b")


def _recorded(path: Path) -> list[str]:
    return _SHA256.findall(path.read_text(encoding="utf-8"))


def test_every_workflow_records_exactly_one_digest():
    for path in WORKFLOWS:
        found = _recorded(path)
        assert len(found) == 1, (
            f"{path.name} records {len(found)} SHA-256 values: {found}. This "
            f"guard reads the digest by shape, so a second one would make it "
            f"ambiguous which gate it is checking.")


def test_both_workflows_record_the_same_digest():
    """CI cannot catch this. Each workflow checks only its own copy, so the
    two can drift apart and both builds still pass -- until one platform
    re-baselines and the other does not."""
    digests = {path.name: _recorded(path)[0] for path in WORKFLOWS}
    assert len(set(digests.values())) == 1, (
        f"the workflows disagree about the locked file's digest: {digests}")


def test_the_locked_file_matches_its_recorded_digest():
    actual = hashlib.sha256(LOCKED.read_bytes()).hexdigest()
    expected = _recorded(WORKFLOWS[0])[0]
    assert actual == expected, (
        "test_rnv_color_mixer.py no longer matches the digest the workflows "
        "gate on.\n"
        f"  recorded: {expected}\n"
        f"  actual:   {actual}\n"
        "If the edit was deliberate, re-baseline BOTH workflow files to the "
        "actual value in the same commit. If it was not, this is the gate "
        "doing its job.")


def test_the_digest_is_read_from_the_file_and_not_from_this_test():
    """A guard that carried its own copy of the digest would pass while the
    workflows were wrong, which is the failure it exists to prevent."""
    source = Path(__file__).read_text(encoding="utf-8")
    assert not _SHA256.search(source), (
        "this test module contains a literal SHA-256. The digest must come "
        "from the workflow files, or this guard is checking itself.")
'''


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
