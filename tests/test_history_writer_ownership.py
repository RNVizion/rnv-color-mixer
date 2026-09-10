"""RNV-HISTORY-WRITER-GUARD -- a save must not destroy the save before it.

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
