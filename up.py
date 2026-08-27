#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Fix rnv-color-mixer's light-mode hint text, which reads below AA.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THE DEFECT

`text_hint` has exactly one consumer: the 10px QLabel under each slider in
core/color_fine_tune.py. That label is added into the QFrame built by
`_create_sliders_section`, so the ground it renders on is `panel_secondary`,
NOT `panel_bg` -- panel_bg paints the QDialog *behind* that frame. Measuring
against the dialog says light is fine. Measuring against the frame says:

    LIGHT   #888888 on #ffffff = 3.5407:1     10px text, AA floor is 4.5

#666666 reads 5.7418 on that frame and clears 4.5 on every other light ground
in this app.

WHY THE APP'S OWN CONTRAST GUARD DID NOT CATCH IT

tests/test_contrast_pairs.py walks the three global stylesheet templates. This
label is styled inline in Python, on a widget, so it is outside that sweep
entirely. The new file measures the palette directly instead.

WHAT LANDS

  utils/config.py            LIGHT_THEME text_hint #888888 -> #666666, with the
                             measurement in a comment beside it
  tests/test_hint_text.py    new

WHAT IS RECORDED AND NOT CHANGED

Dark and image read #888888 on #2a2a2a = 4.0490, also short of 4.5. They are
carried as ACCEPTED entries with the figure and the reason rather than quietly
lifted: #888888 is the value the muted text uses in three other apps, and
moving it in one of them is a ruling rather than a repair. A companion test
fails if either entry stops being true, so the exemption cannot outlive its
reason.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
DESCRIPTION = "fix the light-mode hint text"
SENTINEL_FILE = "utils/config.py"
SENTINEL = "'text_hint': '#666666'"
GUARD = "tests/test_hint_text.py"
SHADOWS = {"config.py", "colors.py", "conftest.py", "mcp.py"}

# Exactly what .github/workflows/tests-linux.yml deselects: that class aborts
# Python natively on offscreen Linux. Running it here produces a crash that
# reads like a regression in whatever change is in flight. It is not one.
DESELECT = ["--deselect",
            "tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths"]
SUITES = [
    ("pytest tests/ (about 4 minutes)",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider",
      *DESELECT]),
]

NOTE = (
    "        # The 10px hint under each fine-tune slider is the only consumer, and\n"
    "        # it sits on the QFrame that section builds -- panel_secondary, not\n"
    "        # panel_bg. #888888 read 3.5407:1 there, below AA for text this\n"
    "        # size. #666666 clears 4.5 on every light ground in this app.\n")


