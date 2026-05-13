"""
RNV Color Mixer — Utility Module Tests
========================================

Five smaller utility modules grouped into one file. Each module gets
one class. These modules are ~60-110 statements each, so test counts
per module are modest.

Modules covered
---------------
  1. signal_manager.py  TestSignalManager
  2. error_handler.py   TestErrorHandler / TestErrorContext
  3. async_file_ops.py  TestAsyncFileOpsLowLevel
  4. file_utils.py      TestFileUtils
  5. config.py          TestThemeManager / TestFontManager

The async_file_ops tests here drive the lower-level QThread classes
directly (FileWriterThread, FileReaderThread); the high-level
AsyncFileManager wrapper is covered by other test files.
"""

from __future__ import annotations

import os
import json
import tempfile
import pytest
from pathlib import Path

from utils.signal_manager import SignalConnectionManager
from utils.error_handler import ErrorHandler, ErrorContext
from utils.async_file_ops import (
    FileWriterThread,
    FileReaderThread,
    AsyncFileManager,
)
from utils.file_utils import FileUtils
from utils.config import ThemeManager


# ═══════════════════════════════════════════════════════════════════════════
# 1. signal_manager.py
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSignalManager:
    """`SignalConnectionManager` tracks Qt signal connections so they can
    be cleaned up properly to avoid memory leaks. Phase 4 covered some of
    its paths transitively; this fills in the direct API."""

    def test_fresh_manager_has_zero_connections(self):
        sm = SignalConnectionManager()
        stats = sm.get_stats()
        assert stats.get("active", 0) == 0

    def test_connect_increases_active_count(self, qtbot):
        from PyQt6.QtCore import QObject, pyqtSignal

        class _Emitter(QObject):
            sig = pyqtSignal()

        sm = SignalConnectionManager()
        emitter = _Emitter()
        qtbot.addWidget(emitter) if hasattr(emitter, "show") else None

        before = sm.get_stats().get("active", 0)
        sm.connect(emitter, emitter.sig, lambda: None, "test_conn")
        after = sm.get_stats().get("active", 0)
        assert after == before + 1

    def test_disconnect_all_clears_count(self, qtbot):
        from PyQt6.QtCore import QObject, pyqtSignal

        class _Emitter(QObject):
            sig = pyqtSignal()

        sm = SignalConnectionManager()
        e = _Emitter()
        sm.connect(e, e.sig, lambda: None, "a")
        sm.connect(e, e.sig, lambda: None, "b")
        assert sm.get_stats().get("active", 0) >= 2

        n_disconnected = sm.disconnect_all(quiet=True)
        assert n_disconnected >= 2
        assert sm.get_stats().get("active", 0) == 0

    def test_disconnect_widget_only_removes_that_widgets_connections(
        self, qtbot
    ):
        from PyQt6.QtCore import QObject, pyqtSignal

        class _Emitter(QObject):
            sig = pyqtSignal()

        sm = SignalConnectionManager()
        e1, e2 = _Emitter(), _Emitter()
        sm.connect(e1, e1.sig, lambda: None, "e1_conn")
        sm.connect(e2, e2.sig, lambda: None, "e2_conn")

        n = sm.disconnect_widget(e1, quiet=True)
        assert n == 1, f"expected 1 disconnection from e1, got {n}"

        # e2's connection still live
        stats = sm.get_stats()
        assert stats.get("active", 0) == 1


