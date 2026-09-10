#!/usr/bin/env python3
"""RNV-PALETTE-IMPORT — read the file, or show the dialog. Not both.

    python up.py             # apply, then run the guard and both suites
    python up.py --check     # rehearse every edit in memory, write nothing

Derived against a fresh clone of rnv-color-mixer at head e538c2f.

WHAT WAS WRONG. `FileUtils.auto_detect_and_import_palette` parsed a palette
file and, on any failure, called `show_warning_dialog` / `show_error_dialog`
from inside the same function. A modal dialog does not return without a
user, so anywhere there is nobody to click it — CI, a test, a batch script —
the function **blocked forever**.

Measured. A valid `.gpl` returned fine; **missing, empty and garbage input
all hung**, printing `This plugin does not support propagateSizeHints()` on
the way in. Not a crash. A hang, which is worse: a crash gets noticed, a
hang gets a job cancelled an hour later and blamed on the runner.

THREE TESTS NAMED AFTER THIS FUNCTION. NONE OF THEM ENTERED IT.

  1. `tests/test_error_recovery_paths.py` held a method called
     `test_auto_detect_palette_skipped` whose body was `pass`, carrying
     `@pytest.mark.skip(reason="Native crash on offscreen Qt")`. A skipped
     `pass` measures nothing; the note was its entire contribution, and the
     note was wrong about the mechanism.

  2 & 3. The locked `test_rnv_color_mixer.py` calls

         r = FileUtils.auto_detect_and_import_palette("/no/such.xyz")

     on the CLASS, with one argument, so `filepath` is never supplied. Both
     raise `TypeError: missing 1 required positional argument` and both
     swallow it with `except Exception: pass`. That is why the locked suite
     never hung — it never called the function. Those two are in the locked
     file and are left alone; this is the record that they measure nothing.

THE FIX, AND WHY NO CALLER CHANGES. `import_palette_data` does the work and
returns `(colors, problem)`, where `problem` is `None` or
`(severity, title, message)`. `auto_detect_and_import_palette` keeps its
name, its signature, its return value and BOTH dialogs, and does no parsing
of its own. Verified in both directions: the wrapper still blocks on its
dialog headless (the feature is intact), and the locked file still sees the
identical `TypeError`.

The severity is returned rather than inferred from the title, because a
title is display text; a wrapper that matched on it would show the wrong
dialog the first time someone rewords a string.

THE RULE, AND THE ONE PLACE IT IS STILL BROKEN. The guard states a general
rule over `utils/file_utils.py`: a function may read a file, or show a
dialog, never both. It is scoped to that module, and it says so, because
**`core/image_handler.py` has the same defect and this round does not fix
it**:

    if file_size_mb > 10:
        reply = QMessageBox.question(None, "Large Image File", ...)

`background.png` is 10.1 MB, so the threshold trips and `load_image` blocks
on a modal question. That is the whole of `test_load_real_image_if_available`,
which `KNOWN_ISSUES.md` has recorded as skipped on **both** runners with
"Planned fix: None required. This is a test-environment artifact, not a code
defect." It is a code defect. This round corrects that entry and leaves the
fix for its own: `load_image` is a hundred lines on the main image path.

Note what the rule does NOT forbid. Showing a dialog is fine, and so is
taking a filepath. `show_format_info_dialog` does both — it splits the
extension off the path and displays a lookup from a table, never opening the
file. The rule is about reading CONTENTS, and it was written by checking it
against every dialog-showing function in the module rather than against the
one that prompted it.
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
SENTINEL_FILE = "utils/file_utils.py"
SENTINEL = "RNV-PALETTE-IMPORT"
GUARD = "tests/test_palette_import.py"
DESCRIPTION = "stop a data path blocking on a modal dialog"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, 355 tests\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-PALETTE-IMPORT-GUARD -- read the file, or show the dialog. Not both.

Installed 2026-09-10.

WHAT WAS WRONG. `FileUtils.auto_detect_and_import_palette` parsed a palette
file and, on any failure, called `show_warning_dialog` / `show_error_dialog`
from inside the same function. A modal dialog does not return without a
user, so in any headless context -- CI, a test, a batch script -- the
function **blocked forever**. Measured: a valid `.gpl` returned fine;
missing, empty and garbage input all hung, with

    This plugin does not support propagateSizeHints()

printed on the way in.

WHAT WAS RECORDED INSTEAD. A test named `test_auto_detect_palette_skipped`,
body `pass`, carrying

    @pytest.mark.skip(reason="Native crash on offscreen Qt -- see Phase 8.7")

It is not a crash, it is a hang, and the difference matters: a crash gets
noticed, a hang gets a CI job cancelled an hour later and blamed on the
runner. And a skipped `pass` measures nothing, so the note was the only
thing that test ever contributed.

THREE TESTS, NONE OF THEM ENTERING THE FUNCTION. The locked
`test_rnv_color_mixer.py` also calls this function twice:

    r = FileUtils.auto_detect_and_import_palette("/no/such.xyz")

on the CLASS, with one argument, so `filepath` is never supplied. Both raise
`TypeError: missing 1 required positional argument` and both swallow it with
`except Exception: pass`. That is why the locked suite never hung: it never
called the function. Those two are in the locked file and are left alone
here; this note is the record that they measure nothing.

THE RULE THIS GUARD ENFORCES. A function may read a file, or it may show a
dialog. Not both. `import_palette_data` does the work and returns
`(colors, problem)`; `auto_detect_and_import_palette` keeps its name, its
return and both dialogs, and does no parsing of its own. Callers are
untouched, and the locked file still sees the identical TypeError.

Note what is NOT in the rule: showing a dialog is fine, and so is taking a
filepath. `show_format_info_dialog` does both -- it splits the extension off
the path and shows a lookup from a table. It never opens the file, so it
cannot block on anything but its own dialog, which is its whole purpose. The
rule is about reading CONTENTS, and it was written by checking it against
every dialog-showing function in the module rather than against the one that
prompted it.

THE SWEEP IS SCOPED TO utils/file_utils.py, AND THERE IS A KNOWN VIOLATION
OUTSIDE IT. `ImageHandler.load_image` in core/image_handler.py has the same
defect and is not fixed by this round:

    if file_size_mb > 10:
        reply = QMessageBox.question(None, "Large Image File", ...)

`resources/background_images/background.png` is 10.1 MB, so the threshold
trips, the modal question blocks, and the load never returns. That is the
whole of `test_load_real_image_if_available`, which KNOWN_ISSUES.md records
as skipped on BOTH runners with "Planned fix: None required. This is a
test-environment artifact, not a code defect." It is a code defect, of
exactly the kind this rule names.

It is left out rather than quietly excluded: `load_image` is a hundred lines
on the application's main image path, and prising the confirmation out of it
is a bigger change than the one this round is carrying. FILES below is the
list to extend when that lands. A guard that had simply pointed at the file
it happened to pass on would have hidden this.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FILE_UTILS = ROOT / "utils" / "file_utils.py"

#: The modules the rule is enforced over. core/image_handler.py belongs here
#: and is not in it yet -- see the module docstring. Adding it before
#: load_image is split would make this guard red on arrival, which is how a
#: guard gets an exemption written into it and stops meaning anything.
FILES = (FILE_UTILS,)

PURE = "import_palette_data"
WRAPPER = "auto_detect_and_import_palette"

#: Calls that mean "this function reads a file's contents". Splitting an
#: extension off a path does not count, and neither does a lookup table.
READS_CONTENT = ("open", "import_palette", "read_text", "read_bytes",
                 "load", "loads", "readlines", "read")


def _functions():
    src = FILE_UTILS.read_text(encoding="utf-8")
    return src, ast.parse(src, str(FILE_UTILS))


def _fn(name: str):
    src, tree = _functions()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _shows_dialog(node) -> list[str]:
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            attr = getattr(n.func, "attr", "")
            if attr.startswith("show_") and "dialog" in attr:
                out.append(attr)
    return out


def _reads_content(node) -> list[str]:
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            name = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if name in READS_CONTENT:
                out.append(name)
    return out


def _fu():
    from utils.file_utils import FileUtils
    return FileUtils()


# ═══════════════════════════════════════════════════════════════════════
# the rule, stated over every function in the module
# ═══════════════════════════════════════════════════════════════════════

def test_no_function_both_reads_a_file_and_shows_a_dialog():
    """The general rule, not a special case for the one that prompted it.

    Checked across the whole module, because the next one to acquire a
    dialog on its error path will not be this one, and a rule written about
    a single function is a rule that only ever catches that function.
    """
    src, tree = _functions()
    bad = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        shows = _shows_dialog(node)
        reads = _reads_content(node)
        if shows and reads:
            bad.append(f"{node.name} (line {node.lineno}): "
                       f"shows {sorted(set(shows))}, reads {sorted(set(reads))}")

    assert not bad, (
        "these functions read a file and show a dialog in the same body:\n  "
        + "\n  ".join(bad)
        + "\n\nA modal dialog never returns without a user, so this blocks "
          "forever anywhere there is no one to click it -- CI, a test, a "
          "batch script. Split it: one function returns the result, another "
          "presents it. See import_palette_data / "
          "auto_detect_and_import_palette.")


def test_the_data_path_shows_nothing():
    """The specific half of the rule, so the message names the function."""
    node = _fn(PURE)
    assert node is not None, f"{PURE} is gone from utils/file_utils.py"

    shows = _shows_dialog(node)
    assert not shows, (
        f"{PURE} calls {sorted(set(shows))}. This is the half that has to be "
        f"callable with nobody watching; put the dialog in the wrapper.")


def test_the_wrapper_still_shows_both_dialogs():
    """No feature was removed, and this is what says so.

    A split that quietly dropped the dialogs would pass every other test
    here and would change what the user sees on a bad file.
    """
    node = _fn(WRAPPER)
    assert node is not None, f"{WRAPPER} is gone; callers depend on it"

    shows = set(_shows_dialog(node))
    assert "show_warning_dialog" in shows, (
        f"{WRAPPER} no longer warns on a file with no usable colours")
    assert "show_error_dialog" in shows, (
        f"{WRAPPER} no longer reports an import failure to the user")


def test_the_wrapper_delegates_rather_than_reimplementing():
    """One copy of the logic.

    A wrapper that parsed the file itself would satisfy every assertion
    above and would drift out of step with the function it shadows.
    """
    node = _fn(WRAPPER)
    assert node is not None

    calls = {getattr(n.func, "attr", getattr(n.func, "id", ""))
             for n in ast.walk(node) if isinstance(n, ast.Call)}
    assert PURE in calls, (
        f"{WRAPPER} does not call {PURE}; the parsing logic has been "
        f"duplicated rather than shared")

    reads = _reads_content(node)
    assert not reads, (
        f"{WRAPPER} reads the file itself ({sorted(set(reads))}) as well as "
        f"delegating. That is two implementations of one thing.")


# ═══════════════════════════════════════════════════════════════════════
# behaviour
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.timeout(60)
def test_every_bad_input_returns_instead_of_blocking(tmp_path):
    """The reproduction, as a test.

    Each of these blocked forever before the split. Sixty seconds is not a
    performance budget -- these run in milliseconds -- it is the line
    between slow and never, wide enough that a cold runner cannot make it
    flaky.
    """
    cases = {
        "missing.gpl": None,
        "empty.gpl": b"",
        "garbage.pal": b"\xa4\x00\xff\xfe" * 64,
        "truncated.json": b'{"colors": [',
    }
    fu = _fu()
    for name, content in cases.items():
        target = tmp_path / name
        if content is not None:
            target.write_bytes(content)

        colors, problem = fu.import_palette_data(str(target))

        assert colors is None, f"{name} produced colours: {colors!r}"
        assert problem is not None, f"{name} reported no problem"


@pytest.mark.timeout(60)
def test_a_good_palette_still_imports(tmp_path):
    """Without this, "does not block" could be satisfied by doing nothing."""
    target = tmp_path / "ok.gpl"
    target.write_bytes(b"GIMP Palette\nName: t\n#\n255 0 0 Red\n")

    colors, problem = _fu().import_palette_data(str(target))

    assert problem is None, f"a valid palette reported: {problem}"
    assert colors, "a valid palette imported no colours"


@pytest.mark.timeout(60)
def test_the_severity_is_returned_not_left_to_the_caller_to_guess(tmp_path):
    """The caller has to choose between a warning and an error dialog.

    Returning only a message would push that decision onto whoever reads the
    string, which is how a wrapper ends up matching on display text.
    """
    empty = tmp_path / "empty.gpl"
    empty.write_bytes(b"")
    _, problem = _fu().import_palette_data(str(empty))
    assert problem is not None
    assert len(problem) == 3, f"expected (severity, title, message), got {problem!r}"
    severity, title, message = problem
    assert severity in ("warning", "error"), f"unknown severity {severity!r}"
    assert title and message, "the caller was given nothing to display"

    missing = tmp_path / "nope.gpl"
    _, problem = _fu().import_palette_data(str(missing))
    assert problem is not None
    assert problem[0] in ("warning", "error")


def test_this_guard_can_see_the_file_it_judges():
    """A sweep that finds nothing passes every assertion above."""
    assert FILE_UTILS.exists(), f"{FILE_UTILS} is not where this guard looks"
    src, tree = _functions()
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert len(functions) >= 20, (
        f"only {len(functions)} functions found in file_utils.py; the guard "
        f"is probably reading the wrong file")
    assert any(_shows_dialog(n) for n in functions), (
        "no function in file_utils.py shows a dialog at all, which means the "
        "rule above has no subject and is passing vacuously")
'''

EDITS = [('utils/file_utils.py', '    def auto_detect_and_import_palette(self, filepath: str) -> list[tuple[tuple[int, int, int], int]] | None:\n        """\n        Auto-detect palette format and import.\n        \n        Args:\n            filepath: Path to palette file\n            \n        Returns:\n            List of (color, weight) tuples or None if failed\n        """\n        try:\n            from core.palette_formats import PaletteFormats\n            \n            # Try to detect format\n            detected_ext = PaletteFormats.detect_format(filepath)\n            if detected_ext:\n                logger.debug(f"Detected format: {detected_ext}")\n            \n            # Import palette\n            colors = PaletteFormats.import_palette(filepath)\n            \n            if colors:\n                # Validate colors\n                colors = PaletteFormats.validate_colors(colors)\n                return colors\n            else:\n                self.show_warning_dialog(\n                    "Import Warning",\n                    "No valid colors found in the file."\n                )\n                return None\n                \n        except Exception as e:\n            self.show_error_dialog(\n                "Import Error",\n                f"Failed to import palette:\\n{str(e)}"\n            )\n            return None', '    def import_palette_data(self, filepath: str) -> tuple[list[tuple[tuple[int, int, int], int]] | None, tuple[str, str, str] | None]:\n        """Auto-detect palette format and import. Shows nothing, ever.\n\n        RNV-PALETTE-IMPORT, 2026-09-10. See tests/test_palette_import.py.\n\n        Returns:\n            (colors, problem). `colors` is a list of (color, weight) tuples,\n            or None. `problem` is None on success, otherwise\n            (severity, title, message) with severity \'warning\' or \'error\'.\n\n        The severity is returned explicitly rather than inferred from the\n        title: a title is display text and will be reworded one day, and a\n        caller that dispatched on it would then quietly show the wrong kind\n        of dialog.\n\n        This half exists so the import can be driven from a test, a script\n        or any headless context. `auto_detect_and_import_palette` below is\n        unchanged for callers and still shows the dialogs.\n        """\n        try:\n            from core.palette_formats import PaletteFormats\n            \n            # Try to detect format\n            detected_ext = PaletteFormats.detect_format(filepath)\n            if detected_ext:\n                logger.debug(f"Detected format: {detected_ext}")\n            \n            # Import palette\n            colors = PaletteFormats.import_palette(filepath)\n            \n            if colors:\n                # Validate colors\n                colors = PaletteFormats.validate_colors(colors)\n                return colors, None\n            \n            return None, ("warning", "Import Warning",\n                          "No valid colors found in the file.")\n                \n        except Exception as e:\n            return None, ("error", "Import Error",\n                          f"Failed to import palette:\\n{str(e)}")\n\n    def auto_detect_and_import_palette(self, filepath: str) -> list[tuple[tuple[int, int, int], int]] | None:\n        """\n        Auto-detect palette format and import.\n        \n        Args:\n            filepath: Path to palette file\n            \n        Returns:\n            List of (color, weight) tuples or None if failed\n        """\n        colors, problem = self.import_palette_data(filepath)\n        if problem is not None:\n            severity, title, message = problem\n            if severity == "warning":\n                self.show_warning_dialog(title, message)\n            else:\n                self.show_error_dialog(title, message)\n        return colors', 1), ('tests/test_error_recovery_paths.py', 'class TestFileUtilsPaletteImport:\n    """`auto_detect_and_import_palette` invokes specific format\n    importers that crash hard on certain inputs in offscreen Qt\n    (likely because of QPixmap reading from binary palette formats).\n    Skipped — covered transitively by integration tests already."""\n\n    @pytest.mark.skip(\n        reason="Native crash on offscreen Qt — see Phase 8.7 report"\n    )\n    def test_auto_detect_palette_skipped(self):\n        pass\n\n\n', 'class TestFileUtilsPaletteImport:\n    """Driving the palette import for real, which nothing did before.\n\n    RESTORED 2026-09-10 (RNV-PALETTE-IMPORT). What stood here was a single\n    method named `test_auto_detect_palette_skipped` whose body was `pass`,\n    carrying `@pytest.mark.skip(reason="Native crash on offscreen Qt")`.\n\n    Two things were wrong with that. It measured nothing — a skipped `pass`\n    reports as a skip and covers no line. And the reason was wrong: the\n    function does not crash, it **hangs**. Its failure path called\n    `show_warning_dialog` / `show_error_dialog`, and a modal dialog never\n    returns without a user. Valid input returned fine; missing, empty and\n    garbage input all blocked forever.\n\n    Nor was it the only test that looked like coverage here. The locked\n    `test_rnv_color_mixer.py` calls `FileUtils.auto_detect_and_import_palette`\n    twice — unbound, with one argument — so both raise\n    `TypeError: missing 1 required positional argument` and both swallow it\n    with `except Exception: pass`. Three tests named after this function, and\n    not one of them entered it.\n\n    `import_palette_data` is the same work with the dialogs lifted out. The\n    wrapper keeps its name, its return and its dialogs, so callers and the\n    locked file see no change at all.\n    """\n\n    @staticmethod\n    def _fu():\n        from utils.file_utils import FileUtils\n        return FileUtils()\n\n    @pytest.mark.timeout(60)\n    def test_a_valid_palette_imports(self, tmp_path):\n        out = tmp_path / "ok.gpl"\n        out.write_bytes(b"GIMP Palette\\nName: t\\n#\\n255 0 0 Red\\n")\n\n        colors, problem = self._fu().import_palette_data(str(out))\n\n        assert problem is None, f"a valid palette reported a problem: {problem}"\n        assert colors, "a valid palette imported no colors"\n\n    @pytest.mark.timeout(60)\n    @pytest.mark.parametrize("name,content", [\n        ("missing.gpl", None),\n        ("empty.gpl", b""),\n        ("garbage.pal", b"\\xa4\\x00\\xff\\xfe" * 64),\n        ("empty.json", b""),\n    ])\n    def test_bad_input_returns_a_problem_instead_of_blocking(\n        self, tmp_path, name, content\n    ):\n        """The whole point. Each of these used to block forever.\n\n        The timeout is the assertion that matters: a regression that puts a\n        dialog back on this path fails the test in a minute instead of\n        hanging CI until someone notices.\n\n        Sixty seconds, not five, on purpose. The bodies here run in under\n        five milliseconds; the number is not a performance budget, it is the\n        line between "slow" and "never". A tight bound would only buy the\n        chance of a false failure on a cold runner.\n        """\n        target = tmp_path / name\n        if content is not None:\n            target.write_bytes(content)\n\n        colors, problem = self._fu().import_palette_data(str(target))\n\n        assert colors is None, f"{name} produced colors: {colors!r}"\n        assert problem is not None, f"{name} reported no problem"\n        severity, title, message = problem\n        assert severity in ("warning", "error"), f"unknown severity {severity!r}"\n        assert title and message, f"{name} gave an empty {title!r}/{message!r}"\n\n    @pytest.mark.timeout(60)\n    def test_the_import_never_raises(self, tmp_path):\n        """It reports; it does not throw.\n\n        Callers treat a None return as "no palette". A function that raises\n        instead would take the caller down, and the original swallowed\n        everything precisely to avoid that.\n        """\n        target = tmp_path / "a-directory-not-a-file.gpl"\n        target.mkdir()\n\n        colors, problem = self._fu().import_palette_data(str(target))\n\n        assert colors is None\n        assert problem is not None\n\n\n', 1), ('KNOWN_ISSUES.md', '**User impact:** None. Production users always run with a real display\nserver, where the load completes instantly. The test passes in the local\ndevelopment environment for the same reason.\n\n**Planned fix:** None required. This is a test-environment artifact, not\na code defect.', '**User impact:** None *on a desktop*. The dialog below is shown and the\nuser clicks through it.\n\n**This is a code defect, not a test-environment artifact.** Corrected\n2026-09-10; the previous wording said "Planned fix: None required. This is\na test-environment artifact, not a code defect", and that is wrong.\n`ImageHandler.load_image` calls\n\n```python\nif file_size_mb > 10:\n    reply = QMessageBox.question(None, "Large Image File", ...)\n```\n\n`resources/background_images/background.png` is 10.1 MB, so the threshold\ntrips and a **modal question dialog** opens inside a data-loading function.\nA modal dialog never returns without a user, so the load never completes\nanywhere there is nobody to click it. Reproduced directly: the call blocks\nuntil killed, printing `This plugin does not support propagateSizeHints()`\non the way in. Nothing about the CI runner is at fault; the same call blocks\nin any headless context.\n\n**Planned fix:** the same split applied to the palette importer on\n2026-09-10 — the function that reads the file returns a result, and the\ncaller decides whether to ask the user. `tests/test_palette_import.py`\nstates the rule and names this as the outstanding violation.\n**Not fixed yet:** `load_image` is a hundred lines on the main image path\nand deserves its own round.', 1)]