def _light_bounds(lines):
    """The three theme dicts carry an identical text_hint line, so the edit has
    to be scoped to LIGHT_THEME rather than matched by string."""
    starts = {}
    for i, line in enumerate(lines):
        m = re.match(r"^\s{4}(DARK_THEME|LIGHT_THEME|IMAGE_THEME)\s*=\s*\{", line)
        if m:
            starts[m.group(1)] = i
    if set(starts) != {"DARK_THEME", "LIGHT_THEME", "IMAGE_THEME"}:
        raise SystemExit(f"expected three theme dicts, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    for i, (name, st) in enumerate(order):
        if name == "LIGHT_THEME":
            return st, (order[i + 1][1] if i + 1 < len(order) else len(lines))
    raise SystemExit("LIGHT_THEME not found")


def edits(tree) -> None:
    lines = tree.read(SENTINEL_FILE).splitlines(keepends=True)
    st, en = _light_bounds(lines)
    hits = [i for i in range(st, en) if lines[i].strip().startswith("'text_hint':")]
    if len(hits) != 1:
        raise SystemExit(f"expected one text_hint in LIGHT_THEME, found {len(hits)}")
    if "'#888888'" not in lines[hits[0]]:
        raise SystemExit(f"LIGHT_THEME text_hint is not #888888: "
                         f"{lines[hits[0]].strip()!r}")
    lines[hits[0]] = NOTE + "        'text_hint': '#666666',\n"
    tree.write(SENTINEL_FILE, "".join(lines))


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count("'text_hint': '#666666',") != 1:
        raise SystemExit("expected exactly one hint at #666666 -- only light "
                         "moves in this pass")
    if src.count("'text_hint': '#888888',") != 2:
        raise SystemExit("dark and image must keep #888888; they are carried "
                         "as ACCEPTED entries in the guard, not changed here")


GUARD_SOURCE = '"""\nThe fine-tune hint label, measured against the ground it actually sits on.\n\n`text_hint` has exactly one consumer: core/color_fine_tune.py, a 10px QLabel\nunder each slider. It is added into the QFrame built by\n`_create_sliders_section`, so its ground is `panel_secondary` -- NOT\n`panel_bg`, which paints the QDialog behind that frame. Measuring against the\ndialog would have said light was fine when it was not.\n\nLight was #888888 on #ffffff = 3.5407:1 for 10px text. It is now #666666,\nwhich clears 4.5 on every light ground in this app.\n\nDark and image are a smaller miss and are carried below rather than quietly\nfixed: moving them would break the value they share with the muted text in\nthree other apps, and that is a ruling rather than a repair.\n"""\nfrom __future__ import annotations\n\nimport pathlib\n\nimport pytest\n\nfrom utils.config import ThemeManager\n\nTEXT_FLOOR = 4.5\n\nTHEMES = {\n    "DARK": ThemeManager.DARK_THEME,\n    "LIGHT": ThemeManager.LIGHT_THEME,\n    "IMAGE": ThemeManager.IMAGE_THEME,\n}\n\n# The ground the label really renders on, and the ground behind it. Both are\n# checked, because a frame that stopped being painted would drop the label onto\n# the dialog and the figures would change without any colour moving.\nGROUNDS = ("panel_secondary", "panel_bg")\n\n# (theme, ground key) -> why it may sit below the floor.\nACCEPTED = {\n    ("DARK", "panel_secondary"):\n        "#888888 on #2a2a2a = 4.0490 -- the same value the muted text uses in "\n        "three other apps; lifting it here alone is a ruling, not a repair",\n    ("IMAGE", "panel_secondary"):\n        "same pair as DARK -- image mode reuses the dark surfaces",\n}\n\n\ndef _luminance(value: str) -> float:\n    h = value.lstrip("#")\n    if len(h) == 8:                      # Qt #AARRGGBB\n        h = h[2:]\n    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]\n    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]\n\n\ndef contrast(a: str, b: str) -> float:\n    la, lb = _luminance(a), _luminance(b)\n    hi, lo = max(la, lb), min(la, lb)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef test_the_hint_key_still_has_exactly_one_consumer():\n    """Guard the guard, and guard the docstring with it.\n\n    Every figure here assumes the label is the one in color_fine_tune. A second\n    consumer on a different ground would make this file measure the wrong pair\n    while still passing.\n    """\n    root = pathlib.Path(__file__).resolve().parent.parent\n    sites = []\n    for path in root.rglob("*.py"):\n        if any(p in path.parts for p in ("tests", ".git", "__pycache__")):\n            continue\n        if path.name.startswith("test_") or path.name == "config.py":\n            continue\n        # A delivery script sitting at the root mentions the key it moves.\n        # Sweeping it makes the guard fail on the very run that installs it --\n        # the same trap the repos\' placement guards already exempt `up*.py` for.\n        if path.parent == root and path.name.startswith("up"):\n            continue\n        if "text_hint" in path.read_text(encoding="utf-8", errors="replace"):\n            sites.append(path.relative_to(root).as_posix())\n    assert sites == ["core/color_fine_tune.py"], (\n        f"text_hint is read in {sites}. The grounds in this file were derived "\n        f"from color_fine_tune alone; re-derive them before trusting these "\n        f"figures.")\n\n\n@pytest.mark.parametrize("theme", sorted(THEMES))\n@pytest.mark.parametrize("ground", GROUNDS)\ndef test_the_hint_clears_aa_on_the_ground_it_sits_on(theme, ground):\n    palette = THEMES[theme]\n    if (theme, ground) in ACCEPTED:\n        pytest.skip(ACCEPTED[(theme, ground)])\n    ink, bg = palette["text_hint"], palette[ground]\n    if not bg.startswith("#"):\n        pytest.skip(f"{theme} {ground} is {bg}, not a flat colour")\n    ratio = contrast(ink, bg)\n    assert ratio >= TEXT_FLOOR, (\n        f"{theme}: hint {ink} on {ground} {bg} = {ratio:.4f}:1, below "\n        f"{TEXT_FLOOR} for 10px text")\n\n\ndef test_the_accepted_entries_are_still_real():\n    """An exemption that no longer describes anything is a licence waiting for\n    a future defect. Each one must still be below the floor."""\n    stale = []\n    for (theme, ground), _why in ACCEPTED.items():\n        palette = THEMES[theme]\n        ratio = contrast(palette["text_hint"], palette[ground])\n        if ratio >= TEXT_FLOOR:\n            stale.append(f"{theme}/{ground} now reads {ratio:.4f} -- delete it")\n    assert not stale, "; ".join(stale)\n\n\ndef test_light_is_the_one_that_was_fixed():\n    """The specific regression: 10px #888888 on white."""\n    light = THEMES["LIGHT"]\n    assert light["text_hint"] != "#888888", (\n        "the light hint is back to #888888, which reads 3.5407:1 on this "\n        "app\'s white frame")\n    assert contrast(light["text_hint"], light["panel_secondary"]) >= TEXT_FLOOR\n'


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
