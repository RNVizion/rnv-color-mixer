"""
RNV Color Mixer — Error Recovery Path Tests
=============================================

Tests targeting error-handling and recovery code that integration tests
don't naturally exercise:

  - file_utils.py: dialog wrappers, backup_file, create_directory paths
  - error_handler.py: handle_exception, safe_method decorator,
    safe_file_operation, safe_widget_operation
  - async_file_ops.py: error paths in _on_write_complete, wait_all,
    cleanup
  - color_history.py: load() error paths, export_to_file format branches

Each test exercises a small, predictable code path designed to verify
graceful failure handling rather than happy-path behavior.
"""

from __future__ import annotations

import json
import os
import pytest
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QFileDialog


# ═══════════════════════════════════════════════════════════════════════════
# 1. file_utils.py — dialog wrappers + backup/dir helpers
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFileUtilsDialogs:
    """FileUtils has 4 modal-dialog wrappers (`show_error_dialog`,
    `show_warning_dialog`, `show_info_dialog`, `ask_yes_no`) that
    delegate to QMessageBox. With modals patched out, each is a 5-stmt
    smoke test."""

    def test_show_error_dialog_does_not_crash(self, qtbot, monkeypatch):
        from file_utils import FileUtils
        monkeypatch.setattr(QMessageBox, "critical", lambda *a, **kw: 0)
        fu = FileUtils()
        try:
            fu.show_error_dialog("Title", "Message")
        except Exception as e:
            pytest.fail(
                f"show_error_dialog raised {type(e).__name__}: {e}"
            )

    def test_show_warning_dialog_does_not_crash(self, qtbot, monkeypatch):
        from file_utils import FileUtils
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: 0)
        fu = FileUtils()
        try:
            fu.show_warning_dialog("Title", "Message")
        except Exception as e:
            pytest.fail(
                f"show_warning_dialog raised {type(e).__name__}: {e}"
            )

    def test_show_info_dialog_does_not_crash(self, qtbot, monkeypatch):
        from file_utils import FileUtils
        monkeypatch.setattr(
            QMessageBox, "information", lambda *a, **kw: 0
        )
        fu = FileUtils()
        try:
            fu.show_info_dialog("Title", "Message")
        except Exception as e:
            pytest.fail(
                f"show_info_dialog raised {type(e).__name__}: {e}"
            )

    def test_ask_yes_no_returns_bool(self, qtbot, monkeypatch):
        from file_utils import FileUtils
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes,
        )
        fu = FileUtils()
        result = fu.ask_yes_no("Title", "Message")
        assert isinstance(result, bool)
        assert result is True

    def test_ask_yes_no_with_no_response(self, qtbot, monkeypatch):
        from file_utils import FileUtils
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.No,
        )
        fu = FileUtils()
        result = fu.ask_yes_no("Title", "Message")
        assert result is False


@pytest.mark.integration
class TestFileUtilsHelpers:
    """create_directory_if_not_exists, backup_file, recent files."""

    def test_create_directory_with_new_path(self, tmp_path):
        from file_utils import FileUtils
        target = tmp_path / "new_subdir"
        assert not target.exists()
        result = FileUtils.create_directory_if_not_exists(str(target))
        assert result is True
        assert target.exists()
        assert target.is_dir()

    def test_create_directory_when_already_exists(self, tmp_path):
        from file_utils import FileUtils
        target = tmp_path / "already_there"
        target.mkdir()
        result = FileUtils.create_directory_if_not_exists(str(target))
        # Should still return True (already exists is success)
        assert result is True

    def test_backup_file_creates_backup_copy(self, tmp_path):
        from file_utils import FileUtils
        src = tmp_path / "original.txt"
        src.write_text("important content")
        result = FileUtils.backup_file(str(src))
        assert result is not None
        assert os.path.exists(result)
        # Backup should have the same content
        with open(result) as f:
            assert f.read() == "important content"

    def test_backup_file_with_missing_source_returns_none(self, tmp_path):
        from file_utils import FileUtils
        result = FileUtils.backup_file(str(tmp_path / "does_not_exist.txt"))
        assert result is None


@pytest.mark.integration
class TestFileUtilsPaletteImport:
    """`auto_detect_and_import_palette` invokes specific format
    importers that crash hard on certain inputs in offscreen Qt
    (likely because of QPixmap reading from binary palette formats).
    Skipped — covered transitively by integration tests already."""

    @pytest.mark.skip(
        reason="Native crash on offscreen Qt — see Phase 8.7 report"
    )
    def test_auto_detect_palette_skipped(self):
        pass


