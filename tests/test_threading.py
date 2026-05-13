"""
RNV Color Mixer — Threading Tests  (Phase 3 deliverable)
=========================================================

These tests bypass the global no-op patches the locked file and conftest
apply to ColorHistory.{__init__, load, save_async}, exercising the REAL
FileWriterThread / FileReaderThread path that:

  • spawns a QThread
  • writes JSON to disk
  • emits a `finished(bool, str)` signal
  • is torn down by ColorHistory.cleanup() (the v3.3.3 close-time crash fix)

Mechanism
---------
The `real_color_history` fixture (defined in tests/conftest.py) temporarily
restores the pristine method references captured at conftest import time —
i.e., BEFORE the locked file's monkey-patches fire — and reinstates the
no-ops on teardown. This means:

  • These tests run against the REAL threading implementation
  • Other tests (locked + Phase 2) continue to see the safe no-op patches
  • No modification of the locked file is required

Synchronization rule
--------------------
NO `time.sleep()` calls anywhere. All waits use `qtbot.waitUntil` (state
polling) or `qtbot.waitSignal` (signal capture) so the test runner is
deterministic and as fast as the underlying I/O permits.

Coverage focus
--------------
Phase 3 lifts coverage on color_history.py and async_file_ops.py by
exercising code paths that the global no-op patches actively prevent the
locked suite from reaching.
"""

from __future__ import annotations

import os
import json
import time
import pytest

