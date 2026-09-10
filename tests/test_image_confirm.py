"""RNV-IMAGE-CONFIRM-GUARD -- the load reads the file; the caller asks.

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