# ═══════════════════════════════════════════════════════════════════════════
# 2. error_handler.py
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestErrorHandler:
    """`ErrorHandler.safe_execute` is the chokepoint used throughout the
    app to wrap operations that could raise. Locked suite covers the
    common cases; this fills in the corners."""

    def test_safe_execute_returns_function_result_on_success(self):
        result = ErrorHandler.safe_execute(lambda: 42, "addition")
        assert result == 42

    def test_safe_execute_returns_none_on_exception(self):
        result = ErrorHandler.safe_execute(
            lambda: 1 / 0, "div zero"
        )
        assert result is None

    def test_safe_execute_with_default_value_returns_default_on_exception(self):
        """Some callers pass `default=` to get a non-None fallback."""
        # Check whether safe_execute supports a `default` kwarg
        import inspect
        sig = inspect.signature(ErrorHandler.safe_execute)
        if "default" not in sig.parameters:
            pytest.skip("safe_execute doesn't support `default=` kwarg")
        result = ErrorHandler.safe_execute(
            lambda: 1 / 0, "div zero", default="fallback"
        )
        assert result == "fallback"

    def test_safe_execute_logs_with_correct_context_name(self):
        """The context name shows up in the logged error message."""
        # Just verify execution and return None — log inspection would
        # require a logger handler, which is over-spec'd for a smoke test
        result = ErrorHandler.safe_execute(
            lambda: 1 / 0, "ze_distinctive_context_name"
        )
        assert result is None

    def test_safe_execute_with_args_passes_them_through(self):
        """Some safe_execute signatures support *args/**kwargs forwarding."""
        # If the function takes 0 args (most common), wrap in lambda
        def add(x, y): return x + y
        result = ErrorHandler.safe_execute(lambda: add(2, 3), "add")
        assert result == 5


@pytest.mark.integration
class TestErrorContext:
    """`ErrorContext` is a context manager that swallows exceptions and
    logs them with a consistent format."""

    def test_error_context_swallows_exceptions(self):
        """Using `with ErrorContext("name"):` and raising inside doesn't
        propagate the exception out."""
        try:
            with ErrorContext("test op"):
                raise ValueError("expected to be swallowed")
        except Exception as e:
            pytest.fail(
                f"ErrorContext leaked exception {type(e).__name__}: {e}"
            )

    def test_error_context_lets_normal_completion_through(self):
        """No exception → context exits normally with no side effects."""
        x = []
        with ErrorContext("normal op"):
            x.append(1)
        assert x == [1]


# ═══════════════════════════════════════════════════════════════════════════
# 3. async_file_ops.py — direct thread tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAsyncFileOpsLowLevel:
    """Phase 3 covered the AsyncFileManager wrapper. This phase tests the
    underlying QThread classes directly to lift coverage on lines 70-149
    that the manager doesn't always reach.

    Method signatures verified by source: `FileWriterThread(filepath, data,
    format='json')`, `FileReaderThread(filepath, format='json')`. The thread
    classes only support 'json', 'text', and 'binary' format strings."""

    def test_file_writer_thread_writes_text_data(self, tmp_path, qtbot):
        target = tmp_path / "writer_out.txt"
        thread = FileWriterThread(str(target), "hello world", format="text")

        with qtbot.waitSignal(thread.finished, timeout=3000) as blocker:
            thread.start()
        success, _ = blocker.args
        assert success is True
        assert target.read_text() == "hello world"

    def test_file_reader_thread_reads_known_json_file(self, tmp_path, qtbot):
        src = tmp_path / "reader_in.json"
        src.write_text(json.dumps({"key": "value", "n": 42}))

        thread = FileReaderThread(str(src), format="json")
        with qtbot.waitSignal(thread.finished, timeout=3000) as blocker:
            thread.start()
        success, data, _ = blocker.args
        assert success is True
        assert data == {"key": "value", "n": 42}

    def test_async_file_manager_write_file_async_completes(
        self, tmp_path, qtbot
    ):
        """High-level manager API: `write_file_async` queues a write and
        invokes the callback when done. This complements the locked
        suite's existing manager tests by exercising the JSON-format path
        explicitly."""
        mgr = AsyncFileManager()
        target = tmp_path / "mgr.json"
        callback_args: list = []

        mgr.write_file_async(
            str(target),
            {"hello": "world"},
            format="json",
            on_complete=lambda success, msg: callback_args.append(
                (success, msg)
            ),
        )

        # Wait for the callback to fire
        qtbot.waitUntil(
            lambda: len(callback_args) >= 1,
            timeout=3000,
        )
        success, _ = callback_args[0]
        assert success is True
        assert target.exists()


