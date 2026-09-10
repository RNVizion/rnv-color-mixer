#!/usr/bin/env python3
"""RNV-HISTORY-WRITER — a save must not destroy the save before it.

    python up.py             # apply, then run the guard and both suites
    python up.py --check     # rehearse every edit in memory, write nothing
    
git checkout -- core/color_history.py tests/test_error_recovery_paths.py KNOWN_ISSUES.md
rm -f tests/test_history_writer_ownership.py


Derived against a fresh clone of rnv-color-mixer at head 61ecf57.

WHAT WAS WRONG. `ColorHistory.save_async()` ended in

    self._save_thread = FileWriterThread(self.history_file, data, 'json')
    self._save_thread.start()

That assignment is the only Python reference to the previous writer. A
second save while the first is still writing therefore drops a **running
QThread**, and Qt aborts the process for that — `QThread: Destroyed while
thread is still running`, SIGABRT, exit 134.

Not a race and not a test artifact. Reproduced through the product API
alone, no pytest and no fixtures, **five times in five**:

    ch = ColorHistory(); ch.clear(); ch.add_color((100, 150, 200))

`clear()` and `add_color()` each call `save_async()`, and both are ordinary
application paths: `RNV_Color_Mixer.py` adds a colour on every mix,
`core/package_d_panel.py` clears the history from the panel. Sixty rapid
saves with no `cleanup()` at all now survive; before, three in three
aborted.

WHAT THIS COST FOR A YEAR. Six tests in `tests/test_error_recovery_paths.py`
carried a class-level skip whose reason said the crash was **Windows-only**
and that the fault lay in "the test harness's interaction with that
thread". `KNOWN_ISSUES.md` recorded **User impact: None**. It reproduces on
Linux, deterministically, through the product's own API, with no harness
present. The tests were right and were skipped for it.

WORSE, AND CORRECTED HERE. The thread-ownership round — mine — wrote into
`KNOWN_ISSUES.md` that "the application itself never had the bug, because
`ColorHistory` holds `_save_thread` on the object ... and checks
`isRunning()` before letting go". `ColorHistory` does hold the thread on the
object. `save_async()` then overwrites that attribute on the next save
without checking anything. Both prose claims are corrected by this round.

THE FIX. A writer is retained until Qt reports it finished, and released on
the next save and in `cleanup()`. `isFinished()` is asked rather than the
`finished` signal, because `FileWriterThread` declares

    finished = pyqtSignal(bool, str)

which SHADOWS `QThread.finished()` and is emitted from inside `run()`, so it
fires while the QThread is still running. That shadowing is the same one the
thread-ownership round found behind seventeen test sites; this is the same
defect in the product rather than the tests.

THE SIX TESTS. They build their histories through a `history_factory`
fixture that calls `cleanup()` on every instance it hands out, so a dropped
instance cannot take the process down. Both halves are load-bearing:
verified by discriminating, the fixture WITHOUT the product fix still aborts
3 times in 3.

One of them additionally waits for the background writes to settle. Its
original note said the round-trip was timing-dependent "because add_color
triggers save_async, so we test save() directly" — but calling `save()`
directly is not enough, because the writes started by `clear()` and
`add_color()` land *after* the synchronous one. Without the wait,
`json.load()` read a half-written file **9 times in 20**. With it, 0 in 25.

NOT FIXED HERE, AND DELIBERATELY. Two async writers can still interleave on
the same path if two saves are started close together, so a history file
could in principle be written by both. In production `save()` is only ever
reached as the no-async fallback, so the sync/async race the test hit cannot
occur there. Left alone rather than folded in: an atomic write-and-rename in
`FileWriterThread` would fix it, and that class is covered by the LOCKED
suite, which is not something to change in passing.
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
SENTINEL_FILE = "core/color_history.py"
SENTINEL = "RNV-HISTORY-WRITER"
GUARD = "tests/test_history_writer_ownership.py"
DESCRIPTION = "stop a save destroying the save before it"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, 355 tests\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-HISTORY-WRITER-GUARD -- a save must not destroy the save before it.

Installed 2026-09-09, un-skipping six tests that had been skipped since
Phase 9.3 and fixing the product defect that was the real reason they could
not run.

WHAT WAS WRONG. `ColorHistory.save_async()` did

    self._save_thread = FileWriterThread(self.history_file, data, 'json')
    self._save_thread.start()

The assignment is the only Python reference to the previous writer, so a
second save while the first is still writing drops a **running QThread**.
Qt aborts the process for that -- `QThread: Destroyed while thread is still
running`, SIGABRT, exit 134.

Not a test artifact and not a race. Reproduced through the product API
alone, no pytest and no fixtures, five times in five:

    ch = ColorHistory(); ch.clear(); ch.add_color((100, 150, 200))

`clear()` and `add_color()` each call `save_async()`. Both are ordinary
application paths -- `RNV_Color_Mixer.py` adds a colour on every mix,
`core/package_d_panel.py` clears the history from the panel.

The skip reason on those six tests said the crash was Windows-only. It
reproduces on Linux, deterministically.

THE FIX. A writer is retained until Qt reports it finished, and released on
the next save and in `cleanup()`. `isFinished()` is asked rather than the
`finished` signal, because `FileWriterThread` declares
`finished = pyqtSignal(bool, str)`, which SHADOWS `QThread.finished()` and
is emitted from inside `run()` -- so it fires while the QThread is still
running. That is the same shadowing the thread-ownership round found behind
seventeen test sites; this is the same defect in the product.

WHAT THIS GUARD CANNOT DO GENTLY. A regression here does not fail a test,
it aborts the interpreter. `test_a_history_survives_rapid_saves` runs the
exact sequence that used to abort, so on a regressed build the suite dies
with exit 134 rather than printing a diff. That is loud and ugly and it is
the correct failure: the defect being guarded is an abort.

Which is why the cheap static check is deliberately FIRST in this file.
pytest runs tests in definition order, and both tampering experiments --
removing the retention, and moving it after the reassignment -- fail that
check with a readable message (`assert None is not None`, `assert 210 <
206`) before the behavioural test gets far enough to kill the run. Ordering
is load-bearing here; do not sort these alphabetically.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "core" / "color_history.py"
RESTORED = ROOT / "tests" / "test_error_recovery_paths.py"


def _fn(path: Path, name: str):
    """The FunctionDef called `name` in `path`, or None."""
    tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _history(real_color_history, tmp_path, **kwargs):
    """A real ColorHistory on a temp file, entries emptied."""
    ch = real_color_history(**kwargs)
    ch.history_file = str(tmp_path / "guard_history.json")
    ch.entries = []
    ch._save_thread = None
    return ch


def _quiet(ch) -> bool:
    current = getattr(ch, "_save_thread", None)
    if current is not None and current.isRunning():
        return False
    return not any(w.isRunning() for w in getattr(ch, "_pending_writers", []))


# ═══════════════════════════════════════════════════════════════════════
# the product
# ═══════════════════════════════════════════════════════════════════════

def test_save_async_retains_before_it_reassigns():
    """Order matters, and only the source can show it.

    Retaining the previous writer *after* rebinding `_save_thread` retains
    the new one and drops the old -- which reads almost identically and
    fixes nothing.
    """
    node = _fn(HISTORY, "save_async")
    assert node is not None, "save_async is gone from core/color_history.py"

    retain = assign = None
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and n.attr == "_pending_writers":
            if retain is None or n.lineno < retain:
                retain = n.lineno
        if (isinstance(n, ast.Assign) and n.targets
                and isinstance(n.targets[0], ast.Attribute)
                and n.targets[0].attr == "_save_thread"):
            if assign is None or n.lineno < assign:
                assign = n.lineno

    assert retain is not None, (
        "save_async no longer retains anything. The previous writer is "
        "dropped when `_save_thread` is rebound, and a running QThread "
        "destroyed that way aborts the process.")
    assert assign is not None, "save_async no longer assigns _save_thread"
    assert retain < assign, (
        f"save_async touches _pending_writers at line {retain}, after it "
        f"rebinds _save_thread at line {assign}. Retaining after the "
        f"reassignment retains the new writer and drops the old one.")


def test_a_history_survives_rapid_saves(real_color_history, tmp_path, qtbot):
    """The reproduction, as a test.

    Two saves close together used to abort the process here, five times in
    five. If this regresses, the run dies rather than fails -- see the
    module docstring.
    """
    ch = _history(real_color_history, tmp_path)
    try:
        ch.clear()
        ch.add_color((100, 150, 200))
        ch.add_color((10, 20, 30))
        ch.add_color((40, 50, 60))
        qtbot.waitUntil(lambda: _quiet(ch), timeout=5000)
    finally:
        ch.cleanup()

    assert os.path.exists(ch.history_file), (
        "four rapid saves left no file behind")


def test_save_async_keeps_the_writer_it_replaces(
    real_color_history, tmp_path, qtbot
):
    """The mechanism, not just the absence of a crash.

    Without this, a fix that made saves synchronous -- or dropped the second
    save entirely -- would also stop the abort and would also be wrong.
    """
    ch = _history(real_color_history, tmp_path)
    try:
        ch.save_async()
        first = ch._save_thread
        assert first is not None, "save_async did not start a writer at all"

        ch.save_async()
        second = ch._save_thread
        assert second is not first, (
            "the second save reused the first writer; it must start its own")

        if first.isRunning():
            assert first in getattr(ch, "_pending_writers", []), (
                "the first writer was still running and was not retained. "
                "Dropping it destroys a running QThread, which aborts the "
                "process.")

        qtbot.waitUntil(lambda: _quiet(ch), timeout=5000)
    finally:
        ch.cleanup()


def test_cleanup_waits_for_retired_writers_too(
    real_color_history, tmp_path, qtbot
):
    """A retired writer left running at shutdown is just as fatal.

    cleanup() handled `_save_thread` only. If it still does, a history torn
    down mid-write takes the process with it at interpreter exit -- which is
    exactly the close-time crash cleanup() was written for.
    """
    ch = _history(real_color_history, tmp_path)
    ch.clear()
    ch.add_color((1, 2, 3))
    ch.add_color((4, 5, 6))

    ch.cleanup()

    assert ch._save_thread is None, "cleanup left the current writer attached"
    assert not any(w.isRunning() for w in getattr(ch, "_pending_writers", [])), (
        "cleanup returned with a retired writer still running")


# ═══════════════════════════════════════════════════════════════════════
# the six restored tests
# ═══════════════════════════════════════════════════════════════════════

def test_the_colorhistory_tests_are_not_skipped():
    """They were skipped for a year for a defect that is now fixed."""
    tree = ast.parse(RESTORED.read_text(encoding="utf-8"), str(RESTORED))
    target = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "TestColorHistoryLoadExport":
            target = node
    assert target is not None, (
        "TestColorHistoryLoadExport is gone. If it was deleted rather than "
        "un-skipped, this guard has no subject and should go with it.")

    skips = [ast.unparse(d) for d in target.decorator_list
             if "skip" in ast.unparse(d)]
    assert not skips, (
        "TestColorHistoryLoadExport is skipped again:\n  "
        + "\n  ".join(skips)
        + "\n\nThe defect behind the original skip -- save_async destroying "
          "a running writer -- is fixed. If a new reason has appeared, it "
          "needs its own diagnosis, not the old decorator back.")

    tests = [f.name for f in target.body if isinstance(f, ast.FunctionDef)]
    assert len(tests) >= 6, (
        f"expected the six restored tests, found {len(tests)}: {tests}")

    inner = [f.name for f in target.body if isinstance(f, ast.FunctionDef)
             and any("skip" in ast.unparse(d) for d in f.decorator_list)]
    assert not inner, f"individual tests are skipped again: {inner}"


def test_every_restored_test_gets_cleanup():
    """The fixture is what makes them safe; a test that bypasses it is not.

    A ColorHistory dropped with a write in flight destroys a running
    QThread. `history_factory` cleans up every instance it makes, so the
    rule is simply that these tests build their histories through it.
    """
    tree = ast.parse(RESTORED.read_text(encoding="utf-8"), str(RESTORED))
    target = next(n for n in tree.body
                  if isinstance(n, ast.ClassDef)
                  and n.name == "TestColorHistoryLoadExport")

    direct = []
    for fn in [f for f in target.body if isinstance(f, ast.FunctionDef)]:
        for n in ast.walk(fn):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "ColorHistory"):
                direct.append(f"{fn.name}:{n.lineno}")
    assert not direct, (
        "these tests build a ColorHistory directly instead of through "
        "history_factory, so nothing cleans it up:\n  " + "\n  ".join(direct))

    factory = _fn(RESTORED, "history_factory")
    assert factory is not None, "the history_factory fixture is gone"
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == "cleanup" for n in ast.walk(factory)), (
        "history_factory no longer calls cleanup(). Every instance it hands "
        "out can then take the process down when it is collected.")


def test_this_guard_can_see_the_files_it_judges():
    """A sweep that finds nothing passes every assertion above."""
    assert HISTORY.exists(), f"{HISTORY} is not where this guard looks"
    assert RESTORED.exists(), f"{RESTORED} is not where this guard looks"
    assert _fn(HISTORY, "save_async") is not None
    assert _fn(HISTORY, "cleanup") is not None
'''

EDITS = [('core/color_history.py', '    def save_async(self, on_complete: callable = None) -> None:\n', '    def _release_finished_writers(self) -> None:\n        """Drop references to writers Qt has finished with.\n\n        RNV-HISTORY-WRITER, 2026-09-09. See\n        tests/test_history_writer_ownership.py.\n\n        isFinished() is asked rather than the `finished` signal, because this\n        thread class declares `finished = pyqtSignal(bool, str)`, which\n        SHADOWS QThread.finished() and is emitted from inside run() -- so it\n        fires while the QThread is still running. tests/test_threading.py\n        waits on the same state for the same reason.\n        """\n        pending = getattr(self, \'_pending_writers\', None)\n        if pending is None:\n            pending = self._pending_writers = []\n        self._pending_writers = [t for t in pending if not t.isFinished()]\n\n    def save_async(self, on_complete: callable = None) -> None:\n', 1), ('core/color_history.py', "            # Create and start writer thread\n            self._save_thread = FileWriterThread(self.history_file, data, 'json')\n", "            # Retire the previous writer rather than dropping it. Replacing\n            # self._save_thread while its QThread is still running destroys a\n            # running QThread, which aborts the process: reproduced 5 times in\n            # 5 with clear() followed by add_color(), on Linux and Windows\n            # alike. Finished writers are released on the next save and on\n            # cleanup(), so this list stays short.\n            self._release_finished_writers()\n            previous = getattr(self, '_save_thread', None)\n            if previous is not None and previous.isRunning():\n                self._pending_writers.append(previous)\n\n            # Create and start writer thread\n            self._save_thread = FileWriterThread(self.history_file, data, 'json')\n", 1), ('core/color_history.py', "            # Stop any running save thread\n            if hasattr(self, '_save_thread') and self._save_thread:\n", "            # Stop any running save thread, current and retired alike. A\n            # writer left behind by a rapid second save is just as fatal at\n            # interpreter shutdown as the current one.\n            for writer in list(getattr(self, '_pending_writers', [])):\n                if writer.isRunning():\n                    writer.quit()\n                    writer.wait(1000)\n            self._pending_writers = []\n\n            if hasattr(self, '_save_thread') and self._save_thread:\n", 1), ('tests/test_error_recovery_paths.py', '@pytest.mark.integration\n@pytest.mark.skip(\n    reason="ColorHistory\'s constructor + add_color() + save() chain "\n    "spawns a QThread for async filesystem writes that crashes Python "\n    "natively on Windows (no traceback, no exit code, just a dead "\n    "process). The locked test_rnv_color_mixer.py works around this by "\n    "module-level-mocking ColorHistory.__init__/load/save_async at "\n    "import time. These integration-style tests can\'t easily replicate "\n    "that pattern without mocking out the very methods they\'re trying "\n    "to verify. Phase 9.3 finding — kept for documentation; future "\n    "refactor could split the QThread machinery off from ColorHistory "\n    "construction so synchronous behavior is testable in isolation."\n)\nclass TestColorHistoryLoadExport:\n    """ColorHistory\'s load() and export_to_file() have format-specific\n    branches that need explicit drives."""\n\n    def test_load_with_no_existing_file_returns_false_or_true(\n        self, isolated_home\n    ):\n        """No prior history file — load() is either a no-op-true or\n        returns False, both fine."""\n        from color_history import ColorHistory\n        ch = ColorHistory()\n        # The constructor calls load() automatically\n        result = ch.load()\n        assert isinstance(result, bool)\n\n    def test_save_writes_history_file(self, isolated_home, tmp_path):\n        """Verify `save()` (the sync version) writes to disk. The\n        round-trip via a new instance is timing-dependent because\n        `add_color` triggers `save_async`, so we test save() directly."""\n        from color_history import ColorHistory\n        ch = ColorHistory()\n        ch.clear()\n        ch.add_color((100, 150, 200))\n\n        # Save synchronously (not save_async)\n        ok = ch.save()\n        assert ok is True\n\n        # File should now exist on disk\n        assert os.path.exists(ch.history_file)\n\n        # File contents should be valid JSON\n        with open(ch.history_file) as f:\n            data = json.load(f)\n        assert "entries" in data\n\n    def test_export_to_json_file(self, tmp_path, isolated_home):\n        from color_history import ColorHistory\n        ch = ColorHistory()\n        ch.add_color((255, 0, 0))\n        out = tmp_path / "hist.json"\n        try:\n            result = ch.export_to_file(str(out))\n        except Exception as e:\n            pytest.fail(\n                f"export_to_file JSON raised {type(e).__name__}: {e}"\n            )\n        if result:\n            assert out.exists()\n\n    def test_export_to_html_file_writes_html_with_color(\n        self, tmp_path, isolated_home\n    ):\n        """`export_to_file(\'*.html\')` writes HTML containing the colors.\n        Verify file exists and contains the hex of the added color."""\n        from color_history import ColorHistory\n        ch = ColorHistory()\n        ch.add_color((0, 255, 0))\n        out = tmp_path / "hist.html"\n\n        ch.export_to_file(str(out))\n\n        assert out.exists(), "HTML export did not write file"\n        text = out.read_text()\n        # Hex of (0, 255, 0) is #00FF00 (case-insensitive)\n        assert "00FF00" in text.upper(), (\n            f"HTML export does not contain hex \'00FF00\' for (0, 255, 0); "\n            f"first 200 chars: {text[:200]!r}"\n        )\n\n    def test_export_to_txt_file_writes_text_with_color(\n        self, tmp_path, isolated_home\n    ):\n        """`export_to_file(\'*.txt\')` writes plain text. Verify file\n        exists and contains a representation of the added color."""\n        from color_history import ColorHistory\n        ch = ColorHistory()\n        ch.add_color((0, 0, 255))\n        out = tmp_path / "hist.txt"\n\n        ch.export_to_file(str(out))\n\n        assert out.exists(), "TXT export did not write file"\n        text = out.read_text()\n        # Should mention the color in some form (hex 0000FF or rgb 0,0,255)\n        text_upper = text.upper()\n        has_hex = "0000FF" in text_upper\n        has_rgb = "0, 0, 255" in text or "(0, 0, 255)" in text\n        assert has_hex or has_rgb, (\n            f"TXT export does not contain (0,0,255) in any format; "\n            f"first 200 chars: {text[:200]!r}"\n        )\n\n    def test_add_color_with_max_entries_evicts_oldest(\n        self, isolated_home\n    ):\n        """ColorHistory caps at max_entries (default 20). Adding more\n        than that should evict the oldest."""\n        from color_history import ColorHistory\n        ch = ColorHistory(max_entries=5)\n        for i in range(10):\n            ch.add_color((i * 25, i * 25, i * 25))\n        entries = ch.get_entries()\n        # Should be capped at max_entries\n        assert len(entries) <= 5\n\n\n# ═══════════════════════════════════════════════════════════════════════════\n', 'def _settle(ch, qtbot, timeout: int = 3000) -> None:\n    """Wait until every background write this history started has finished.\n\n    `clear()` and `add_color()` each kick off a FileWriterThread against\n    `history_file`. Anything that then reads or rewrites that path is racing\n    them. Waiting on isRunning() rather than the `finished` signal is\n    deliberate and is the rule the thread-ownership round established: this\n    thread class declares `finished = pyqtSignal(bool, str)`, shadowing\n    QThread.finished(), and emits it from inside run() -- so it fires while\n    the QThread is still going. tests/test_threading.py waits the same way.\n    """\n    def quiet() -> bool:\n        current = getattr(ch, \'_save_thread\', None)\n        if current is not None and current.isRunning():\n            return False\n        return not any(\n            w.isRunning() for w in getattr(ch, \'_pending_writers\', []))\n\n    qtbot.waitUntil(quiet, timeout=timeout)\n\n\n@pytest.fixture\ndef history_factory(real_color_history, tmp_path):\n    """Build real ColorHistory instances and guarantee they are cleaned up.\n\n    `real_color_history` (tests/conftest.py) restores the pristine\n    __init__/load/save_async that conftest and the locked file patch to\n    no-ops, so these tests drive the REAL FileWriterThread. That is the\n    point of them -- and it is also why they were skipped for a year: a\n    ColorHistory dropped with a write still in flight destroys a running\n    QThread, and Qt aborts the process. `cleanup()` is the codebase\'s own\n    answer to that, and this fixture applies it to every instance a test\n    makes, whatever the test asserts or how it fails.\n\n    Each instance gets its own file under tmp_path. The pristine __init__\n    calls load() against the real home directory, so entries are reset\n    immediately -- the same precaution _fresh_history takes in\n    tests/test_threading.py.\n    """\n    made = []\n\n    def make(**kwargs):\n        ch = real_color_history(**kwargs)\n        ch.history_file = str(tmp_path / f"history_{len(made)}.json")\n        ch.entries = []\n        ch._save_thread = None\n        made.append(ch)\n        return ch\n\n    yield make\n\n    for ch in made:\n        ch.cleanup()\n\n\n@pytest.mark.integration\nclass TestColorHistoryLoadExport:\n    """ColorHistory\'s load() and export_to_file() have format-specific\n    branches that need explicit drives.\n\n    UN-SKIPPED 2026-09-09 (RNV-HISTORY-WRITER). These six ran against the\n    real threading path and aborted the process, so the class carried a\n    class-level skip whose reason said the pattern could not be replicated\n    "without mocking out the very methods they\'re trying to verify". It can:\n    tests/test_threading.py has driven the same path through\n    `real_color_history` since Phase 3. Two things were actually needed --\n    a product fix so `save_async` stops destroying its own running writer,\n    and the fixture above so a dropped instance cannot take the process with\n    it.\n    """\n\n    def test_load_with_no_existing_file_returns_false_or_true(\n        self, history_factory\n    ):\n        """No prior history file — load() is either a no-op-true or\n        returns False, both fine."""\n        ch = history_factory()\n        result = ch.load()\n        assert isinstance(result, bool)\n\n    def test_save_writes_history_file(self, history_factory, qtbot):\n        """Verify `save()` (the sync version) writes to disk.\n\n        The original note here said the round-trip was timing-dependent\n        "because add_color triggers save_async, so we test save() directly".\n        Calling save() directly is not enough on its own: clear() and\n        add_color() have each already started a background write to this same\n        path, and they land *after* the synchronous one. Without the wait\n        below, json.load() read a half-written file 9 times in 20.\n        """\n        ch = history_factory()\n        ch.clear()\n        ch.add_color((100, 150, 200))\n\n        # Let the two background writes finish before writing synchronously.\n        _settle(ch, qtbot)\n\n        # Save synchronously (not save_async)\n        ok = ch.save()\n        assert ok is True\n\n        # File should now exist on disk\n        assert os.path.exists(ch.history_file)\n\n        # File contents should be valid JSON\n        with open(ch.history_file) as f:\n            data = json.load(f)\n        assert "entries" in data\n\n    def test_export_to_json_file(self, history_factory, tmp_path):\n        ch = history_factory()\n        ch.add_color((255, 0, 0))\n        out = tmp_path / "hist.json"\n        try:\n            result = ch.export_to_file(str(out))\n        except Exception as e:\n            pytest.fail(\n                f"export_to_file JSON raised {type(e).__name__}: {e}"\n            )\n        if result:\n            assert out.exists()\n\n    def test_export_to_html_file_writes_html_with_color(\n        self, history_factory, tmp_path\n    ):\n        """`export_to_file(\'*.html\')` writes HTML containing the colors.\n        Verify file exists and contains the hex of the added color."""\n        ch = history_factory()\n        ch.add_color((0, 255, 0))\n        out = tmp_path / "hist.html"\n\n        ch.export_to_file(str(out))\n\n        assert out.exists(), "HTML export did not write file"\n        text = out.read_text()\n        # Hex of (0, 255, 0) is #00FF00 (case-insensitive)\n        assert "00FF00" in text.upper(), (\n            f"HTML export does not contain hex \'00FF00\' for (0, 255, 0); "\n            f"first 200 chars: {text[:200]!r}"\n        )\n\n    def test_export_to_txt_file_writes_text_with_color(\n        self, history_factory, tmp_path\n    ):\n        """`export_to_file(\'*.txt\')` writes plain text. Verify file\n        exists and contains a representation of the added color."""\n        ch = history_factory()\n        ch.add_color((0, 0, 255))\n        out = tmp_path / "hist.txt"\n\n        ch.export_to_file(str(out))\n\n        assert out.exists(), "TXT export did not write file"\n        text = out.read_text()\n        # Should mention the color in some form (hex 0000FF or rgb 0,0,255)\n        text_upper = text.upper()\n        has_hex = "0000FF" in text_upper\n        has_rgb = "0, 0, 255" in text or "(0, 0, 255)" in text\n        assert has_hex or has_rgb, (\n            f"TXT export does not contain (0,0,255) in any format; "\n            f"first 200 chars: {text[:200]!r}"\n        )\n\n    def test_add_color_with_max_entries_evicts_oldest(self, history_factory):\n        """ColorHistory caps at max_entries (default 20). Adding more\n        than that should evict the oldest."""\n        ch = history_factory(max_entries=5)\n        for i in range(10):\n            ch.add_color((i * 25, i * 25, i * 25))\n        entries = ch.get_entries()\n        # Should be capped at max_entries\n        assert len(entries) <= 5\n\n\n', 1), ('KNOWN_ISSUES.md', "Six tests in `tests/test_error_recovery_paths.py` exercise the\n`ColorHistory` constructor + `add_color()` + `save()` chain. The save\npath spawns a QThread for async filesystem writes, and the test harness's\ninteraction with that thread crashes Python natively on Windows.\n\n**User impact:** None. These tests were attempts to extend coverage on\nexisting code paths; the code itself works correctly at runtime.\n\n**Planned fix:** Split QThread machinery off from `ColorHistory`\nconstruction. Same architectural pattern as the `AsyncFileOps` refactor\nlisted above — both classes mix lifecycle management of background\nthreads into operations that conceptually shouldn't require them.", '**Fixed 2026-09-09.** All six run on both runners.\n\nThe skip reason blamed "the test harness\'s interaction with that thread"\nand recorded **User impact: None**. Both were wrong. `save_async()`\nassigned the new `FileWriterThread` straight over `self._save_thread`,\nwhich is the only Python reference to the previous writer — so a second\nsave while the first was still writing destroyed a **running QThread** and\nQt aborted the process.\n\nReproduced through the product API alone, no pytest and no fixtures, five\ntimes in five, and on Linux as well as Windows:\n\n```python\nch = ColorHistory(); ch.clear(); ch.add_color((100, 150, 200))\n```\n\n`clear()` and `add_color()` each call `save_async()`. Both are ordinary\napplication paths — the mixer adds a colour on every mix, and\n`core/package_d_panel.py` clears the history from the panel. Sixty rapid\nsaves now survive with no `cleanup()` at all; before, three in three\naborted.\n\nA writer is now retained until Qt reports it finished, and released on the\nnext save and in `cleanup()`. The six tests build their histories through\na `history_factory` fixture that calls `cleanup()` on every instance, and\none of them waits for the background writes to settle before reading the\nfile — without that wait it read a half-written file 9 times in 20.\n\nGuarded by `tests/test_history_writer_ownership.py`. The planned\narchitectural split is no longer required for these tests to run, though\nit remains a reasonable thing to want.', 1), ('KNOWN_ISSUES.md', 'tests rather than to `utils/async_file_ops.py`; the application itself never\nhad the bug, because `ColorHistory` holds `_save_thread` on the object and\n`AsyncFileManager` keeps `_active_threads`, and both check `isRunning()`\nbefore letting go.', 'tests rather than to `utils/async_file_ops.py`.\n\n**That round also claimed the application itself never had the bug, on the\ngrounds that `ColorHistory` holds `_save_thread` on the object and\n`AsyncFileManager` keeps `_active_threads`, and both check `isRunning()`\nbefore letting go. The claim was wrong and is corrected here.**\n`ColorHistory` did hold the thread on the object — and `save_async()`\noverwrote that attribute on the next save without checking anything, which\nis the same defect one level up. Fixed 2026-09-09; see the entry above.\n`AsyncFileManager` was checked again and is fine.', 1)]


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


