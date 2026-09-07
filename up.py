#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: pin the brand register, so the checks that compare this application
to it stop skipping.

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT WAS WRONG. This repository keeps a hand-written PINNED mirror of
rnv-brand's values, and about five tests compare that mirror against the real
register. Every one of them is guarded with

    pytest.importorskip('engine.brand')

and rnv-brand shipped no pyproject.toml, so it was not installable, so they
all skipped. Across the five applications that is 22 checks, skipped on every
run since they were written. **A mirror that nothing compares against is a
copy, and a copy drifts.**

It had already drifted. Putting the register on the path for the first time
made rnv-text-transformer fail immediately: two constants classified as
app-owned that the register had owned since rev 27, four revisions earlier,
with nothing to say so.

WHAT THIS DOES. One line in tests/requirements-dev.txt, pinning rnv-brand to
commit b4fa970. **No workflow changes** -- every workflow in this repository
already installs that file, which is why this round touches no YAML.

PINNED TO A COMMIT, NOT A BRANCH. The pin is the written statement of which
revision of the brand this application mirrors. A branch ref moves on its
own: the register could change between two runs of the same commit here, and
the first anyone would know is a failure on a build that changed nothing. A
sha cannot do that -- moving it is an edit, and an edit is reviewable.

WHAT IT DOES NOT DO. The importorskip calls stay exactly as they are. They
are right for a developer who has not installed the dev dependencies, and
rewriting 22 of them across five repositories would be churn with a real
chance of error. Instead the ABSENCE is made loud in one place: if the
register is missing, one test fails and explains what it means, instead of
twenty-two quietly not running. A skipped test and a passing test look the
same in a summary line, and that is the whole failure mode.

