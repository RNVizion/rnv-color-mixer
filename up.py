#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Fix the docstring the ink script installed in tests/test_app_mirror.py.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT WENT WRONG

The ink pass installed tests/test_app_mirror.py with a docstring that had two
faults, and CI caught the first one:

1. IT QUOTED A RETIRED GOLD. tests/test_brand_mirror.py sweeps every tracked
   file for the retired values and exempts only files carrying a marker that
   says naming them IS that file's job. The docstring cited one in passing, to
   illustrate what happens when a value stops following its base. CI went red.

2. IT DESCRIBED THE WRONG APP. The docstring said this app "carried #e0e0e0,
   #1a1a1a, #2a2a2a and #333333 as bare hex literals with no constant and no
   provenance", and referred to an APP_CARD constant. None of that is true
   here -- that is rnv-icon-builder's situation, and the text arrived when
   this guard was derived from that app's. This app did its neutral rewire on
   2026-08-27; every rendered hex already had a constant. What was missing was
   a check that those constants still matched the register.

The second fault is the worse one. A wrong docstring in a guard file survives
every run, tells the next reader a false history of the code, and nothing ever
reports it.

WHY THE MARKER WOULD HAVE BEEN THE WRONG FIX

Adding RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN would have turned CI
green in one line. It would also have made this file permanently exempt from a
sweep it has no business being exempt from -- a dead exemption is a licence
waiting for a defect, which is the reasoning that put the marker mechanism
there in the first place. The value is simply removed from the prose instead.

WHY LOCAL VERIFICATION COULD NOT SEE THIS

tests/test_brand_mirror.py enumerates files with `git ls-files`. A file the
delivery script CREATES is untracked until it is committed, so the sweep never
looked at it in any pre-delivery run. The suite was green here and red in CI
for that reason alone, and no amount of re-running would have shown it.

Two things change because of that:

  - verification now stages the script's own output before running the suites,
    so created files are visible to any git-driven guard;
  - and checks() below reads the RETIRED table out of tests/test_brand_mirror.py
    and refuses to install a guard file containing any of those values. The
    repo's own list is the source of truth, so this cannot go stale against it.
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
DESCRIPTION = "correct the guard docstring installed by the ink pass"
SENTINEL_FILE = "tests/test_app_mirror.py"
SENTINEL = "NO RETIRED GOLD IS QUOTED IN THIS FILE"
GUARD = "tests/test_app_mirror.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

MIRROR_TEST = "tests/test_brand_mirror.py"

SUITES = [
    ("pytest tests/ (about 4 minutes)",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider",
      "--deselect",
      "tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths"]),
    ("pytest test_rnv_color_mixer.py",
     [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
      "-p", "no:cacheprovider", "--deselect",
      "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"]),
]

