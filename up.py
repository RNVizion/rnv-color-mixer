#!/usr/bin/env python3
"""RNV-IMAGE-CONFIRM — the load reads the file; the caller asks.

    python up.py             # apply, then run the guards and both suites
    python up.py --check     # rehearse every edit in memory, write nothing

Derived against a fresh clone of rnv-color-mixer at head e538c2f with
up-for-rnv-color-mixer-palette-import.py already applied. **Run that one
first** — this round widens the guard it installs, and refuses if it is
not there.

THIS RETIRES THE LAST DESELECT IN THE REPOSITORY.

WHAT WAS WRONG. `ImageHandler.load_image` — a function whose whole job is to
read an image off disk — contained

    if file_size_mb > 10:
        reply = QMessageBox.question(None, "Large Image File", ...)

A modal question does not return until a person answers it, and
`resources/background_images/background.png` is **10.1 MB**, so the
threshold tripped and the load never completed anywhere there was nobody to
click. Both CI workflows deselected the locked
`test_load_real_image_if_available` because of it — the only skip left on
either runner — and `KNOWN_ISSUES.md` recorded

    **Planned fix:** None required. This is a test-environment artifact,
    not a code defect.

It is a code defect. Nothing about the runners was at fault: the same call
blocks in any headless process. Measured: the test hangs until killed on the
tree before this change and passes three times in three after.

THE FIX. `large_image_confirmation_size` stats the file and returns the size
in MB when the user should be asked, or None. It never opens the file and
never shows anything. `load_image` no longer asks at all. The question moved
to `RNV_Color_Mixer._do_image_load`, the one production path a person
actually takes — the only place that knows there is someone to answer it —
with the wording copied across unchanged.

The threshold became `ImageHandler.LARGE_IMAGE_WARNING_MB` rather than a
bare `10`, because the check and the caller now both have to agree about
what counts as large, and two copies of a magic number drift. The caller
never sees the number: it asks whether there is a size to confirm and
displays whatever it is handed.

THE RULE GOT WIDER, WHICH MATTERS MORE THAN THIS FIX. The palette round
installed a guard saying a function may read a file or wait on a dialog,
never both — and scoped it to `utils/file_utils.py`, naming this defect as
a known violation left for its own round. That guard **would not have caught
this one**: it looked for the project's own `show_*_dialog` helpers, and
this blocker was a plain `QMessageBox.question`. A rule named after one
helper only ever catches code that uses that helper. It now recognises any
blocking Qt call — QMessageBox and friends, QInputDialog, a bare `.exec()` —
across both modules. Checked against the trees before each fix: the wider
rule flags both original defects and neither fixed one.

ONE FILE IS DELETED. `tests/test_ci_deselects.py` swept every `--deselect`
in CI and asserted the node it named still existed. With none left it would
pass over nothing, and its own failure message says to delete it in the
commit that removes the last one. That is this commit.
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
SENTINEL_FILE = "core/image_handler.py"
SENTINEL = "RNV-IMAGE-CONFIRM"
GUARD = "tests/test_image_confirm.py"
DESCRIPTION = "move the large-image question off the data path"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, now 356 tests with nothing deselected\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-IMAGE-CONFIRM-GUARD -- the load reads the file; the caller asks.

Installed 2026-09-10. This retires the last deselect in the repository.

WHAT WAS WRONG. `ImageHandler.load_image` -- a function whose job is to read
an image off disk -- contained

    if file_size_mb > 10:
        reply = QMessageBox.question(None, "Large Image File", ...)

A modal question does not return until a person answers it.
`resources/background_images/background.png` is **10.1 MB**, so the
threshold tripped and the load never completed anywhere there was nobody to
click. Measured: on the tree before this change the locked
`test_load_real_image_if_available` hangs until killed; after, it passes
three times in three.

WHAT WAS RECORDED. `KNOWN_ISSUES.md` carried it as

    **Planned fix:** None required. This is a test-environment artifact,
    not a code defect.

and both CI workflows deselected the test -- the only skip left on either
runner. It was a code defect, and nothing about the runners was at fault:
the same call blocks in any headless process.

THE FIX. `large_image_confirmation_size` stats the file and returns the size
in MB when the user should be asked, or None. It never opens the file and
never shows anything. `load_image` no longer asks at all. The question moved
to `RNV_Color_Mixer._do_image_load`, the one production path a person
actually takes -- the only place that knows there is someone to answer it --
with the wording unchanged.

WHY THE THRESHOLD IS A NAMED CONSTANT NOW. The check and the caller both
have to agree about what counts as large. It was a bare `10` in one
function; two copies of a magic number drift, so it is
`ImageHandler.LARGE_IMAGE_WARNING_MB` and the caller never sees the number
at all -- it asks whether there is a size to confirm and shows what it is
handed.

THE RULE THIS SITS UNDER. tests/test_palette_import.py states it: a
function may read a file, or wait on a dialog, never both. That guard's
sweep now covers this module too. Worth recording why it did not catch this
one on the day it was written: it looked for the project's own
`show_*_dialog` helpers, and this blocker was a plain `QMessageBox.question`.
A rule named after one helper only ever catches code using that helper.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HANDLER = ROOT / "core" / "image_handler.py"
APP = ROOT / "RNV_Color_Mixer.py"
WORKFLOWS = ROOT / ".github" / "workflows"

CHECK = "large_image_confirmation_size"
DESELECTED = "test_load_real_image_if_available"


def _fn(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _waits(node) -> list[str]:
    out = []
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        rendered = ast.unparse(n.func)
        attr = getattr(n.func, "attr", "")
        if rendered.startswith(("QMessageBox.", "QInputDialog.", "QColorDialog.",
                                "QFontDialog.")):
            out.append(rendered)
        elif attr in ("exec", "exec_"):
            out.append(rendered)
        elif attr.startswith("show_") and "dialog" in attr:
            out.append(rendered)
    return out


def _handler():
    from core.image_handler import ImageHandler
    return ImageHandler()


# ═══════════════════════════════════════════════════════════════════════
# the data path
# ═══════════════════════════════════════════════════════════════════════

def test_load_image_waits_for_nobody():
    """The defect, stated where the message will be read.

    The general rule in tests/test_palette_import.py covers this too. This
    one exists so the failure names `load_image` and says what breaks.
    """
    node = _fn(HANDLER, "load_image")
    assert node is not None, "load_image is gone from core/image_handler.py"

    waits = _waits(node)
    assert not waits, (
        f"load_image waits on {sorted(set(waits))}. It reads a file, so it "
        f"has to be callable with nobody watching -- a modal call here hangs "
        f"CI, a batch script, and anything else without a person in front of "
        f"it. The question belongs to the caller.")


def test_the_confirmation_check_shows_nothing_either():
    node = _fn(HANDLER, CHECK)
    assert node is not None, f"{CHECK} is gone"

    waits = _waits(node)
    assert not waits, (
        f"{CHECK} waits on {sorted(set(waits))}; its whole purpose is to let "
        f"the caller decide without one")

    reads = [n for n in ast.walk(node) if isinstance(n, ast.Call)
             and getattr(n.func, "id", getattr(n.func, "attr", "")) == "open"]
    assert not reads, (
        f"{CHECK} opens the file. It should stat it and nothing more -- "
        f"opening it here duplicates work load_image is about to do.")


# ═══════════════════════════════════════════════════════════════════════
# the feature, which must survive the move
# ═══════════════════════════════════════════════════════════════════════

def test_the_caller_still_asks_before_loading_a_large_image():
    """Moving a dialog out is only a refactor if it lands somewhere.

    Every other test here would pass if the confirmation had simply been
    deleted, and a user would silently wait on a 150 MB load with no warning.
    """
    node = _fn(APP, "_do_image_load")
    assert node is not None, "_do_image_load is gone from RNV_Color_Mixer.py"

    calls = {ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)}
    assert any(c.endswith(CHECK) for c in calls), (
        f"_do_image_load never calls {CHECK}, so nothing decides whether to "
        f"warn about a large image")
    assert any(c.startswith("QMessageBox.") for c in calls), (
        "_do_image_load no longer asks the user anything. The large-image "
        "confirmation was removed rather than moved.")


def test_the_caller_does_not_hardcode_the_threshold():
    """One definition of "large".

    The caller asks whether there is a size to confirm and displays what it
    is given. If it grew its own `> 10`, the two would drift the first time
    the constant changed.
    """
    node = _fn(APP, "_do_image_load")
    assert node is not None

    # Read as a comparison against the number 10, not as the text "> 10".
    # The first version of this test matched the substring and fired on
    # `canvas_size.width() > 100`, which is the same use-versus-mention
    # mistake in numeric form.
    hardcoded = [ast.unparse(c) for c in ast.walk(node)
                 if isinstance(c, ast.Compare)
                 for comp in c.comparators
                 if isinstance(comp, ast.Constant) and comp.value in (10, 10.0)]
    assert not hardcoded, (
        f"_do_image_load compares against 10 itself:\n  "
        + "\n  ".join(hardcoded)
        + f"\n\nThe threshold lives in ImageHandler.LARGE_IMAGE_WARNING_MB "
          f"and reaches the caller through {CHECK}. Two copies drift.")

    body = ast.unparse(node)
    assert "LARGE_IMAGE_WARNING_MB" not in body, (
        "_do_image_load reaches for the threshold constant directly; it "
        f"should ask {CHECK} whether there is a size to confirm and display "
        f"whatever it is handed")


# ═══════════════════════════════════════════════════════════════════════
# behaviour
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.timeout(60)
def test_the_real_background_image_loads_without_a_person(qapp):
    """The reproduction, as a test.

    This is the exact call the locked suite makes and that both runners
    deselected. It hung. Sixty seconds is the line between slow and never,
    not a performance budget.
    """
    import utils.config as cfg
    target = getattr(cfg, "DEFAULT_BACKGROUND", None)
    if not target or not os.path.exists(target):
        pytest.skip("the default background image is not in this checkout")

    size_mb = os.path.getsize(target) / (1024 * 1024)
    assert size_mb > 10, (
        f"the background image is {size_mb:.1f}MB, below the 10MB threshold "
        f"that made this hang. The test still passes, but it is no longer "
        f"exercising the case it was written for -- point it at a larger "
        f"file or retire it.")

    assert isinstance(_handler().load_image(target), bool)


@pytest.mark.timeout(60)
def test_the_check_asks_only_when_it_should(tmp_path, qapp):
    handler = _handler()

    small = tmp_path / "small.png"
    small.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 512)
    assert handler.large_image_confirmation_size(str(small)) is None, (
        "a small image should load without asking anyone anything")

    assert handler.large_image_confirmation_size(str(tmp_path / "nope.png")) is None, (
        "a missing file should not produce a dialog; load_image reports it")

    not_an_image = tmp_path / "notes.txt"
    not_an_image.write_text("hello")
    assert handler.large_image_confirmation_size(str(not_an_image)) is None, (
        "an unsupported extension is refused by load_image, so asking first "
        "would show the user a pointless dialog before the refusal")

    import utils.config as cfg
    target = getattr(cfg, "DEFAULT_BACKGROUND", None)
    if target and os.path.exists(target):
        got = handler.large_image_confirmation_size(target)
        assert isinstance(got, float) and got > 10, (
            f"the 10.1MB background image should be confirmed, got {got!r}")


# ═══════════════════════════════════════════════════════════════════════
# the deselect, retired
# ═══════════════════════════════════════════════════════════════════════

def test_the_locked_test_is_not_deselected_on_any_runner():
    """It was skipped on both runners for a defect that is now fixed.

    A deselect is the cheapest thing in the world to re-add when a test goes
    red, and the reason it went red is the thing worth knowing.
    """
    assert WORKFLOWS.is_dir(), f"{WORKFLOWS} is not where this guard looks"

    offenders = []
    for wf in sorted(WORKFLOWS.glob("*.yml")):
        text = wf.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if DESELECTED in line and "--deselect" in line:
                offenders.append(f"{wf.name}:{i}")

    assert not offenders, (
        f"{DESELECTED} is deselected again at:\n  " + "\n  ".join(offenders)
        + f"\n\nIt was skipped because ImageHandler.load_image raised a modal "
          f"QMessageBox.question for files over 10MB and the background image "
          f"is 10.1MB. If it is failing again, that is worth diagnosing "
          f"rather than hiding.")


def test_this_guard_can_see_the_files_it_judges():
    for path in (HANDLER, APP):
        assert path.exists(), f"{path} is not where this guard looks"
    assert list(WORKFLOWS.glob("*.yml")), "no workflows found to check"
    assert _fn(HANDLER, "load_image") is not None
    assert _fn(HANDLER, CHECK) is not None
'''

EDITS = [('core/image_handler.py', '    MAX_FILE_SIZE_MB = 200  # Maximum file size in megabytes\n', "    MAX_FILE_SIZE_MB = 200  # Maximum file size in megabytes\n\n    #: Above this, loading is slow enough that the user is asked first.\n    #: RNV-IMAGE-CONFIRM, 2026-09-10 -- named rather than the bare 10 it was,\n    #: because the caller now applies the same threshold and two copies of a\n    #: magic number drift.\n    LARGE_IMAGE_WARNING_MB = 10\n\n    #: One definition, used by load_image and by the confirmation check, so\n    #: the two cannot disagree about what is loadable.\n    VALID_IMAGE_EXTENSIONS = frozenset({\n        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'})\n    # Signals\n    image_loaded = pyqtSignal(str)  # image path\n    image_cleared = pyqtSignal()\n    zoom_changed = pyqtSignal(float)  # zoom level\n    status_message = pyqtSignal(str)  # status message\n    ", 1), ('core/image_handler.py', "            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}\n", '            valid_extensions = self.VALID_IMAGE_EXTENSIONS\n', 1), ('core/image_handler.py', '            # === LARGE IMAGE WARNING (>10MB) ===\n            from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication\n            from PyQt6.QtCore import Qt\n            \n            if file_size_mb > 10:\n                reply = QMessageBox.question(\n                    None,\n                    "Large Image File",\n                    f"This image is {file_size_mb:.1f}MB.\\n\\n"\n                    f"Large images may:\\n"\n                    f"• Use significant memory\\n"\n                    f"• Take longer to load and zoom\\n"\n                    f"• Slow down color sampling\\n\\n"\n                    f"Continue loading?",\n                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,\n                    QMessageBox.StandardButton.Yes\n                )\n                \n                if reply != QMessageBox.StandardButton.Yes:\n                    self.status_message.emit("Image loading cancelled by user")\n                    return False\n            \n', '            # === LARGE IMAGE WARNING ===\n            # The confirmation used to be a QMessageBox.question right here.\n            # A modal question never returns without a user, so this\n            # function -- which reads a file -- could not be called headless\n            # at all: background.png is 10.1MB, the threshold tripped, and\n            # the load blocked forever. The question now belongs to the\n            # caller, which is the only place that knows whether there is\n            # anyone to answer it. See large_image_confirmation_size above.\n            from PyQt6.QtWidgets import QProgressDialog, QApplication\n            from PyQt6.QtCore import Qt\n            \n', 1), ('core/image_handler.py', '    def load_image(self, path: str) -> bool:\n', '    def large_image_confirmation_size(self, path: str) -> float | None:\n        """The file\'s size in MB if the user should be asked before loading it.\n\n        RNV-IMAGE-CONFIRM, 2026-09-10. See tests/test_image_confirm.py.\n\n        Returns None when there is nothing to ask about: the file cannot be\n        stat-ed, is not an image this handler accepts, is small enough to\n        load without comment, or is over MAX_FILE_SIZE_MB and will be\n        refused anyway.\n\n        Stats the file. Never opens it, and never shows anything -- so it can\n        be called from a test, a script or CI. The conditions are exactly the\n        ones under which load_image used to raise its own dialog, which is\n        what keeps the user-visible behaviour identical.\n        """\n        try:\n            if not path or not isinstance(path, str) or len(path) > 255:\n                return None\n            if not os.path.exists(path) or not os.access(path, os.R_OK):\n                return None\n            if os.path.splitext(path)[1].lower() not in self.VALID_IMAGE_EXTENSIONS:\n                return None\n            size_mb = os.path.getsize(path) / (1024 * 1024)\n        except OSError:\n            return None\n\n        if size_mb <= self.LARGE_IMAGE_WARNING_MB:\n            return None\n        if size_mb > self.MAX_FILE_SIZE_MB:\n            return None\n        return size_mb\n\n    def load_image(self, path: str) -> bool:\n', 1), ('RNV_Color_Mixer.py', '            if not self.image_handler.load_image(path):', '            # RNV-IMAGE-CONFIRM, 2026-09-10. This question used to live\n            # inside ImageHandler.load_image, where it made a file-reading\n            # function impossible to call without a user -- the load blocked\n            # forever on CI, which KNOWN_ISSUES.md recorded as a test\n            # environment quirk for months. It belongs here instead: this is\n            # the path a person actually took, so this is the place that\n            # knows there is someone to answer. The wording is unchanged.\n            file_size_mb = self.image_handler.large_image_confirmation_size(path)\n            if file_size_mb is not None:\n                from PyQt6.QtWidgets import QMessageBox\n                reply = QMessageBox.question(\n                    None,\n                    "Large Image File",\n                    f"This image is {file_size_mb:.1f}MB.\\n\\n"\n                    f"Large images may:\\n"\n                    f"• Use significant memory\\n"\n                    f"• Take longer to load and zoom\\n"\n                    f"• Slow down color sampling\\n\\n"\n                    f"Continue loading?",\n                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,\n                    QMessageBox.StandardButton.Yes\n                )\n                if reply != QMessageBox.StandardButton.Yes:\n                    logger.info("Image loading cancelled by user")\n                    self.status_updated.emit("Image loading cancelled by user")\n                    return\n\n            if not self.image_handler.load_image(path):', 1), ('tests/test_palette_import.py', '"""RNV-PALETTE-IMPORT-GUARD -- read the file, or show the dialog. Not both.\n\nInstalled 2026-09-10.\n\nWHAT WAS WRONG. `FileUtils.auto_detect_and_import_palette` parsed a palette\nfile and, on any failure, called `show_warning_dialog` / `show_error_dialog`\nfrom inside the same function. A modal dialog does not return without a\nuser, so in any headless context -- CI, a test, a batch script -- the\nfunction **blocked forever**. Measured: a valid `.gpl` returned fine;\nmissing, empty and garbage input all hung, with\n\n    This plugin does not support propagateSizeHints()\n\nprinted on the way in.\n\nWHAT WAS RECORDED INSTEAD. A test named `test_auto_detect_palette_skipped`,\nbody `pass`, carrying\n\n    @pytest.mark.skip(reason="Native crash on offscreen Qt -- see Phase 8.7")\n\nIt is not a crash, it is a hang, and the difference matters: a crash gets\nnoticed, a hang gets a CI job cancelled an hour later and blamed on the\nrunner. And a skipped `pass` measures nothing, so the note was the only\nthing that test ever contributed.\n\nTHREE TESTS, NONE OF THEM ENTERING THE FUNCTION. The locked\n`test_rnv_color_mixer.py` also calls this function twice:\n\n    r = FileUtils.auto_detect_and_import_palette("/no/such.xyz")\n\non the CLASS, with one argument, so `filepath` is never supplied. Both raise\n`TypeError: missing 1 required positional argument` and both swallow it with\n`except Exception: pass`. That is why the locked suite never hung: it never\ncalled the function. Those two are in the locked file and are left alone\nhere; this note is the record that they measure nothing.\n\nTHE RULE THIS GUARD ENFORCES. A function may read a file, or it may show a\ndialog. Not both. `import_palette_data` does the work and returns\n`(colors, problem)`; `auto_detect_and_import_palette` keeps its name, its\nreturn and both dialogs, and does no parsing of its own. Callers are\nuntouched, and the locked file still sees the identical TypeError.\n\nNote what is NOT in the rule: showing a dialog is fine, and so is taking a\nfilepath. `show_format_info_dialog` does both -- it splits the extension off\nthe path and shows a lookup from a table. It never opens the file, so it\ncannot block on anything but its own dialog, which is its whole purpose. The\nrule is about reading CONTENTS, and it was written by checking it against\nevery dialog-showing function in the module rather than against the one that\nprompted it.\n\nTHE SWEEP IS SCOPED TO utils/file_utils.py, AND THERE IS A KNOWN VIOLATION\nOUTSIDE IT. `ImageHandler.load_image` in core/image_handler.py has the same\ndefect and is not fixed by this round:\n\n    if file_size_mb > 10:\n        reply = QMessageBox.question(None, "Large Image File", ...)\n\n`resources/background_images/background.png` is 10.1 MB, so the threshold\ntrips, the modal question blocks, and the load never returns. That is the\nwhole of `test_load_real_image_if_available`, which KNOWN_ISSUES.md records\nas skipped on BOTH runners with "Planned fix: None required. This is a\ntest-environment artifact, not a code defect." It is a code defect, of\nexactly the kind this rule names.\n\nIt is left out rather than quietly excluded: `load_image` is a hundred lines\non the application\'s main image path, and prising the confirmation out of it\nis a bigger change than the one this round is carrying. FILES below is the\nlist to extend when that lands. A guard that had simply pointed at the file\nit happened to pass on would have hidden this.\n"""\nfrom __future__ import annotations\n\nimport ast\nfrom pathlib import Path\n\nimport pytest\n\nROOT = Path(__file__).resolve().parent.parent\nFILE_UTILS = ROOT / "utils" / "file_utils.py"\n\n#: The modules the rule is enforced over. core/image_handler.py belongs here\n#: and is not in it yet -- see the module docstring. Adding it before\n#: load_image is split would make this guard red on arrival, which is how a\n#: guard gets an exemption written into it and stops meaning anything.\nFILES = (FILE_UTILS,)\n\nPURE = "import_palette_data"\nWRAPPER = "auto_detect_and_import_palette"\n\n#: Calls that mean "this function reads a file\'s contents". Splitting an\n#: extension off a path does not count, and neither does a lookup table.\nREADS_CONTENT = ("open", "import_palette", "read_text", "read_bytes",\n                 "load", "loads", "readlines", "read")\n\n\ndef _functions():\n    src = FILE_UTILS.read_text(encoding="utf-8")\n    return src, ast.parse(src, str(FILE_UTILS))\n\n\ndef _fn(name: str):\n    src, tree = _functions()\n    for node in ast.walk(tree):\n        if isinstance(node, ast.FunctionDef) and node.name == name:\n            return node\n    return None\n\n\ndef _shows_dialog(node) -> list[str]:\n    out = []\n    for n in ast.walk(node):\n        if isinstance(n, ast.Call):\n            attr = getattr(n.func, "attr", "")\n            if attr.startswith("show_") and "dialog" in attr:\n                out.append(attr)\n    return out\n\n\ndef _reads_content(node) -> list[str]:\n    out = []\n    for n in ast.walk(node):\n        if isinstance(n, ast.Call):\n            name = getattr(n.func, "attr", getattr(n.func, "id", ""))\n            if name in READS_CONTENT:\n                out.append(name)\n    return out\n\n\ndef _fu():\n    from utils.file_utils import FileUtils\n    return FileUtils()\n\n\n# ═══════════════════════════════════════════════════════════════════════\n# the rule, stated over every function in the module\n# ═══════════════════════════════════════════════════════════════════════\n\ndef test_no_function_both_reads_a_file_and_shows_a_dialog():\n    """The general rule, not a special case for the one that prompted it.\n\n    Checked across the whole module, because the next one to acquire a\n    dialog on its error path will not be this one, and a rule written about\n    a single function is a rule that only ever catches that function.\n    """\n    src, tree = _functions()\n    bad = []\n    for node in ast.walk(tree):\n        if not isinstance(node, ast.FunctionDef):\n            continue\n        shows = _shows_dialog(node)\n        reads = _reads_content(node)\n        if shows and reads:\n            bad.append(f"{node.name} (line {node.lineno}): "\n                       f"shows {sorted(set(shows))}, reads {sorted(set(reads))}")\n\n    assert not bad, (\n        "these functions read a file and show a dialog in the same body:\\n  "\n        + "\\n  ".join(bad)\n        + "\\n\\nA modal dialog never returns without a user, so this blocks "\n          "forever anywhere there is no one to click it -- CI, a test, a "\n          "batch script. Split it: one function returns the result, another "\n          "presents it. See import_palette_data / "\n          "auto_detect_and_import_palette.")\n\n\ndef test_the_data_path_shows_nothing():\n    """The specific half of the rule, so the message names the function."""\n    node = _fn(PURE)\n    assert node is not None, f"{PURE} is gone from utils/file_utils.py"\n\n    shows = _shows_dialog(node)\n    assert not shows, (\n        f"{PURE} calls {sorted(set(shows))}. This is the half that has to be "\n        f"callable with nobody watching; put the dialog in the wrapper.")\n\n\ndef test_the_wrapper_still_shows_both_dialogs():\n    """No feature was removed, and this is what says so.\n\n    A split that quietly dropped the dialogs would pass every other test\n    here and would change what the user sees on a bad file.\n    """\n    node = _fn(WRAPPER)\n    assert node is not None, f"{WRAPPER} is gone; callers depend on it"\n\n    shows = set(_shows_dialog(node))\n    assert "show_warning_dialog" in shows, (\n        f"{WRAPPER} no longer warns on a file with no usable colours")\n    assert "show_error_dialog" in shows, (\n        f"{WRAPPER} no longer reports an import failure to the user")\n\n\ndef test_the_wrapper_delegates_rather_than_reimplementing():\n    """One copy of the logic.\n\n    A wrapper that parsed the file itself would satisfy every assertion\n    above and would drift out of step with the function it shadows.\n    """\n    node = _fn(WRAPPER)\n    assert node is not None\n\n    calls = {getattr(n.func, "attr", getattr(n.func, "id", ""))\n             for n in ast.walk(node) if isinstance(n, ast.Call)}\n    assert PURE in calls, (\n        f"{WRAPPER} does not call {PURE}; the parsing logic has been "\n        f"duplicated rather than shared")\n\n    reads = _reads_content(node)\n    assert not reads, (\n        f"{WRAPPER} reads the file itself ({sorted(set(reads))}) as well as "\n        f"delegating. That is two implementations of one thing.")\n\n\n# ═══════════════════════════════════════════════════════════════════════\n# behaviour\n# ═══════════════════════════════════════════════════════════════════════\n\n@pytest.mark.timeout(60)\ndef test_every_bad_input_returns_instead_of_blocking(tmp_path):\n    """The reproduction, as a test.\n\n    Each of these blocked forever before the split. Sixty seconds is not a\n    performance budget -- these run in milliseconds -- it is the line\n    between slow and never, wide enough that a cold runner cannot make it\n    flaky.\n    """\n    cases = {\n        "missing.gpl": None,\n        "empty.gpl": b"",\n        "garbage.pal": b"\\xa4\\x00\\xff\\xfe" * 64,\n        "truncated.json": b\'{"colors": [\',\n    }\n    fu = _fu()\n    for name, content in cases.items():\n        target = tmp_path / name\n        if content is not None:\n            target.write_bytes(content)\n\n        colors, problem = fu.import_palette_data(str(target))\n\n        assert colors is None, f"{name} produced colours: {colors!r}"\n        assert problem is not None, f"{name} reported no problem"\n\n\n@pytest.mark.timeout(60)\ndef test_a_good_palette_still_imports(tmp_path):\n    """Without this, "does not block" could be satisfied by doing nothing."""\n    target = tmp_path / "ok.gpl"\n    target.write_bytes(b"GIMP Palette\\nName: t\\n#\\n255 0 0 Red\\n")\n\n    colors, problem = _fu().import_palette_data(str(target))\n\n    assert problem is None, f"a valid palette reported: {problem}"\n    assert colors, "a valid palette imported no colours"\n\n\n@pytest.mark.timeout(60)\ndef test_the_severity_is_returned_not_left_to_the_caller_to_guess(tmp_path):\n    """The caller has to choose between a warning and an error dialog.\n\n    Returning only a message would push that decision onto whoever reads the\n    string, which is how a wrapper ends up matching on display text.\n    """\n    empty = tmp_path / "empty.gpl"\n    empty.write_bytes(b"")\n    _, problem = _fu().import_palette_data(str(empty))\n    assert problem is not None\n    assert len(problem) == 3, f"expected (severity, title, message), got {problem!r}"\n    severity, title, message = problem\n    assert severity in ("warning", "error"), f"unknown severity {severity!r}"\n    assert title and message, "the caller was given nothing to display"\n\n    missing = tmp_path / "nope.gpl"\n    _, problem = _fu().import_palette_data(str(missing))\n    assert problem is not None\n    assert problem[0] in ("warning", "error")\n\n\ndef test_this_guard_can_see_the_file_it_judges():\n    """A sweep that finds nothing passes every assertion above."""\n    assert FILE_UTILS.exists(), f"{FILE_UTILS} is not where this guard looks"\n    src, tree = _functions()\n    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]\n    assert len(functions) >= 20, (\n        f"only {len(functions)} functions found in file_utils.py; the guard "\n        f"is probably reading the wrong file")\n    assert any(_shows_dialog(n) for n in functions), (\n        "no function in file_utils.py shows a dialog at all, which means the "\n        "rule above has no subject and is passing vacuously")\n', '"""RNV-PALETTE-IMPORT-GUARD -- read the file, or show the dialog. Not both.\n\nInstalled 2026-09-10.\n\nWHAT WAS WRONG. `FileUtils.auto_detect_and_import_palette` parsed a palette\nfile and, on any failure, called `show_warning_dialog` / `show_error_dialog`\nfrom inside the same function. A modal dialog does not return without a\nuser, so in any headless context -- CI, a test, a batch script -- the\nfunction **blocked forever**. Measured: a valid `.gpl` returned fine;\nmissing, empty and garbage input all hung, with\n\n    This plugin does not support propagateSizeHints()\n\nprinted on the way in.\n\nWHAT WAS RECORDED INSTEAD. A test named `test_auto_detect_palette_skipped`,\nbody `pass`, carrying\n\n    @pytest.mark.skip(reason="Native crash on offscreen Qt -- see Phase 8.7")\n\nIt is not a crash, it is a hang, and the difference matters: a crash gets\nnoticed, a hang gets a CI job cancelled an hour later and blamed on the\nrunner. And a skipped `pass` measures nothing, so the note was the only\nthing that test ever contributed.\n\nTHREE TESTS, NONE OF THEM ENTERING THE FUNCTION. The locked\n`test_rnv_color_mixer.py` also calls this function twice:\n\n    r = FileUtils.auto_detect_and_import_palette("/no/such.xyz")\n\non the CLASS, with one argument, so `filepath` is never supplied. Both raise\n`TypeError: missing 1 required positional argument` and both swallow it with\n`except Exception: pass`. That is why the locked suite never hung: it never\ncalled the function. Those two are in the locked file and are left alone\nhere; this note is the record that they measure nothing.\n\nTHE RULE THIS GUARD ENFORCES. A function may read a file, or it may show a\ndialog. Not both. `import_palette_data` does the work and returns\n`(colors, problem)`; `auto_detect_and_import_palette` keeps its name, its\nreturn and both dialogs, and does no parsing of its own. Callers are\nuntouched, and the locked file still sees the identical TypeError.\n\nNote what is NOT in the rule: showing a dialog is fine, and so is taking a\nfilepath. `show_format_info_dialog` does both -- it splits the extension off\nthe path and shows a lookup from a table. It never opens the file, so it\ncannot block on anything but its own dialog, which is its whole purpose. The\nrule is about reading CONTENTS, and it was written by checking it against\nevery dialog-showing function in the module rather than against the one that\nprompted it.\n\nTHE SWEEP NOW COVERS core/image_handler.py TOO, AND THE RULE IS WIDER.\nWhen this guard was installed it looked only for `show_*_dialog` helpers,\nand it was scoped to utils/file_utils.py with a note naming\n`ImageHandler.load_image` as a known violation left for its own round. That\nround landed on 2026-09-10.\n\nTwo things had to change, and the first is the more interesting. The\noriginal rule would **not** have caught load_image at all: its blocker was\n\n    reply = QMessageBox.question(None, "Large Image File", ...)\n\nwhich is not a `show_*_dialog` call. A rule that names one project-specific\nhelper only ever catches code that uses that helper. It now recognises any\nblocking Qt call -- QMessageBox and friends, QInputDialog, and a bare\n`.exec()` -- and it is checked over both modules. Verified against the trees\nbefore each fix: the wider rule flags both original defects and neither\nfixed one.\n\n"""\nfrom __future__ import annotations\n\nimport ast\nfrom pathlib import Path\n\nimport pytest\n\nROOT = Path(__file__).resolve().parent.parent\nFILE_UTILS = ROOT / "utils" / "file_utils.py"\n\n#: The modules the rule is enforced over.\nIMAGE_HANDLER = ROOT / "core" / "image_handler.py"\n\nFILES = (FILE_UTILS, IMAGE_HANDLER)\n\nPURE = "import_palette_data"\nWRAPPER = "auto_detect_and_import_palette"\n\n#: Calls that mean "this function reads a file\'s contents". Splitting an\n#: extension off a path does not count, and neither does a lookup table.\nREADS_CONTENT = ("open", "import_palette", "read_text", "read_bytes",\n                 "load", "loads", "readlines", "read")\n\n\ndef _functions():\n    src = FILE_UTILS.read_text(encoding="utf-8")\n    return src, ast.parse(src, str(FILE_UTILS))\n\n\ndef _fn(name: str):\n    src, tree = _functions()\n    for node in ast.walk(tree):\n        if isinstance(node, ast.FunctionDef) and node.name == name:\n            return node\n    return None\n\n\n#: Qt classes whose methods open a modal window and do not return until a\n#: person acts. QFileDialog is here for completeness even though its\n#: functions never read a file\'s contents, so the rule cannot fire on them.\nBLOCKING_CLASSES = ("QMessageBox.", "QInputDialog.", "QColorDialog.",\n                    "QFontDialog.", "QFileDialog.", "QProgressDialog.")\n\n\ndef _shows_dialog(node) -> list[str]:\n    """Every call in `node` that waits for a person.\n\n    Wider than the project\'s own `show_*_dialog` helpers on purpose. The\n    version of this guard that looked only for those would have passed\n    `ImageHandler.load_image`, whose blocker was a plain\n    `QMessageBox.question` -- so the rule caught the defect it was written\n    from and would have missed its twin.\n    """\n    out = []\n    for n in ast.walk(node):\n        if not isinstance(n, ast.Call):\n            continue\n        rendered = ast.unparse(n.func)\n        attr = getattr(n.func, "attr", "")\n        if attr.startswith("show_") and "dialog" in attr:\n            out.append(rendered)\n        elif rendered.startswith(BLOCKING_CLASSES):\n            out.append(rendered)\n        elif attr in ("exec", "exec_"):\n            out.append(rendered)\n    return out\n\n\ndef _all_functions():\n    """(path, FunctionDef) for every function in every governed module."""\n    for path in FILES:\n        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))\n        for node in ast.walk(tree):\n            if isinstance(node, ast.FunctionDef):\n                yield path, node\n\n\ndef _reads_content(node) -> list[str]:\n    out = []\n    for n in ast.walk(node):\n        if isinstance(n, ast.Call):\n            name = getattr(n.func, "attr", getattr(n.func, "id", ""))\n            if name in READS_CONTENT:\n                out.append(name)\n    return out\n\n\ndef _fu():\n    from utils.file_utils import FileUtils\n    return FileUtils()\n\n\n# ═══════════════════════════════════════════════════════════════════════\n# the rule, stated over every function in the module\n# ═══════════════════════════════════════════════════════════════════════\n\ndef test_no_function_both_reads_a_file_and_shows_a_dialog():\n    """The general rule, not a special case for the one that prompted it.\n\n    Checked across the whole module, because the next one to acquire a\n    dialog on its error path will not be this one, and a rule written about\n    a single function is a rule that only ever catches that function.\n    """\n    bad = []\n    for path, node in _all_functions():\n        shows = _shows_dialog(node)\n        reads = _reads_content(node)\n        if shows and reads:\n            bad.append(f"{path.name}::{node.name} (line {node.lineno}): "\n                       f"waits on {sorted(set(shows))}, reads {sorted(set(reads))}")\n\n    assert not bad, (\n        "these functions read a file and show a dialog in the same body:\\n  "\n        + "\\n  ".join(bad)\n        + "\\n\\nA modal dialog never returns without a user, so this blocks "\n          "forever anywhere there is no one to click it -- CI, a test, a "\n          "batch script. Split it: one function returns the result, another "\n          "presents it. See import_palette_data / "\n          "auto_detect_and_import_palette.")\n\n\ndef test_the_data_path_shows_nothing():\n    """The specific half of the rule, so the message names the function."""\n    node = _fn(PURE)\n    assert node is not None, f"{PURE} is gone from utils/file_utils.py"\n\n    shows = _shows_dialog(node)\n    assert not shows, (\n        f"{PURE} calls {sorted(set(shows))}. This is the half that has to be "\n        f"callable with nobody watching; put the dialog in the wrapper.")\n\n\ndef test_the_wrapper_still_shows_both_dialogs():\n    """No feature was removed, and this is what says so.\n\n    A split that quietly dropped the dialogs would pass every other test\n    here and would change what the user sees on a bad file.\n    """\n    node = _fn(WRAPPER)\n    assert node is not None, f"{WRAPPER} is gone; callers depend on it"\n\n    shows = set(_shows_dialog(node))\n    # Matched by suffix: _shows_dialog reports the rendered call, so a\n    # helper reached through self comes back as "self.show_warning_dialog".\n    for needed in ("show_warning_dialog", "show_error_dialog"):\n        assert any(s.endswith(needed) for s in shows), (\n            f"{WRAPPER} no longer calls {needed}. That is a feature removed, "\n            f"not a refactor: the user stops being told why an import failed."\n            f" Calls found: {sorted(shows)}")\n\n\ndef test_the_wrapper_delegates_rather_than_reimplementing():\n    """One copy of the logic.\n\n    A wrapper that parsed the file itself would satisfy every assertion\n    above and would drift out of step with the function it shadows.\n    """\n    node = _fn(WRAPPER)\n    assert node is not None\n\n    calls = {getattr(n.func, "attr", getattr(n.func, "id", ""))\n             for n in ast.walk(node) if isinstance(n, ast.Call)}\n    assert PURE in calls, (\n        f"{WRAPPER} does not call {PURE}; the parsing logic has been "\n        f"duplicated rather than shared")\n\n    reads = _reads_content(node)\n    assert not reads, (\n        f"{WRAPPER} reads the file itself ({sorted(set(reads))}) as well as "\n        f"delegating. That is two implementations of one thing.")\n\n\n# ═══════════════════════════════════════════════════════════════════════\n# behaviour\n# ═══════════════════════════════════════════════════════════════════════\n\n@pytest.mark.timeout(60)\ndef test_every_bad_input_returns_instead_of_blocking(tmp_path):\n    """The reproduction, as a test.\n\n    Each of these blocked forever before the split. Sixty seconds is not a\n    performance budget -- these run in milliseconds -- it is the line\n    between slow and never, wide enough that a cold runner cannot make it\n    flaky.\n    """\n    cases = {\n        "missing.gpl": None,\n        "empty.gpl": b"",\n        "garbage.pal": b"\\xa4\\x00\\xff\\xfe" * 64,\n        "truncated.json": b\'{"colors": [\',\n    }\n    fu = _fu()\n    for name, content in cases.items():\n        target = tmp_path / name\n        if content is not None:\n            target.write_bytes(content)\n\n        colors, problem = fu.import_palette_data(str(target))\n\n        assert colors is None, f"{name} produced colours: {colors!r}"\n        assert problem is not None, f"{name} reported no problem"\n\n\n@pytest.mark.timeout(60)\ndef test_a_good_palette_still_imports(tmp_path):\n    """Without this, "does not block" could be satisfied by doing nothing."""\n    target = tmp_path / "ok.gpl"\n    target.write_bytes(b"GIMP Palette\\nName: t\\n#\\n255 0 0 Red\\n")\n\n    colors, problem = _fu().import_palette_data(str(target))\n\n    assert problem is None, f"a valid palette reported: {problem}"\n    assert colors, "a valid palette imported no colours"\n\n\n@pytest.mark.timeout(60)\ndef test_the_severity_is_returned_not_left_to_the_caller_to_guess(tmp_path):\n    """The caller has to choose between a warning and an error dialog.\n\n    Returning only a message would push that decision onto whoever reads the\n    string, which is how a wrapper ends up matching on display text.\n    """\n    empty = tmp_path / "empty.gpl"\n    empty.write_bytes(b"")\n    _, problem = _fu().import_palette_data(str(empty))\n    assert problem is not None\n    assert len(problem) == 3, f"expected (severity, title, message), got {problem!r}"\n    severity, title, message = problem\n    assert severity in ("warning", "error"), f"unknown severity {severity!r}"\n    assert title and message, "the caller was given nothing to display"\n\n    missing = tmp_path / "nope.gpl"\n    _, problem = _fu().import_palette_data(str(missing))\n    assert problem is not None\n    assert problem[0] in ("warning", "error")\n\n\ndef test_this_guard_can_see_the_file_it_judges():\n    """A sweep that finds nothing passes every assertion above."""\n    for path in FILES:\n        assert path.exists(), f"{path} is not where this guard looks"\n    src, tree = _functions()\n    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]\n    assert len(functions) >= 20, (\n        f"only {len(functions)} functions found in file_utils.py; the guard "\n        f"is probably reading the wrong file")\n    assert any(_shows_dialog(n) for n in functions), (\n        "no function in file_utils.py shows a dialog at all, which means the "\n        "rule above has no subject and is passing vacuously")\n', 1), ('.github/workflows/tests-linux.yml', '          # Skips:\n          #   - test_load_real_image_if_available (unittest):\n          #       Hangs on offscreen Qt when loading background image.\n          #\n', '          # Skips: none. The list below records what was restored and why.\n          #\n          # RESTORED 2026-09-10 — test_load_real_image_if_available is no\n          # longer deselected, on either runner. It was skipped for a hang\n          # that KNOWN_ISSUES.md called "a test-environment artifact, not a\n          # code defect". It was a code defect: ImageHandler.load_image\n          # raised a modal QMessageBox.question for files over 10MB, and\n          # background.png is 10.1MB, so a file-reading function waited for\n          # a click that no runner can give. The question now belongs to the\n          # caller. Measured: the test hangs on the tree before this change\n          # and passes three times in three after.\n          # tests/test_image_confirm.py keeps the data path silent.\n          #\n', 1), ('.github/workflows/tests-linux.yml', '          coverage run --data-file=.coverage.unittest --branch -m pytest test_rnv_color_mixer.py -v --deselect "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"', '          coverage run --data-file=.coverage.unittest --branch -m pytest test_rnv_color_mixer.py -v', 1), ('.github/workflows/tests-windows.yml', '        # Skip test_load_real_image_if_available — it hangs on offscreen\n        # Qt (works fine locally with a real display). See KNOWN_ISSUES.md.\n', '        # RESTORED 2026-09-10 — nothing is deselected here any more.\n        # test_load_real_image_if_available hung because\n        # ImageHandler.load_image raised a modal QMessageBox.question for\n        # files over 10MB and background.png is 10.1MB. The question moved\n        # to the caller; the data path is silent. See KNOWN_ISSUES.md and\n        # tests/test_image_confirm.py.\n', 1), ('.github/workflows/tests-windows.yml', '          python -m pytest test_rnv_color_mixer.py -v --deselect "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"', '          python -m pytest test_rnv_color_mixer.py -v', 1), ('tests/test_brand_mirror.py', '        if path.suffix.lower() not in (".py", ".qss", ".css"):\n            continue\n', '        if path.suffix.lower() not in (".py", ".qss", ".css"):\n            continue\n        # `git ls-files` reports the INDEX, so a file deleted from the\n        # working tree is still listed until the deletion is committed.\n        # That is an ordinary transient state -- any `rm` before `git rm`\n        # produces it -- and reading it raised FileNotFoundError, turning a\n        # normal edit into three red tests with no useful message.\n        # test_the_retired_scan_is_still_looking still catches the case\n        # that matters, a scan that has stopped finding anything.\n        if not path.exists():\n            continue\n', 1), ('KNOWN_ISSUES.md', 'The following tests pass locally but are skipped on GitHub Actions CI\nrunners due to environment-specific quirks (no display server, virtualized\nfilesystems, etc.). Each skip is annotated in the workflow file with a\ncomment explaining the cause.', '**There are no CI-skipped tests as of 2026-09-10.** Both runners run both\nsuites complete. This section is kept as the record of what was skipped and\nwhy each one was retired — three of the four turned out to be code defects\nthat the skip was hiding, not the environment quirks they were filed as.', 1), ('KNOWN_ISSUES.md', '### `test_load_real_image_if_available` (locked unittest)\n\n**Skipped on:** Linux CI, Windows CI', '### `test_load_real_image_if_available` (locked unittest) — RESTORED\n\n**Skipped on:** nothing. Restored to both runners on 2026-09-10, and it was\nthe last deselect in the repository: the locked suite now runs all 356 of\nits tests on Linux and on Windows.\n', 1), ('KNOWN_ISSUES.md', '**Planned fix:** the same split applied to the palette importer on\n2026-09-10 — the function that reads the file returns a result, and the\ncaller decides whether to ask the user. `tests/test_palette_import.py`\nstates the rule and names this as the outstanding violation.\n**Not fixed yet:** `load_image` is a hundred lines on the main image path\nand deserves its own round.', '**Fixed 2026-09-10.** `ImageHandler.large_image_confirmation_size` stats\nthe file and returns the size in MB when the user should be asked, or None;\nit never opens the file and never shows anything. `load_image` no longer\nasks at all. The question moved to `RNV_Color_Mixer._do_image_load` — the\none production path a person actually takes, and so the only place that\nknows there is someone to answer it — with the wording unchanged. The\nthreshold is now `ImageHandler.LARGE_IMAGE_WARNING_MB` rather than a bare\n`10`, because the check and the caller both have to agree about it.\n\nMeasured: the test hangs until killed on the tree before this change, and\npasses three times in three after. Guarded by\n`tests/test_image_confirm.py`, which also fails if the deselect is ever\nre-added to either workflow.\n\n`tests/test_ci_deselects.py` was deleted in the same change. It swept every\n`--deselect` in CI and asserted the node it named still existed; with none\nleft it would have passed over nothing, and its own failure message said to\ndelete it in the commit that removed the last one.', 1)]
DELETIONS = ['tests/test_ci_deselects.py']

