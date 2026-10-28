"""The history records the mixes that follow something the user did.

Ruling 103 A, 2026-10-27.

WHAT WAS THERE. As it starts, the app mixes its slots: the mix debounce
(100 ms) runs once on the slots it has just built, and the mix went into the
history as if the user had made it. Every launch added the default slots'
gray. Three launches in a fresh home left three entries of it, so the History
tab's empty line was never seen in use, and the history filled with a color
nobody mixed. A session restored at startup was recorded again the same way:
the crash-recovery offer answered Yes, or Auto-load last session. Its mixes
are in the history already, from when they were made. Found on 27 October,
from a test race on Chris's Windows run (tests/test_empty_history_line_draws.py).

WHAT IS THERE NOW. A change made while the app starts, or while it restores a
session at startup, schedules a mix the history does not record. A change
after that is the user's, and its mix is recorded, as before, when Enable
color history and Auto-save mixed colors are on.

Each test launches the app the way a person does, in a home of its own
(tests/conftest.py, isolated_home).
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QMessageBox

from tests.test_settings_that_act import (SESSION_SLOTS, _launch, _record_session,
                                          _slot_state, _write_settings)

pytestmark = pytest.mark.integration

#: Long enough for everything a launch schedules: the mix debounce (100 ms)
#: and the startup restore (500 ms).
SETTLE_MS = 900

#: A color a user picks, and its slot weight.
PICKED = ((40, 90, 200), 60)


def _entries(win) -> list:
    return [tuple(e.color) for e in win.color_history.get_entries()]


@pytest.fixture
def answer_yes(monkeypatch):
    """Answer every question Yes, and every notice OK. Record the titles."""
    shown: list[str] = []

    def box(answer):
        def show(parent, title, *args, **kwargs):
            shown.append(title)
            return answer
        return staticmethod(show)

    monkeypatch.setattr(QMessageBox, "question", box(QMessageBox.StandardButton.Yes))
    monkeypatch.setattr(QMessageBox, "information", box(0))
    monkeypatch.setattr(QMessageBox, "warning", box(0))
    return shown


def test_launches_add_nothing_to_the_history(isolated_home, qtbot, main_module):
    first = _launch(main_module, qtbot, wait_ms=SETTLE_MS)
    assert first.current_mixed_color, "the launch mixed nothing: nothing was tested"
    assert _entries(first) == [], f"the first launch recorded {_entries(first)}"
    first.close()
    second = _launch(main_module, qtbot, wait_ms=SETTLE_MS)
    try:
        assert _entries(second) == [], f"two launches left {_entries(second)} in the history"
    finally:
        second.close()


def test_a_session_auto_loaded_at_startup_is_not_recorded(isolated_home, qtbot, main_module, answer_yes):
    _record_session(isolated_home)
    _write_settings(isolated_home, preferences={"auto_load_last_session": True})
    win = _launch(main_module, qtbot, wait_ms=SETTLE_MS)
    try:
        assert _slot_state(win) == SESSION_SLOTS, "the session was not loaded: nothing was tested"
        assert _entries(win) == [], f"the auto-loaded session's mix was recorded: {_entries(win)}"
    finally:
        win.close()


def test_a_session_recovered_at_startup_is_not_recorded_again(isolated_home, qtbot, main_module,
                                                               answer_yes):
    """A run ends without closing, holding a mix the user made; the next launch
    offers recovery, answered Yes. The recovered mix is shown and not added:
    the history recorded it when it was made. (Each launch here starts with
    a history of its own, tests/conftest.py, so the second launch's history
    is compared before and after the recovery.)"""
    first = _launch(main_module, qtbot, wait_ms=SETTLE_MS)
    first.slots[0].set_color(PICKED[0])
    first.slots[0].set_weight(PICKED[1])
    qtbot.wait(400)
    assert len(_entries(first)) == 1, f"the user's mix was not recorded: {_entries(first)}"
    first.session_manager._autosave()            # what the 60 s timer does
    # The process dies here: no closeEvent, so the recovery flag stays.
    second = _launch(main_module, qtbot)
    before = _entries(second)
    qtbot.wait(SETTLE_MS)
    try:
        assert "Recover Previous Session?" in answer_yes, "no recovery was offered: nothing was tested"
        assert second.current_mixed_color == first.current_mixed_color, "the session was not recovered"
        assert _entries(second) == before, f"the recovered mix was recorded again: {_entries(second)}"
    finally:
        second.close()
        first.close()


def test_a_change_after_the_launch_is_recorded(isolated_home, qtbot, main_module):
    win = _launch(main_module, qtbot, wait_ms=SETTLE_MS)
    try:
        win.slots[0].set_color(PICKED[0])
        qtbot.wait(400)
        assert len(_entries(win)) == 1, f"the user's change was not recorded: {_entries(win)}"
    finally:
        win.close()


def test_a_change_while_the_startup_mix_is_pending_is_recorded(isolated_home, qtbot, main_module):
    """The user's change wins over the quiet startup mix it overtakes: the one
    mix that runs follows something the user did."""
    win = _launch(main_module, qtbot)
    try:
        assert win._mix_debounce_timer.isActive(), "the startup mix already ran: nothing was tested"
        win.slots[0].set_color(PICKED[0])
        qtbot.wait(SETTLE_MS)
        assert len(_entries(win)) == 1, f"the user's change was not recorded: {_entries(win)}"
    finally:
        win.close()