PURE = "import_palette_data"
WRAPPER = "auto_detect_and_import_palette"
READS_CONTENT = ("open", "import_palette", "read_text", "read_bytes",
                 "load", "loads", "readlines", "read")


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL in src:
        raise SystemExit(f"already applied -- '{SENTINEL}' is present in "
                         f"{SENTINEL_FILE}")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)

    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))


def _shows(node) -> list:
    return [getattr(n.func, "attr", "") for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "").startswith("show_")
            and "dialog" in getattr(n.func, "attr", "")]


def _reads(node) -> list:
    return [getattr(n.func, "attr", getattr(n.func, "id", ""))
            for n in ast.walk(node) if isinstance(n, ast.Call)
            and getattr(n.func, "attr", getattr(n.func, "id", "")) in READS_CONTENT]


def checks(tree) -> None:
    fu = tree.files["utils/file_utils.py"]
    erp = tree.files["tests/test_error_recovery_paths.py"]

    # 1. both files parse, or every check below is vacuous rather than red.
    for rel, text in (("utils/file_utils.py", fu),
                      ("tests/test_error_recovery_paths.py", erp)):
        try:
            ast.parse(text, rel)
        except SyntaxError as e:
            raise SystemExit(f"{rel} does not parse after the edits: {e}")

    tree_fu = ast.parse(fu)
    funcs = {n.name: n for n in ast.walk(tree_fu) if isinstance(n, ast.FunctionDef)}

    # 2. the rule, over the whole module rather than the one function that
    #    prompted it. Checked here as well as in the installed guard so a
    #    broken tree is refused before anything is written.
    bad = []
    for name, node in funcs.items():
        shows, reads = _shows(node), _reads(node)
        if shows and reads:
            bad.append(f"{name}: shows {sorted(set(shows))}, reads {sorted(set(reads))}")
    if bad:
        raise SystemExit("a function still reads a file and shows a dialog: "
                         + "; ".join(bad))

    # 3. the pure half is silent and the wrapper still speaks. Both halves
    #    matter: a split that dropped the dialogs would pass the rule above
    #    and would change what a user sees on a bad file.
    if PURE not in funcs:
        raise SystemExit(f"{PURE} did not land")
    if _shows(funcs[PURE]):
        raise SystemExit(f"{PURE} shows a dialog; it is the half that has to "
                         f"be callable with nobody watching")
    if WRAPPER not in funcs:
        raise SystemExit(f"{WRAPPER} is gone; callers depend on it")
    kept = set(_shows(funcs[WRAPPER]))
    for needed in ("show_warning_dialog", "show_error_dialog"):
        if needed not in kept:
            raise SystemExit(f"{WRAPPER} no longer calls {needed} -- that is a "
                             f"feature removed, not a refactor")

    # 4. the wrapper delegates rather than keeping a second copy of the parse.
    calls = {getattr(n.func, "attr", getattr(n.func, "id", ""))
             for n in ast.walk(funcs[WRAPPER]) if isinstance(n, ast.Call)}
    if PURE not in calls:
        raise SystemExit(f"{WRAPPER} does not call {PURE}; the logic has been "
                         f"duplicated rather than shared")

    # 5. the placeholder is gone and what replaced it actually drives the
    #    function. A skipped `pass` is what this round exists to remove.
    tree_erp = ast.parse(erp)
    klass = next((n for n in tree_erp.body if isinstance(n, ast.ClassDef)
                  and n.name == "TestFileUtilsPaletteImport"), None)
    if klass is None:
        raise SystemExit("TestFileUtilsPaletteImport did not survive the rewrite")
    skipped = [f.name for f in klass.body if isinstance(f, ast.FunctionDef)
               and any("skip" in ast.unparse(d) for d in f.decorator_list)]
    if skipped:
        raise SystemExit(f"tests are still skipped: {skipped}")
    tests = [f for f in klass.body if isinstance(f, ast.FunctionDef)
             and f.name.startswith("test_")]
    if len(tests) < 3:
        raise SystemExit(f"only {len(tests)} tests replaced the placeholder")
    for f in tests:
        body = ast.unparse(f)
        if "pass" == body.strip().splitlines()[-1].strip():
            raise SystemExit(f"{f.name} still has an empty body")
    if PURE not in erp:
        raise SystemExit("the replacement tests do not call the function")

    # 6. a hang cannot be caught by waiting, so every drive carries a bound.
    if "timeout" not in erp:
        raise SystemExit("the replacement tests carry no timeout; a "
                         "regression would hang CI rather than fail it")

    # 7. the prose. Collapsed whitespace, because markdown wraps where the
    #    width runs out and a check has failed here before on a line break.
    ki = " ".join(tree.files["KNOWN_ISSUES.md"].split())
    if "test-environment artifact, not a code defect" in ki and "is wrong" not in ki:
        raise SystemExit("KNOWN_ISSUES.md still calls the image-load hang a "
                         "test-environment artifact")
    if "test_palette_import.py" not in ki:
        raise SystemExit("KNOWN_ISSUES.md does not name the guard")

    # 8. the sentinel is in the file the re-run check reads. Shipped broken
    #    once: the script applied everything and then died on a missing
    #    anchor because the already-applied guard could never fire.
    if SENTINEL not in fu:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")

    print("  guards: the data path is silent, both dialogs kept, "
          "placeholder replaced by 6 bounded tests")


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