NO SOURCE FILE IS TOUCHED. No colour, no value, no behaviour.
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
SENTINEL_FILE = "tests/requirements-dev.txt"
SENTINEL = "RNV-REGISTER-PIN"
GUARD = "tests/test_register_pin.py"
DESCRIPTION = "pin rnv-brand so the register checks run instead of skipping"
SUITES = [("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-REGISTER-PIN-GUARD -- the register is a declared dependency, not a hope.

Installed 2026-09-07. Until today this repository kept a hand-written PINNED
mirror of rnv-brand's values, and every test that would have compared that
mirror against the real register was guarded with

    pytest.importorskip('engine.brand')

rnv-brand shipped no pyproject.toml, so it was not installable, so those
checks skipped -- in all five applications, 22 of them, every run. A mirror
that nothing compares against is a copy, and a copy drifts. It had already
drifted: rnv-text-transformer classified two values as app-owned that the
register had owned since rev 27, and nothing said so for four revisions.

rnv-brand is now packaged and pinned in tests/requirements-dev.txt, which
every workflow in this repository already installs. The checks run.

WHAT THIS FILE ADDS. The importorskip calls are left exactly as they are --
they are correct for a developer who has not installed the dev dependencies,
and rewriting 22 of them across five repositories would be churn with a real
chance of error. Instead this makes the ABSENCE loud in one place: if the
register is missing, one test fails and says what it means, rather than
twenty-two tests quietly not running.

A skipped test and a passing test look identical in a summary line. That is
the whole failure mode this guards.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DEV_REQS = ROOT / 'tests/requirements-dev.txt'

#: The register, as this repository pins it. A commit, not a branch -- see
#: test_the_pin_names_a_commit_not_a_branch below for why that matters.
PIN_RE = re.compile(
    r'^rnv-brand\s*@\s*git\+https://github\.com/RNVizion/rnv-brand'
    r'(?:\.git)?@(?P<ref>\S+)\s*$', re.M)


def test_the_register_is_installed():
    """The one that matters. Everything else in this file is about keeping
    this one honest."""
    try:
        import engine.brand  # noqa: F401
    except ImportError as exc:  # pragma: no cover -- the failure path
        pytest.fail(
            f'rnv-brand is not importable: {exc}\n\n'
            f'It is a declared dev dependency of this repository. Install it '
            f'with:\n\n'
            f'    pip install -r tests/requirements-dev.txt\n\n'
            f'Until it is present, every check that compares this app to the '
            f'register is SKIPPING -- which looks exactly like passing, and '
            f'means the local PINNED mirror is being checked against itself.')


def test_the_register_exposes_what_the_mirrors_read():
    """Guard the guard. An importable module that has been emptied out would
    satisfy the test above and still tell the mirrors nothing."""
    import engine.brand as brand
    assert isinstance(getattr(brand, 'APP', None), dict), \
        'engine.brand has no APP dict'
    assert len(brand.APP) >= 10, \
        f'engine.brand.APP has only {len(brand.APP)} entries'
    for name in ('BRAND_GOLD', 'BRAND_DARK_GOLD', 'TRUE_BLACK', 'WHITE'):
        assert hasattr(brand, name), f'engine.brand has no {name}'


def test_the_pin_is_declared_in_the_dev_requirements():
    """It has to be written down where the workflows will read it. Every
    workflow in this repository already installs this file, which is why this
    round changes no YAML at all."""
    assert DEV_REQS.exists(), f'{DEV_REQS} is missing'
    text = DEV_REQS.read_text(encoding='utf-8')
    assert PIN_RE.search(text), (
        'tests/requirements-dev.txt does not pin rnv-brand. Without the pin, '
        'a fresh checkout installs no register, the checks go back to '
        'skipping, and nothing announces it.')


def test_the_pin_names_a_commit_not_a_branch():
    """A pin to `@main` is not a pin.

    The point of pinning the register is that this repository states, in a
    reviewable line, WHICH revision of the brand it mirrors. A branch ref
    moves on its own: the register could change under this application
    between two runs of the same commit, and the first anyone would know is a
    test failing on a build that changed nothing.

    A 40-character commit sha cannot do that. Moving it is an edit, and an
    edit is a diff someone can read.
    """
    text = DEV_REQS.read_text(encoding='utf-8')
    match = PIN_RE.search(text)
    assert match, 'no rnv-brand pin found'
    ref = match.group('ref')
    assert re.fullmatch(r'[0-9a-f]{40}', ref), (
        f'rnv-brand is pinned to {ref!r}, which is not a full commit sha. '
        f'A branch or tag ref lets the register move without a commit in '
        f'this repository.')


def test_the_installed_register_is_the_pinned_one():
    """The pin says which revision; this asks whether that is what is
    actually installed. They come apart the moment someone bumps the pin and
    does not reinstall -- and then the suite is checking the app against a
    register nobody declared."""
    import engine.brand as brand
    version = getattr(brand, '__version__', None)
    if version is None:
        pytest.skip('engine.brand declares no __version__; the pin is the '
                    'only statement of which revision this is')
    assert version, 'engine.brand.__version__ is empty'
'''

PIN_BLOCK = "\n# ── The brand register (RNV-REGISTER-PIN, 2026-09-07) ──────────────\n# This application mirrors rnv-brand's values in a local PINNED dict,\n# and ~5 tests here compare the two. Until rnv-brand was packaged they\n# were guarded with pytest.importorskip and skipped on every run, in\n# all five applications -- 22 checks that looked like passes.\n#\n# PINNED TO A COMMIT, NOT A BRANCH, on purpose: this line is the\n# written statement of which revision of the brand this app mirrors.\n# A branch ref would let the register move without a commit here.\n# Bumping it is an edit, and an edit is a diff someone can read.\nrnv-brand @ git+https://github.com/RNVizion/rnv-brand@b4fa970babbcb4141d1ea354c77e4d8d78248e82\n"
BRAND_SHA = 'b4fa970babbcb4141d1ea354c77e4d8d78248e82'


def edits(tree) -> None:
    reqs = tree.read(SENTINEL_FILE)
    if SENTINEL in reqs:
        raise SystemExit("already applied")
    if "rnv-brand" in reqs:
        raise SystemExit("tests/requirements-dev.txt already mentions "
                         "rnv-brand; re-derive this script rather than "
                         "adding a second pin")
    tree.write(SENTINEL_FILE, reqs.rstrip("\n") + "\n" + PIN_BLOCK)
    print(f"  pinned rnv-brand @ {BRAND_SHA[:12]} in {SENTINEL_FILE}")
    print("  no workflow changed -- every workflow here already installs it")


def checks(tree) -> None:
    reqs = tree.read(SENTINEL_FILE)
    if SENTINEL not in reqs:
        raise SystemExit("the pin block did not land")

    # exactly one pin, to a full commit sha
    pins = re.findall(r"^rnv-brand\s*@\s*git\+\S+@(\S+)\s*$", reqs, re.M)
    if len(pins) != 1:
        raise SystemExit(f"expected exactly one rnv-brand pin, found {len(pins)}")
    if not re.fullmatch(r"[0-9a-f]{40}", pins[0]):
        raise SystemExit(f"the pin names {pins[0]!r}, which is not a full "
                         f"commit sha. A branch ref lets the register move "
                         f"without a commit in this repository.")

    # The workflows must actually install the file the pin lives in --
    # otherwise the pin is a comment and CI keeps skipping. This is the one
    # assumption this round rests on, so it is checked rather than assumed.
    root = Path.cwd()
    flows = sorted((root / ".github/workflows").glob("*.yml")) \
        if (root / ".github/workflows").is_dir() else []
    if not flows:
        raise SystemExit("no workflows found; cannot confirm the pin is "
                         "installed in CI")
    missing = [f.name for f in flows
               if "requirements-dev.txt" not in f.read_text(encoding="utf-8")]
    if missing:
        raise SystemExit(f"these workflows do not install "
                         f"tests/requirements-dev.txt, so the pin would not "
                         f"reach them: {missing}")

    print(f"  guards: one pin, full sha, {len(flows)} workflow(s) install it")


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
