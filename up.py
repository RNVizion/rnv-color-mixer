#!/usr/bin/env python3
"""
RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP

Rename the main button keys to main_btn_*, and give the three dialogs the
family they were borrowing from.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

NOT ONE PIXEL MOVES. Every value the dialogs gain is the value they already
painted.

`button_*` holds the black-and-white MAIN scheme here, and the gold DIALOG
scheme in rnv-color-picker and rnv-icon-builder. One name, two schemes,
decided by which repository you have open -- and a name that cannot be carried
into a new project is not a standard. After this pass the name says where the
button lives:

    main_btn_*     the main window at launch
    dialog_btn_*   anything that opens later

THE FINDING THAT MADE THIS WORTH DOING HERE

Reading button_pressed_bg out of these palettes says the main button presses
to GOLD. It does not. The main window's buttons are painted by the QSS blocks
in utils/config.py, which press to APP_BTN_PRESSED #444444 with the label
inverting -- the same black-and-white scheme as the other four applications.
The gold pressed plate is read in exactly one place, core/package_d_panel.py,
and PackageDPanel is a QDialog.

So the gold was always the dialog's. The palette key just did not say so, and
an audit that read the key instead of the paint reported the mixer as the one
application disagreeing with the pressed-plate ruling of 26 August. It never
disagreed. That report was withdrawn, and this rename is what stops the same
misreading happening again.

WHAT MOVES

Forty-five quoted occurrences in eleven files, nine new palette entries (three
keys across three palettes), and four repointed dialog reads:

    ui/about_dialog.py         the rest plate, and the hover plate
    core/color_fine_tune.py    the rest plate
    core/package_d_panel.py    the gold pressed plate

core/color_slot.py and ui/ui_handler.py keep the main family. ColorSlot is a
QWidget in the main window, not a dialog.

DOCUMENTATION IS NOT TOUCHED, ON PURPOSE

The docs pass runs once, after alignment settles, so it is written against the
finished state rather than chased through it. The guard sweeps code, not prose.

WHAT THE GUARD ASSERTS

tests/test_button_key_names.py fails if an old name comes back, if a palette
loses a key, if any of the eighteen main values or nine dialog values moved,
if a dialog starts reading the main family, or if main-window code starts
reading the dialog one. It also records the finding above as an assertion, so
the next reader of button_pressed_bg is not left to rediscover it.

It reads the palettes by importing ThemeManager rather than by parsing it: two
of these values are derived aliases, and a static resolver returns None for
them, then compares None with None and passes.
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
DESCRIPTION = "rename the main button keys and give the dialogs their own"
SENTINEL_FILE = "utils/config.py"
SENTINEL = "'dialog_btn_bg'"
GUARD = "tests/test_button_key_names.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"])
]

OLD_KEYS = ("button_bg", "button_text", "button_hover_bg", "button_pressed_bg",
            "button_pressed_text", "button_pressed_border")
RENAME = {k: "main_" + k.replace("button_", "btn_") for k in OLD_KEYS}

#: path -> how many QUOTED occurrences that file holds. Written down so the
#: script refuses to run against a tree that has moved under it.
QUOTED = {
    "utils/config.py": 18,
    "core/color_slot.py": 7,
    "ui/ui_handler.py": 5,
    "test_rnv_color_mixer.py": 4,
    "tests/test_brand_mirror.py": 3,
    "tests/test_contrast_pairs.py": 2,
    "ui/about_dialog.py": 2,
    "core/color_fine_tune.py": 1,
    "core/package_d_panel.py": 1,
    "tests/test_app_mirror.py": 1,
    "tests/test_utility_modules.py": 1,
}

#: The dialog family, inserted beside the main family it was borrowing from.
#: Anchored on the renamed pressed-border line rather than on a line number.
#: Dark and image share an anchor because they share every value.
_NOTE = ("        # The plate, hover and pressed a DIALOG button takes. Added\n"
         "        # 2026-09-01, holding what the three dialogs already painted.\n"
         "        # Before this they read the main family, which is how a gold\n"
         "        # pressed plate that only a QDialog ever used came to look\n"
         "        # like the main window's.\n")
INSERT = [
    ("        'main_btn_pressed_border': BRAND_GOLD,\n",
     "        'main_btn_pressed_border': BRAND_GOLD,\n" + _NOTE +
     "        'dialog_btn_bg': APP_SURFACE_DARK,\n"
     "        'dialog_btn_hover_bg': APP_BORDER_DARK,\n"
     "        'dialog_btn_pressed_bg': BRAND_GOLD_PRESSED,\n",
     2),
    ("        'main_btn_pressed_border': BRAND_DARK_GOLD,\n",
     "        'main_btn_pressed_border': BRAND_DARK_GOLD,\n" + _NOTE +
     "        'dialog_btn_bg': '#ffffff',\n"
     "        'dialog_btn_hover_bg': '#333333',\n"
     "        'dialog_btn_pressed_bg': BRAND_DARK_GOLD_PRESSED,\n",
     1),
]

#: The four dialog reads, repointed after the rename has run.
REPOINT = [
    ("ui/about_dialog.py", "_d['main_btn_hover_bg']", "_d['dialog_btn_hover_bg']", 1),
    ("ui/about_dialog.py", "_l['main_btn_bg']", "_l['dialog_btn_bg']", 1),
    ("core/color_fine_tune.py", "_l['main_btn_bg']", "_l['dialog_btn_bg']", 1),
    ("core/package_d_panel.py", "t['main_btn_pressed_bg']",
     "t['dialog_btn_pressed_bg']", 1),
]

_QUOTED_RE = re.compile(r"(['\"])(" + "|".join(sorted(RENAME, key=len, reverse=True))
                        + r")\1")


def _rename_quoted(text: str) -> tuple[str, int]:
    hits = 0

    def swap(m: re.Match) -> str:
        nonlocal hits
        hits += 1
        return f"{m.group(1)}{RENAME[m.group(2)]}{m.group(1)}"

    return _QUOTED_RE.sub(swap, text), hits


def edits(tree) -> None:
    total = 0
    for rel, expected in QUOTED.items():
        new, hits = _rename_quoted(tree.read(rel))
        if hits != expected:
            raise SystemExit(f"{rel}: expected {expected} quoted key(s), found "
                             f"{hits}. The file moved; re-derive this edit "
                             f"before trusting the script.")
        tree.write(rel, new)
        total += hits
    for old, new, times in INSERT:
        tree.sub(SENTINEL_FILE, old, new, times)
    for rel, old, new, times in REPOINT:
        tree.sub(rel, old, new, times)
    print(f"  renamed {total} quoted keys in {len(QUOTED)} files, "
          f"added 9 dialog entries, repointed {len(REPOINT)} dialog reads")


def checks(tree) -> None:
    for rel in QUOTED:
        text = tree.read(rel)
        for old in RENAME:
            if re.search(r"(['\"])" + old + r"\1", text):
                raise SystemExit(f"{rel}: {old!r} survived the rename")

    config = tree.read(SENTINEL_FILE)
    for key in ("'dialog_btn_bg'", "'dialog_btn_hover_bg'",
                "'dialog_btn_pressed_bg'"):
        if config.count(key) != 3:
            raise SystemExit(f"expected 3 {key} entries, found "
                             f"{config.count(key)}")

    import ast
    palettes = []
    for node in ast.walk(ast.parse(config)):
        if not isinstance(node, ast.Dict):
            continue
        pairs = {k.value: ast.unparse(v) for k, v in zip(node.keys, node.values)
                 if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if "dialog_btn_bg" in pairs:
            palettes.append(pairs)
    if len(palettes) != 3:
        raise SystemExit(f"expected 3 palettes, found {len(palettes)}")
    for pairs in palettes:
        for dialog_key, main_key in (("dialog_btn_bg", "main_btn_bg"),
                                     ("dialog_btn_hover_bg", "main_btn_hover_bg"),
                                     ("dialog_btn_pressed_bg", "main_btn_pressed_bg")):
            if pairs[dialog_key] != pairs[main_key]:
                raise SystemExit(
                    f"{dialog_key} is {pairs[dialog_key]} where {main_key} is "
                    f"{pairs[main_key]}. The dialog family is supposed to hold "
                    f"what those dialogs already painted; a difference here is "
                    f"a colour decision hiding inside a rename.")

    for rel in ("ui/about_dialog.py", "core/color_fine_tune.py",
                "core/package_d_panel.py"):
        if re.search(r"(['\"])main_btn_", tree.read(rel)):
            raise SystemExit(f"{rel} still reads the main family")
    for rel in ("ui/ui_handler.py", "core/color_slot.py"):
        if "dialog_btn_" in tree.read(rel):
            raise SystemExit(f"{rel} is main-window code and must not read the "
                             f"dialog family")
    print("  guards: no old name survives, three palettes carry both families, "
          "dialog values equal what those dialogs painted")


GUARD_SOURCE = r'''"""The button keys say where the button lives.