CHECK = "large_image_confirmation_size"
DESELECTED = "test_load_real_image_if_available"


def edits(tree) -> None:
    handler = tree.read(SENTINEL_FILE)
    if SENTINEL in handler:
        raise SystemExit(f"already applied -- '{SENTINEL}' is present in "
                         f"{SENTINEL_FILE}")
    if "RNV-PALETTE-IMPORT" not in tree.read("utils/file_utils.py"):
        raise SystemExit(
            "this round builds on the palette-import round, which is not "
            "applied here. Run up-for-rnv-color-mixer-palette-import.py "
            "first: this one widens the guard that one installs.")

    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    for rel in DELETIONS:
        tree.delete(rel)

    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))
    print("  deleted: " + ", ".join(DELETIONS))


def _waits(node) -> list:
    out = []
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        rendered = ast.unparse(n.func)
        attr = getattr(n.func, "attr", "")
        if rendered.startswith(("QMessageBox.", "QInputDialog.", "QColorDialog.",
                                "QFontDialog.")) or attr in ("exec", "exec_"):
            out.append(rendered)
        elif attr.startswith("show_") and "dialog" in attr:
            out.append(rendered)
    return out


def _fn(text, name):
    for n in ast.walk(ast.parse(text)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def checks(tree) -> None:
    handler = tree.files["core/image_handler.py"]
    app = tree.files["RNV_Color_Mixer.py"]

    for rel, text in (("core/image_handler.py", handler),
                      ("RNV_Color_Mixer.py", app),
                      ("tests/test_palette_import.py",
                       tree.files["tests/test_palette_import.py"])):
        try:
            ast.parse(text, rel)
        except SyntaxError as e:
            raise SystemExit(f"{rel} does not parse after the edits: {e}")

    # 1. the data path waits for nobody.
    load = _fn(handler, "load_image")
    if load is None:
        raise SystemExit("load_image is gone from core/image_handler.py")
    waiting = _waits(load)
    if waiting:
        raise SystemExit(f"load_image still waits on {sorted(set(waiting))}")

    check = _fn(handler, CHECK)
    if check is None:
        raise SystemExit(f"{CHECK} did not land")
    if _waits(check):
        raise SystemExit(f"{CHECK} waits on a dialog; it exists not to")

    # 2. the feature moved rather than vanished. Every other check here
    #    would pass if the confirmation had simply been deleted, and a user
    #    would then sit through a 150MB load with no warning at all.
    do_load = _fn(app, "_do_image_load")
    if do_load is None:
        raise SystemExit("_do_image_load is gone from RNV_Color_Mixer.py")
    calls = {ast.unparse(n.func) for n in ast.walk(do_load) if isinstance(n, ast.Call)}
    if not any(c.endswith(CHECK) for c in calls):
        raise SystemExit(f"_do_image_load never calls {CHECK}")
    if not any(c.startswith("QMessageBox.") for c in calls):
        raise SystemExit("_do_image_load no longer asks the user anything; "
                         "the confirmation was removed, not moved")

    # 3. one definition of "large". Read as a comparison against the NUMBER
    #    10 -- the first draft matched the text "> 10" and fired on
    #    `canvas_size.width() > 100`.
    hardcoded = [ast.unparse(c) for c in ast.walk(do_load)
                 if isinstance(c, ast.Compare)
                 for comp in c.comparators
                 if isinstance(comp, ast.Constant) and comp.value in (10, 10.0)]
    if hardcoded:
        raise SystemExit(f"_do_image_load compares against 10 itself: {hardcoded}")

    # 4. no workflow deselects it any more, and none deselects anything.
    for rel in (".github/workflows/tests-linux.yml",
                ".github/workflows/tests-windows.yml"):
        if DESELECTED in tree.files[rel] and "--deselect" in tree.files[rel]:
            for line in tree.files[rel].splitlines():
                if DESELECTED in line and "--deselect" in line:
                    raise SystemExit(f"{rel} still deselects {DESELECTED}")

    # 5. the widened rule is actually wider. A guard that still looked only
    #    for show_*_dialog would pass this tree and would have passed the
    #    defect it was supposed to catch.
    widened = tree.files["tests/test_palette_import.py"]
    if "QMessageBox." not in widened:
        raise SystemExit("the palette guard was not widened to blocking Qt "
                         "calls; it would still miss QMessageBox.question")
    if "image_handler" not in widened:
        raise SystemExit("the palette guard's sweep does not cover "
                         "core/image_handler.py")

    # 6. the prose no longer contradicts the code.
    ki = " ".join(tree.files["KNOWN_ISSUES.md"].split())
    # The phrase survives in the file as a QUOTATION of the wording being
    # corrected, so its presence proves nothing on its own. What matters is
    # that the correction stands beside it. Checking for the phrase alone
    # failed the round's own prose -- use versus mention, a third time.
    if ("test-environment artifact, not a code defect" in ki
            and "This is a code defect, not a test-environment artifact" not in ki):
        raise SystemExit("KNOWN_ISSUES.md still calls the hang an artifact "
                         "without the correction beside it")
    if "test_image_confirm.py" not in ki:
        raise SystemExit("KNOWN_ISSUES.md does not name the guard")

    # 7. the sentinel is in the file the re-run check reads. Shipped broken
    #    once; never again without a check.
    if SENTINEL not in handler:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    print("  guards: load_image waits for nobody, the caller still asks, "
          "no workflow deselects anything")


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