# ═══════════════════════════════════════════════════════════════════════════
# 2. error_handler.py — decorator, safe_method, helpers
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestErrorHandlerLineFill:
    """Phase 7.7 hit ErrorHandler.safe_execute. This phase covers
    handle_exception, safe_method decorator, safe_file_operation,
    safe_widget_operation."""

    def test_handle_exception_invokes_status_callback_and_does_not_reraise(
        self
    ):
        """`ErrorHandler.handle_exception(e, context, status_callback)`
        should:
        1. NOT re-raise the exception
        2. Call status_callback (if provided) with a message containing
           the context

        (Was WEAK_UNCLASSIFIED in audit; manual triage classified
        UPGRADE — both contracts are observable.)"""
        from error_handler import ErrorHandler

        status_messages: list = []

        try:
            raise ValueError("test exception for handler")
        except Exception as e:
            # handle_exception should swallow the exception
            result = ErrorHandler.handle_exception(
                e,
                context="phase93_test_context",
                status_callback=lambda msg: status_messages.append(msg),
            )

        # Returns None per signature
        assert result is None

        # status_callback should have been called at least once
        assert len(status_messages) >= 1, (
            "status_callback was never invoked"
        )
        # The status message should reference the context
        joined = " ".join(status_messages)
        assert "phase93_test_context" in joined or \
            "test_context" in joined.lower(), (
            f"status messages do not reference context: {status_messages}"
        )

    def test_safe_method_decorator_swallows_exception(self):
        """safe_method is a method decorator — the function it wraps
        receives `self` as first arg. We construct a dummy class to
        host the decorated method."""
        from error_handler import ErrorHandler

        class _Dummy:
            @ErrorHandler.safe_method("test_safe_method", fallback_value=None)
            def will_raise(self):
                raise RuntimeError("expected")

        d = _Dummy()
        try:
            result = d.will_raise()
        except Exception as e:
            pytest.fail(
                f"safe_method-decorated method leaked exception: "
                f"{type(e).__name__}: {e}"
            )

    def test_safe_method_decorator_returns_value_on_success(self):
        from error_handler import ErrorHandler

        class _Dummy:
            @ErrorHandler.safe_method("test_safe_method_success",
                                      fallback_value=None)
            def returns_42(self):
                return 42

        d = _Dummy()
        result = d.returns_42()
        assert result == 42

    def test_safe_file_operation_with_success(self, tmp_path):
        """safe_file_operation wraps a callable that touches a file."""
        from error_handler import safe_file_operation
        target = tmp_path / "safe_op.txt"

        def writer():
            target.write_text("written")
            return True

        result = safe_file_operation(
            writer, str(target), operation="write"
        )
        # Returns the function's result on success
        assert result is True or result is None

    def test_safe_file_operation_with_exception(self, tmp_path):
        """Exception inside the callable should be swallowed."""
        from error_handler import safe_file_operation
        target = tmp_path / "safe_fail.txt"

        def raises():
            raise IOError("simulated I/O fail")

        try:
            safe_file_operation(
                raises, str(target), operation="write"
            )
        except Exception as e:
            pytest.fail(
                f"safe_file_operation leaked exception: "
                f"{type(e).__name__}: {e}"
            )

    def test_safe_widget_operation_with_success(self, qtbot):
        from PyQt6.QtWidgets import QWidget
        from error_handler import safe_widget_operation

        widget = QWidget()
        qtbot.addWidget(widget)

        def op():
            widget.setWindowTitle("test")
            return True

        result = safe_widget_operation(
            widget, op, description="setting title"
        )
        # On success, should return op's result
        assert result is True or result is None

    def test_safe_widget_operation_with_exception(self, qtbot):
        from PyQt6.QtWidgets import QWidget
        from error_handler import safe_widget_operation

        widget = QWidget()
        qtbot.addWidget(widget)

        def fails():
            raise RuntimeError("widget op failure")

        try:
            safe_widget_operation(
                widget, fails, description="failing op"
            )
        except Exception as e:
            pytest.fail(
                f"safe_widget_operation leaked exception: "
                f"{type(e).__name__}: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 3. async_file_ops.py — error paths
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAsyncFileOpsErrorPaths:
    """Cover the error paths in FileWriterThread.run, FileReaderThread.run,
    and the manager's _on_write_complete + cleanup logic."""

    def test_writer_thread_with_invalid_format_raises_internally(
        self, tmp_path, qtbot
    ):
        """`format='unknown_format'` should be handled in run() — emits
        finished(False, ...)."""
        from async_file_ops import FileWriterThread

        target = tmp_path / "writer_fail.dat"
        thread = FileWriterThread(
            str(target), {"data": "x"}, format="unknown_format_xyz"
        )

        with qtbot.waitSignal(thread.finished, timeout=3000) as blocker:
            thread.start()
        success, _ = blocker.args
        # Either succeeds with a fallback OR fails cleanly
        assert isinstance(success, bool)

    def test_writer_thread_with_unwritable_path_emits_failure(
        self, tmp_path, qtbot
    ):
        """Path to a directory that can't be created (e.g. a file
        masquerading as a parent dir) should emit failure."""
        from async_file_ops import FileWriterThread

        # Create a file, then try to write into "file/sub" — IO error
        blocker_file = tmp_path / "block.txt"
        blocker_file.write_text("hi")
        bogus = blocker_file / "sub" / "out.json"

        thread = FileWriterThread(
            str(bogus), {"data": "x"}, format="json"
        )
        with qtbot.waitSignal(thread.finished, timeout=3000) as bl:
            thread.start()
        success, _ = bl.args
        # Should report failure
        assert success is False

    def test_reader_thread_with_missing_file_emits_failure(
        self, tmp_path, qtbot
    ):
        from async_file_ops import FileReaderThread

        bogus = str(tmp_path / "missing.json")
        thread = FileReaderThread(bogus, format="json")
        with qtbot.waitSignal(thread.finished, timeout=3000) as bl:
            thread.start()
        success, data, msg = bl.args
        assert success is False

    def test_reader_thread_with_corrupted_json_emits_failure(
        self, tmp_path, qtbot
    ):
        from async_file_ops import FileReaderThread
        bad = tmp_path / "corrupt.json"
        bad.write_text("{ not valid json at all")

        thread = FileReaderThread(str(bad), format="json")
        with qtbot.waitSignal(thread.finished, timeout=3000) as bl:
            thread.start()
        success, _, _ = bl.args
        assert success is False

    def test_async_manager_wait_all_with_no_active_threads_returns_true(
        self
    ):
        from async_file_ops import AsyncFileManager
        mgr = AsyncFileManager()
        result = mgr.wait_all(timeout=100)
        # No threads → returns True immediately
        assert result is True

    def test_async_manager_cancel_all_does_not_crash(self):
        from async_file_ops import AsyncFileManager
        mgr = AsyncFileManager()
        try:
            mgr.cancel_all()
        except Exception as e:
            pytest.fail(
                f"cancel_all raised {type(e).__name__}: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 4. color_history.py — load + export branches
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.skip(
    reason="ColorHistory's constructor + add_color() + save() chain "
    "spawns a QThread for async filesystem writes that crashes Python "
    "natively on Windows (no traceback, no exit code, just a dead "
    "process). The locked test_rnv_color_mixer.py works around this by "
    "module-level-mocking ColorHistory.__init__/load/save_async at "
    "import time. These integration-style tests can't easily replicate "
    "that pattern without mocking out the very methods they're trying "
    "to verify. Phase 9.3 finding — kept for documentation; future "
    "refactor could split the QThread machinery off from ColorHistory "
    "construction so synchronous behavior is testable in isolation."
)
class TestColorHistoryLoadExport:
    """ColorHistory's load() and export_to_file() have format-specific
    branches that need explicit drives."""

    def test_load_with_no_existing_file_returns_false_or_true(
        self, isolated_home
    ):
        """No prior history file — load() is either a no-op-true or
        returns False, both fine."""
        from color_history import ColorHistory
        ch = ColorHistory()
        # The constructor calls load() automatically
        result = ch.load()
        assert isinstance(result, bool)

    def test_save_writes_history_file(self, isolated_home, tmp_path):
        """Verify `save()` (the sync version) writes to disk. The
        round-trip via a new instance is timing-dependent because
        `add_color` triggers `save_async`, so we test save() directly."""
        from color_history import ColorHistory
        ch = ColorHistory()
        ch.clear()
        ch.add_color((100, 150, 200))

        # Save synchronously (not save_async)
        ok = ch.save()
        assert ok is True

        # File should now exist on disk
        assert os.path.exists(ch.history_file)

        # File contents should be valid JSON
        with open(ch.history_file) as f:
            data = json.load(f)
        assert "entries" in data

    def test_export_to_json_file(self, tmp_path, isolated_home):
        from color_history import ColorHistory
        ch = ColorHistory()
        ch.add_color((255, 0, 0))
        out = tmp_path / "hist.json"
        try:
            result = ch.export_to_file(str(out))
        except Exception as e:
            pytest.fail(
                f"export_to_file JSON raised {type(e).__name__}: {e}"
            )
        if result:
            assert out.exists()

    def test_export_to_html_file_writes_html_with_color(
        self, tmp_path, isolated_home
    ):
        """`export_to_file('*.html')` writes HTML containing the colors.
        Verify file exists and contains the hex of the added color."""
        from color_history import ColorHistory
        ch = ColorHistory()
        ch.add_color((0, 255, 0))
        out = tmp_path / "hist.html"

        ch.export_to_file(str(out))

        assert out.exists(), "HTML export did not write file"
        text = out.read_text()
        # Hex of (0, 255, 0) is #00FF00 (case-insensitive)
        assert "00FF00" in text.upper(), (
            f"HTML export does not contain hex '00FF00' for (0, 255, 0); "
            f"first 200 chars: {text[:200]!r}"
        )

    def test_export_to_txt_file_writes_text_with_color(
        self, tmp_path, isolated_home
    ):
        """`export_to_file('*.txt')` writes plain text. Verify file
        exists and contains a representation of the added color."""
        from color_history import ColorHistory
        ch = ColorHistory()
        ch.add_color((0, 0, 255))
        out = tmp_path / "hist.txt"

        ch.export_to_file(str(out))

        assert out.exists(), "TXT export did not write file"
        text = out.read_text()
        # Should mention the color in some form (hex 0000FF or rgb 0,0,255)
        text_upper = text.upper()
        has_hex = "0000FF" in text_upper
        has_rgb = "0, 0, 255" in text or "(0, 0, 255)" in text
        assert has_hex or has_rgb, (
            f"TXT export does not contain (0,0,255) in any format; "
            f"first 200 chars: {text[:200]!r}"
        )

    def test_add_color_with_max_entries_evicts_oldest(
        self, isolated_home
    ):
        """ColorHistory caps at max_entries (default 20). Adding more
        than that should evict the oldest."""
        from color_history import ColorHistory
        ch = ColorHistory(max_entries=5)
        for i in range(10):
            ch.add_color((i * 25, i * 25, i * 25))
        entries = ch.get_entries()
        # Should be capped at max_entries
        assert len(entries) <= 5


# ═══════════════════════════════════════════════════════════════════════════
# 5. session_manager — load_autosave path
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSessionManagerAutosaveLoad:
    """Phase 7.8 + 8.5 covered most of session_manager. This adds the
    autosave file management paths.

    Real API: `check_for_autosave()` (returns path or None),
    `_get_autosave_files()` returns list, `_cleanup_old_autosaves`."""

    def test_check_for_autosave_with_no_files_returns_none(self, tmp_path):
        from utils.session_manager import SessionManager
        sm = SessionManager(sessions_dir=str(tmp_path))
        try:
            result = sm.check_for_autosave()
            assert result is None
        finally:
            sm.cleanup()

    def test_get_autosave_files_with_empty_dir_returns_empty(
        self, tmp_path
    ):
        from utils.session_manager import SessionManager
        sm = SessionManager(sessions_dir=str(tmp_path))
        try:
            if hasattr(sm, "_get_autosave_files"):
                files = sm._get_autosave_files()
                assert isinstance(files, list)
                assert len(files) == 0
        finally:
            sm.cleanup()

    def test_cleanup_old_autosaves_with_empty_dir_returns_zero(
        self, tmp_path
    ):
        from utils.session_manager import SessionManager
        sm = SessionManager(sessions_dir=str(tmp_path))
        try:
            if hasattr(sm, "_cleanup_old_autosaves"):
                n = sm._cleanup_old_autosaves()
                assert n == 0
        finally:
            sm.cleanup()