OLD_DOC = '"""\nThe APP register, mirrored -- and the ink move that made mirroring necessary.\n\nWHY THIS FILE EXISTS. Until 2026-08-28 this app carried #e0e0e0, #1a1a1a,\n#2a2a2a and #333333 as bare hex literals with no constant and no provenance.\nEvery one of them is a REGISTERED value in RNVizion/rnv-brand. A registered\nvalue could have moved upstream and this app would have kept the old one\nsilently -- the same failure #c4a458 had, one level down.\n\nIt nearly happened. `APP["text"]` moved from #e0e0e0 to #dddddd in\nrnv-brand@68d195e, and nothing here would have noticed.\n\nTHE INK GRID, published in the brand beside that move:\n\n    grey(n) = n * 0x11, n in 0..15.   TRUE_BLACK -> WHITE in fifteen steps.\n\nIt governs INKS AND EDGES and deliberately does not govern surfaces --\nBRAND_BLACK sits at n = 1.53 and APP_CARD at n = 2.47, and BRAND_BLACK is a\npermanent that will not move to fit a ladder.\n\nTWO GUARDS, NOT ONE. rnv-text-transformer\'s mirror test guards with\n`pytest.importorskip(\'engine.brand\')`, so where rnv-brand is not importable it\nreports clean and drift hides. Every register value here is therefore pinned\nLOCALLY as well as mirrored UPSTREAM: the pin catches drift when the brand is\nabsent, the mirror catches the brand moving. Neither alone is enough.\n"""\n'
NEW_DOC = '"""\nThe APP register mirrored, and the ink move onto the published grid.\n\nWHY THIS FILE EXISTS. This app did its neutral rewire on 2026-08-27, so every\nrendered hex already carried a constant -- but nothing checked those constants\nagainst RNVizion/rnv-brand. APP_TEXT_DARK, APP_SURFACE_DARK and APP_BORDER_DARK\nare all REGISTERED values, and the register could move upstream while this app\nkept the old ones, silently and with a clean test run.\n\nIt nearly happened: APP["text"] moved to #dddddd in rnv-brand@68d195e, and\nnothing here would have noticed.\n\nTHE INK GRID, published in the brand beside that move:\n\n    grey(n) = n * 0x11, n in 0..15.   TRUE_BLACK -> WHITE in fifteen steps.\n\nIt governs INKS AND EDGES and deliberately does not govern surfaces:\nAPP_SURFACE_DARK is BRAND_BLACK #1a1a1a at n = 1.53, a permanent that will not\nmove to fit a ladder.\n\nTWO GUARDS, NOT ONE. rnv-text-transformer\'s mirror test guards with\n`pytest.importorskip(\'engine.brand\')`, so where rnv-brand is not importable it\nreports clean and drift hides. Every register value here is therefore pinned\nLOCALLY as well as mirrored UPSTREAM: the pin catches drift when the brand is\nabsent, the mirror catches the brand moving. Neither alone is enough.\n\nNO RETIRED GOLD IS QUOTED IN THIS FILE, AND THAT IS DELIBERATE.\ntests/test_brand_mirror.py sweeps every tracked file for the retired values and\nexempts only files that declare, by marker, that naming them IS their job. The\nfirst draft of this docstring cited one in passing to illustrate a point and\nturned CI red. Taking the marker would have been the wrong repair -- it would\nhave made this file permanently exempt from a sweep it has no business being\nexempt from. So the prose describes the failure without quoting the value, and\nthe delivery script now refuses to install a guard that would trip the sweep.\n"""\n'


def _retired_values(tree_text: str) -> list[str]:
    """The repo's own RETIRED table, read rather than restated."""
    tree = ast.parse(tree_text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(target, "id", None) == "RETIRED" and isinstance(node.value, ast.Dict):
                return [k.value for k in node.value.keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, str)]
    raise SystemExit("could not find RETIRED in tests/test_brand_mirror.py")


def edits(tree) -> None:
    tree.sub(SENTINEL_FILE, OLD_DOC, NEW_DOC)


def checks(tree) -> None:
    guard = tree.read(SENTINEL_FILE)
    if SENTINEL not in guard:
        raise SystemExit("the corrected docstring did not land")

    # Guard the guard, using the repo's own table. A hand-copied list here
    # would go stale behind the real one, in the direction that reports clean.
    retired = _retired_values(tree.read(MIRROR_TEST))
    if not retired:
        raise SystemExit("the RETIRED table is empty -- this check is not "
                         "checking anything")
    hits = [value for value in retired if value in guard]
    if hits:
        raise SystemExit(
            "the guard file still names retired value(s) " + ", ".join(hits)
            + ". Taking the by-design marker would silence this and is the "
              "wrong repair -- remove the value from the prose instead.")

    # And the second fault: the text that described a different app.
    #
    # Anchored on the wrong SENTENCE, not the bare name. `APP_CARD` also
    # appears further down, in a comment explaining that this app deliberately
    # does NOT use that spelling -- a correct mention, and sweeping for the
    # token alone fails on it. That is the fourth time this pass has tripped
    # over use-versus-mention; every one of them was a check reading a word
    # instead of a claim.
    for wrong in ("bare hex literals with no constant and no provenance",
                  "APP_CARD at n = 2.47"):
        if wrong in guard:
            raise SystemExit(f"the guard still says {wrong!r}, which is not "
                             f"true of this app")


GUARD_SOURCE = None   # this pass edits the guard rather than installing one


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