def checks(tree) -> None:
    ch = tree.files["core/color_history.py"]
    erp = tree.files["tests/test_error_recovery_paths.py"]

    # 1. both files parse. Every check below reads a syntax tree, and a file
    #    that does not parse makes them vacuous rather than red.
    for rel, text in (("core/color_history.py", ch),
                      ("tests/test_error_recovery_paths.py", erp)):
        try:
            ast.parse(text, rel)
        except SyntaxError as e:
            raise SystemExit(f"{rel} does not parse after the edits: {e}")

    tree_ch = ast.parse(ch)
    save_async = next((n for n in ast.walk(tree_ch)
                       if isinstance(n, ast.FunctionDef) and n.name == "save_async"), None)
    if save_async is None:
        raise SystemExit("save_async is gone from core/color_history.py")

    # 2. the retention happens BEFORE the reassignment. Retaining after it
    #    retains the new writer and drops the old one, which reads almost
    #    identically and fixes nothing. This is the check that caught the
    #    inverted-order tampering in under a fifth of a second, before the
    #    behavioural test could abort the run.
    retain = assign = None
    for n in ast.walk(save_async):
        if isinstance(n, ast.Attribute) and n.attr == "_pending_writers":
            retain = n.lineno if retain is None else min(retain, n.lineno)
        if (isinstance(n, ast.Assign) and n.targets
                and isinstance(n.targets[0], ast.Attribute)
                and n.targets[0].attr == "_save_thread"):
            assign = n.lineno if assign is None else min(assign, n.lineno)
    if retain is None:
        raise SystemExit("save_async does not retain the previous writer")
    if assign is None:
        raise SystemExit("save_async no longer assigns _save_thread")
    if retain >= assign:
        raise SystemExit(f"save_async retains at line {retain}, after it "
                         f"reassigns at line {assign} -- that keeps the new "
                         f"writer and drops the old one")

    # 3. cleanup() drains the retired writers too. A writer left running at
    #    interpreter shutdown is exactly the close-time crash cleanup() was
    #    written for.
    cleanup = next((n for n in ast.walk(tree_ch)
                    if isinstance(n, ast.FunctionDef) and n.name == "cleanup"), None)
    if cleanup is None:
        raise SystemExit("cleanup() is gone from ColorHistory")
    if not any(isinstance(n, ast.Attribute) and n.attr == "_pending_writers"
               for n in ast.walk(cleanup)):
        raise SystemExit("cleanup() does not drain the retired writers")

    # 4. the six tests are un-skipped, still six, and none of them builds a
    #    ColorHistory outside the fixture that cleans it up.
    tree_erp = ast.parse(erp)
    klass = next((n for n in tree_erp.body if isinstance(n, ast.ClassDef)
                  and n.name == "TestColorHistoryLoadExport"), None)
    if klass is None:
        raise SystemExit("TestColorHistoryLoadExport did not survive the rewrite")
    skipped = [ast.unparse(d) for d in klass.decorator_list if "skip" in ast.unparse(d)]
    if skipped:
        raise SystemExit(f"the class is still skipped: {skipped}")
    tests = [f for f in klass.body if isinstance(f, ast.FunctionDef)]
    if len(tests) != 6:
        raise SystemExit(f"expected six tests, found {len(tests)}: "
                         f"{[f.name for f in tests]}")
    inner = [f.name for f in tests if any("skip" in ast.unparse(d) for d in f.decorator_list)]
    if inner:
        raise SystemExit(f"individual tests are still skipped: {inner}")
    direct = [f"{f.name}:{n.lineno}" for f in tests for n in ast.walk(f)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "ColorHistory"]
    if direct:
        raise SystemExit(f"these tests build a ColorHistory outside the "
                         f"fixture, so nothing cleans it up: {direct}")

    factory = next((n for n in ast.walk(tree_erp)
                    if isinstance(n, ast.FunctionDef) and n.name == "history_factory"), None)
    if factory is None:
        raise SystemExit("the history_factory fixture did not land")
    if not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == "cleanup" for n in ast.walk(factory)):
        raise SystemExit("history_factory does not call cleanup()")

    # 5. the prose. Read with whitespace collapsed, because a markdown
    #    paragraph wraps where the width runs out and a check that looked for
    #    a phrase the file had split across a line break has failed here
    #    before on the line break rather than the meaning.
    ki = " ".join(tree.files["KNOWN_ISSUES.md"].split())
    if "User impact:** None. These tests were attempts" in ki:
        raise SystemExit("KNOWN_ISSUES.md still records User impact: None")
    if "the application itself never had the bug" in ki and "claim was wrong" not in ki:
        raise SystemExit("KNOWN_ISSUES.md still asserts the application was clean")
    if "test_history_writer_ownership.py" not in ki:
        raise SystemExit("KNOWN_ISSUES.md does not name the guard")

    # 6. the sweep sees something. A guard that reads no file passes every
    #    assertion above; the image-budget round shipped exactly that.
    if "_release_finished_writers" not in ch:
        raise SystemExit("the release helper did not land")

    # 7. the sentinel is actually IN the file the re-run check reads. The
    #    first version of this script checked core/color_history.py for
    #    "RNV-HISTORY-WRITER" and never wrote it there, so a second run
    #    skipped the "already applied" message and died on a missing anchor
    #    instead. A guard against re-running that cannot fire is worse than
    #    none, because it looks like protection.
    if SENTINEL not in ch:
        raise SystemExit(f"'{SENTINEL}' is not in {SENTINEL_FILE}, so the "
                         f"already-applied check can never fire")
    print("  guards: retention precedes reassignment, cleanup drains, "
          "6 tests un-skipped and all cleaned up")


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