# Bootstrap (sys.path setup) is done by tests/conftest.py
from core.color_history import ColorHistory, ColorHistoryEntry  # noqa: E402
from utils.async_file_ops import (  # noqa: E402
    FileWriterThread,
    FileReaderThread,
    AsyncFileManager,
    async_save_json,
    async_load_json,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _fresh_history(real_color_history_cls, tmp_path, name: str = "history.json") -> ColorHistory:
    """
    Instantiate a real (pristine-method) ColorHistory wired to a tmp path
    and reset entries to empty.

    The pristine `__init__` calls `load()` against the user's home dir,
    which may pick up real entries on a developer machine. We override
    `history_file` and clear `entries` immediately so each test starts
    from a known-empty state.
    """
    ch = real_color_history_cls()
    ch.history_file = str(tmp_path / name)
    ch.entries = []
    ch._save_thread = None
    return ch


# ═══════════════════════════════════════════════════════════════════════════
# Sanity check on the fixture itself — verifies pristine methods are active
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.threading
class TestRealColorHistoryFixture:
    """Confirms the fixture actually provides pristine, non-patched methods."""

    def test_fixture_yields_color_history_class(self, real_color_history):
        assert real_color_history is ColorHistory

    def test_pristine_init_is_not_a_lambda(self, real_color_history):
        # The conftest's no-op patch for __init__ is a regular function named
        # `_tests_safe_ch_init`; the pristine one is the original method.
        # If this check ever fires it means the pristine capture failed.
        init = real_color_history.__init__
        assert init.__name__ == "__init__", (
            f"Fixture installed wrong __init__: {init.__name__!r}; "
            "pristine method capture in conftest may have run after the "
            "locked file's patches fired."
        )

    def test_pristine_save_async_creates_real_thread(
        self, real_color_history, tmp_path, qtbot
    ):
        ch = _fresh_history(real_color_history, tmp_path)
        ch.save_async()
        # The no-op patch never assigns _save_thread; the pristine version does.
        assert ch._save_thread is not None
        assert isinstance(ch._save_thread, FileWriterThread)
        # Wait for the spawned thread to finish before tearing down
        qtbot.waitUntil(lambda: not ch._save_thread.isRunning(), timeout=2000)


# ═══════════════════════════════════════════════════════════════════════════
# TestColorHistoryThreading — the FileWriterThread + cleanup() lifecycle
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.threading
class TestColorHistoryThreading:
    """Real-thread tests for ColorHistory.save_async and cleanup."""

    def test_save_async_actually_writes_file(
        self, real_color_history, tmp_path, qtbot
    ):
        ch = _fresh_history(real_color_history, tmp_path)
        ch.entries = [ColorHistoryEntry((255, 0, 0))]
        ch.save_async()

        qtbot.waitUntil(lambda: not ch._save_thread.isRunning(), timeout=2000)

        assert os.path.exists(ch.history_file), (
            "save_async did not produce the expected file"
        )
        with open(ch.history_file, "r") as f:
            data = json.load(f)
        assert data["entries"][0]["color"] == [255, 0, 0]

    def test_save_async_emits_finished_with_success_true(
        self, real_color_history, tmp_path, qtbot
    ):
        ch = _fresh_history(real_color_history, tmp_path)
        ch.entries = [ColorHistoryEntry((10, 20, 30))]

        # Build the thread directly (mirrors what save_async does internally)
        # so we can wrap qtbot.waitSignal cleanly around it.
        data = {
            "version": "1.0",
            "max_entries": ch.max_entries,
            "entries": [e.to_dict() for e in ch.entries],
        }
        thread = FileWriterThread(ch.history_file, data, "json")

        with qtbot.waitSignal(thread.finished, timeout=2000) as blocker:
            thread.start()

        success, message = blocker.args
        assert success is True, f"Unexpected failure: {message}"
        assert ch.history_file in message

    def test_cleanup_returns_quickly_when_thread_already_finished(
        self, real_color_history, tmp_path, qtbot
    ):
        ch = _fresh_history(real_color_history, tmp_path)
        ch.entries = [ColorHistoryEntry((1, 2, 3))]
        ch.save_async()
        qtbot.waitUntil(lambda: not ch._save_thread.isRunning(), timeout=2000)

        start = time.perf_counter()
        ch.cleanup()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Cleanup of an already-finished thread should be near-instant.
        assert elapsed_ms < 500, (
            f"cleanup() took {elapsed_ms:.1f} ms with a finished thread "
            f"(expected < 500 ms)"
        )

    def test_cleanup_waits_for_running_thread_then_clears(
        self, real_color_history, tmp_path, qtbot
    ):
        ch = _fresh_history(real_color_history, tmp_path)
        ch.entries = [ColorHistoryEntry((50, 60, 70))]
        ch.save_async()

        # Don't wait for the thread — call cleanup while it may still be running.
        # cleanup() must internally quit() and wait(1000) before returning.
        ch.cleanup()

        # Post-cleanup invariants
        assert ch._save_thread is None, (
            "cleanup() must null _save_thread after waiting for it"
        )
        assert ch.entries == [], "cleanup() must clear entries"

    def test_cleanup_idempotent_called_twice(
        self, real_color_history, tmp_path, qtbot
    ):
        """Regression: the v3.3.3 close-time crash was triggered by an
        unguarded second call. Calling cleanup() twice must not raise."""
        ch = _fresh_history(real_color_history, tmp_path)
        ch.entries = [ColorHistoryEntry((100, 100, 100))]
        ch.save_async()
        qtbot.waitUntil(lambda: not ch._save_thread.isRunning(), timeout=2000)

        ch.cleanup()  # first
        ch.cleanup()  # second — must not crash

        assert ch._save_thread is None
        assert ch.entries == []

    def test_cleanup_safe_when_no_save_thread_was_ever_started(
        self, real_color_history, tmp_path
    ):
        """Edge case: instantiate, never call save_async, call cleanup."""
        ch = _fresh_history(real_color_history, tmp_path)
        # Untouched _save_thread (None from helper)
        ch.cleanup()  # must not raise
        assert ch.entries == []

    def test_add_color_then_cleanup_flushes_to_disk(
        self, real_color_history, tmp_path, qtbot
    ):
        """add_color triggers save_async; cleanup must wait for completion
        before returning, so the file should be present afterwards."""
        ch = _fresh_history(real_color_history, tmp_path)
        ch.add_color((222, 111, 33))

        ch.cleanup()  # must wait for the save_async thread internally

        assert os.path.exists(ch.history_file), (
            "File must exist after cleanup completes (cleanup waits for "
            "the in-flight save_async thread to finish)"
        )
        with open(ch.history_file, "r") as f:
            data = json.load(f)
        # The entry was written, even though cleanup later cleared in-memory.
        assert len(data["entries"]) == 1
        assert data["entries"][0]["color"] == [222, 111, 33]

    def test_reinstantiate_after_cleanup_loads_prior_data(
        self, real_color_history, tmp_path, qtbot
    ):
        """A second ColorHistory pointed at the same file must read what
        the first one wrote."""
        history_path = tmp_path / "shared.json"

        ch1 = real_color_history()
        ch1.history_file = str(history_path)
        ch1.entries = []
        ch1._save_thread = None
        ch1.add_color((33, 66, 99))
        qtbot.waitUntil(
            lambda: ch1._save_thread is not None
                    and not ch1._save_thread.isRunning(),
            timeout=2000,
        )
        ch1.cleanup()

        # Second instance — pristine __init__ runs load() against home dir,
        # but we redirect and re-load from our shared path.
        ch2 = real_color_history()
        ch2.history_file = str(history_path)
        ch2.entries = []
        ok = ch2.load()

        assert ok is True
        assert len(ch2.entries) == 1
        assert ch2.entries[0].color == (33, 66, 99)


# ═══════════════════════════════════════════════════════════════════════════
# TestAsyncFileOpsThreading — FileWriterThread / FileReaderThread / manager
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.threading
class TestAsyncFileOpsThreading:
    """Real-thread tests for the async_file_ops module using qtbot."""

    def test_file_writer_thread_emits_finished_with_success_true(
        self, tmp_path, qtbot
    ):
        path = str(tmp_path / "out.json")
        thread = FileWriterThread(path, {"alpha": 1, "beta": [2, 3]}, "json")

        with qtbot.waitSignal(thread.finished, timeout=2000) as blocker:
            thread.start()

        success, message = blocker.args
        assert success is True
        assert os.path.exists(path)
        with open(path) as f:
            assert json.load(f) == {"alpha": 1, "beta": [2, 3]}

    def test_file_writer_thread_emits_failure_on_invalid_path(
        self, tmp_path, qtbot
    ):
        # A directory path that doesn't exist as a parent — write will fail
        bad_path = str(tmp_path / "no" / "such" / "dir" / "out.json")
        thread = FileWriterThread(bad_path, {"x": 1}, "json")

        with qtbot.waitSignal(thread.finished, timeout=2000) as blocker:
            thread.start()

        success, message = blocker.args
        assert success is False
        assert "fail" in message.lower() or "error" in message.lower()

    def test_file_writer_thread_progress_signal_reaches_100(
        self, tmp_path, qtbot
    ):
        path = str(tmp_path / "progress.json")
        thread = FileWriterThread(path, {"k": "v"}, "json")
        seen: list[int] = []
        thread.progress.connect(seen.append)

        with qtbot.waitSignal(thread.finished, timeout=2000):
            thread.start()

        # The implementation emits at least 10 → 30 → 90 → 100
        assert 100 in seen, f"progress should reach 100; saw {seen}"
        assert seen == sorted(seen), f"progress should be monotonic; saw {seen}"

    def test_file_reader_thread_round_trip(self, tmp_path, qtbot):
        path = tmp_path / "rt.json"
        path.write_text(json.dumps({"hello": "world", "nums": [4, 5, 6]}))

        thread = FileReaderThread(str(path), "json")
        with qtbot.waitSignal(thread.finished, timeout=2000) as blocker:
            thread.start()

        success, data, message = blocker.args
        assert success is True
        assert data == {"hello": "world", "nums": [4, 5, 6]}

    def test_async_save_json_invokes_callback_with_success(
        self, tmp_path, qtbot
    ):
        path = str(tmp_path / "saved.json")
        callback_args: list[tuple] = []

        def on_complete(success, message):
            callback_args.append((success, message))

        manager = async_save_json(path, {"q": 42}, on_complete=on_complete)

        # Wait for the user callback to actually fire — NOT for thread-count
        # to drop to zero. The thread count goes to 0 the instant run() returns
        # in the worker thread, but the `finished` signal slot (which calls
        # our on_complete) is queued to the main thread and may not have run
        # yet, producing an order-dependent race.
        qtbot.waitUntil(lambda: len(callback_args) >= 1, timeout=2000)

        assert len(callback_args) == 1, (
            f"on_complete should fire exactly once; saw {callback_args}"
        )
        success, message = callback_args[0]
        assert success is True
        assert os.path.exists(path)

    def test_async_load_json_invokes_callback_with_data(
        self, tmp_path, qtbot
    ):
        path = tmp_path / "load.json"
        path.write_text(json.dumps({"loaded": True, "value": 99}))
        captured: list[tuple] = []

        def on_complete(success, data, message):
            captured.append((success, data, message))

        manager = async_load_json(str(path), on_complete=on_complete)
        # Wait on the callback firing, not on thread-count (see save_json
        # comment above — same race).
        qtbot.waitUntil(lambda: len(captured) >= 1, timeout=2000)

        assert len(captured) == 1
        success, data, _ = captured[0]
        assert success is True
        assert data == {"loaded": True, "value": 99}

    def test_async_file_manager_wait_all_returns_true_when_done(
        self, tmp_path, qtbot
    ):
        manager = AsyncFileManager()
        manager.write_file_async(
            str(tmp_path / "a.json"), {"a": 1}, format="json"
        )
        manager.write_file_async(
            str(tmp_path / "b.json"), {"b": 2}, format="json"
        )

        # wait_all blocks for all active threads
        assert manager.wait_all(timeout=2000) is True
        assert os.path.exists(tmp_path / "a.json")
        assert os.path.exists(tmp_path / "b.json")