RNV-BUTTON-NAMING-GUARD

main_btn_* is the main window at launch. dialog_btn_* is anything that opens
later. Before this pass the main family here was called button_* -- the same
name that holds the GOLD DIALOG scheme in rnv-color-picker and
rnv-icon-builder. One name, two schemes, decided by which repository you had
open. These tests are what stop it drifting back.

Worth knowing about this application specifically: the main window's buttons
are painted by the QSS blocks in utils/config.py from module constants, not
from these palette keys at all. The keys are read by ColorSlot and by the UI
handler in the main window, and by three dialogs. The dialogs now read a
family of their own.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD = ("button_bg", "button_text", "button_hover_bg", "button_pressed_bg",
       "button_pressed_text", "button_pressed_border")
NEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD)
DIALOG = ("dialog_btn_bg", "dialog_btn_hover_bg", "dialog_btn_pressed_bg")

PINNED_MAIN = {
    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
             "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#d2bc93",
             "main_btn_pressed_text": "#000000",
             "main_btn_pressed_border": "#d2bc93"},
    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",
              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#8c7337",
              "main_btn_pressed_text": "#ffffff",
              "main_btn_pressed_border": "#8c7337"},
    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#d2bc93",
              "main_btn_pressed_text": "#000000",
              "main_btn_pressed_border": "#d2bc93"},
}

