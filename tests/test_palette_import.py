"""RNV-PALETTE-IMPORT-GUARD -- read the file, or show the dialog. Not both.

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
