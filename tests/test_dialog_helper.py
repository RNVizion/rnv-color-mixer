"""
RNV Color Mixer — DialogHelper Tests  (Phase 7.9 deliverable)
================================================================

`utils.dialog_helper.DialogHelper` is a centralized wrapper around
`QMessageBox` for consistent error/warning/info/confirmation dialogs
across the app. Every method calls `msg_box.exec()` (modal), so the
whole module sits at 0% coverage in the offscreen test environment.

This phase pushes the module past 60% by monkeypatching `QMessageBox.exec`
to return specific button values, simulating user clicks without showing
any UI. Same pattern used in Phase 7.1 for QColorDialog and Phase 7.2 for
QFileDialog.

The pattern: pick the OUTERMOST modal entry point and mock it. We don't
mock `QMessageBox` itself because the helpers need to construct it,
inspect properties (icon, title, etc.), and call set* methods. We just
short-circuit `exec()`.

Methods covered
---------------
- show_error / show_warning / show_info — return None, just exec'd
- confirm — returns bool based on Yes/No exec result
- ask_yes_no_cancel — returns DialogResult enum
- show_about — uses QMessageBox.about (different API path)
- show_custom — returns the clicked StandardButton

Module-level convenience aliases (`error`, `warning`, `info`, `confirm`)
are also tested via one smoke test each — they delegate to DialogHelper.
"""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QMessageBox

from dialog_helper import DialogHelper, DialogResult


# ═══════════════════════════════════════════════════════════════════════════
# Common patch helper
# ═══════════════════════════════════════════════════════════════════════════

def _patch_exec(monkeypatch, return_value):
    """Make every QMessageBox in `dialog_helper` return the given value
    from exec() without actually showing a dialog.

    Replacing QMessageBox.exec via setattr crashes Qt's C++ side. Instead
    we substitute a fake QMessageBox class in the dialog_helper module's
    namespace — DialogHelper imports `from PyQt6.QtWidgets import QMessageBox`,
    so swapping the module attribute redirects construction to our stub.

    `return_value` should be a `QMessageBox.StandardButton` enum.
    """
    import dialog_helper as dh

    class _FakeMsgBox:
        # Class-level attributes mirror the real QMessageBox enums we use
        Icon = QMessageBox.Icon
        StandardButton = QMessageBox.StandardButton

        def __init__(self, parent=None):
            self.parent = parent
            self._title = ""
            self._text = ""
            self._icon = None
            self._buttons = None
            self._default_button = None
            self._detailed_text = None

        # All the setter methods the helpers call — make them no-ops
        def setIcon(self, icon): self._icon = icon
        def setWindowTitle(self, t): self._title = t
        def setText(self, t): self._text = t
        def setStandardButtons(self, b): self._buttons = b
        def setDefaultButton(self, b): self._default_button = b
        def setDetailedText(self, t): self._detailed_text = t

        def exec(self):
            return return_value

        # Mirror static method `about` — write to a sink the test can read
        @staticmethod
        def about(parent, title, message):
            _FakeMsgBox._about_calls.append((title, message))

    _FakeMsgBox._about_calls = []
    monkeypatch.setattr(dh, "QMessageBox", _FakeMsgBox)
    return _FakeMsgBox


# ═══════════════════════════════════════════════════════════════════════════
# 1. DialogResult enum (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestDialogResultEnum:
    def test_dialog_result_has_all_four_values(self):
        """Catches accidental rename or removal."""
        assert DialogResult.YES.value == 1
        assert DialogResult.NO.value == 2
        assert DialogResult.CANCEL.value == 3
        assert DialogResult.OK.value == 4


# ═══════════════════════════════════════════════════════════════════════════
# 2. show_error (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestShowError:
    def test_show_error_with_default_title(self, monkeypatch):
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        # No exception, no return value (returns None)
        result = DialogHelper.show_error(None, "Something broke")
        assert result is None

    def test_show_error_with_detailed_text(self, monkeypatch):
        """The detailed_text branch is a separate code path."""
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        result = DialogHelper.show_error(
            None, "Failed", title="Custom Error",
            detailed_text="Stack trace would go here",
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# 3. show_warning + show_info (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestShowWarningAndInfo:
    def test_show_warning_does_not_crash(self, monkeypatch):
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        DialogHelper.show_warning(None, "This is a warning")

    def test_show_info_with_custom_title(self, monkeypatch):
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        DialogHelper.show_info(None, "Heads up", title="Notice")


# ═══════════════════════════════════════════════════════════════════════════
# 4. confirm (3 tests — the most important path)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestConfirm:
    """`confirm` returns True iff exec returned StandardButton.Yes.
    Every other case returns False."""

    def test_confirm_yes_click_returns_true(self, monkeypatch):
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Yes)
        assert DialogHelper.confirm(None, "Are you sure?") is True

    def test_confirm_no_click_returns_false(self, monkeypatch):
        _patch_exec(monkeypatch, QMessageBox.StandardButton.No)
        assert DialogHelper.confirm(None, "Are you sure?") is False

    def test_confirm_with_default_yes_branch(self, monkeypatch):
        """The default_yes=True parameter takes a different branch in the
        body (`setDefaultButton`). Verify it doesn't change the return."""
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Yes)
        assert DialogHelper.confirm(
            None, "Are you sure?", default_yes=True
        ) is True