#: What the three dialogs painted before the rename, key for key.
PINNED_DIALOG = {
    "dark": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_hover_bg": "#333333",
             "dialog_btn_pressed_bg": "#d2bc93"},
    "light": {"dialog_btn_bg": "#ffffff", "dialog_btn_hover_bg": "#333333",
              "dialog_btn_pressed_bg": "#8c7337"},
    "image": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_hover_bg": "#333333",
              "dialog_btn_pressed_bg": "#d2bc93"},
}

SKIP = {".git", "build", "dist", ".venv", "__pycache__"}

#: A sweep for a name cannot tell a USE from a MENTION. The two files certain
#: to mention the old names are this guard -- which lists them in order to
#: forbid them -- and the delivery script that performs the rename. Skipped by
#: marker rather than by filename: the script arrives under whatever name it
#: is saved as.
MARKERS = ("RNV-BUTTON-NAMING-GUARD", "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP")

DIALOG_FILES = ("ui/about_dialog.py", "core/color_fine_tune.py",
                "core/package_d_panel.py")
MAIN_FILES = ("ui/ui_handler.py", "core/color_slot.py")


def _palettes():
    from utils.config import ThemeManager
    return {"dark": ThemeManager.DARK_THEME, "light": ThemeManager.LIGHT_THEME,
            "image": ThemeManager.IMAGE_THEME}


def _sources():
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            continue
        yield path, text


def test_no_old_button_key_name_survives():
    offenders = []
    for path, text in _sources():
        for old in OLD:
            if re.search(r"(['\"])" + old + r"\1", text):
                offenders.append(f"{path.relative_to(ROOT)}: {old}")
    assert not offenders, (
        "these keys must say where the button lives:\n  " + "\n  ".join(offenders))


def test_the_marker_exemption_covers_only_the_two_tools():
    marked = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            marked.append(path.relative_to(ROOT))
    assert len(marked) <= 2, f"unexpected marked file(s): {marked}"
    assert Path(__file__).relative_to(ROOT) in marked


def test_all_three_palettes_carry_both_families():
    for mode, palette in _palettes().items():
        missing = [n for n in NEW + DIALOG if n not in palette]
        assert not missing, f"{mode} palette missing {missing}"


def test_the_rename_moved_no_value():
    for mode, pins in PINNED_MAIN.items():
        actual = {k: _palettes()[mode].get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} main button values changed.\n"
            f"  wanted {pins}\n  found  {actual}\n"
            "A rename that changes a value is not a rename.")


def test_the_dialog_family_holds_what_the_dialogs_already_painted():
    for mode, pins in PINNED_DIALOG.items():
        actual = {k: _palettes()[mode].get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} dialog button values are not what those dialogs "
            f"painted before the rename.\n  wanted {pins}\n  found  {actual}")


def test_dialogs_read_the_dialog_family_and_not_the_main_one():
    for rel in DIALOG_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert "dialog_btn_" in src, f"{rel} no longer reads the dialog family"
        assert not re.search(r"(['\"])main_btn_", src), (
            f"{rel} reads the main family. Dialogs open later and take the "
            f"dialog scheme; wiring one to main_btn_* refuses the distinction "
            f"this rename exists to make.")


def test_the_main_window_reads_the_main_family():
    for rel in MAIN_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert re.search(r"(['\"])main_btn_", src), (
            f"{rel} no longer reads the main family")
        assert "dialog_btn_" not in src, (
            f"{rel} is main-window code and must not read the dialog family")


def test_the_gold_press_belongs_to_the_dialog_family_too():
    """The gold pressed plate is read by exactly one place, and it is a dialog.

    This is the finding that made the rename worth doing here. Reading
    button_pressed_bg out of the palette suggested the MAIN button pressed to
    gold; it does not -- the main window's pressed plate is #444444, written
    into the QSS blocks in utils/config.py as APP_BTN_PRESSED. The gold was
    always the dialog's. The name now says so.
    """
    config = (ROOT / "utils" / "config.py").read_text(encoding="utf-8-sig")
    assert "APP_BTN_PRESSED" in config
    panel = (ROOT / "core" / "package_d_panel.py").read_text(encoding="utf-8-sig")
    assert "dialog_btn_pressed_bg" in panel
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