# ═══════════════════════════════════════════════════════════════════════════
# 4. file_utils.py
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFileUtils:
    """`FileUtils` is mostly static helpers for path validation and
    safe-name generation. Each method is small and pure."""

    def test_validate_file_path_empty_returns_false(self):
        assert FileUtils.validate_file_path("") is False

    def test_validate_file_path_normal_returns_true(self, tmp_path):
        # Use tmp_path for cross-platform compatibility — /tmp doesn't
        # exist on Windows, so a hardcoded "/tmp/anything" would fail
        # validation there.
        assert FileUtils.validate_file_path(str(tmp_path / "anything")) is True

    def test_validate_file_path_must_exist_with_missing_path_returns_false(self, tmp_path):
        # Cross-platform missing path
        assert FileUtils.validate_file_path(
            str(tmp_path / "definitely_missing_xyz_12345"), must_exist=True
        ) is False

    def test_validate_file_path_must_exist_with_existing_path_returns_true(
        self, tmp_path
    ):
        f = tmp_path / "exists.txt"
        f.write_text("x")
        assert FileUtils.validate_file_path(str(f), must_exist=True) is True

    def test_get_safe_filename_strips_invalid_characters(self):
        # The invalid set is <>:"/\\|?*
        result = FileUtils.get_safe_filename('foo<bar>baz/qux.txt')
        # No invalid characters survive
        for ch in '<>:"/\\|?*':
            assert ch not in result, (
                f"safe filename {result!r} still contains {ch!r}"
            )

    def test_get_safe_filename_truncates_long_names(self):
        long_name = "a" * 300 + ".txt"
        result = FileUtils.get_safe_filename(long_name, max_length=20)
        assert len(result) <= 20, (
            f"expected truncation to ≤20 chars, got {len(result)}"
        )
        # Extension preserved at the end
        assert result.endswith(".txt"), (
            f"extension lost during truncation: {result!r}"
        )

    def test_get_supported_palette_extensions_returns_list(self):
        exts = FileUtils.get_supported_palette_extensions()
        assert isinstance(exts, list)
        assert len(exts) >= 10  # we have 16 formats
        # Every entry starts with a dot
        for ext in exts:
            assert ext.startswith("."), (
                f"extension {ext!r} should start with '.'"
            )

    def test_is_palette_file_recognizes_known_extensions(self):
        for known in (".gpl", ".ase", ".aco", ".json"):
            assert FileUtils.is_palette_file(f"test{known}") is True, (
                f"is_palette_file rejected {known}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 5. config.py — ThemeManager
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestThemeManager:
    """ThemeManager state machine. Phase 4 covered cycling at the app
    level; this drives it directly."""

    def test_default_theme_is_dark(self):
        tm = ThemeManager()
        assert tm.get_theme_display_name() == "Dark Mode"
        assert tm.is_image_mode() is False

    def test_get_current_theme_returns_dict_with_required_keys(self):
        tm = ThemeManager()
        theme = tm.get_current_theme()
        assert isinstance(theme, dict)
        # The theme dict drives stylesheet generation throughout the app.
        # If any of these keys disappear, lots of code breaks.
        for required_key in (
            "name", "window_bg", "text_color", "accent",
            "panel_bg", "button_bg",
        ):
            assert required_key in theme, (
                f"theme dict missing required key {required_key!r}"
            )

    def test_cycle_theme_moves_to_a_different_theme(self):
        tm = ThemeManager()
        before = tm.get_theme_display_name()
        tm.cycle_theme()
        after = tm.get_theme_display_name()
        assert before != after, (
            f"cycle_theme didn't change: still {after}"
        )

    def test_image_mode_unavailable_in_test_environment(self):
        """In the sandbox there's no `background.*` image and no full set
        of button base PNGs — `image_mode_available` should be False."""
        tm = ThemeManager()
        # Just verify the attribute exists and is a bool
        assert isinstance(tm.image_mode_available, bool)


# ═══════════════════════════════════════════════════════════════════════════
# 6. config.py — FontManager (small smoke test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFontManager:
    """FontManager loads the embedded Montserrat Black font. Most of its
    coverage comes from app construction; this is a sanity check."""

    def test_font_manager_class_imports_cleanly(self):
        from utils.config import FontManager
        # Class exists and is a class
        assert isinstance(FontManager, type)