# ═══════════════════════════════════════════════════════════════════════════
# 5. ask_yes_no_cancel (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAskYesNoCancel:
    def test_yes_returns_dialog_result_yes(self, monkeypatch):
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Yes)
        assert DialogHelper.ask_yes_no_cancel(
            None, "Save?"
        ) == DialogResult.YES

    def test_no_returns_dialog_result_no(self, monkeypatch):
        _patch_exec(monkeypatch, QMessageBox.StandardButton.No)
        assert DialogHelper.ask_yes_no_cancel(
            None, "Save?"
        ) == DialogResult.NO

    def test_cancel_returns_dialog_result_cancel(self, monkeypatch):
        """Cancel button OR any unrecognised result falls through to
        the CANCEL branch."""
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Cancel)
        assert DialogHelper.ask_yes_no_cancel(
            None, "Save?"
        ) == DialogResult.CANCEL


# ═══════════════════════════════════════════════════════════════════════════
# 6. show_about (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestShowAbout:
    def test_show_about_constructs_html_message(self, monkeypatch):
        """`show_about` uses `QMessageBox.about(parent, title, message)`,
        a static method. Our fake captures these calls in `_about_calls`."""
        fake = _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)

        DialogHelper.show_about(
            None,
            app_name="Color Mixer",
            version="3.3.3",
            description="Professional color mixing tool",
            copyright_info="© 2026",
        )

        assert len(fake._about_calls) == 1
        title, message = fake._about_calls[0]
        assert "Color Mixer" in title
        assert "Color Mixer" in message
        assert "3.3.3" in message
        assert "Professional" in message

    def test_show_about_without_copyright_info(self, monkeypatch):
        """Optional copyright_info branch."""
        fake = _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        DialogHelper.show_about(
            None,
            app_name="X",
            version="1.0",
            description="Test",
        )
        assert len(fake._about_calls) == 1


# ═══════════════════════════════════════════════════════════════════════════
# 7. show_custom (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestShowCustom:
    def test_show_custom_returns_clicked_button(self, monkeypatch):
        """show_custom returns whatever exec() returned."""
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Yes)
        result = DialogHelper.show_custom(
            None,
            title="Custom",
            message="Choose",
            icon=QMessageBox.Icon.Question,
            buttons=(QMessageBox.StandardButton.Yes
                     | QMessageBox.StandardButton.No),
        )
        # exec returned Yes — show_custom passes it through
        assert result == QMessageBox.StandardButton.Yes

    def test_show_custom_with_default_button_and_detailed_text(
        self, monkeypatch
    ):
        """Two optional branches: setDefaultButton and setDetailedText."""
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        result = DialogHelper.show_custom(
            None,
            title="Detail",
            message="Top message",
            default_button=QMessageBox.StandardButton.Ok,
            detailed_text="Long stack trace",
        )
        assert result == QMessageBox.StandardButton.Ok


# ═══════════════════════════════════════════════════════════════════════════
# 8. Module-level convenience aliases (4 tests, one per alias)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestModuleLevelAliases:
    """`error()`, `warning()`, `info()`, `confirm()` at module level
    delegate to DialogHelper. Each is a one-liner, but uncovered."""

    def test_module_level_error_alias_works(self, monkeypatch):
        from dialog_helper import error
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        error(None, "alias test")  # No return value

    def test_module_level_warning_alias_works(self, monkeypatch):
        from dialog_helper import warning
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        warning(None, "alias test")

    def test_module_level_info_alias_works(self, monkeypatch):
        from dialog_helper import info
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Ok)
        info(None, "alias test")

    def test_module_level_confirm_alias_returns_bool(self, monkeypatch):
        from dialog_helper import confirm
        _patch_exec(monkeypatch, QMessageBox.StandardButton.Yes)
        assert confirm(None, "alias test") is True
